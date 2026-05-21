from datetime import date
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.db.models import Q
from api.models import DimFornecedor, FatoCompra
from .utils import _dim_data_para_date, _normaliza_texto


@require_GET
def fornecedor_pedidos_api(request, id_fornecedor):
    fornecedor = get_object_or_404(DimFornecedor, codigo_fornecedor=id_fornecedor)

    compras = FatoCompra.objects.filter(fornecedor=fornecedor).select_related(
        'data_pedido',
        'data_previsao_entrega',
        'solicitacao__projeto',
        'solicitacao__material',
    )

    projeto_filtro = request.GET.get('id_projeto', None)
    if projeto_filtro:
        compras = compras.filter(
            Q(solicitacao__projeto__codigo_projeto__icontains=projeto_filtro)
            | Q(solicitacao__projeto__nome_projeto__icontains=projeto_filtro)
        )

    compras = compras.order_by(
        '-data_pedido__ano', '-data_pedido__mes', '-data_pedido__dia'
    )

    data_atual = date.today()
    quantidade_pedidos_totais = 0
    quantidade_atrasos = 0

    lista_pedidos = []

    for compra in compras:
        quantidade_pedidos_totais += 1

        data_pedido = _dim_data_para_date(compra.data_pedido)
        data_previsao = _dim_data_para_date(compra.data_previsao_entrega)

        status_normalizado = _normaliza_texto(compra.status)
        is_atrasado = False

        if (
            data_previsao
            and data_atual > data_previsao
            and status_normalizado
            not in {'entregue', 'cancelado', 'parcialmente entregue'}
        ):
            is_atrasado = True
            quantidade_atrasos += 1

        lista_pedidos.append(
            {
                "codigo_projeto": compra.solicitacao.projeto.codigo_projeto,
                "codigo_do_pedido": compra.numero_pedido,
                "nome_do_material": compra.solicitacao.material.descricao,
                "valor_gasto": float(compra.valor_total),
                "data_pedida": data_pedido.isoformat() if data_pedido else None,
                "data_previsao": data_previsao.isoformat() if data_previsao else None,
                "is_atrasado": is_atrasado,
                "status": compra.status,
            }
        )

    return JsonResponse(
        {
            "fornecedor": fornecedor.razao_social,
            "quantidade_pedidos_totais": quantidade_pedidos_totais,
            "quantidade_atrasos": quantidade_atrasos,
            "pedidos": lista_pedidos,
        }
    )
