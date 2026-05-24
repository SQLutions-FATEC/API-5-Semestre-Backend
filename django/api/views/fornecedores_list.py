from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from api.models import DimFornecedor

@require_GET
def listagem_fornecedores(request):
    fornecedores = DimFornecedor.objects.all()

    nome = request.GET.get('fornecedor_nome')
    cidade = request.GET.get('fornecedor_cidade')
    categoria = request.GET.get('categoria')
    programa = request.GET.get('programa_nome')
    projeto = request.GET.get('projeto_nome')

    if nome:
        fornecedores = fornecedores.filter(razao_social__icontains=nome)
        
    if cidade:
        fornecedores = fornecedores.filter(cidade__icontains=cidade)
        
    if categoria:
        fornecedores = fornecedores.filter(categoria__icontains=categoria)

    if projeto:
        fornecedores = fornecedores.filter(
            fatocompra__solicitacao__projeto__nome_projeto__icontains=projeto
        )
        
    if programa:
        fornecedores = fornecedores.filter(
            fatocompra__solicitacao__projeto__programa__nome_programa__icontains=programa
        )

    if projeto or programa:
        fornecedores = fornecedores.distinct()

    lista_fornecedores = []
    for f in fornecedores:
        lista_fornecedores.append({
            "id_fornecedor": f.id,
            "codigo_fornecedor": f.codigo_fornecedor,
            "razao_social": f.razao_social,
            "cidade": f.cidade,
            "categoria": f.categoria,
            "status": f.status
        })

    return JsonResponse(lista_fornecedores, safe=False)