from django.urls import path
from . import views

urlpatterns = [
    path('instrumento/<int:pk>/', views.instrumento_detail, name='instrumento_detail'),

    path('home/', views.home, name='home'),
    path('instrumentos-data/', views.instrumentos_data, name='instrumentos_data'),

    path('instrumento/qrcode/<str:tag>/', views.qrcode_view, name='qrcode_view'),
    path('instrumento/historico/<str:tag>/<int:pk_ponto>/', views.historico_view, name='historico_view'),

    path('substituir-instrumento/', views.substituir_instrumento, name='substituir_instrumento'),
    path('escolher-responsavel/', views.escolher_responsavel, name='escolher_responsavel'),
    path('editar-responsavel/', views.editar_responsavel, name='editar_responsavel'),

]
