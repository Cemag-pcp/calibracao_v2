from django.urls import path

from . import views

urlpatterns = [
    path('enviar-calibracao/', views.enviar_view, name='enviar_view'),
    path('receber-calibracao/', views.receber_view, name='receber_view'),
    path('analisar-calibracao/', views.analisar_view, name='analisar_view'),

    path('instrumento/info/<int:pk_ponto>/<int:id_envio>/', views.info_instrumento, name='info_instrumento'),
    path('instrumento/info/ultima_analise/<int:pk_ponto>/<int:id_envio>/', views.info_instrumento_ultima_analise, name='info_instrumento'),
    path('home/versoes', views.versoes, name='versoes')

]
