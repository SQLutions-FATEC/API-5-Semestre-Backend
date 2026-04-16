from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoCompra, DimSolicitacao, DimMaterial
from .utils import _dim_data_para_date, _normaliza_texto


def _adiciona_pedido_atrasado(pedidos_atrasados, compra, data_atual, data_previsao_entrega, status_normalizado):
    if not data_previsao_entrega or data_atual <= data_previsao_entrega or status_normalizado == 'concluida':
        return

    pedidos_atrasados.append({
        'numero_pedido': compra.numero_pedido,
        'status': compra.status,
        'data_previsao_entrega': data_previsao_entrega.isoformat(),
        'dias_atraso': (data_atual - data_previsao_entrega).days,
    })


def _adiciona_pedido_prioritario_pendente(pedidos_prioritarios_pendentes, compra, data_pedido, prioridade_normalizada, status_normalizado):
    if prioridade_normalizada not in {'alta', 'urgente'} or status_normalizado not in {'aberto', 'enviado'}:
        return

    pedidos_prioritarios_pendentes.append({
        'numero_pedido': compra.numero_pedido,
        'prioridade': compra.solicitacao.prioridade,
        'status': compra.status,
        'data_pedido': data_pedido.isoformat() if data_pedido else None,
    })


def _adiciona_material_pedido_recente(materiais_pedidos_recentes_ids, compra, data_pedido, limite_pedido_recente):
    if data_pedido and data_pedido >= limite_pedido_recente:
        materiais_pedidos_recentes_ids.add(compra.solicitacao.material_id)


def _serializa_pedido_recente(compra):
    data_solicitacao = _dim_data_para_date(compra.solicitacao.data_solicitacao)
    data_pedido = _dim_data_para_date(compra.data_pedido)
    data_previsao = _dim_data_para_date(compra.data_previsao_entrega)

    return {
        'pedido': {
            'numero_pedido': compra.numero_pedido,
            'status': compra.status,
            'valor_total': float(compra.valor_total),
            'data_pedido': data_pedido.isoformat() if data_pedido else None,
            'data_previsao_entrega': data_previsao.isoformat() if data_previsao else None,
            'solicitacao_numero': data_solicitacao.isoformat() if data_solicitacao else None,
        }
    }

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
    ultimas_solicitacoes_com_pedido = []
    
    materiais_pedidos_recentes_ids = set()

    for compra in compras:
        data_previsao_entrega = _dim_data_para_date(compra.data_previsao_entrega)
        data_pedido = _dim_data_para_date(compra.data_pedido)
        status_normalizado = _normaliza_texto(compra.status)
        prioridade_normalizada = _normaliza_texto(compra.solicitacao.prioridade)

        _adiciona_pedido_atrasado(
            pedidos_atrasados,
            compra,
            data_atual,
            data_previsao_entrega,
            status_normalizado,
        )
        _adiciona_pedido_prioritario_pendente(
            pedidos_prioritarios_pendentes,
            compra,
            data_pedido,
            prioridade_normalizada,
            status_normalizado,
        )
        _adiciona_material_pedido_recente(
            materiais_pedidos_recentes_ids,
            compra,
            data_pedido,
            limite_pedido_recente,
        )

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
    
    solicitacoes_aprovadas_recentes = (
        DimSolicitacao.objects
        .filter(projeto=projeto, status__iexact='Aprovada')
        .order_by(
            '-data_solicitacao__ano',
            '-data_solicitacao__mes',
            '-data_solicitacao__dia',
            '-id',
        )[:3]
    )

    compras_recentes = (
        FatoCompra.objects
        .filter(solicitacao__in=solicitacoes_aprovadas_recentes)
        .select_related('solicitacao__data_solicitacao', 'data_pedido', 'data_previsao_entrega')
        .order_by(
            '-solicitacao__data_solicitacao__ano',
            '-solicitacao__data_solicitacao__mes',
            '-solicitacao__data_solicitacao__dia',
            '-solicitacao_id',
            '-id',
        )
    )

    for compra in compras_recentes:
        ultimas_solicitacoes_com_pedido.append(_serializa_pedido_recente(compra))

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
            'solicitacoes_para_projetos': ultimas_solicitacoes_com_pedido,
        },
    })
