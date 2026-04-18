from django.db.models import Q
from api.models import DimPrograma, DimProjeto
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def programa_api(request):
    programas = (
        DimPrograma.objects
        .prefetch_related('dimprojeto_set')
        .order_by('codigo_programa')
    )

    response_data = []
    for programa in programas:
        response_data.append({
            'codigo_programa': programa.codigo_programa,
            'nome_programa': programa.nome_programa,
            'status': programa.status,
            'gerente': programa.gerente_programa,
            'gerente_tecnico': programa.gerente_tecnico,
            
        })

    return JsonResponse({'programas': response_data})


@require_GET
def busca_projetos(request, programa_cod):
    q = request.GET.get('q', '').strip()
    
    projetos_query = DimProjeto.objects.filter(programa__codigo_programa=programa_cod)
    
    if q:
        projetos_query = projetos_query.filter(
            Q(nome_projeto__icontains=q) | Q(codigo_projeto__icontains=q)
        )
        
    resultados = []
    for projeto in projetos_query:
        resultados.append({
            'nome_projeto': projeto.nome_projeto,
            'codigo_projeto': projeto.codigo_projeto,
            'status': projeto.status,
            'responsavel': projeto.responsavel
        })
        
    return JsonResponse(resultados, safe=False)
