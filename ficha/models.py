from django.db import models
from django.utils import timezone
from datetime import datetime
from cadastro.models import InfoInstrumento, Funcionario

class AssinaturaInstrumento(models.Model):
    instrumento = models.ForeignKey(InfoInstrumento, on_delete=models.CASCADE, related_name='assinatura_instrumento',default=False)
    assinante = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, blank=True, null=True)
    data_assinatura = models.DateTimeField(auto_now_add=True)
    data_entrega = models.DateTimeField(default=timezone.now, blank=True)
    foto_assinatura = models.ImageField(upload_to='assinaturas_fotos/', null=True, blank=True)
    motivo = models.CharField(max_length=100, blank=False, null=False,default='Devolução')

    def __str__(self):
        return f'Assinatura de {self.assinante.nome if self.assinante else "N/A"} em {self.data_assinatura.strftime("%d/%m/%Y %H:%M:%S")}'

    class Meta:
        verbose_name = "Assinatura de Instrumento"
        verbose_name_plural = "Assinaturas de Instrumentos"
        ordering = ['-data_assinatura']
