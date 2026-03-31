from django.views.decorators.http import require_GET
from decimal import Decimal
from datetime import date, timedelta
import unicodedata
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from api.models import DimMaterial, DimProjeto, DimSolicitacao, DimTarefa, FatoTarefa, FatoCompra, FatoEmpenho

def _normaliza_texto(valor):
        if valor is None:
                return ''

        texto_sem_acentos = unicodedata.normalize('NFKD', str(valor)).encode('ASCII', 'ignore').decode('ASCII')
        return texto_sem_acentos.strip().lower()


def _dim_data_para_date(dim_data):
        if dim_data is None:
                return None

        try:
                return date(dim_data.ano, dim_data.mes, dim_data.dia)
        except (TypeError, ValueError):
                return None

@require_GET
def projeto_dashboard_api(request, codigo_projeto):
    # Fetch project and its related dimensions (program and dates)
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


@require_GET
def projeto_tarefas_timesheet_api(request, codigo_projeto):
        projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

        tarefas_qs = (
                DimTarefa.objects
                .filter(projeto=projeto)
                .annotate(total_horas_trabalhadas=Sum('fatotarefa__horas_trabalhadas'))
                .values(
                        'codigo_tarefa',
                        'titulo',
                        'responsavel',
                        'estimativa',
                        'status',
                        'total_horas_trabalhadas',
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

        Data = {
                        'projeto': {
                                'codigo': projeto.codigo_projeto,
                                'nome': projeto.nome_projeto,
                        },
                        'tarefas': tarefas,
                        'evolucao_horas': evolucao_horas,
                }
        
        return JsonResponse(Data)


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
        materiais_pedidos_recentes_ids = set()

        for compra in compras:
                data_previsao_entrega = _dim_data_para_date(compra.data_previsao_entrega)
                data_pedido = _dim_data_para_date(compra.data_pedido)
                status_normalizado = _normaliza_texto(compra.status)
                prioridade_normalizada = _normaliza_texto(compra.solicitacao.prioridade)

                if data_previsao_entrega and data_atual > data_previsao_entrega and status_normalizado != 'Concluída':
                        pedidos_atrasados.append({
                                'numero_pedido': compra.numero_pedido,
                                'status': compra.status,
                                'data_previsao_entrega': data_previsao_entrega.isoformat(),
                                'dias_atraso': (data_atual - data_previsao_entrega).days,
                        })

                if prioridade_normalizada in {'Alta', 'Urgente'} and (status_normalizado == 'Aberto' or status_normalizado == 'Enviado'):
                        pedidos_prioritarios_pendentes.append({
                                'numero_pedido': compra.numero_pedido,
                                'prioridade': compra.solicitacao.prioridade,
                                'status': compra.status,
                                'data_pedido': data_pedido.isoformat() if data_pedido else None,
                        })

                if data_pedido and data_pedido >= limite_pedido_recente:
                        materiais_pedidos_recentes_ids.add(compra.solicitacao.material_id)

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

        data = {
                'projeto': {
                        'codigo': projeto.codigo_projeto,
                        'nome': projeto.nome_projeto,
                },
                'data_referencia': data_atual.isoformat(),
                'alertas_criticos': {
                        'pedidos_atrasados': pedidos_atrasados,
                        'pedidos_prioritarios_pendentes': pedidos_prioritarios_pendentes,
                        'materiais_obsoletos': materiais_obsoletos,
                },
        }

        return JsonResponse(data)

@require_GET
def projeto_empenho_api(request, codigo_projeto):
    projeto = get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

    # Query base anotada com o custo calculado (quantidade * custo_estimado do material)
    empenhos = FatoEmpenho.objects.filter(projeto=projeto).annotate(
        custo=ExpressionWrapper(
            F('quantidade_empenhada') * F('material__custo_estimado'),
            output_field=DecimalField()
        )
    )

    # 1. Custo total do projeto (empenho)
    total_empenho = empenhos.aggregate(total=Sum('custo'))['total'] or 0.0

    # 2. Custo por categoria
    custo_por_categoria_qs = empenhos.values(categoria=F('material__categoria')).annotate(
        total_custo=Sum('custo')
    ).order_by('categoria')

    custo_por_categoria = [
        {
            "categoria": item['categoria'],
            "total_custo": float(item['total_custo'] or 0.0)
        }
        for item in custo_por_categoria_qs
    ]

    # 3. Empenho por material (quantidade e custo)
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

    # 4. Dados em função do tempo
    empenhos_tempo_materiais_qs = empenhos.values(
        ano=F('data_empenho__ano'),
        mes=F('data_empenho__mes'),
        dia=F('data_empenho__dia'),
        codigo_material=F('material__codigo_material'),
        descricao=F('material__descricao'),
        custo_unitario=F('material__custo_estimado')
    ).annotate(
        quantidade_total=Sum('quantidade_empenhada'),
        total_custo=Sum('custo')
    ).order_by('ano', 'mes', 'dia', 'descricao')

    custo_por_tempo_dict = {}
    for item in empenhos_tempo_materiais_qs:
        data_str = f"{item['ano']:04d}-{item['mes']:02d}-{item['dia']:02d}"
        
        if data_str not in custo_por_tempo_dict:
            custo_por_tempo_dict[data_str] = {
                "data": data_str,
                "total_custo": 0.0,
                "materiais": []
            }
        
        custo_item = float(item['total_custo'] or 0.0)
        custo_por_tempo_dict[data_str]["total_custo"] += custo_item
        custo_por_tempo_dict[data_str]["materiais"].append({
            "codigo_material": item['codigo_material'],
            "descricao": item['descricao'],
            "custo_unitario": float(item['custo_unitario'] or 0.0),
            "quantidade": item['quantidade_total'] or 0,
            "total_custo": custo_item
        })

    custo_por_tempo = list(custo_por_tempo_dict.values())

    data = {
        "projeto": {
            "codigo": projeto.codigo_projeto,
            "nome": projeto.nome_projeto,
        },
        "empenho_total": float(total_empenho),
        "empenho_por_categoria": custo_por_categoria,
        "empenho_por_material": empenho_por_material,
        "empenho_por_tempo": custo_por_tempo,
    }

    return JsonResponse(data)
