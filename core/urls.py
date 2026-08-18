import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.apps import apps
from orders.views import home_redirect


urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
     # Главная страница — редирект по ролям
    path('', home_redirect, name='home'),
    path('orders/', include('orders.urls'))
]

# Модули (если есть)
if apps.is_installed('employees'):
    urlpatterns.append(path('employees/', include('employees.urls')))
    
if apps.is_installed('customers'):
    urlpatterns.append(path('customers/', include('customers.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)