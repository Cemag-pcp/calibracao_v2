from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max
from django.http import JsonResponse
from django.db.models import Q, Prefetch
from django.core.cache import cache
from django.db import transaction
from django.utils.dateparse import parse_date
from django.core.files.base import ContentFile

from inspecao.models import Envio, Laboratorio, AnaliseCertificado
from ficha.models import AssinaturaInstrumento, StatusInstrumento
from .models import InfoInstrumento, HistoricoInstrumento, Funcionario, DesignarInstrumento, Operadores, PontoCalibracao, TipoInstrumento, Marca, Unidade
from cadastro.utils import *
from django.http import HttpResponse, JsonResponse

from datetime import datetime
import time
import json
import base64
import uuid

def calcular_status_calibracao(ultimo_envio, proxima_calibracao, hoje):
    if ultimo_envio and ultimo_envio.status == 'enviado':
        return 'Em calibração'
    elif proxima_calibracao:
        if proxima_calibracao >= hoje:
            dias_para_vencer = (proxima_calibracao - hoje).days
            return f'Em dia, faltam {dias_para_vencer} dias'
        else:
            dias_atrasado = (hoje - proxima_calibracao).days
            return f'Atrasado há {dias_atrasado} dias'
    else:
        return 'Sem próxima calibração definida'

def formatar_responsavel(designacao):
    if designacao and designacao.responsavel:
        return {
            'id': designacao.responsavel.id,
            'matriculaNome': f"{designacao.responsavel.matricula} - {designacao.responsavel.nome}",
            'dataEntrega': designacao.data_entrega_funcionario
        }
    else:
        return {
            'id': None,
            'matriculaNome': None,
            'dataEntrega': None
        }

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

from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import datetime
import time

def instrumentos_data(request):
    hoje = datetime.now().date()
    start_date = time.time()

    # Pré-carregar envios e análises de certificados
    envios_prefetch = Prefetch(
        'ponto',  # Substitua por 'envio_set' se o related_name não for 'envios'
        queryset=Envio.objects.prefetch_related(
            Prefetch(
                'analise_envio',  # related_name no modelo AnaliseCertificado
                queryset=AnaliseCertificado.objects.all()
            )
        ).order_by('-id')
    )

    pontos_calibracao_prefetch = Prefetch(
        'pontos_calibracao',
        queryset=PontoCalibracao.objects.prefetch_related(envios_prefetch)
    )

    assinaturas_prefetch = Prefetch(
        'assinatura_instrumento',
        queryset=AssinaturaInstrumento.objects.order_by('-data_assinatura')
    )

    instrumentos = InfoInstrumento.objects.prefetch_related(
        pontos_calibracao_prefetch,
        assinaturas_prefetch,
        'designar_instrumento'
    ).all()

    instrumentos_detalhes = {}
    for instrumento in instrumentos:
        ultima_assinatura = instrumento.assinatura_instrumento.first()
        ultimo_assinante = ultima_assinatura.assinante if ultima_assinatura else None

        for ponto in instrumento.pontos_calibracao.all():
            ultimo_envio = ponto.ponto.first()  # Substitua por 'envio_set' se necessário
            analise_certificado = ultimo_envio.analise_envio.first() if ultimo_envio else None

            status_calibracao = calcular_status_calibracao(ultimo_envio, instrumento.proxima_calibracao, hoje)

            designacao = instrumento.designar_instrumento.first()
            responsavel = formatar_responsavel(designacao)

            if instrumento.tag not in instrumentos_detalhes:
                instrumentos_detalhes[instrumento.tag] = {
                    'id': instrumento.id,
                    'tag': instrumento.tag,
                    'tipo_instrumento': instrumento.tipo_instrumento.nome,
                    'marca': instrumento.marca.nome,
                    'status_instrumento': instrumento.status_instrumento,
                    'ultima_calibracao': instrumento.ultima_calibracao,
                    'proxima_calibracao': instrumento.proxima_calibracao,
                    'status_calibracao_string': status_calibracao,
                    'status_calibracao': ultimo_envio.status if ultimo_envio else None,
                    'tempo_calibracao': instrumento.tempo_calibracao,
                    'responsavel': responsavel,
                    'ultimo_assinante': {
                        'nome': ultimo_assinante.nome if ultimo_assinante else None,
                        'id': ultimo_assinante.id if ultimo_assinante else None
                    },
                    'pontos_calibracao': []
                }

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

    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(instrumentos_page),
    }

    end_date = time.time()
    duration = end_date - start_date
    print(f"Duração: {duration} segundos")

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

def template_instrumento(request):
    # Carregar instrumentos cadastrados com os pontos de calibração relacionados
    instrumentos = InfoInstrumento.objects.prefetch_related(
        'pontos_calibracao',  # Usando o related_name para prefetch dos pontos de calibração
        'tipo_instrumento', 'marca'
    ).all()

    # Criar a estrutura desejada no formato {'instrumento': <InfoInstrumento>, 'pontos_calibracao': <QuerySet>}
    instrumentos_com_pontos_calibracao = [
        {
            'instrumento': instrumento,
            'pontos_calibracao': instrumento.pontos_calibracao.all()  # Acessando os pontos de calibração diretamente
        }
        for instrumento in instrumentos
    ]

    # Passar os instrumentos com pontos de calibração para o template
    return render(request, 'cadastro.html', {
        'instrumentos_com_pontos_calibracao': instrumentos_com_pontos_calibracao
    })

def add_instrumento(request):

    if request.method == 'POST':

        start_time = time.time()

        data = request.POST
        tag = data.get("modal-add-tag")
        tipo_nome = data.get("modal-add-tipo")
        marca_nome = data.get("modal-add-marca")
        status_exibido = data.get("modal-add-status")
        tempo_calib = data.get("modal-add-tempo")
        ultima_calib = data.get("modal-add-ultima")

        # Verificação antecipada para evitar consultas desnecessárias
        if not all([tag, tipo_nome, marca_nome, status_exibido, tempo_calib, ultima_calib]):
            return JsonResponse({"error": "Todos os campos são obrigatórios"}, status=400)

        try:
            tempo_calibracao = int(tempo_calib)
            ultima_calibracao = parse_date(ultima_calib)
            if not ultima_calibracao:
                return JsonResponse({"error": "Data de última calibração inválida"}, status=400)

            # Mapeia status de exibição para chave armazenada no banco
            STATUS_DICT = dict(InfoInstrumento.STATUS_INSTRUMENTO_CHOICES)
            status = next((key for key, value in STATUS_DICT.items() if value == status_exibido), None)

            if status is None:
                return JsonResponse({"error": "Status inválido"}, status=400)

            tipo = TipoInstrumento.objects.select_related().get(nome=tipo_nome)
            marca, _ = Marca.objects.get_or_create(nome=marca_nome)

            # Criando o novo instrumento
            novo_instrumento = InfoInstrumento(
                tag=tag,
                tipo_instrumento=tipo,
                marca=marca,
                status_instrumento=status,
                tempo_calibracao=tempo_calibracao,
                ultima_calibracao=ultima_calibracao
            )
            novo_instrumento.save()
            
            end_time = time.time()  # Fim da medição
            duration = end_time - start_time  # Tempo decorrido
            
            print(duration)

            return JsonResponse({"message": "Instrumento adicionado com sucesso!", "id": novo_instrumento.id})

        except TipoInstrumento.DoesNotExist:
            return JsonResponse({"error": "Tipo de instrumento não encontrado"}, status=400)
        except ValueError:
            return JsonResponse({"error": "Erro ao converter os valores numéricos"}, status=400)
    
    elif request.method == 'GET':

        # Modal adicionar instrumento

        start_time = time.time()
    
        list_status = [status[1] for status in InfoInstrumento.STATUS_INSTRUMENTO_CHOICES]

        lists_type = TipoInstrumento.objects.values_list('nome', flat=True)

        list_type = [types for types in lists_type]

        end_time = time.time()  # Fim da medição
        duration = end_time - start_time  # Tempo decorrido

        print(duration)

        return JsonResponse({"statusList": list_status, "typeList": list_type})

def add_tipo_instrumento(request):

    with transaction.atomic():
        try:
            if request.method == 'POST':

                data = json.loads(request.body)
                tipo_instrumento = data.get("tipo-instrumento").strip()

                if TipoInstrumento.objects.filter(nome__iexact=tipo_instrumento).exists():
                    return JsonResponse({'status': 'error', 'message': 'Este tipo de instrumento já existe'}, status=400)

                if tipo_instrumento and tipo_instrumento != "":
                    TipoInstrumento.objects.create(
                        nome=tipo_instrumento
                    )

                return JsonResponse({"data":data})
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
def adicionar_ponto_calibracao(request):

    if request.method == "POST":
        try:
            # Carrega os dados enviados no corpo da requisição
            data = json.loads(request.body)

            # Valida os dados recebidos (você pode adicionar mais validações conforme necessário)
            instrumento_id = data.get('instrumento_id_ponto_calibracao')
            descricao = data.get('descricao-pc')
            faixa_nominal = data.get('faixa_nominal-pc')
            unidade = data.get('unidade-pc')
            status = data.get('status-pc', 'ativo')  # Status padrão é 'ativo'

            # Busca as referências para 'instrumento' e 'unidade'
            instrumento = InfoInstrumento.objects.get(id=instrumento_id)
            unidade = Unidade.objects.get(nome=unidade)

            PontoCalibracao.objects.create(
                descricao=descricao,
                instrumento=instrumento,
                faixa_nominal=faixa_nominal,
                unidade=unidade,
                status_ponto_calibracao=status
            )

            # Retorna a resposta JSON com os dados do novo ponto de calibração
            return JsonResponse({"data": "Ponto de calibração adicionado com sucesso!"})

        except Exception as e:
            print("error", str(e))
            return JsonResponse({"error": str(e)}, status=400)
    
    elif request.method == "GET":

        lists_unit = Unidade.objects.values_list('nome', flat=True)

        list_unit = [unit for unit in lists_unit]

        return JsonResponse({"unitList": list_unit})

    return JsonResponse({"error": "Método não permitido"}, status=405)

def add_unidade_ponto_calibracao(request):
    with transaction.atomic():
        try:
            if request.method == 'POST':

                data = json.loads(request.body)
                unidade_instrumento = data.get("unidade-instrumento").strip()

                if Unidade.objects.filter(nome__iexact=unidade_instrumento).exists():
                    return JsonResponse({'status': 'error', 'message': 'Este tipo de unidade já existe'}, status=400)

                if unidade_instrumento and unidade_instrumento != "":
                    Unidade.objects.create(
                        nome=unidade_instrumento
                    )

                return JsonResponse({"data":data})
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)