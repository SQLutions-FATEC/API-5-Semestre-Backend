"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import projeto_dashboard_api, projeto_tarefas_timesheet_api, projeto_empenho_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/projetos/<str:codigo_projeto>/', projeto_dashboard_api, name='projeto-detalhe'),
    path(
        'api/projetos/tarefas/<str:codigo_projeto>',
        projeto_tarefas_timesheet_api,
        name='projeto-tarefas-timesheet',
    ),
    path('api/projetos/<str:codigo_projeto>/empenhos/', projeto_empenho_api, name='projeto-empenho'),
]
