# Dentro de sua_app/views/__init__.py

from .dashboard import projeto_dashboard_api
from .compras import compras_projeto_api, evolucao_gastos_api
from .tarefas import projeto_tarefas_timesheet_api
from .alertas import projeto_alertas_api
from .empenhos import projeto_empenho_api, empenhos_programa
from .solicitacoesStats import request_analytics_api
from .solicitacoesLista import listagem_solicitacoes
from .programas import programa_api, busca_projetos

__all__ = [
    'projeto_dashboard_api',
    'compras_projeto_api',
    'projeto_tarefas_timesheet_api',
    'projeto_alertas_api',
    'projeto_empenho_api',
    'empenhos_programa',
    'request_analytics_api',
    'listagem_solicitacoes',
    'evolucao_gastos_api',
    'programa_api',
    'busca_projetos'
]
