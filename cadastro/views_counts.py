from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import F, Q, Count, OuterRef, Subquery, Func, Value

from cadastro.models import InfoInstrumento
from inspecao.models import Envio

from datetime import timedelta

hoje = timezone.now().date()

@login_required
def dashboard_counts(request):
    try:
        em_uso = InfoInstrumento.objects.filter(status_instrumento='em_uso').count()
        disponivel = InfoInstrumento.objects.filter(status_instrumento='ativo').count()
        danificado = InfoInstrumento.objects.filter(status_instrumento='danificado').count()
        em_calibracao = InfoInstrumento.objects.filter(envios__status='enviado').distinct().count()

        return JsonResponse({
            'em_calibracao': em_calibracao,
            'em_uso': em_uso,
            'disponivel': disponivel,
            'danificado': danificado,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def counts_atrasado(request):

    try:
        ultimo_envio = (
            Envio.objects.filter(instrumento_id=OuterRef('pk'))
            .order_by('-data_envio', '-id')
        )

        # Query principal: conta instrumentos cujo prazo já venceu
        total_vencidos = (
            InfoInstrumento.objects.annotate(
                envio_status=Subquery(ultimo_envio.values('status')[:1])
            )
            .filter(
                ~Q(status_instrumento='danificado'),
                proxima_calibracao__lt=hoje,  # CURRENT_DATE > proxima_calibracao
            )
            .count()
        )

        return JsonResponse({
            'em_atraso': total_vencidos,
        })
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
