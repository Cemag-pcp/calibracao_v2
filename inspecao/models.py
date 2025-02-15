from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User

from cadastro.models import InfoInstrumento, Operadores, PontoCalibracao

from datetime import timedelta, date

class Laboratorio(models.Model):

    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    )

    nome = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f'{self.nome} - {self.status}'

    class Meta:
        verbose_name = "Laboratório"
        verbose_name_plural = "Laboratórios"
        ordering = ['nome']

class Envio(models.Model):
    
    STATUS_CHOICES = (
        ('enviado', 'Enviado'),
        ('recebido', 'Recebido'),
    )

    NATUREZA_CHOICES = (
        ('verificacao', 'Verificação'),
        ('calibracao', 'Calibração'),
    )

    METODO_CHOICES = (('interno','Interno'),('externo','Externo'))

    instrumento = models.ForeignKey(InfoInstrumento, on_delete=models.CASCADE, related_name='envios')
    ponto_calibracao = models.ForeignKey(PontoCalibracao, on_delete=models.CASCADE, related_name='ponto')
    responsavel_envio = models.ForeignKey(Operadores, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsavel_envio')
    data_envio = models.DateField(null=True, blank=True)
    data_retorno = models.DateField(null=True, blank=True)
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE)
    natureza = models.CharField(max_length=20, choices=NATUREZA_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    pdf = models.URLField(null=True, blank=True)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    analise = models.BooleanField(default=False, null=True)

    def calcular_proxima_calibracao(self):
        """Calcula e define a data da próxima calibração."""
        if self.data_retorno and self.instrumento.tempo_calibracao:
            self.instrumento.ultima_calibracao = self.data_retorno
            data_prox_calibracao = self.data_retorno + timedelta(days=self.instrumento.tempo_calibracao)
            self.instrumento.proxima_calibracao = data_prox_calibracao

            self.instrumento.save()  # Salva a alteração no modelo InfoInstrumento

    class Meta:
        verbose_name = "Envio"
        verbose_name_plural = "Envios"
        ordering = ['data_envio']

class AnaliseCertificado(models.Model):
    ANALISE_CERTIFICADO_CHOICES = (('aprovado', 'Aprovado'), ('reprovado', 'Reprovado'))

    envio = models.ForeignKey(Envio, on_delete=models.CASCADE, related_name='analise_envio')
    analise_certificado = models.CharField(max_length=20, choices=ANALISE_CERTIFICADO_CHOICES, blank=True, null=True)
    incerteza = models.FloatField(blank=True, null=True)
    tendencia = models.FloatField(blank=True, null=True)
    responsavel_analise = models.ForeignKey(Operadores, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsavel_analise')
    data_analise = models.DateField(blank=True, null=True)

class Versao(models.Model):
    
    TIPO_CHOICES = (
        ('bug', 'Bug'),
        ('funcionalidade', 'Funcionalidade'),
        ('implementacao', 'Implementação'),
    )
    
    numero = models.CharField(max_length=10, unique=True, blank=True)
    data_lancamento = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField()

    def save(self, *args, **kwargs):
        if not self.pk:  # Só gera uma nova versão se for um novo registro
            ultima_versao = Versao.objects.order_by('-data_lancamento').first()

            if ultima_versao:
                partes = [int(x) for x in ultima_versao.numero.split('.')]  # Divide a versão em [X, Y, Z]
            else:
                partes = [0, 0, 0]  # Se não houver versões, inicia com "1.0.0"

            # Define o incremento com base no tipo de alteração
            if self.tipo == 'bug':
                partes[2] += 1  # Ex: 1.0.1 → 1.0.2
            elif self.tipo == 'funcionalidade':
                partes[1] += 1  # Ex: 1.1.0 → 1.2.0
                partes[2] = 0  # Reinicia o último número
            elif self.tipo == 'implementacao':
                partes[0] += 1  # Ex: 2.0.0 → 3.0.0
                partes[1] = 0
                partes[2] = 0  # Reinicia os números menores

            self.numero = f"{partes[0]}.{partes[1]}.{partes[2]}"  # Monta a nova versão

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Versão {self.numero}"
