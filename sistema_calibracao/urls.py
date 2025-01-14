from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inspecao.urls')),
    path('', include('cadastro.urls')),
    path('', include('ficha.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
