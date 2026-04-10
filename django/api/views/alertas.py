from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoCompra, DimSolicitacao, DimMaterial
from .utils import _dim_data_para_date, _normaliza_texto

@require_GET
def projeto_alertas_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    data_atual = date.today()
    limite_pedido_recente = data_atual - timedelta(days=30)

    compras = (
        FatoCompra.objects
        .filter(solicitacao__projeto=projeto)
        .select_related('data_previsao_entrega', 'data_pedido', 'solicitacao__material')
        .order_by('numero_pedido')
    )

    pedidos_atrasados = []
    pedidos_prioritarios_pendentes = []
    materiais_pedidos_recentes_ids = set()

    for compra in compras:
        data_previsao_entrega = _dim_data_para_date(compra.data_previsao_entrega)
        data_pedido = _dim_data_para_date(compra.data_pedido)
        status_normalizado = _normaliza_texto(compra.status)
        prioridade_normalizada = _normaliza_texto(compra.solicitacao.prioridade)

        if data_previsao_entrega and data_atual > data_previsao_entrega and status_normalizado != 'concluida':
            pedidos_atrasados.append({
                'numero_pedido': compra.numero_pedido,
                'status': compra.status,
                'data_previsao_entrega': data_previsao_entrega.isoformat(),
                'dias_atraso': (data_atual - data_previsao_entrega).days,
            })

        if prioridade_normalizada in {'alta', 'urgente'} and status_normalizado in {'aberto', 'enviado'}:
            pedidos_prioritarios_pendentes.append({
                'numero_pedido': compra.numero_pedido,
                'prioridade': compra.solicitacao.prioridade,
                'status': compra.status,
                'data_pedido': data_pedido.isoformat() if data_pedido else None,
            })

        if data_pedido and data_pedido >= limite_pedido_recente:
            materiais_pedidos_recentes_ids.add(compra.solicitacao.material_id)

    materiais_obsoletos_vinculados_ids = set(
        DimSolicitacao.objects
        .filter(projeto=projeto, material__status__iexact='Obsoleto')
        .values_list('material_id', flat=True)
    )

    materiais_obsoletos_criticos_ids = materiais_obsoletos_vinculados_ids | materiais_pedidos_recentes_ids

    materiais_obsoletos_qs = (
        DimMaterial.objects
        .filter(id__in=materiais_obsoletos_criticos_ids, status__iexact='Obsoleto')
        .order_by('codigo_material')
    )

    materiais_obsoletos = [
        {
            'codigo_material': material.codigo_material,
            'descricao': material.descricao,
            'status': material.status,
            'vinculado_ao_projeto': material.id in materiais_obsoletos_vinculados_ids,
            'pedido_recente': material.id in materiais_pedidos_recentes_ids,
        }
        for material in materiais_obsoletos_qs
    ]

    return JsonResponse({
        'projeto': {
            'codigo': projeto.codigo_projeto,
            'nome': projeto.nome_projeto,
        },
        'data_referencia': data_atual.isoformat(),
        'alertas_criticos': {
            'pedidos_atrasados': pedidos_atrasados,
            'pedidos_prioritarios_pendentes': pedidos_prioritarios_pendentes,
            'materiais_obsoletos': materiais_obsoletos,
        },
    })