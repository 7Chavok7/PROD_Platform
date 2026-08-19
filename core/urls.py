# core/urls.py
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from employees.views import home_redirect


urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
     # Главная страница — редирект по ролям
    path('', home_redirect, name='home'),
    
    # Модули
    path('employees/', include('employees.urls')),
    path('customers/', include('customers.urls')),
    path('orders/', include('orders.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)