from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_GET
from api.models import DimProjeto, DimTarefa, FatoTarefa

@require_GET
def projeto_tarefas_timesheet_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    tarefas_qs = (
        DimTarefa.objects
        .filter(projeto=projeto)
        .annotate(total_horas_trabalhadas=Sum('fatotarefa__horas_trabalhadas'))
        .values(
            'codigo_tarefa', 'titulo', 'responsavel', 
            'estimativa', 'status', 'total_horas_trabalhadas'
        )
        .order_by('codigo_tarefa')
    )

    tarefas = [
        {
            'codigo': tarefa['codigo_tarefa'],
            'titulo': tarefa['titulo'],
            'responsavel': tarefa['responsavel'],
            'estimativa': tarefa['estimativa'],
            'status': tarefa['status'],
            'total_horas_trabalhadas': round(float(tarefa['total_horas_trabalhadas'] or 0.0), 2),
        }
        for tarefa in tarefas_qs
    ]

    evolucao_qs = (
        FatoTarefa.objects
        .filter(tarefa__projeto=projeto)
        .values('data__ano', 'data__mes', 'data__dia')
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('data__ano', 'data__mes', 'data__dia')
    )

    evolucao_horas = {
        f"{item['data__ano']:04d}-{item['data__mes']:02d}-{item['data__dia']:02d}": round(float(item['total_horas'] or 0.0), 2)
        for item in evolucao_qs
    }

    return JsonResponse({
        'projeto': {
            'codigo': projeto.codigo_projeto,
            'nome': projeto.nome_projeto,
        },
        'tarefas': tarefas,
        'evolucao_horas': evolucao_horas,
    })