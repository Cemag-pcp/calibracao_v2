from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from cadastro.models import InfoInstrumento


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

