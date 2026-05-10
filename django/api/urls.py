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
from .views import (
    projeto_dashboard_api, 
    projeto_alertas_api, 
    projeto_tarefas_timesheet_api,
    projeto_empenho_api,
    compras_projeto_api,
    empenhos_programa,
    programa_api,
    request_analytics_api,
    listagem_solicitacoes,
    evolucao_gastos_api,
    busca_projetos,
    detalhamento_gastos_projeto_api,
    projeto_sem_filtro,
    otimizacao_sobras_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/<str:programa_cod>/projetos/busca/', busca_projetos, name='busca-projetos-programa'),
    path('api/projetos/<str:codigo_projeto>/', projeto_dashboard_api, name='projeto-detalhe'),
    path('api/projetos/<str:codigo_projeto>/compras/', compras_projeto_api, name='compras_projeto'),
    path('api/projetos/<str:codigo_projeto>/gastos/evolucao/', evolucao_gastos_api, name='evolucao-gastos'),
    path('api/empenhos-programa/', empenhos_programa, name='empenhos-programa'),
    path('api/<str:programa_cod>/projetos/', projeto_sem_filtro, name='projeto-sem-filtro'),
    path('api/programas/busca/', programa_api, name='programa-projetos'),
     path(
        'api/projetos/tarefas/<str:codigo_projeto>',
        projeto_tarefas_timesheet_api,
        name='projeto-tarefas-timesheet',
    ),
    path(
        'api/projetos/criticos/<str:codigo_projeto>',
        projeto_alertas_api,
        name='projeto-alertas',
    ), 
    path(
        'api/projetos/<str:codigo_projeto>/empenhos/', 
        projeto_empenho_api, 
        name='projeto-empenho'
    ),
    path(
        'api/projetos/<str:codigo_projeto>/solicitacoes/stats/',
        request_analytics_api, 
        name='projeto-solicitacoes-stats'
    ),
    path(
        'api/projetos/<str:codigo_projeto>/solicitacoes/detalhes/',
        listagem_solicitacoes, 
        name='projeto-solicitacoes-detalhes'
    ),
    path(
        'api/projetos/<str:codigo_projeto>/gastos/detalhes/',
        detalhamento_gastos_projeto_api,
        name='projeto-gastos-detalhes',
    ),
    path('api/projetos/<str:codigo_projeto>/estoque/sobras/',
         otimizacao_sobras_api,
         name='projeto-estoque-sobras'),
]
