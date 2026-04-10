from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoEmpenho

@require_GET
def projeto_empenho_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    empenhos = FatoEmpenho.objects.filter(projeto=projeto).annotate(
        custo=ExpressionWrapper(
            F('quantidade_empenhada') * F('material__custo_estimado'),
            output_field=DecimalField()
        )
    )

    total_empenho = empenhos.aggregate(total=Sum('custo'))['total'] or 0.0

    custo_por_categoria_qs = empenhos.values(categoria=F('material__categoria')).annotate(
        total_custo=Sum('custo')
    ).order_by('categoria')

    custo_por_categoria = [
        {"categoria": item['categoria'], "total_custo": float(item['total_custo'] or 0.0)}
        for item in custo_por_categoria_qs
    ]

    empenho_por_material_qs = empenhos.values(
        codigo_material=F('material__codigo_material'),
        descricao=F('material__descricao'),
        categoria=F('material__categoria'),
        custo_unitario=F('material__custo_estimado')
    ).annotate(
        quantidade_total=Sum('quantidade_empenhada'),
        total_custo=Sum('custo')
    ).order_by('descricao')

    empenho_por_material = [
        {
            "codigo_material": item['codigo_material'],
            "descricao": item['descricao'],
            "categoria": item['categoria'],
            "custo_unitario": float(item['custo_unitario'] or 0.0),
            "quantidade_total": item['quantidade_total'] or 0,
            "total_custo": float(item['total_custo'] or 0.0)
        }
        for item in empenho_por_material_qs
    ]

    empenhos_tempo_materiais_qs = empenhos.values(
        ano=F('data_empenho__ano'), mes=F('data_empenho__mes'), dia=F('data_empenho__dia'),
        codigo_material=F('material__codigo_material'), descricao=F('material__descricao'),
        custo_unitario=F('material__custo_estimado')
    ).annotate(
        quantidade_total=Sum('quantidade_empenhada'),
        total_custo=Sum('custo')
    ).order_by('ano', 'mes', 'dia', 'descricao')

    custo_por_tempo_dict = {}
    for item in empenhos_tempo_materiais_qs:
        data_str = f"{item['ano']:04d}-{item['mes']:02d}-{item['dia']:02d}"
        if data_str not in custo_por_tempo_dict:
            custo_por_tempo_dict[data_str] = {"data": data_str, "total_custo": 0.0, "materiais": []}
        
        custo_item = float(item['total_custo'] or 0.0)
        custo_por_tempo_dict[data_str]["total_custo"] += custo_item
        custo_por_tempo_dict[data_str]["materiais"].append({
            "codigo_material": item['codigo_material'],
            "descricao": item['descricao'],
            "custo_unitario": float(item['custo_unitario'] or 0.0),
            "quantidade": item['quantidade_total'] or 0,
            "total_custo": custo_item
        })

    return JsonResponse({
        "projeto": {
            "codigo": projeto.codigo_projeto,
            "nome": projeto.nome_projeto,
        },
        "empenho_total": float(total_empenho),
        "empenho_por_categoria": custo_por_categoria,
        "empenho_por_material": empenho_por_material,
        "empenho_por_tempo": list(custo_por_tempo_dict.values()),
    })

@require_GET
def empenhos_programa(request):
    programa_id = request.GET.get('programa_id')
    categoria = request.GET.get('categoria')

    queryset = FatoEmpenho.objects.select_related(
        'projeto__programa', 'material', 'data_empenho'
    )

    if programa_id:
        queryset = queryset.filter(projeto__programa__id=programa_id)
    if categoria:
        queryset = queryset.filter(material__categoria=categoria)

    resultados = []
    total = 0

    for emp in queryset:
        valor = emp.quantidade_empenhada * emp.material.custo_estimado
        total += valor
        resultados.append({
            "nome_projeto": emp.projeto.nome_projeto,
            "nome_material": emp.material.descricao,
            "quantidade_empenhada": emp.quantidade_empenhada,
            "valor_empenhado": float(valor),
            "data_empenho": f"{emp.data_empenho.dia}/{emp.data_empenho.mes}/{emp.data_empenho.ano}"
        })

    return JsonResponse({
        "resultados": resultados,
        "valor_total_empenhado": float(total)
    })