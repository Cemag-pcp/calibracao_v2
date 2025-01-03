from django.db import models
from django.urls import reverse
from django.core.files import File
from django.contrib.auth.models import User

import qrcode
from io import BytesIO
from PIL import Image
from datetime import timedelta, date

class Setor(models.Model):

    nome = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Setor"
        verbose_name_plural = "Setores"
        ordering = ['nome']

class Funcionario(models.Model):

    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    )

    matricula = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='ativo')

    def __str__(self):
        return f'{self.matricula} - {self.nome}'

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ['nome']

class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nome']

class Unidade(models.Model):

    nome = models.CharField(max_length=20)
    
    def __str__(self):
        return self.nome

class TipoInstrumento(models.Model):

    nome = models.CharField(max_length=100 ,unique=True)

    def __str__(self):
        return self.nome

class PontoCalibracao(models.Model):
    STATUS_PONTO_CALIBRACAO_CHOICES = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo')
    )
    descricao = models.CharField(max_length=100)
    instrumento = models.ForeignKey(
        'InfoInstrumento', 
        on_delete=models.CASCADE, 
        related_name='pontos_calibracao'
    )
    unidade = models.ForeignKey('Unidade', on_delete=models.CASCADE)
    faixa_nominal = models.CharField(max_length=50)
    unidade = models.CharField(max_length=20)
    tolerancia_admissivel = models.FloatField(blank=True, null=True)
    status_ponto_calibracao = models.CharField(
        max_length=10, 
        choices=STATUS_PONTO_CALIBRACAO_CHOICES, 
        default='ativo'
    )

    def __str__(self):
        return f'{self.descricao} ({self.faixa_nominal} {self.unidade})'

    class Meta:
        verbose_name = "Ponto de Calibração"
        verbose_name_plural = "Pontos de Calibração"

class InfoInstrumento(models.Model):
    STATUS_INSTRUMENTO_CHOICES = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('em_uso', 'Em uso'),
        ('desuso', 'Desuso'),
        ('danificado', 'Danificado'),
    )

    tag = models.CharField(max_length=50, unique=True)
    tipo_instrumento = models.ForeignKey(
        'TipoInstrumento', 
        on_delete=models.CASCADE, 
        related_name='tipo_instrumento'
    )
    marca = models.ForeignKey('Marca', on_delete=models.CASCADE)
    status_instrumento = models.CharField(
        max_length=10, 
        choices=STATUS_INSTRUMENTO_CHOICES, 
        default='ativo'
    )
    tempo_calibracao = models.IntegerField(
        help_text='Tempo entre uma calibração e outra (em dias)'
    )
    ultima_calibracao = models.DateField()
    proxima_calibracao = models.DateField(blank=True, null=True)
    qrcode = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.ultima_calibracao:
            self.proxima_calibracao = self.ultima_calibracao + timedelta(days=self.tempo_calibracao)

        super().save(*args, **kwargs)

        if not self.qrcode:
            url = reverse('instrumento_detail', kwargs={'pk': self.pk})
            qr = qrcode.make(f'{self.get_full_url()}{url}')
            qr_io = BytesIO()
            qr.save(qr_io, 'PNG')
            qr_file = File(qr_io, name=f'{self.tag}_qrcode.png')
            self.qrcode = qr_file
            super().save(*args, **kwargs)

    def get_full_url(self):
        return 'http://127.0.0.1:8000'

    def __str__(self):
        return f'{self.tag} - {self.tipo_instrumento.nome} - {self.marca.nome} - {self.status_instrumento}'

    class Meta:
        verbose_name = "Informação do Instrumento"
        verbose_name_plural = "Informações dos Instrumentos"
        ordering = ['tipo_instrumento']

class DesignarInstrumento(models.Model):
    
    instrumento_escolhido = models.ForeignKey(InfoInstrumento, on_delete=models.CASCADE, related_name='designar_instrumento')
    responsavel = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, blank=True, null=True)
    data_entrega_funcionario = models.DateField()
    pdf = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Verifica se o instrumento está ativo antes de atribuir
        if self.instrumento_escolhido.status_instrumento != 'ativo' and not self.pk:
            raise ValueError("O instrumento só pode ser atribuído se estiver 'ativo'.")

        # Atualiza o status do instrumento
        self.instrumento_escolhido.status_instrumento = 'em_uso' if self.responsavel else 'ativo'
        self.instrumento_escolhido.save()

        # Salva o objeto
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Se a designação for deletada, verifica se o instrumento deve voltar ao status 'ativo'
        if not DesignarInstrumento.objects.filter(instrumento_escolhido=self.instrumento_escolhido).exclude(pk=self.pk).exists():
            self.instrumento_escolhido.status_instrumento = 'ativo'
            self.instrumento_escolhido.save()

        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.instrumento_escolhido.tag} - {self.instrumento_escolhido.tipo_instrumento.nome} - Responsável: {self.responsavel.nome if self.responsavel else "N/A"}'

    class Meta:
        verbose_name = "Designação de Instrumento"
        verbose_name_plural = "Designações de Instrumentos"
        ordering = ['instrumento_escolhido']

class HistoricoInstrumento(models.Model):

    TIPO_MUDANCA_CHOICES = [
        ('enviado', 'Enviado'),
        ('recebido', 'Recebido'),
        ('analisado', 'Analisado'),
        ('troca_reponsavel', 'Troca de responsável'),
        ('primeira_atribuicao','Primeira atribuição')
    ]

    instrumento = models.ForeignKey(InfoInstrumento, on_delete=models.CASCADE, related_name='historico')
    ponto_calibracao = models.ForeignKey(PontoCalibracao, on_delete=models.CASCADE, related_name='ponto_calibracao_historico', null=True)
    tipo_mudanca = models.CharField(max_length=50,choices=TIPO_MUDANCA_CHOICES,help_text="Tipo da mudança ocorrida (ex: enviado, recebido, analisado).")
    data_mudanca = models.DateTimeField(auto_now_add=True)
    descricao_mudanca = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Histórico de {self.instrumento.tipo_instrumento.nome} - {self.data_mudanca}'

    class Meta:
        verbose_name = "Histórico de Instrumento"
        verbose_name_plural = "Históricos de Instrumentos"
        ordering = ['-data_mudanca']

class Operadores(models.Model):

    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    )

    matricula = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='ativo')

    def __str__(self):
        return f'{self.matricula} - {self.nome}'

    class Meta:
        verbose_name = "Operadores"
        verbose_name_plural = "Operadoress"
        ordering = ['nome']
