from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from django.core.files.base import ContentFile

from inspecao.models import Envio, Laboratorio, AnaliseCertificado
from ficha.models import AssinaturaInstrumento, StatusInstrumento
from .models import InfoInstrumento, HistoricoInstrumento, Funcionario, DesignarInstrumento, Operadores, PontoCalibracao
from cadastro.utils import *
from django.http import HttpResponse, JsonResponse

from datetime import datetime
import json
import base64
import uuid

def instrumento_detail(request, pk):
    instrumento = get_object_or_404(InfoInstrumento, pk=pk)
    calibracoes = instrumento.envios.all()

    # Obtendo o último responsável pelo instrumento
    ultimo_responsavel = instrumento.designar_instrumento.order_by('-data_entrega_funcionario').first()

    return render(request, 'instrumento_detail.html', {
        'instrumento': instrumento,
        'calibracoes': calibracoes,
        'ultimo_responsavel': ultimo_responsavel,
    })

def home(request):
    
    laboratorios = Laboratorio.objects.filter(status='ativo')
    operadores = Operadores.objects.filter(status='ativo')
    naturezas = Envio.NATUREZA_CHOICES
    metodos = Envio.METODO_CHOICES
    motivos = AssinaturaInstrumento.STATUS_CHOICES
    funcionarios = Funcionario.objects.all()
    instrumento = InfoInstrumento.objects.all()

    return render(request, "home.html", {'laboratorios':laboratorios,
                                         'operadores':operadores,
                                         'naturezas':naturezas,
                                         'metodos':metodos,
                                         'funcionarios':funcionarios,
                                         'motivos':motivos,
                                         'instrumentos':instrumento})

def instrumentos_data(request):

    hoje = datetime.now().date()

    # Coleta os instrumentos
    instrumentos = InfoInstrumento.objects.all()

    # Processar os dados para DataTable
    instrumentos_detalhes = {}
    for instrumento in instrumentos:

        # Adiciona os detalhes dos pontos de calibração
        pontos_calibracao = instrumento.pontos_calibracao.all()  # Obtém todos os pontos relacionados ao instrumento

        # Obtém a última assinatura do instrumento
        ultima_assinatura = AssinaturaInstrumento.objects.filter(instrumento=instrumento).order_by('-data_assinatura').first()
        ultimo_assinante = ultima_assinatura.assinante if ultima_assinatura else None

        for ponto in pontos_calibracao:
            # Obtém o último envio específico para o ponto de calibração
            ultimo_envio = Envio.objects.filter(instrumento=instrumento, ponto_calibracao=ponto).order_by('-id').first()

            proxima_calibracao = instrumento.proxima_calibracao  # Usando a data de calibração do instrumento

            # Busca o último certificado associado ao envio
            analise_certificado = AnaliseCertificado.objects.filter(envio=ultimo_envio).first()

            if ultimo_envio:
                if ultimo_envio.status == 'enviado':
                    status_calibracao = 'Em calibração'
                    proxima_calibracao = 'Aguardando retornar'
                else:
                    if proxima_calibracao and proxima_calibracao >= hoje:
                        dias_para_vencer = (proxima_calibracao - hoje).days
                        status_calibracao = f'Em dia, faltam {dias_para_vencer} dias'
                    elif proxima_calibracao:
                        dias_atrasado = (hoje - proxima_calibracao).days
                        status_calibracao = f'Atrasado há {dias_atrasado} dias'
                    else:
                        status_calibracao = 'Sem próxima calibração definida'
            else:
                if proxima_calibracao and proxima_calibracao >= hoje:
                    dias_para_vencer = (proxima_calibracao - hoje).days
                    status_calibracao = f'Em dia, faltam {dias_para_vencer} dias'
                elif proxima_calibracao:
                    dias_atrasado = (hoje - proxima_calibracao).days
                    status_calibracao = f'Atrasado há {dias_atrasado} dias'
                else:
                    status_calibracao = 'Sem próxima calibração definida'

            designacao = DesignarInstrumento.objects.filter(instrumento_escolhido=instrumento).first()

            if designacao and designacao.responsavel:
                responsavel_id = designacao.responsavel.id
                responsavel = f"{designacao.responsavel.matricula} - {designacao.responsavel.nome}"
                responsavel_data_entrega = designacao.data_entrega_funcionario
            else:
                responsavel = None
                responsavel_id = None
                responsavel_data_entrega = None

            # Agrupar os dados por TAG
            if instrumento.tag not in instrumentos_detalhes:
                instrumentos_detalhes[instrumento.tag] = {
                    'id': instrumento.id,
                    'tag': instrumento.tag,
                    'tipo_instrumento': instrumento.tipo_instrumento.nome,
                    'marca': instrumento.marca.nome,
                    'status_instrumento': instrumento.status_instrumento,
                    'ultima_calibracao': instrumento.ultima_calibracao,
                    'proxima_calibracao': proxima_calibracao,
                    'status_calibracao_string': status_calibracao,
                    'status_calibracao': ultimo_envio.status if ultimo_envio else None,
                    'tempo_calibracao': instrumento.tempo_calibracao,
                    'responsavel': {'id': responsavel_id, 'matriculaNome': responsavel, 'dataEntrega': responsavel_data_entrega},
                    'ultimo_assinante': {
                        'nome': ultimo_assinante.nome if ultimo_assinante else None,
                        'id': ultimo_assinante.id if ultimo_assinante else None
                    },
                    'pontos_calibracao': []
                }

            # Adiciona os detalhes dos pontos ao agrupamento da tag
            instrumentos_detalhes[instrumento.tag]['pontos_calibracao'].append({
                'ultimo_envio_pk': ultimo_envio.pk if ultimo_envio else None,
                'ponto_pk': ponto.pk,
                'ponto_descricao': ponto.descricao,
                'ponto_faixa_nominal': ponto.faixa_nominal,
                'ponto_unidade': ponto.unidade,
                'ponto_tolerancia_admissivel': ponto.tolerancia_admissivel,
                'status_ponto_calibracao': ponto.status_ponto_calibracao,
                'ultimo_certificado': analise_certificado.analise_certificado if analise_certificado else None,
                'analise_certificado': analise_certificado.analise_certificado if analise_certificado else None,
                'ultimo_pdf': ultimo_envio.pdf if ultimo_envio else None,
            })

    # Paginação
    page = int(request.GET.get('start', 0)) // int(request.GET.get('length', 10)) + 1
    limit = int(request.GET.get('length', 10))
    paginator = Paginator(list(instrumentos_detalhes.values()), limit)

    try:
        instrumentos_page = paginator.page(page)
    except EmptyPage:
        instrumentos_page = []

    # Formato esperado pelo DataTable
    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(instrumentos_page),
    }

    return JsonResponse(data)

def designar_instrumentos(request):
    if request.method == 'POST':
        with transaction.atomic():
            try:
                data = json.loads(request.body)
                
                funcionario_id = data.get('funcionario-designar-varios-instrumentos')
                instrumentos_ids = list(set(data.get('instrumentos', [])))
                assinatura_base64 = data.get('signature')
                data_entrega = data.get('data-designar-varios-instrumentos')

                if not funcionario_id or not instrumentos_ids or not assinatura_base64 or not data_entrega:
                    return JsonResponse({"sucesso": False, "erro": "Dados incompletos"}, status=400)

                funcionario = Funcionario.objects.get(id=funcionario_id)

                data_entrega = datetime.fromisoformat(data_entrega).date()

                format, imgstr = assinatura_base64.split(';base64,') 
                ext = format.split('/')[-1]  # Extensão do arquivo, como 'png', 'jpg', etc.
                
                # Gerar um UUID para o nome do arquivo
                file_name = f"{uuid.uuid4()}.{ext}"

                # Criar o arquivo a partir da string base64
                assinatura_path = ContentFile(base64.b64decode(imgstr), name=file_name)

                for instrumento_id in instrumentos_ids:
                    instrumento = InfoInstrumento.objects.get(id=instrumento_id)

                    # Criar a designação do instrumento com a data especificada
                    DesignarInstrumento.objects.create(
                        instrumento_escolhido=instrumento,
                        responsavel=funcionario,
                        data_entrega_funcionario=data_entrega
                    )

                    # Criar a assinatura associada
                    AssinaturaInstrumento.objects.create(
                        instrumento=instrumento,
                        assinante=funcionario,
                        foto_assinatura=assinatura_path,
                        data_entrega=data_entrega,
                        motivo='Entrega'
                    )

                    descricao = f"Atribuindo a responsabilidade para: {funcionario.matricula} - {funcionario.nome} na data {data_entrega}"
                    registrar_primeiro_responsavel(instrumento, descricao)

                return JsonResponse({"sucesso": True})
            
            except Exception as e:
                return JsonResponse({"sucesso": False, "erro": str(e)}, status=500)
        
    elif request.method == 'GET':
        # Deve pegar todos os instrumentos que não possui designação
        enviados_instrument_ids = Envio.objects.filter(status='enviado').values_list('instrumento_id', flat=True)
        instrumentos = InfoInstrumento.objects.exclude(designar_instrumento__isnull = False).exclude(id__in=enviados_instrument_ids).filter(status_instrumento='ativo')
        instrumentos_data = list(instrumentos.values('id', 'tag'))

        return JsonResponse({"sucesso": True, "instrumentos": instrumentos_data})

def qrcode_view(request, tag):

    instrumento = InfoInstrumento.objects.get(tag=tag)
    return JsonResponse({'qrcode_url': instrumento.qrcode.url})

def historico_view(request, tag, pk_ponto):

    instrumento_object=get_object_or_404(InfoInstrumento, tag=tag)
    ponto_calibracao_object=get_object_or_404(PontoCalibracao, pk=pk_ponto)

    historico_objects = HistoricoInstrumento.objects.filter(
        Q(instrumento=instrumento_object) & (Q(ponto_calibracao=ponto_calibracao_object) | Q(ponto_calibracao=None))
    )

    # Constrói a lista de históricos com informações sobre o ponto de calibração
    historico = [
        {
            "data": historico_item.data_mudanca.strftime('%Y-%m-%d'),
            "descricao": historico_item.descricao_mudanca or "Mudança registrada sem descrição detalhada.",
            "tipo": historico_item.get_tipo_mudanca_display(),
        }
        for historico_item in historico_objects
    ]

    # Retorna o histórico como JSON
    return JsonResponse({'historico': historico})
    
def escolher_responsavel(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Parse do corpo da requisição
                data = json.loads(request.body)

                signature_base64 = data.get('signature', '')

                format, imgstr = signature_base64.split(';base64,') 
                ext = format.split('/')[-1]  # Extensão do arquivo, como 'png', 'jpg', etc.
                
                # Gerar um UUID para o nome do arquivo
                file_name = f"{uuid.uuid4()}.{ext}"

                # Criar o arquivo a partir da string base64
                signature_file = ContentFile(base64.b64decode(imgstr), name=file_name)
                    
                data_entrega_str = data.get('dataEntrega')
                motivo_responsavel = data.get('motivo-responsavel')

                if not data_entrega_str:
                    return JsonResponse({'status': 'error', 'message': 'Data de análise não fornecida'}, status=400)
                try:
                    # Converte a string em objeto datetime.date
                    data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

                # Obtém os objetos relacionados
                funcionario_object = get_object_or_404(Funcionario, pk=data.get('nome-responsavel'))
                instrumento_object = get_object_or_404(InfoInstrumento, tag=data.get('tag-instrumento-responsavel'))

                # Verifica se o instrumento já possui um responsável
                designacao = DesignarInstrumento.objects.filter(instrumento_escolhido=instrumento_object).first()

                if designacao:
                    # Atualiza o responsável existente
                    descricao = f"Mudando responsável de: {designacao.responsavel.matricula} - {designacao.responsavel.nome} para: {funcionario_object.matricula} - {funcionario_object.nome}\nLink da ficha assinada:"
                    registrar_mudanca_responsavel(instrumento_object,descricao=descricao)
                    
                    designacao.responsavel = funcionario_object
                    designacao.data_entrega_funcionario=data_entrega
                    designacao.save()

                else:
                    # Cria uma nova designação
                    descricao = f"Atribuindo a responsabilidade para: {funcionario_object.matricula} - {funcionario_object.nome} na data {data_entrega}"
                    registrar_primeiro_responsavel(instrumento_object,descricao=descricao)

                    designacao = DesignarInstrumento.objects.create(
                        instrumento_escolhido=instrumento_object,
                        responsavel=funcionario_object,
                        data_entrega_funcionario=data_entrega
                    )
                
                AssinaturaInstrumento.objects.create(
                    instrumento=instrumento_object,
                    assinante=funcionario_object,
                    data_entrega=data_entrega,
                    foto_assinatura=signature_file,
                    motivo=motivo_responsavel
                )

                return JsonResponse({'status': 'success',}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def editar_responsavel(request):

    if request.method == 'POST':
        
        try:
            with transaction.atomic():
                # Parse do corpo da requisição
                data = json.loads(request.body)

                id_novo_responsavel = data.get('nome-editar-responsavel')
                nome_ultimo_responsavel = data.get('nome-ultimo-responsavel')
                id_novo_responsavel = None if data.get('nome-editar-responsavel') == '' else id_novo_responsavel
                motivo_editar_responsavel = data.get('motivo-editar-responsavel')

                if id_novo_responsavel != None and (id_novo_responsavel != nome_ultimo_responsavel):
                    signature_base64 = data.get('signature', '')

                    format, imgstr = signature_base64.split(';base64,') 
                    ext = format.split('/')[-1]  # Extensão do arquivo, como 'png', 'jpg', etc.
                    
                    # Gerar um UUID para o nome do arquivo
                    file_name = f"{uuid.uuid4()}.{ext}"

                    # Criar o arquivo a partir da string base64
                    signature_file = ContentFile(base64.b64decode(imgstr), name=file_name)

                    # Obtém os objetos relacionados
                # funcionario_object = get_object_or_404(Funcionario, pk=data.get('nome-editar-responsavel'))
                funcionario_object = Funcionario.objects.filter(id=id_novo_responsavel).first()
                ultimo_funcionario = Funcionario.objects.filter(id=nome_ultimo_responsavel).first()

                data_entrega_str = data.get('dataEntregaEdicao')

                if not data_entrega_str:
                    return JsonResponse({'status': 'error', 'message': 'Data de análise não fornecida'}, status=400)
                try:
                    # Converte a string em objeto datetime.date
                    data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)
                instrumento_object = get_object_or_404(InfoInstrumento, tag=data.get('tag-instrumento-responsavel-editar'))

                # Verifica se o instrumento já possui um responsável
                designacao = DesignarInstrumento.objects.filter(instrumento_escolhido=instrumento_object).first()

                if designacao and id_novo_responsavel != None and (id_novo_responsavel != nome_ultimo_responsavel):
                    # Atualiza o responsável existente
                    descricao = f"Mudando responsável de: {designacao.responsavel.matricula} - {designacao.responsavel.nome} para: {funcionario_object.matricula} - {funcionario_object.nome} - na data {data_entrega}"
                    registrar_mudanca_responsavel(instrumento_object,descricao=descricao)
                    
                    designacao.responsavel = funcionario_object
                    designacao.data_entrega_funcionario=data_entrega
                    designacao.save()
                    AssinaturaInstrumento.objects.create(
                        instrumento=instrumento_object,
                        assinante=funcionario_object,
                        data_entrega=data_entrega,
                        foto_assinatura=signature_file,
                        motivo=motivo_editar_responsavel
                    )
                else:
                    # Atualiza o responsável existente
                    descricao = f"Instrumento: {instrumento_object.tag} - Devolvido para o Controle da Qualidade pelo funcionário: {ultimo_funcionario} - na data {data_entrega}"
                    registrar_instrumento_devolucao(instrumento_object, descricao)
                    instrumento_object.status_instrumento = 'ativo'
                    instrumento_object.save()
                    designacao.delete()

                StatusInstrumento.objects.create(
                    instrumento=instrumento_object,
                    funcionario=ultimo_funcionario,
                    data_entrega=data_entrega,
                    motivo='devolução'
                )

                return JsonResponse({'status': 'success',}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def substituir_instrumento(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                print(data)
                id_responsavel = data['responsavel-id']
                tag_instrumento_status_substituido = data['tag-instrumento-status-substituido']
                data_substituicao = data['data-substituicao']
                instrumento_substituira = data['instrumento_substituira']

                instrumento = InfoInstrumento.objects.filter(id=tag_instrumento_status_substituido).first()

                instrumento.status_instrumento = 'danificado'
                instrumento.save()

                PontoCalibracao.objects.filter(instrumento=instrumento).update(status_ponto_calibracao='inativo')

                designacao = DesignarInstrumento.objects.filter(instrumento_escolhido=instrumento).first()
                
                if instrumento_substituira != '':
                    novo_instrumento = InfoInstrumento.objects.filter(id=instrumento_substituira).first()
                    funcionario = Funcionario.objects.filter(id=id_responsavel).first()

                    ultima_assinatura = AssinaturaInstrumento.objects.filter(assinante=funcionario).order_by('-data_assinatura').first()
                    foto_assinatura = ultima_assinatura.foto_assinatura if ultima_assinatura else None

                    # Criar AssinaturaInstrumento
                    AssinaturaInstrumento.objects.create(
                        instrumento=novo_instrumento,
                        assinante=funcionario,
                        foto_assinatura=foto_assinatura,
                        motivo='Entrega',
                        data_entrega=data_substituicao
                    )

                    descricao = f"Atribuindo a responsabilidade para: {funcionario.matricula} - {funcionario.nome} na data {data_substituicao}"
                    registrar_primeiro_responsavel(novo_instrumento, descricao)
                    
                    DesignarInstrumento.objects.filter(pk=designacao.pk).delete()

                    DesignarInstrumento.objects.create(
                        instrumento_escolhido=novo_instrumento,
                        responsavel=funcionario,
                        data_entrega_funcionario=data_substituicao
                    )

                    StatusInstrumento.objects.create(
                        funcionario=funcionario,
                        instrumento=instrumento,
                        motivo='substituição',
                        data_entrega=data_substituicao,
                        observacoes='danificado'
                    )

                    descricao = f"Instrumento: {instrumento.tag} - Danificado - na data {data_substituicao}"
                    registrar_instrumento_danificado(instrumento, descricao)

                elif designacao and id_responsavel != 'null': 
                    funcionario = Funcionario.objects.filter(id=id_responsavel).first()
                    DesignarInstrumento.objects.filter(pk=designacao.pk).delete()

                    StatusInstrumento.objects.create(
                        funcionario=funcionario,
                        instrumento=instrumento,
                        motivo='substituição',
                        data_entrega=data_substituicao,
                        observacoes='danificado'
                    )

                    descricao = f"Instrumento: {instrumento.tag} - Danificado - na data {data_substituicao}"
                    registrar_instrumento_danificado(instrumento, descricao)

                return JsonResponse({'status': 'success',}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else: 
        assigned_instrument_ids = DesignarInstrumento.objects.values_list('instrumento_escolhido_id', flat=True)
        enviados_instrument_ids = Envio.objects.filter(status='enviado').values_list('instrumento_id', flat=True)
        unassigned_instruments = InfoInstrumento.objects.exclude(id__in=assigned_instrument_ids).exclude(id__in=enviados_instrument_ids).filter(status_instrumento='ativo').values(
            'id', 'tag'
        )
        print(unassigned_instruments)
        return JsonResponse(list(unassigned_instruments), safe=False)

def historico(request):
    instrumentos = InfoInstrumento.objects.all()
    instrumento_selecionado = request.GET.get('instrumento','')

    return render(request, 'historico.html', {
        'instrumentos': instrumentos,
        'instrumento_selecionado':instrumento_selecionado
    })

def historico_instrumento(request, id):
    
    if request.method == 'GET':
        # Obtém o instrumento pelo ID ou retorna erro 404 se não existir
        instrumento = get_object_or_404(InfoInstrumento, id=id)

        # Obtém os pontos de calibração relacionados ao instrumento
        pontos_calibracao = instrumento.pontos_calibracao.all()

        designacao = instrumento.designar_instrumento.first()  # Pegamos apenas o primeiro registro (caso exista)
        responsavel = designacao.responsavel.nome if designacao and designacao.responsavel else None

        STATUS_INSTRUMENTO_MAP = {
            'ativo': 'Ativo',
            'inativo': 'Inativo',
            'em_uso': 'Em uso',
            'desuso': 'Desuso',
            'danificado': 'Danificado',
        }

        # Serializa os dados do instrumento
        instrumento_data = {
            "id": instrumento.id,
            "tag": instrumento.tag,
            "tipo_equipamento": instrumento.tipo_instrumento.nome,  # Ajuste se necessário
            "marca": instrumento.marca.nome,  # Ajuste se necessário
            "status_instrumento": STATUS_INSTRUMENTO_MAP.get(instrumento.status_instrumento, ""),
            "tempo_calibracao": instrumento.tempo_calibracao,
            "ultima_calibracao": instrumento.ultima_calibracao.strftime("%Y-%m-%d"),
            "proxima_calibracao": instrumento.proxima_calibracao.strftime("%Y-%m-%d") if instrumento.proxima_calibracao else None,
            "responsavel": responsavel,
        }

        pontos_data = []
        # Serializa os dados dos pontos de calibração
        for ponto in pontos_calibracao:
            ultimo_envio = Envio.objects.filter(instrumento=instrumento, ponto_calibracao=ponto).order_by('-id').first()
            analise_certificado = AnaliseCertificado.objects.filter(envio=ultimo_envio).first() if ultimo_envio else None

            pontos_data.append({
                "id": ponto.id,
                "descricao": ponto.descricao,
                "faixa_nominal": ponto.faixa_nominal,
                "unidade": ponto.unidade,
                "tolerancia_admissivel": ponto.tolerancia_admissivel,
                "status": ponto.status_ponto_calibracao,
                "analise_certificado": analise_certificado.analise_certificado if analise_certificado else None
            })

        # Retorna os dados como JSON
        return JsonResponse({
            "instrumento": instrumento_data,
            "pontos_calibracao": pontos_data,
        })

def historico_datatable_instrumento(request, id):

    instrumento = get_object_or_404(InfoInstrumento, id=id)

    historico_instrumento = HistoricoInstrumento.objects.filter(instrumento=instrumento)
    historico_data = [
        {
            "tipo_mudanca": historico.tipo_mudanca,
            "data_mudanca": historico.data_mudanca.strftime("%Y-%m-%d %H:%M:%S"),
            "descricao_mudanca": historico.descricao_mudanca
        }
        for historico in historico_instrumento
    ]
             
    return JsonResponse({
        "historico": historico_data
    })

def cadastrar_instrumento(request):

    instrumentos_cadastrados = InfoInstrumento.objects.all()

    return render(request, 'cadastro.html', {
        'instrumentos_cadastrados':instrumentos_cadastrados
    })