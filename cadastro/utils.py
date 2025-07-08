from django.utils import timezone

from cadastro.models import HistoricoInstrumento

def registrar_envio_calibracao(instrumento, ponto_calibracao, descricao):
    """
    Registra no histórico o envio do ponto de calibração do instrumento para calibração.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        ponto_calibracao=ponto_calibracao,
        tipo_mudanca='enviado',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_recebimento_calibracao(instrumento, ponto_calibracao, descricao):
    """
    Registra no histórico o recebimento do ponto de calibração do instrumento após a calibração.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        ponto_calibracao=ponto_calibracao,
        tipo_mudanca='recebido',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_analise_ponto(instrumento, ponto_calibracao, descricao):
    """
    Registra no histórico a análise realizada em um ponto de calibração do instrumento.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        ponto_calibracao=ponto_calibracao,
        tipo_mudanca='analisado',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_mudanca_responsavel(instrumento, descricao):
    """
    Função genérica para registrar um tipo de mudança customizado no histórico.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        tipo_mudanca='troca_responsavel',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_primeiro_responsavel(instrumento, descricao):
    """
    Função genérica para registrar um tipo de mudança customizado no histórico.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        tipo_mudanca='atribuicao',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_instrumento_danificado(instrumento, descricao):
    """
    Registra no histórico o instrumento danificado.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        tipo_mudanca='danificado',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_instrumento_devolucao(instrumento, descricao):
    """
    Registra no histórico o instrumento devolvido.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        tipo_mudanca='devolucao',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )

def registrar_instrumento_alterar_link(instrumento, descricao):
    """
    Registra no histórico o instrumento devolvido.
    """

    HistoricoInstrumento.objects.create(
        instrumento=instrumento,
        tipo_mudanca='link_modificado',
        descricao_mudanca=descricao,
        data_mudanca=timezone.now()
    )