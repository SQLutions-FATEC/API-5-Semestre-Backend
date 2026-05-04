from datetime import date
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoCompra
from django.db.models import Count

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

@require_GET
def evolucao_gastos_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    # Informações de debug se a query vier com ?debug=true
    is_debug = request.GET.get('debug', 'false').lower() == 'true'
    debug_info = {}
    
    if is_debug:
        todas_compras = FatoCompra.objects.filter(solicitacao__projeto=projeto)
        debug_info = {
            "total_compras_geral": todas_compras.count(),
            "compras_por_status": list(todas_compras.values('status').annotate(total=Count('id'))),
            "codigo_projeto": projeto.codigo_projeto,
            "data_inicio_projeto": f"{projeto.data_inicio.ano}-{projeto.data_inicio.mes:02d}"
        }

    gastos_agrupados = (
        FatoCompra.objects.filter(
            solicitacao__projeto=projeto,
            status__in=["ENVIADO", "ENTREGUE", "PARCIALMENTE ENTREGUE"]
        )
        .values('data_pedido__ano', 'data_pedido__mes')
        .annotate(total=Sum('valor_total'))
        .order_by('data_pedido__ano', 'data_pedido__mes')
    )

    dados_dict = {
        (g['data_pedido__ano'], g['data_pedido__mes']): float(g['total'] or 0)
        for g in gastos_agrupados
    }

    if not dados_dict:
        if is_debug:
            return JsonResponse({"resultado": [], "debug": debug_info})
        return JsonResponse([], safe=False)

    anos_meses = list(dados_dict.keys())
    
    ano_inicio = projeto.data_inicio.ano
    mes_inicio = projeto.data_inicio.mes
    ano_fim, mes_fim = max(anos_meses)

    if min(anos_meses) < (ano_inicio, mes_inicio):
        ano_inicio, mes_inicio = min(anos_meses)

    resultado = []
    ano_atual, mes_atual = ano_inicio, mes_inicio

    while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
        total = dados_dict.get((ano_atual, mes_atual), 0.0)
        data_str = f"{ano_atual}-{mes_atual:02d}"
        resultado.append({
            "data": data_str,
            "total_gasto": total,
        })

        mes_atual += 1
        if mes_atual > 12:
            mes_atual = 1
            ano_atual += 1

    if is_debug:
        return JsonResponse({"resultado": resultado, "debug": debug_info})

    return JsonResponse(resultado, safe=False)
