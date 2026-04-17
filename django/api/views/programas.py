from api.models import DimPrograma
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def programa_projetos_api(request):
    programas = (
        DimPrograma.objects
        .prefetch_related('dimprojeto_set')
        .order_by('codigo_programa')
    )

    response_data = []
    for programa in programas:
        projetos = programa.dimprojeto_set.order_by('codigo_projeto')
        response_data.append({
            'codigo_programa': programa.codigo_programa,
            'nome_programa': programa.nome_programa,
            'status': programa.status,
            'gerente': programa.gerente_programa,
            'projetos': [
                {
                    'codigo_projeto': projeto.codigo_projeto,
                    'nome_projeto': projeto.nome_projeto,
                    'status': projeto.status,
                }
                for projeto in projetos
            ],
        })

    return JsonResponse({'programas': response_data})
