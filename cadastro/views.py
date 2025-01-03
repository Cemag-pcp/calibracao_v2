from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db.models import Q

from inspecao.models import Envio, Laboratorio, AnaliseCertificado
from .models import InfoInstrumento, HistoricoInstrumento, Funcionario, DesignarInstrumento, Operadores, PontoCalibracao
from cadastro.utils import *

from datetime import datetime
import json

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
    funcionarios = Funcionario.objects.all()

    return render(request, "home.html", {'laboratorios':laboratorios,
                                         'operadores':operadores,
                                         'naturezas':naturezas,
                                         'metodos':metodos,
                                         'funcionarios':funcionarios})

def instrumentos_data(request):
    hoje = datetime.now().date()

    # Coleta os instrumentos
    instrumentos = InfoInstrumento.objects.all()

    # Processar os dados para DataTable
    instrumentos_detalhes = {}
    for instrumento in instrumentos:

        # Adiciona os detalhes dos pontos de calibração
        pontos_calibracao = instrumento.pontos_calibracao.all()  # Obtém todos os pontos relacionados ao instrumento

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
                responsavel = f"{designacao.responsavel.matricula} - {designacao.responsavel.nome}"
            else:
                responsavel = None

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
                    'responsavel': responsavel,
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
            # Parse do corpo da requisição
            data = json.loads(request.body)
            
            link_ficha=data.get('linkFicha')
            
            data_entrega_str = data.get('dataEntrega')
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
                descricao = f"Mudando responsável de: {designacao.responsavel.matricula} - {designacao.responsavel.nome} para: {funcionario_object.matricula} - {funcionario_object.nome}\nLink da ficha assinada: {link_ficha if link_ficha else 'Pendente'}"
                registrar_mudanca_responsavel(instrumento_object,descricao=descricao)
                
                designacao.responsavel = funcionario_object
                designacao.data_entrega_funcionario=data_entrega
                designacao.pdf=link_ficha
                designacao.save()

            else:
                # Cria uma nova designação
                descricao = f"Atribuindo a responsabilidade para: {funcionario_object.matricula} - {funcionario_object.nome}"
                registrar_primeiro_responsavel(instrumento_object,descricao=descricao)

                DesignarInstrumento.objects.create(
                    instrumento_escolhido=instrumento_object,
                    responsavel=funcionario_object,
                    data_entrega_funcionario=data_entrega
                )

            return JsonResponse({'status': 'success',}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erro ao processar o JSON enviado'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)