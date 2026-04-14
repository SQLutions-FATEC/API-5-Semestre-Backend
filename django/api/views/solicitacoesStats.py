from datetime import date
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimSolicitacao, DimProjeto
from .utils import _dim_data_para_date

@require_GET
def request_analytics_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    total_pendentes = DimSolicitacao.objects.filter(
        projeto = projeto,
        status__iexact = 'aberto'
    ).count()

    solicitacoes_criticas = DimSolicitacao.objects.filter(
        projeto = projeto,
        status__iexact = 'pendente',
        prioridade__in=['ALTA', 'URGENTE','Alta','Urgente']
    ).select_related('data_solicitacao')

    hoje = date.today()
    lista_urgentes = []

    for sol in solicitacoes_criticas:
        data_criacao = _dim_data_para_date(sol.data_solicitacao)
        dias_pendentes = (hoje - data_criacao).days if data_criacao else 0

        lista_urgentes.append({
            "numero_solicitacao": sol.numero_solicitacao,
            "prioridade": sol.prioridade,
            "status": sol.status,
            "dias_desde_criacao": dias_pendentes
        })

    data = {
        "projeto": projeto.codigo_projeto,
        "estatisticas": {
            "total_pendentes": total_pendentes,
            "urgentes_criticas": lista_urgentes
        }
    }
    return JsonResponse(data)





