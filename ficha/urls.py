from django.urls import path
from . import views

urlpatterns = [
    path('ficha/',views.ficha_por_funcionario,name='ficha'),
    path('gerar_ficha/<int:id>',views.emissao_ficha_por_funcionario,name='emitir_ficha')
]