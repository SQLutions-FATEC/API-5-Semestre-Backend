from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_GET
from api.models import DimProjeto, FatoTarefa, FatoCompra

@require_GET
def projeto_dashboard_api(request, codigo_projeto):
    projeto = get_object_or_404(
        DimProjeto.objects.select_related('programa', 'data_inicio', 'data_fim_prevista'),
        codigo_projeto=codigo_projeto
    )

    horas_trabalhadas = FatoTarefa.objects.filter(tarefa__projeto=projeto).aggregate(
        total_horas=Sum('horas_trabalhadas')
    )
    total_horas = horas_trabalhadas['total_horas'] or 0.0

    compras_agregadas = FatoCompra.objects.filter(solicitacao__projeto=projeto).aggregate(
        total_materiais=Sum('valor_total')
    )
    total_materiais = compras_agregadas['total_materiais'] or Decimal('0.00')
    
    custo_mao_de_obra = Decimal(str(total_horas)) * projeto.custo_hora
    custo_total = custo_mao_de_obra + total_materiais
    
    data_inicio_str = f"{projeto.data_inicio.ano}-{projeto.data_inicio.mes:02d}-{projeto.data_inicio.dia:02d}"
    data_fim_str = f"{projeto.data_fim_prevista.ano}-{projeto.data_fim_prevista.mes:02d}-{projeto.data_fim_prevista.dia:02d}"
    
    data = {
        "projeto": {
            "codigo": projeto.codigo_projeto,
            "nome": projeto.nome_projeto,
            "status": projeto.status,
            "data_inicio": data_inicio_str,
            "data_fim_prevista": data_fim_str,
            "responsavel": projeto.responsavel
        },
        "financeiro": {
            "total_horas_trabalhadas": round(total_horas, 2),
            "custo_total_materiais": float(total_materiais),
            "custo_total_projeto": float(custo_total)
        },
        "programa": {
            "codigo": projeto.programa.codigo_programa,
            "nome": projeto.programa.nome_programa,
            "gerente": projeto.programa.gerente_programa
        }
    }

    return JsonResponse(data)