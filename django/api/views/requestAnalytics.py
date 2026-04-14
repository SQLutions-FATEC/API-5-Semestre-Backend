from datetime import date
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimSolicitacao
from .utils import _dim_data_para_date

@require_GET
def request_analytics_api(request, codigo_projeto):
    projeto = get_object_or_404(codigo_projeto=codigo_projeto)

    total_pendentes = DimSolicitacao.objects.filter(
        projeto = projeto,
        status__iexact = 'aberto'
    ).count()

    solicitacoes_criticas = DimSolicitacao.objects.filter(
        projeto = projeto,
        status__iexact = 'aberto',
        prioridadade__in=['ALTA', 'URGENTE']
    ).select_related('data_solicitacao')


