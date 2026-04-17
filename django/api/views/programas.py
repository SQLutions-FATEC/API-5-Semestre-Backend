from api.models import DimPrograma
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
