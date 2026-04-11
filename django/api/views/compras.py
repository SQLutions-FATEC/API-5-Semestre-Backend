from datetime import date
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoCompra

@require_GET
def compras_projeto_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    compras = FatoCompra.objects.filter(
        solicitacao__projeto=projeto
    ).select_related(
        'fornecedor',
        'data_pedido',
        'data_previsao_entrega',
        'solicitacao__projeto'
    )

    lista_compras = []
    soma_dias_entrega = 0
    quantidade_pedidos = 0

    for compra in compras:
        dt_pedido = compra.data_pedido
        dt_previsao = compra.data_previsao_entrega

        data_emissao = date(dt_pedido.ano, dt_pedido.mes, dt_pedido.dia)
        data_previsao = date(dt_previsao.ano, dt_previsao.mes, dt_previsao.dia)

        dias_previstos = (data_previsao - data_emissao).days

        soma_dias_entrega += dias_previstos
        quantidade_pedidos += 1

        lista_compras.append({
            "numero": compra.numero_pedido,
            "emissao": data_emissao.strftime("%Y-%m-%d"),
            "previsao": data_previsao.strftime("%Y-%m-%d"),
            "fornecedor": compra.fornecedor.razao_social,
            "nome_material": compra.solicitacao.material.descricao,
            "status": compra.status,
            "dias_previstos_entrega": dias_previstos
        })
    
    tempo_medio = round(soma_dias_entrega / quantidade_pedidos, 2) if quantidade_pedidos > 0 else 0.0

    return JsonResponse({
        "projeto": projeto.codigo_projeto,
        "tempo_medio_entrega_dias": tempo_medio,
        "pedidos": lista_compras
    })