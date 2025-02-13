from django.urls import path
from . import views

urlpatterns = [
    path('instrumento/<int:pk>/', views.instrumento_detail, name='instrumento_detail'),

    path('home/', views.home, name='home'),
    path('instrumentos-data/', views.instrumentos_data, name='instrumentos_data'),

    path('instrumento/qrcode/<str:tag>/', views.qrcode_view, name='qrcode_view'),
    path('instrumento/historico/<str:tag>/<int:pk_ponto>/', views.historico_view, name='historico_view'),

    path('template-instrumento/', views.template_instrumento, name='template_instrumento'),
    path('add-instrumento/', views.add_instrumento, name='add-instrumentos'),
    path('add-tipo-instrumento/', views.add_tipo_instrumento, name='add-tipo-instrumentos'),

    path('adicionar-ponto-calibracao/', views.adicionar_ponto_calibracao, name='adicionar_ponto_calibracao'),
    path('editar-ponto-calibracao/', views.editar_ponto_calibracao, name='editar-ponto-calibracao'),

    path('add-unidade-ponto-calibracao/', views.add_unidade_ponto_calibracao, name='add_unidade_ponto_calibracao'),
    path('add-laboratorio/', views.add_laboratorio, name='add-laboratorio'),
    path('edit-instrumento/', views.edit_instrumento, name='edit-instrumento'),

    path('editar-ultima-analise/', views.edit_ultima_analise, name='edit-ultima-analise'),

    path('substituir-instrumento/', views.substituir_instrumento, name='substituir_instrumento'),
    path('escolher-responsavel/', views.escolher_responsavel, name='escolher_responsavel'),
    path('editar-responsavel/', views.editar_responsavel, name='editar_responsavel'),

    path('historico/', views.historico, name='historico'),
    path('historico/<int:id>/', views.historico_instrumento, name='historico-instrumento'),
    path('historico/datatable/<int:id>/', views.historico_datatable_instrumento, name='historico-datatable-instrumento'),

    path('designar-mais-instrumentos/', views.designar_instrumentos, name='designar-instrumentos'),
]
