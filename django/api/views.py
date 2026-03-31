from django.http import JsonResponse
from .models import FatoEmpenho

def empenhos_programa(request):
    programa_id = request.GET.get('programa_id')
    categoria = request.GET.get('categoria')

    queryset = FatoEmpenho.objects.select_related(
        'projeto__programa',
        'material',
        'data_empenho'
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