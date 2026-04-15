from django.db.models import F, ExpressionWrapper, DecimalField
from datetime import date
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimSolicitacao, DimProjeto
from .utils import _dim_data_para_date

@require_GET
def listagem_solicitacoes(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    solicitacoes = DimSolicitacao.objects.filter(
        projeto = projeto
    ).select_related(
        'material_id',
        'data_solicitacao'
    ).prefetch_related(
        'fatocompra_set'
    ).annotate(
        valor_total_estimado=ExpressionWrapper(
            F('quantidade') * F('material__custo_estimado'),
            output_field=DecimalField()
        )
    )

    return null