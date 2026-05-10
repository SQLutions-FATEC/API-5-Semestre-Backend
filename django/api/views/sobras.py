from django.http import JsonResponse
from django.db.models import Sum
from django.views.decorators.http import require_GET
from api.models import FatoEstoqueSaldo, DimSolicitacao, FatoCompra
from .utils import obter_projeto

@require_GET
def otimizacao_sobras_api(request, codigo_projeto):
    """
    Retorna alertas de estoque ocioso em projetos concluidos/suspensos
    e verifica conflitos com compras abertas.
    """
    projeto_alvo = obter_projeto(codigo_projeto)
    programa_alvo = projeto_alvo.programa

    # 1. Buscar Sobras (Projetos CONCLUÍDOS/SUSPENSOS do mesmo programa)
    sobras_qs = FatoEstoqueSaldo.objects.filter(
        projeto__programa=programa_alvo,
        quantidade_disponivel__gt=0,
        projeto__status__in=['CONCLUIDO', 'CONCLUÍDO', 'SUSPENSO']
    ).exclude(projeto=projeto_alvo).select_related('material', 'projeto', 'localizacao')

    sobras_por_material = {}
    valor_total_material = 0.0

    for sobra in sobras_qs:
        mat_cod = sobra.material.codigo_material
        if mat_cod not in sobras_por_material:
            sobras_por_material[mat_cod] = {
                'material': sobra.material,
                'total_disponivel': 0,
                'detalhes': []
            }
        sobras_por_material[mat_cod]['total_disponivel'] += sobra.quantidade_disponivel
        sobras_por_material[mat_cod]['detalhes'].append({
            'projeto_origem_codigo': sobra.projeto.codigo_projeto,
            'projeto_origem_nome': sobra.projeto.nome_projeto,
            'quantidade_disponivel': sobra.quantidade_disponivel,
            'status_projeto_origem': sobra.projeto.status,
            'localizacao_fisica': sobra.localizacao.localizacao
        })
        valor_total_material += float(sobra.valor_total)

    # 2. Solicitações Abertas do Projeto Alvo
    solicitacoes_abertas = DimSolicitacao.objects.filter(
        projeto=projeto_alvo,
        status__in=['ABERTO', 'Aberto', 'PENDENTE']
    ).select_related('material')

    alertas_estoque_ocioso = []
    for sol in solicitacoes_abertas:
        mat_cod = sol.material.codigo_material
        if mat_cod in sobras_por_material:
            sobra_info = sobras_por_material[mat_cod]
            #economia é a intersecção entre o que eu preciso e o que sobrou * custo
            qtd_aproveitavel = min(sol.quantidade, sobra_info['total_disponivel'])
            economia = float(qtd_aproveitavel * sol.material.custo_estimado)

            alertas_estoque_ocioso.append({
                'codigo_material': mat_cod,
                'descricao': sol.material.descricao,
                'quantidade_solicitada_atual': sol.quantidade,
                'sobras_detectadas': sobra_info['detalhes'],
                'potencial_economia_estimada': round(economia, 2)
            })

    # 3. Conflitos de Compra Aberta
    # Regra: Disparar se houver saldo em QUALQUER projeto do mesmo programa
    compras_abertas = FatoCompra.objects.filter(
        solicitacao__projeto=projeto_alvo,
        status__in=['PENDENTE', 'ABERTO', 'EM ANDAMENTO']
    ).select_related('solicitacao__material')

    estoque_geral_programa = FatoEstoqueSaldo.objects.filter(
        projeto__programa=programa_alvo,
        quantidade_disponivel__gt=0
    ).exclude(projeto=projeto_alvo).values('material__codigo_material').annotate(
        total_disp=Sum('quantidade_disponivel')
    )

    disp_geral_dict = {item['material__codigo_material']: item['total_disp'] for item in estoque_geral_programa}

    conflitos_compra_aberta = []
    for compra in compras_abertas:
        mat_cod = compra.solicitacao.material.codigo_material
        if mat_cod in disp_geral_dict and disp_geral_dict[mat_cod] > 0:
            conflitos_compra_aberta.append({
                'material': compra.solicitacao.material.descricao,
                'pedido_compra_atual': compra.numero_pedido,
                'quantidade_no_pedido': compra.solicitacao.quantidade,
                'alerta': 'Existe estoque disponível em outros projetos que supre esta necessidade sem nova compra.',
                'disponivel_outras_fontes': disp_geral_dict[mat_cod]
            })

    return JsonResponse({
        'projeto_alvo': {
            'codigo': projeto_alvo.codigo_projeto,
            'nome': projeto_alvo.nome_projeto
        },
        'alertas_estoque_ocioso': alertas_estoque_ocioso,
        'conflitos_compra_aberta': conflitos_compra_aberta,
        'valor_total_material': round(valor_total_material, 2)
    })