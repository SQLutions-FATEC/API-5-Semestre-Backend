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

    lista_detalhes = []

    for sol in solicitacoes:
        data_sol = _dim_data_para_date(sol.data_solicitacao)

        pedido_vinculado = sol.fatocompra_set.first()
        numero_pedido = pedido_vinculado.numero_pedido if pedido_vinculado else None

        lista_detalhes.append({
            "numero_solicitacao": sol.numero_solicitacao,
            "numero_pedido": numero_pedido,
            "nome_material": sol.material.descricao,
            "data_solicitacao": data_sol.isoformat() if data_sol else None,
            "valor_total_estimado": float(sol.valor_total_estimado) if sol.valor_total_estimado else 0.0,
            "status": sol.status
        })

    return JsonResponse({
        "projeto": projeto.codigo_projeto,
        "solicitacoes": lista_detalhes
    })