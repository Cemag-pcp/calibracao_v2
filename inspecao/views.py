from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required

from cadastro.models import InfoInstrumento, Operadores, DesignarInstrumento, Funcionario
from inspecao.models import Laboratorio, Envio, AnaliseCertificado, PontoCalibracao, Versao
from ficha.models import AssinaturaInstrumento, StatusInstrumento
from cadastro.utils import *

import json
from datetime import datetime

@login_required
def enviar_view(request):
    with transaction.atomic():
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                
                laboratorio = int(data.get('laboratorio'))
                data_envio = data.get('dataEnvio')
                responsavel_envio = int(data.get('responsavelEnvio'))
                natureza = data.get('natureza')
                metodo = data.get('metodo')
                tag = data.get('tag-instrumento-envio')
                validacao_de_substituicao = data.get('validacao-de-substituicao')
                instrumento_substituira_envio = data.get('instrumento-substituira-envio')
                
                responsavel_envio_object = get_object_or_404(Operadores, pk=responsavel_envio)
                laboratorio_object = get_object_or_404(Laboratorio, pk=laboratorio)
                instrumento_object = get_object_or_404(InfoInstrumento, tag=tag)

                designicao = DesignarInstrumento.objects.filter(instrumento_escolhido=instrumento_object).first()

                if designicao:
                    designicao.delete()

                if validacao_de_substituicao == 'Sim':

                    novo_instrumento = InfoInstrumento.objects.filter(id=instrumento_substituira_envio).first()
                    funcionario = Funcionario.objects.filter(id=designicao.responsavel.id).first()

                    ultima_assinatura = AssinaturaInstrumento.objects.filter(assinante=funcionario).order_by('-data_assinatura').first()
                    foto_assinatura = ultima_assinatura.foto_assinatura if ultima_assinatura else None

                    # Criar AssinaturaInstrumento
                    AssinaturaInstrumento.objects.create(
                        instrumento=novo_instrumento,
                        assinante=funcionario,
                        foto_assinatura=foto_assinatura,
                        motivo='Entrega',
                        data_entrega=data_envio
                    )

                    descricao = f"Atribuindo a responsabilidade para: {funcionario.matricula} - {funcionario.nome} na data {data_envio}"
                    registrar_primeiro_responsavel(novo_instrumento, descricao)

                    DesignarInstrumento.objects.create(
                        instrumento_escolhido=novo_instrumento,
                        responsavel=funcionario,
                        data_entrega_funcionario=data_envio
                    )

                    StatusInstrumento.objects.create(
                        funcionario=funcionario,
                        instrumento=instrumento_object,
                        motivo='substituição',
                        data_entrega=data_envio,
                        observacoes='calibração'
                    )

                elif validacao_de_substituicao == 'Não' and designicao != None:

                    funcionario = Funcionario.objects.filter(id=designicao.responsavel.id).first()

                    ultima_assinatura = AssinaturaInstrumento.objects.filter(assinante=funcionario).order_by('-data_assinatura').first()
                    foto_assinatura = ultima_assinatura.foto_assinatura if ultima_assinatura else None

                    StatusInstrumento.objects.create(
                        funcionario=funcionario,
                        instrumento=instrumento_object,
                        motivo='devolução',
                        data_entrega=data_envio,
                        observacoes='calibração'
                    )

                    descricao = f"Instrumento: {instrumento_object.tag} - Devolvido pelo funcionário: {funcionario} - na data {data_envio}"
                    registrar_instrumento_devolucao(instrumento_object, descricao)

                # Buscar todos os pontos de calibração relacionados
                pontos_calibracao = instrumento_object.pontos_calibracao.filter(status_ponto_calibracao='ativo')

                if not pontos_calibracao.exists():
                    return JsonResponse({'status': 'error', 'message': 'Nenhum ponto de calibração encontrado para este instrumento.'}, status=400)

                # Processar cada ponto de calibração
                for ponto in pontos_calibracao:
                    status_atual = Envio.objects.filter(instrumento=instrumento_object, ponto_calibracao=ponto).order_by('-id').first()

                    if status_atual and status_atual.status == 'enviado':
                        return JsonResponse({'status': 'error', 'message': f'Instrumento já enviado para o ponto {ponto.descricao}!'}, status=400)

                    Envio.objects.create(
                        ponto_calibracao=ponto,
                        instrumento=instrumento_object,
                        laboratorio=laboratorio_object,
                        data_envio=data_envio,
                        responsavel_envio=responsavel_envio_object,
                        natureza=natureza,
                        metodo=metodo,
                        status='enviado'
                    )

                    if laboratorio_object.nome == 'N/A':
                        descricao = f'Instrumento enviado para calibração no ponto {ponto.descricao} no dia {data_envio}.\n Instrumento novo com certificado'
                    else:    
                        descricao = f'Instrumento enviado para calibração no ponto {ponto.descricao} no dia {data_envio}.\nLaboratório responsável: {laboratorio_object}'

                    registrar_envio_calibracao(instrumento_object, ponto, descricao)

                return JsonResponse({'status': 'success', 'message': 'Instrumento enviado para calibração em todos os pontos!'}, status=200)
            except Exception as e:
                return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@login_required
def receber_view(request):
        
    if request.method == 'POST':

        with transaction.atomic():
            try:
                # Parse do corpo da requisição
                data = json.loads(request.body)

                # Validação dos campos recebidos
                id_envios = json.loads(data.get('id-instrumento-recebimento'))

                if not id_envios:
                    return JsonResponse({'status': 'error', 'message': 'ID do envio não fornecido'}, status=400)
                
                # Verifica se id_envios é uma lista, caso contrário, retorna erro
                if not isinstance(id_envios, list):
                    return JsonResponse({'status': 'error', 'message': 'id-instrumento-recebimento deve ser uma lista.'}, status=400)

                data_recebimento_str  = data.get('dataRecebimento')
                if not data_recebimento_str:
                    return JsonResponse({'status': 'error', 'message': 'Data de recebimento não fornecida'}, status=400)

                try:
                    # Converte a string em objeto datetime.date
                    data_recebimento = datetime.strptime(data_recebimento_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

                obs_recebimento = data.get('obsRecebimento', '')  # Observação pode ser opcional
                link_certificado = data.get('linkCertificado', None)  # Link pode ser opcional

                # Itera sobre a lista de IDs de envio
                for id_envio in id_envios:
                    # Busca o objeto Envio
                    envio_object = get_object_or_404(Envio, pk=int(id_envio))

                    if envio_object.status == 'recebido' and envio_object.ponto_calibracao.status_ponto_calibracao == 'inativo':
                        continue
                    elif envio_object.status == 'recebido':
                        return JsonResponse({'status': 'error', 'message': f'Instrumento com ID {id_envio} já foi recebido!'}, status=400)

                    # Atualiza os dados do envio
                    envio_object.data_retorno = data_recebimento
                    envio_object.observacoes = obs_recebimento
                    envio_object.pdf = link_certificado
                    envio_object.status = 'recebido'
                    envio_object.save()

                    envio_object.calcular_proxima_calibracao()

                    # Registra o recebimento da calibração
                    if envio_object.laboratorio.nome == 'N/A':
                        descricao = f'Instrumento no ponto {envio_object.ponto_calibracao}. Instrumento novo com certificado recebido no dia {data_recebimento}. <a href="{link_certificado}" target="_blank">Link do Certificado</a>'
                    else:
                        descricao = f'Instrumento no ponto {envio_object.ponto_calibracao}, recebido do laboratório {envio_object.laboratorio} dia {data_recebimento}. <a href="{link_certificado}" target="_blank">Link do Certificado</a>'

                    registrar_recebimento_calibracao(envio_object.instrumento, envio_object.ponto_calibracao, descricao)

                return JsonResponse({'status': 'success', 'message': 'Instrumentos recebidos com sucesso'}, status=200)

            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)

            except Exception as e:
                return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@login_required
def analisar_view(request):
    if request.method == 'POST':
        with transaction.atomic():
            try:
                # Parse do corpo da requisição
                data = json.loads(request.body)

                # Validação dos campos recebidos
                id_envio = data.get('id-instrumento-analise')
                if not id_envio:
                    return JsonResponse({'status': 'error', 'message': 'ID do envio não fornecido'}, status=400)

                data_analise_str = data.get('dataAnalise')
                if not data_analise_str:
                    return JsonResponse({'status': 'error', 'message': 'Data de análise não fornecida'}, status=400)

                try:
                    # Converte a string em objeto datetime.date
                    data_analise = datetime.strptime(data_analise_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

                incerteza_analise = float(data.get('incertezaAnalise'))  # Valor padrão como 0
                tendencia_analise = float(data.get('tendenciaAnalise'))  # Valor padrão como 0
                resultado_analise = data.get('resultadoAnalise')
                responsavel_analise = data.get('responsavelAnalise')

                if not resultado_analise or not responsavel_analise:
                    return JsonResponse({'status': 'error', 'message': 'Dados incompletos na análise'}, status=400)

                # Busca o objeto responsável
                responsavel_analise_object = get_object_or_404(Operadores, pk=int(responsavel_analise))

                # Busca o objeto Envio
                envio_object = get_object_or_404(Envio, pk=int(id_envio))

                # Atualiza os dados do envio
                envio_object.analise = True
                envio_object.save()

                # Cria análise de certificado
                AnaliseCertificado.objects.create(
                    envio=envio_object,
                    analise_certificado=resultado_analise,
                    incerteza=incerteza_analise,
                    tendencia=tendencia_analise,  # Corrigido o campo
                    data_analise=data_analise,
                    responsavel_analise=responsavel_analise_object
                )

                descricao=f'Instrumento no ponto {envio_object.ponto_calibracao} foi analisado por {responsavel_analise_object} dia {data_analise}.\nResultado da análise: {resultado_analise}.'
                registrar_analise_ponto(envio_object.instrumento, envio_object.ponto_calibracao, descricao)

                return JsonResponse({'status': 'success', 'message': 'Análise realizada com sucesso'}, status=200)

            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Erro inesperado: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@login_required
def info_instrumento(request,pk_ponto,id_envio):

    ponto_calibracao_object = get_object_or_404(PontoCalibracao, pk=pk_ponto)
    
    faixa_nominal = ponto_calibracao_object.faixa_nominal
    tol_admissivel = ponto_calibracao_object.tolerancia_admissivel

    envio_object = get_object_or_404(Envio, pk=id_envio)
    certificado = envio_object.pdf

    print(certificado)

    info = [{
        'faixa_nominal':faixa_nominal,
        'tol_admissivel':tol_admissivel if tol_admissivel else None,
        'certificado':certificado
    }]

    return JsonResponse({'info':info})

@login_required
def info_instrumento_ultima_analise(request,pk_ponto,id_envio):

    ponto_calibracao_object = get_object_or_404(PontoCalibracao, pk=pk_ponto)
    
    faixa_nominal = ponto_calibracao_object.faixa_nominal
    tol_admissivel = ponto_calibracao_object.tolerancia_admissivel
    unidade = ponto_calibracao_object.unidade

    envio = Envio.objects.filter(ponto_calibracao_id=pk_ponto).order_by('-id').first()
    # envio = get_object_or_404(Envio, ponto_calibracao_id=pk_ponto)

    print(envio)

    # Obtém a análise de certificado relacionada ao envio
    analise_certificado = AnaliseCertificado.objects.filter(envio=envio).order_by('-id').first()

    if not analise_certificado:
        envio_anterior = Envio.objects.filter(ponto_calibracao_id=pk_ponto).order_by('-id')  # Ordene pela coluna desejada
        penultimo_envio = envio_anterior[1]
        analise_certificado = AnaliseCertificado.objects.filter(envio=penultimo_envio).first()

    info = [{
        'ponto_calibracao': {
            'faixa_nominal':faixa_nominal,
            'tol_admissivel':tol_admissivel if tol_admissivel else None,
            'unidade':unidade,
        },
        'analise_certificado': {
            'analise_certificado': analise_certificado.analise_certificado,
            'incerteza': analise_certificado.incerteza,
            'tendencia': analise_certificado.tendencia,
            'responsavel_analise': analise_certificado.responsavel_analise.id if analise_certificado.responsavel_analise else None,
            'data_analise': analise_certificado.data_analise,
        },
        'pdf': envio.pdf
    }]

    return JsonResponse({'info':info})

@login_required
def versoes(request):

    versao = Versao.objects.all()

    return render(request, "versoes.html", {
        "versoes": versao
    })