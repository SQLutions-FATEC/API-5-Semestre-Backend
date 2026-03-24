from django.db import connections
from etl.utils.logger import get_logger

logger = get_logger(__name__)

#mapeia cada extractor para sua tabela de stage e colunas correspondentes
STAGE_TABLES = {
    "ProgramasEmpresaExtractor": {
        "table": "stage_programas",
        "columns": ["id", "codigo_programa", "nome_programa", "gerente_programa", "data_inicio", "status"],
    },
    "ProjetosProgramasExtractor": {
        "table": "stage_projetos",
        "columns": ["id", "codigo_projeto", "nome_projeto", "programa_id", "responsavel", "data_inicio", "status"],
    },
    "TarefasProjetoExtractor": {
        "table": "stage_tarefas",
        "columns": ["id", "codigo_tarefa", "titulo", "projeto_id", "programa_id", "responsavel", "estimativa_horas", "status"],
    },
    "TempoTarefasExtractor": {
        "table": "stage_tempo_tarefas",
        "columns": ["id", "tarefa_id", "usuario", "data", "horas_trabalhadas"],
    },
    "MateriaisEngenhariaExtractor": {
        "table": "stage_materiais",
        "columns": ["id", "codigo_material", "categoria", "descricao", "unidade_medida", "fabricante", "lead_time_dias", "custo_estimado_usd", "status"],
    },
    "FornecedoresExtractor": {
        "table": "stage_fornecedores",
        "columns": ["id", "codigo_fornecedor", "razao_social", "nome_fantasia", "cnpj", "cidade", "estado", "email", "telefone", "condicao_pagamento", "categoria_fornecedor", "status", "data_cadastro"],
    },
    "SolicitacoesCompraExtractor": {
        "table": "stage_solicitacoes",
        "columns": ["id", "numero_solicitacao", "data_solicitacao", "solicitante", "departamento", "centro_custo", "descricao_item", "quantidade", "valor_unitario", "valor_total", "fornecedor", "data_necessidade", "status", "prioridade"],
    },
    "PedidosCompraExtractor": {
        "table": "stage_pedidos_compra",
        "columns": ["id", "numero_pedido", "data_emissao", "data_previsao_entrega", "fornecedor_id", "centro_custo", "condicao_pagamento", "valor_total", "status", "prioridade", "observacoes"],
    },
    "EmpenhoMateriaisExtractor": {
        "table": "stage_empenho_materiais",
        "columns": ["id", "material_id", "projeto_id", "quantidade_empenhada", "data_empenho"],
    },
    "ComprasProjetoExtractor": {
        "table": "stage_compras_projeto",
        "columns": ["id", "pedido_compra_id", "projeto_id", "valor_alocado"],
    },
    "EstoqueMateriaisExtractor": {
        "table": "stage_estoque_materiais",
        "columns": ["id", "material_id", "projeto_id", "quantidade", "localizacao"],
    },
}


def load_to_stage(extractor_name: str, data: list[dict]) -> int:
    config = STAGE_TABLES.get(extractor_name)
    if not config:
        raise ValueError(f"Nenhuma configuração de stage encontrada para o extractor: {extractor_name}")

    table = config["table"]
    columns = config["columns"]

    logger.info(f"[StageLoader] Carregando {len(data)} registros na tabela '{table}'...")

    with connections["default"].cursor() as cursor:
        #limpa a tabela de stage antes de carregar os novos dados
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY")

        for row in data:
            values = [row.get(col) for col in columns]
            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join(columns)
            cursor.execute(
                f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})",
                values,
            )

    logger.info(f"[StageLoader] Tabela '{table}' carregada com sucesso: {len(data)} registros.")
    return len(data)