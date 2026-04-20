from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoCompra

@require_GET
def detalhamento_gastos_projeto_api(request, codigo_projeto):
    #busca o projeto ou retorna 404
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    #busca todos os pedidos vinculados ao projeto através da solicitação
    #otimiza a busca trazendo material e fornecedor junto
    pedidos_qs = FatoCompra.objects.filter(
        solicitacao__projeto=projeto
    ).select_related(
        'solicitacao__material',
        'fornecedor'
    ).order_by('-valor_total')

    #calcula o gasto total consolidado
    gasto_total_consolidado = pedidos_qs.aggregate(
        total=Sum('valor_total')
    )['total'] or 0.0

    #monta a lista detalhada
    lista_pedidos = [
        {
            "numero_pedido": pedido.numero_pedido,
            "material_nome": pedido.solicitacao.material.descricao,
            "fornecedor_nome": pedido.fornecedor.razao_social,
            "valor_total_pedido": float(pedido.valor_total),
            "status": pedido.status
        }
        for pedido in pedidos_qs
    ]

    response_data = {
        "projeto": {
            "codigo": projeto.codigo_projeto,
            "nome": projeto.nome_projeto
        },
        "gasto_total_consolidado": float(gasto_total_consolidado),
        "pedidos": lista_pedidos
    }

    return JsonResponse(response_data)
