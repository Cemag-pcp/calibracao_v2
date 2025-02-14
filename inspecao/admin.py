from django.contrib import admin

from .models import Envio,Laboratorio,AnaliseCertificado, Versao

class EnvioAdmin(admin.ModelAdmin):
    list_display = ('instrumento', 'status', 'data_envio', 'data_retorno', 'responsavel_envio')
    list_filter = ('status', 'data_envio')
    search_fields = ('instrumento__nome',)

class VersaoAdmin(admin.ModelAdmin):
    list_display = ('id','numero', 'data_lancamento', 'tipo', 'descricao')
    list_filter = ('status', 'data_envio')
    search_fields = ('instrumento__nome',)


admin.site.register(Envio, EnvioAdmin)
admin.site.register(Laboratorio)
admin.site.register(AnaliseCertificado)
admin.site.register(Versao)

