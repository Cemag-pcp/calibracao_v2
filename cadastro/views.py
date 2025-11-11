from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max
from django.http import JsonResponse
from django.db.models import Q, Prefetch, Count, OuterRef, Subquery

from django.core.cache import cache
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.dateparse import parse_date
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required

from inspecao.models import Envio, Laboratorio, AnaliseCertificado
from ficha.models import AssinaturaInstrumento, StatusInstrumento
from .models import InfoInstrumento, HistoricoInstrumento, Funcionario, DesignarInstrumento, Operadores, PontoCalibracao, TipoInstrumento, Marca, Unidade
from cadastro.utils import *
from django.http import HttpResponse, JsonResponse

from datetime import datetime, date
import time
import json
import base64
import uuid
from collections import defaultdict

def calcular_status_calibracao(ultimo_envio, proxima_calibracao, hoje):
    if ultimo_envio and ultimo_envio.status == 'enviado':
        return 'Em calibração'
    elif ultimo_envio and ultimo_envio.status == 'recebido' and not ultimo_envio.analise:
        return 'A analisar'
    elif proxima_calibracao:
        if proxima_calibracao >= hoje:
            dias_para_vencer = (proxima_calibracao - hoje).days
            return f'Em dia, faltam {dias_para_vencer} dias'
        else:
            dias_atrasado = (hoje - proxima_calibracao).days
            return f'Atrasado há {dias_atrasado} dias'
    else:
        return 'Sem próxima calibração definida'

def determinar_status_calibracao_val(ultimo_envio, proxima_calibracao, hoje):
    if ultimo_envio and ultimo_envio.status == 'enviado':
        return 'Em calibração'
    elif ultimo_envio and ultimo_envio.status == 'recebido' and not ultimo_envio.analise_envio.first():
        return 'A analisar'
    elif proxima_calibracao:
        if proxima_calibracao >= hoje:
            return 'Em dia'
        else:
            return 'Atrasado'
    return None

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

@login_required
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

@login_required
def home(request):
    
    laboratorios = Laboratorio.objects.filter(status='ativo')
    operadores = Operadores.objects.filter(status='ativo')
    naturezas = Envio.NATUREZA_CHOICES
    metodos = Envio.METODO_CHOICES
    motivos = AssinaturaInstrumento.STATUS_CHOICES
    funcionarios = Funcionario.objects.all()
    instrumento = InfoInstrumento.objects.all()
    status_instrumento = InfoInstrumento.STATUS_INSTRUMENTO_CHOICES

    status_calibracao = (
        ('atrasado', 'Atrasado'), 
        ('em_dia', 'Em dia'), 
        ('em_calibracao', 'Em calibração'), 
        ('a_analisar', 'A analisar')
    )


    return render(request, "home.html", {'laboratorios':laboratorios,
                                         'operadores':operadores,
                                         'naturezas':naturezas,
                                         'metodos':metodos,
                                         'funcionarios':funcionarios,
                                         'motivos':motivos,
                                         'instrumentos':instrumento,
                                         'status_instrumento':status_instrumento,
                                         'status_calibracao':status_calibracao})

@login_required
def instrumentos_data(request):
    start_time = time.time()
    
    # Parâmetros do DataTables
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10)) # Ajustado para 10 como no JS
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')

    # Parâmetros dos filtros
    tag = request.GET.get('tag', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    status_instrumento = request.GET.get('status_instrumento', '').split(',') if request.GET.get('status_instrumento') else []
    status_calibracao = request.GET.get('status_calibracao', '').split(',') if request.GET.get('status_calibracao') else []
    data_ultima_inicio = request.GET.get('data_ultima_inicio', '')
    data_ultima_fim = request.GET.get('data_ultima_fim', '')
    data_proxima_inicio = request.GET.get('data_proxima_inicio', '')
    data_proxima_fim = request.GET.get('data_proxima_fim', '')

    # Mapeamento de colunas para ordenação
    column_map = {
        0: 'tag',
        1: 'tipo_instrumento__nome',
        2: 'status_instrumento',
        3: 'ultima_calibracao',
        4: 'proxima_calibracao',
        # O campo 5 não existe mais diretamente no DB, a ordenação será por tag se selecionado
    }
    order_column = column_map.get(order_column_index, 'tag')

    # Consulta base otimizada
    queryset = InfoInstrumento.objects.select_related(
        'tipo_instrumento', 'marca'
    ).prefetch_related(
        Prefetch('pontos_calibracao', queryset=PontoCalibracao.objects.only(
            'id', 'descricao', 'faixa_nominal', 'unidade', 
            'tolerancia_admissivel', 'status_ponto_calibracao', 'instrumento_id'
        )),
        Prefetch('designar_instrumento', queryset=DesignarInstrumento.objects.select_related('responsavel')),
        Prefetch('assinatura_instrumento', queryset=AssinaturaInstrumento.objects.select_related('assinante').order_by('-data_assinatura'))
    )

    # ==================== MUDANÇA PRINCIPAL ====================
    # Filtra a queryset para incluir APENAS instrumentos que possuem pontos de calibração.
    # .distinct() é crucial para evitar duplicatas.
    queryset = queryset.filter(pontos_calibracao__isnull=False).distinct()
    # ==========================================================

    # Aplicar filtros
    if tag:
        queryset = queryset.filter(tag__icontains=tag)
    if tipo:
        queryset = queryset.filter(tipo_instrumento__nome__icontains=tipo)
    if status_instrumento:
        queryset = queryset.filter(status_instrumento__in=status_instrumento)
    
    # Filtros de data
    if data_ultima_inicio and data_ultima_fim:
        try:
            queryset = queryset.filter(ultima_calibracao__range=[data_ultima_inicio, data_ultima_fim])
        except ValueError:
            pass
    
    if data_proxima_inicio and data_proxima_fim:
        try:
            queryset = queryset.filter(proxima_calibracao__range=[data_proxima_inicio, data_proxima_fim])
        except ValueError:
            pass

    # Total de registros ANTES da paginação, mas DEPOIS dos filtros
    total_filtrado_antes_paginacao = queryset.count()

    # Ordenação
    if order_direction == 'desc':
        order_column = f'-{order_column}'
    queryset = queryset.order_by(order_column)

    # Paginação no banco de dados
    instrumentos_paginados = queryset[start:start + length]

    # --- Otimização: A lógica de buscar pontos, envios e análises pode ser simplificada ---
    # Como já garantimos que todos os instrumentos têm pontos, podemos processar os dados
    
    instrumento_ids = [i.id for i in instrumentos_paginados]
    
    # Buscando todos os pontos necessários de uma vez
    pontos_dos_instrumentos = PontoCalibracao.objects.filter(instrumento_id__in=instrumento_ids)
    
    # Buscando os últimos envios para esses pontos
    ultimo_envio_subquery = Envio.objects.filter(ponto_calibracao=OuterRef('pk')).order_by('-id').values('pk')[:1]
    pontos_com_ultimo_envio = pontos_dos_instrumentos.annotate(
        ultimo_envio_id=Subquery(ultimo_envio_subquery)
    )

    # Mapeando pontos por instrumento para fácil acesso
    pontos_por_instrumento = {}
    for ponto in pontos_com_ultimo_envio:
        if ponto.instrumento_id not in pontos_por_instrumento:
            pontos_por_instrumento[ponto.instrumento_id] = []
        pontos_por_instrumento[ponto.instrumento_id].append(ponto)

    # Buscando as análises de uma vez
    envio_ids = [p.ultimo_envio_id for p in pontos_com_ultimo_envio if p.ultimo_envio_id]
    analises = {a.envio_id: a for a in AnaliseCertificado.objects.filter(envio_id__in=envio_ids)}
    
    # Buscando os envios de uma vez
    envios = {e.id: e for e in Envio.objects.filter(id__in=envio_ids)}

    # Processar os dados
    hoje = date.today()
    instrumentos_detalhes = []
    
    for instrumento in instrumentos_paginados:
        designacao = instrumento.designar_instrumento.first()
        ultima_assinatura = instrumento.assinatura_instrumento.first()
        
        pontos_do_instrumento_atual = pontos_por_instrumento.get(instrumento.id, [])
        
        # O status de calibração é baseado no primeiro ponto encontrado
        primeiro_ponto = pontos_do_instrumento_atual[0] if pontos_do_instrumento_atual else None
        envio_do_primeiro_ponto = envios.get(primeiro_ponto.ultimo_envio_id) if primeiro_ponto else None

        status_calibracao_str = calcular_status_calibracao(
            envio_do_primeiro_ponto, instrumento.proxima_calibracao, hoje
        )
        status_calibracao_val = determinar_status_calibracao_val(
            envio_do_primeiro_ponto, instrumento.proxima_calibracao, hoje
        )
        
        # Aplicar filtro de status_calibracao (lógica em Python)
        if status_calibracao and status_calibracao_val not in status_calibracao:
            continue

        pontos_formatados = []
        for ponto in pontos_do_instrumento_atual:
            envio = envios.get(ponto.ultimo_envio_id)
            analise = analises.get(ponto.ultimo_envio_id)
            pontos_formatados.append({
                'ultimo_envio_pk': envio.id if envio else None,
                'ponto_pk': ponto.id,
                'ponto_descricao': ponto.descricao,
                'ponto_faixa_nominal': ponto.faixa_nominal,
                'ponto_unidade': ponto.unidade,
                'ponto_tolerancia_admissivel': ponto.tolerancia_admissivel,
                'status_ponto_calibracao': ponto.status_ponto_calibracao,
                'ultimo_certificado': analise.analise_certificado if analise else None,
                'analise_certificado': analise.analise_certificado if analise else None,
                'ultimo_pdf': envio.pdf if envio else None,
            })

        if len(status_instrumento) == 1:
            if status_instrumento[0] == 'danificado':
                status_calibracao_str = 'N/A'

        if instrumento.status_instrumento == 'ativo' and  status_calibracao_str == 'Em calibração':
            status = 'Aguardando retornar da calibração'
        elif instrumento.status_instrumento == 'ativo':
            status = 'Disponível'
        else:
            status = instrumento.status_instrumento

        # proxima calibração
        proxima_calibracao = instrumento.proxima_calibracao.strftime('%d/%m/%Y') if instrumento.proxima_calibracao else None,

        if len(status_instrumento) == 1:
            if status_instrumento[0] == 'danificado':
                proxima_calibracao = 'N/A'

        if status_calibracao_str == 'Em calibração':
            proxima_calibracao = 'N/A'

        instrumentos_detalhes.append({
            'id': instrumento.id,
            'tag': instrumento.tag,
            'tipo_instrumento': instrumento.tipo_instrumento.nome,
            'marca': instrumento.marca.nome,
            'status_instrumento': status,
            'ultima_calibracao': instrumento.ultima_calibracao.strftime('%d/%m/%Y') if instrumento.ultima_calibracao else None,
            'proxima_calibracao': proxima_calibracao,
            'status_calibracao_string': status_calibracao_str,
            'status_calibracao': envio_do_primeiro_ponto.status if envio_do_primeiro_ponto else None,
            'tempo_calibracao': instrumento.tempo_calibracao,
            'responsavel': {
                'id': designacao.responsavel.id if designacao and designacao.responsavel else None,
                'matriculaNome': f"{designacao.responsavel.matricula} - {designacao.responsavel.nome}" if designacao and designacao.responsavel else None,
                'dataEntrega': designacao.data_entrega_funcionario if designacao else None
            },
            'ultimo_assinante': {
                'nome': ultima_assinatura.assinante.nome if ultima_assinatura and ultima_assinatura.assinante else None,
                'id': ultima_assinatura.assinante.id if ultima_assinatura and ultima_assinatura.assinante else None
            },
            'pontos_calibracao': pontos_formatados
        })

    # O total filtrado é a contagem antes da paginação, mas se o filtro de status_calibracao (em python)
    # for aplicado, precisamos ajustar.
    total_filtrado_final = len(instrumentos_detalhes) if status_calibracao else total_filtrado_antes_paginacao

    data = {
        'draw': draw,
        'recordsTotal': InfoInstrumento.objects.filter(pontos_calibracao__isnull=False).distinct().count(), # Contagem total correta
        'recordsFiltered': total_filtrado_final,
        'data': instrumentos_detalhes,
    }

    duration = time.time() - start_time
    print(f"Duração: {duration:.2f} segundos")
    
    return JsonResponse(data)

@login_required
def designar_instrumentos(request):
    if request.method == 'POST':
        with transaction.atomic():
            try:
                data = json.loads(request.body)
                
                funcionario_id = data.get('funcionario-designar-varios-instrumentos')
                instrumentos_ids = list(set(data.get('instrumentos', [])))
                assinatura_base64 = data.get('signature')
                data_entrega = data.get('data-designar-varios-instrumentos')

                # Verificação de dados
                if not all([funcionario_id, instrumentos_ids, assinatura_base64, data_entrega]):
                    return JsonResponse({"sucesso": False, "erro": "Dados incompletos"}, status=400)

                # Buscar o funcionário
                funcionario = Funcionario.objects.get(id=funcionario_id)

                # Converter a data de entrega
                data_entrega = datetime.fromisoformat(data_entrega).date()

                # Decodificar a assinatura uma única vez
                format, imgstr = assinatura_base64.split(';base64,') 
                ext = format.split('/')[-1]  # Extensão do arquivo, como 'png', 'jpg', etc.
                file_name = f"{uuid.uuid4()}.{ext}"
                assinatura_path = ContentFile(base64.b64decode(imgstr), name=file_name)

                # Buscar todos os instrumentos de uma vez
                instrumentos = InfoInstrumento.objects.filter(id__in=instrumentos_ids)

                # Listas para bulk_create
                designacoes = []
                assinaturas = []

                for instrumento in instrumentos:
                    # Criar a designação do instrumento com a data especificada
                    designacoes.append(DesignarInstrumento(
                        instrumento_escolhido=instrumento,
                        responsavel=funcionario,
                        data_entrega_funcionario=data_entrega
                    ))

                    # Criar a assinatura associada
                    assinaturas.append(AssinaturaInstrumento(
                        instrumento=instrumento,
                        assinante=funcionario,
                        foto_assinatura=assinatura_path,
                        data_entrega=data_entrega,
                        motivo='Entrega'
                    ))

                    descricao = f"Atribuindo a responsabilidade para: {funcionario.matricula} - {funcionario.nome} na data {data_entrega}"
                    registrar_primeiro_responsavel(instrumento, descricao)

                # Inserir todas as designações e assinaturas de uma vez
                DesignarInstrumento.objects.bulk_create(designacoes)
                AssinaturaInstrumento.objects.bulk_create(assinaturas)

                return JsonResponse({"sucesso": True})
            
            except Exception as e:
                return JsonResponse({"sucesso": False, "erro": str(e)}, status=500)
        
    elif request.method == 'GET':
        # Deve pegar todos os instrumentos que não possuem designação e que possuem pelo menos um ponto de calibração ativo
        enviados_instrument_ids = Envio.objects.filter(status='enviado').values_list('instrumento_id', flat=True)
        
        # Filtra os instrumentos que não têm designação, não foram enviados, estão ativos e possuem pelo menos um ponto de calibração ativo
        instrumentos = InfoInstrumento.objects.exclude(designar_instrumento__isnull=False) \
                                            .exclude(id__in=enviados_instrument_ids) \
                                            .filter(status_instrumento='ativo') \
                                            .filter(pontos_calibracao__status_ponto_calibracao='ativo').distinct()
        
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

@login_required
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
                    registrar_primeiro_responsavel(instrumento_object, descricao=descricao)

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

@login_required
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

@login_required
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

@login_required
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

@login_required
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
    
        list_status = [status[1] for status in InfoInstrumento.STATUS_INSTRUMENTO_CHOICES if status[1] in ['Ativo','Inativo', 'Desuso']]

        lists_type = TipoInstrumento.objects.values_list('nome', flat=True)

        list_type = [types for types in lists_type]

        end_time = time.time()  # Fim da medição
        duration = end_time - start_time  # Tempo decorrido

        print(duration)

        return JsonResponse({"statusList": list_status, "typeList": list_type})

@login_required
def edit_instrumento(request):

    if request.method == 'POST':

        with transaction.atomic():

            try:
                data = json.loads(request.body)
                
                id = data.get("modal-edit-id")
                tag = data.get("modal-edit-tag")
                tipo_nome = data.get("modal-edit-tipo")
                marca_nome = data.get("modal-edit-marca")
                status_exibido = data.get("modal-edit-status")
                tempo_calib = data.get("modal-edit-tempo")
                ultima_calib = data.get("modal-edit-ultima")

                # Busca o instrumento ou retorna erro se não existir
                instrumento = get_object_or_404(InfoInstrumento, id=id)

                ultimo_envio = Envio.objects.filter(instrumento=instrumento).order_by('-id').first()
                if ultimo_envio and ultimo_envio.status == 'enviado':
                    return JsonResponse({"message": "Não é possível editar um instrumento enquanto estiver em processo de calibração."}, status=400)

                # Dicionário para armazenar alterações
                alteracoes = {}

                # Verifica cada campo e adiciona ao dicionário se houve mudança
                if tag and instrumento.tag != tag:
                    alteracoes["tag"] = tag
                
                if tipo_nome:
                    tipo_instrumento = TipoInstrumento.objects.select_related().get(nome=tipo_nome)
                    if instrumento.tipo_instrumento != tipo_instrumento:
                        alteracoes["tipo_instrumento"] = tipo_instrumento
                
                if marca_nome:
                    marca, created = Marca.objects.get_or_create(nome=marca_nome)
                    if instrumento.marca != marca:
                        alteracoes["marca"] = marca
                
                # Mapeia status de exibição para chave armazenada no banco
                STATUS_DICT = dict(InfoInstrumento.STATUS_INSTRUMENTO_CHOICES)
                status = next((key for key, value in STATUS_DICT.items() if value == status_exibido), None)

                if status is None:
                    return JsonResponse({"error": "Status inválido"}, status=400)
                
                if status and instrumento.status_instrumento != status:
                    alteracoes["status_instrumento"] = status
                
                if tempo_calib and instrumento.tempo_calibracao != int(tempo_calib):
                    alteracoes["tempo_calibracao"] = int(tempo_calib)

                if ultima_calib:
                    ultima_calibracao_date = parse_date(ultima_calib)
                    if instrumento.ultima_calibracao != ultima_calibracao_date:
                        alteracoes["ultima_calibracao"] = ultima_calibracao_date

                # Se houver mudanças, atualiza e salva o objeto
                if alteracoes:
                    for campo, valor in alteracoes.items():
                        setattr(instrumento, campo, valor)
                    instrumento.save()
                    return JsonResponse({"message": "Instrumento atualizado com sucesso!"})

                return JsonResponse({"message": "Nenhuma alteração realizada."})
            
            except IntegrityError as e:
                return JsonResponse({"message": f"Verifique se a tag que está sendo criada já existe: {e}"}, status=400)
            
            except Exception as e:
                return JsonResponse({"message": f"Nenhuma alteração realizada. {e}"}, status=400)

    return JsonResponse({"message": "Método não permitido"}, status=405)

@login_required
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
    
@login_required
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
            tolerancia_admissivel = data.get('tolerancia-pc')
            status = data.get('status-pc', 'ativo')  # Status padrão é 'ativo'

            # Busca as referências para 'instrumento' e 'unidade'
            instrumento = InfoInstrumento.objects.get(id=instrumento_id)

            ultimo_envio = Envio.objects.filter(instrumento=instrumento).order_by('-id').first()
            if ultimo_envio and ultimo_envio.status == 'enviado':
                return JsonResponse({"message": "Não é possível adicionar um ponto de calibração enquanto o item estiver em processo de calibração."}, status=400)

            unidade = Unidade.objects.get(nome=unidade)

            PontoCalibracao.objects.create(
                descricao=descricao,
                instrumento=instrumento,
                unidade=unidade,
                faixa_nominal=faixa_nominal,
                tolerancia_admissivel=tolerancia_admissivel,
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

@login_required
def editar_ponto_calibracao(request):

    if request.method == 'POST':

        with transaction.atomic():

            try:
                data = json.loads(request.body)
                
                pc_id = data.get('modal-edit-pc-id')
                descricao = data.get('modal-edit-pc-descricao')
                faixa_nominal = data.get('modal-edit-pc-faixa-nominal')
                unidade_str = data.get('modal-edit-pc-unidade').strip()
                tolerancia_admissivel = data.get('modal-edit-pc-tolerancia-admissivel')
                status = data.get('modal-edit-pc-status', 'Ativo')  # Status padrão é 'ativo'

                # Busca o instrumento ou retorna erro se não existir
                ponto_calibracao = get_object_or_404(PontoCalibracao, id=pc_id)

                # Verifica o status do último envio
                ultimo_envio = Envio.objects.filter(ponto_calibracao=ponto_calibracao).order_by('-id').first()
                if ultimo_envio and ultimo_envio.status == 'enviado':
                    return JsonResponse({"message": "Não é possível editar o ponto de calibração enquanto o item estiver em processo de calibração."}, status=400)

                try:
                    tolerancia_admissivel = float(tolerancia_admissivel)
                except Exception as e:
                    return JsonResponse({"message": "Tolerância admissivel deve ser um número"}, 400)

                # Dicionário para armazenar alterações
                alteracoes = {}

                if unidade_str and ponto_calibracao.unidade != unidade_str:
                    alteracoes["unidade"] = unidade_str

                if status is None:
                    return JsonResponse({"error": "Status inválido"}, status=400)
                
                if status and ponto_calibracao.status_ponto_calibracao != status:
                    alteracoes["status_ponto_calibracao"] = status
                
                if descricao and ponto_calibracao.descricao != descricao:
                    alteracoes["descricao"] = descricao

                if faixa_nominal and ponto_calibracao.faixa_nominal != faixa_nominal:
                    alteracoes["faixa_nominal"] = faixa_nominal
                
                if tolerancia_admissivel and ponto_calibracao.tolerancia_admissivel != tolerancia_admissivel:
                    alteracoes["tolerancia_admissivel"] = tolerancia_admissivel

                # Se houver mudanças, atualiza e salva o objeto
                if alteracoes:
                    for campo, valor in alteracoes.items():
                        setattr(ponto_calibracao, campo, valor)
                    ponto_calibracao.save()
                    return JsonResponse({"message": "Instrumento atualizado com sucesso!"})

                return JsonResponse({"message": "Nenhuma alteração realizada."})
            
            except IntegrityError as e:
                return JsonResponse({"message": f"Verifique a tag que está sendo criada já existe: {e}"}, status=400)
            
            except Exception as e:
                return JsonResponse({"message": f"Nenhuma alteração realizada. {e}"}, status=400)

    return JsonResponse({"message": "Método não permitido"}, status=405)

@login_required
def add_unidade_ponto_calibracao(request):

    try:
        if request.method == 'POST':
            with transaction.atomic():
                data = json.loads(request.body)
                unidade_instrumento = data.get("unidade-instrumento").strip()

                if Unidade.objects.filter(nome__iexact=unidade_instrumento).exists():
                    return JsonResponse({'status': 'error', 'message': 'Este tipo de unidade já existe'}, status=400)

                if unidade_instrumento and unidade_instrumento != "":
                    Unidade.objects.create(
                        nome=unidade_instrumento
                    )

                return JsonResponse({"data":data})
        else:
            return JsonResponse({"message": "Método não permitido"}, status=405)
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def add_laboratorio(request):

    try:
        if request.method == 'POST': 

            with transaction.atomic():

                    data = json.loads(request.body)

                    laboratorio_instrumento = data.get("laboratorio-instrumento").strip()

                    if Laboratorio.objects.filter(nome__iexact=laboratorio_instrumento).exists():
                        return JsonResponse({'status': 'error', 'message': 'Este laboratório já existe'}, status=400)

                    if laboratorio_instrumento and laboratorio_instrumento != "":
                        laboratorio = Laboratorio.objects.create(
                            nome=laboratorio_instrumento,
                            status='ativo'
                        )

                    return JsonResponse({'status': 'Criado com sucesso', 'laboratorio_id':laboratorio.id})
        else:
            return JsonResponse({"message": "Método não permitido"}, status=405)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def edit_ultima_analise(request):

    if request.method == 'POST':
        with transaction.atomic():
            try:
                data = json.loads(request.body)
                
                id = data.get('id-instrumento-ultima-analise')
                incerteza = data.get('incertezaUltimaAnalise')
                tendencia = data.get('tendeciaUltimaAnalise')
                resultado = data.get('resultadoUltimaAnalise')

                # Busca o instrumento ou retorna erro se não existir
                ponto_calibracao = get_object_or_404(PontoCalibracao, id=id)

                # Verifica o status do último envio
                ultimo_envio = Envio.objects.filter(ponto_calibracao=ponto_calibracao).order_by('-id').first()
                if ultimo_envio and ultimo_envio.status == 'enviado':
                    return JsonResponse({"message": "Não é possível editar o ponto de calibração enquanto o item estiver em processo de calibração."}, status=400)

                try:
                    incerteza = float(incerteza) if incerteza is not None else None
                    tendencia = float(tendencia) if tendencia is not None else None
                except Exception as e:
                    return JsonResponse({"message": "Digite os campos corretamente"}, status=400)

                # Busca a análise do certificado associada ao envio
                analise_certificado = AnaliseCertificado.objects.filter(envio=ultimo_envio).first()
                if not analise_certificado:
                    return JsonResponse({"message": "Análise de certificado não encontrada."}, status=404)

                # Dicionário para armazenar alterações
                alteracoes = {}

                # Verifica se houve mudanças nos campos e armazena as alterações
                if analise_certificado.incerteza != incerteza:
                    alteracoes['incerteza'] = incerteza
                if analise_certificado.tendencia != tendencia:
                    alteracoes['tendencia'] = tendencia
                if analise_certificado.analise_certificado != resultado:
                    alteracoes['analise_certificado'] = resultado

                # Se houver mudanças, atualiza e salva o objeto
                if alteracoes:
                    for campo, valor in alteracoes.items():
                        setattr(analise_certificado, campo, valor)
                    analise_certificado.save()
                    return JsonResponse({"message": "Análise de certificado atualizada com sucesso!"})

                return JsonResponse({"message": "Nenhuma alteração realizada."})
            
            except IntegrityError as e:
                return JsonResponse({"message": f"Verifique a tag que está sendo criada já existe: {e}"}, status=400)
            
            except Exception as e:
                return JsonResponse({"message": f"Nenhuma alteração realizada. {e}"}, status=400)

    return JsonResponse({"message": "Método não permitido"}, status=405)

def edit_certificado(request, id):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            dados_envio = Envio.objects.filter(id=id).first()

            print(data)
            print(dados_envio)
            
            if not dados_envio:
                return JsonResponse({"error": "Envio não encontrado"}, status=404)
            
            dados_envio.pdf = data.get('certificado')  # Mais seguro que data.certificado
            dados_envio.save()

            if data.get("certificado"):
                descricao = f'Link do certificado alterado para: <a href="{data.get("certificado")}" target="_blank">Novo link do Certificado</a>'
            else:
                descricao = f'Link do certificado foi removido'

            registrar_instrumento_alterar_link(dados_envio.instrumento, descricao)
            
            return JsonResponse({"success": "Editado com sucesso"}, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"message": "Método não permitido"}, status=405)
