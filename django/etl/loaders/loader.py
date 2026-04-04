import pandas as pd
from datetime import datetime
from api.models import (
    DimData, DimPrograma, DimProjeto, DimTarefa, DimMaterial,
    DimFornecedor, DimSolicitacao, FatoTarefa, FatoEmpenho, FatoCompra
)
from etl.utils.logger import get_logger

logger = get_logger(__name__)

#funções auxiliares de cache
def get_date_cache(df: pd.DataFrame, columns: list) -> dict:
    """
    Pré-processa todas as datas únicas do DataFrame e garante que existam na DimData.
    Retorna um dicionário {date_obj: dim_data_instance} para acesso rápido.
    """
    all_dates = pd.concat([df[col] for col in columns if col in df.columns]).unique()
    cache = {}
    
    for date_str in all_dates:
        if pd.isna(date_str): continue
        
        clean_date = str(date_str)[:10]
        dt_obj = datetime.strptime(clean_date, '%Y-%m-%d').date()
        
        #o get_or_create aqui seguro porque roda poucas vezes (apenas para datas únicas)
        obj, _ = DimData.objects.get_or_create(
            dia=dt_obj.day,
            mes=dt_obj.month,
            ano=dt_obj.year
        )
        cache[date_str] = obj
    return cache

def filter_valid_ids(df: pd.DataFrame, model, column_name: str) -> pd.DataFrame:
    """
    Remove linhas do DataFrame que referenciam IDs inexistentes no banco de dados.
    """
    valid_ids = set(model.objects.values_list('id', flat=True))
    initial_count = len(df)
    df_filtered = df[df[column_name].isin(valid_ids)]
    
    diff = initial_count - len(df_filtered)
    if diff > 0:
        logger.warning(f"[Integridade] {diff} registros descartados em {model.__name__} por ID inválido em {column_name}.")
    
    return df_filtered

# --- LOADERS REFATORADOS ---

def load_programas(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimPrograma...")
    DimPrograma.objects.all().delete()
    date_cache = get_date_cache(df, ['data_inicio', 'data_fim_prevista'])
    
    objs = [
        DimPrograma(
            id=row['id'],
            codigo_programa=row['codigo_programa'],
            nome_programa=row['nome_programa'],
            gerente_programa=row['gerente_programa'],
            gerente_tecnico=row['gerente_tecnico'],
            data_inicio=date_cache.get(row['data_inicio']),
            data_fim_prevista=date_cache.get(row['data_fim_prevista']),
            status=row['status']
        ) for _, row in df.iterrows()
    ]
    DimPrograma.objects.bulk_create(objs)
    logger.info(f"[Loader] DimPrograma carregado: {len(objs)} registros.")

def load_projetos(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimProjeto...")
    #valida FK com programas
    df = filter_valid_ids(df, DimPrograma, 'programa_id')
    
    DimProjeto.objects.all().delete()
    date_cache = get_date_cache(df, ['data_inicio', 'data_fim_prevista'])
    
    objs = [
        DimProjeto(
            id=row['id'],
            codigo_projeto=row['codigo_projeto'],
            nome_projeto=row['nome_projeto'],
            programa_id=row['programa_id'],
            responsavel=row['responsavel'],
            custo_hora=row['custo_hora'],
            data_inicio=date_cache.get(row['data_inicio']),
            data_fim_prevista=date_cache.get(row['data_fim_prevista']),
            status=row['status'],
            lead_time_dias=row.get('lead_time_dias', 0),
            is_atrasado=row.get('is_atrasado', False)
        ) for _, row in df.iterrows()
    ]
    DimProjeto.objects.bulk_create(objs)
    logger.info(f"[Loader] DimProjeto carregado: {len(objs)} registros.")

def load_tarefas(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimTarefa...")
    df = filter_valid_ids(df, DimProjeto, 'projeto_id')
    
    DimTarefa.objects.all().delete()
    date_cache = get_date_cache(df, ['data_inicio', 'data_fim_prevista'])
    
    objs = [
        DimTarefa(
            id=row['id'],
            codigo_tarefa=row['codigo_tarefa'],
            projeto_id=row['projeto_id'],
            titulo=row['titulo'],
            responsavel=row['responsavel'],
            estimativa=row['estimativa_horas'],
            data_inicio=date_cache.get(row['data_inicio']),
            data_fim_prevista=date_cache.get(row['data_fim_prevista']),
            status=row['status'],
            lead_time_dias=row.get('lead_time_dias', 0),
            is_atrasado=row.get('is_atrasado', False)
        ) for _, row in df.iterrows()
    ]
    DimTarefa.objects.bulk_create(objs)
    logger.info(f"[Loader] DimTarefa carregado: {len(objs)} registros.")

def load_materiais(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimMaterial...")
    DimMaterial.objects.all().delete()
    objs = [
        DimMaterial(
            id=row['id'],
            codigo_material=row['codigo_material'],
            descricao=row['descricao'],
            categoria=row['categoria'],
            fabricante=row['fabricante'],
            custo_estimado=row['custo_estimado'],
            status=row['status']
        ) for _, row in df.iterrows()
    ]
    DimMaterial.objects.bulk_create(objs)
    logger.info(f"[Loader] DimMaterial carregado: {len(objs)} registros.")

def load_fornecedores(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimFornecedor...")
    DimFornecedor.objects.all().delete()
    objs = [
        DimFornecedor(
            id=row['id'],
            codigo_fornecedor=row['codigo_fornecedor'],
            razao_social=row['razao_social'],
            cidade=row['cidade'],
            estado=row['estado'],
            categoria=row['categoria'],
            status=row['status']
        ) for _, row in df.iterrows()
    ]
    DimFornecedor.objects.bulk_create(objs)
    logger.info(f"[Loader] DimFornecedor carregado: {len(objs)} registros.")

def load_solicitacoes(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimSolicitacao...")
    df = filter_valid_ids(df, DimProjeto, 'projeto_id')
    df = filter_valid_ids(df, DimMaterial, 'material_id')
    
    DimSolicitacao.objects.all().delete()
    date_cache = get_date_cache(df, ['data_solicitacao'])
    
    objs = [
        DimSolicitacao(
            id=row['id'],
            numero_solicitacao=row['numero_solicitacao'],
            projeto_id=row['projeto_id'],
            material_id=row['material_id'],
            quantidade=row['quantidade'],
            data_solicitacao=date_cache.get(row['data_solicitacao']),
            prioridade=row['prioridade'],
            status=row['status']
        ) for _, row in df.iterrows()
    ]
    DimSolicitacao.objects.bulk_create(objs)
    logger.info(f"[Loader] DimSolicitacao carregado: {len(objs)} registros.")

def load_fato_tarefa(df: pd.DataFrame):
    logger.info("[Loader] Carregando FatoTarefa...")
    df = filter_valid_ids(df, DimTarefa, 'tarefa_id')
    
    FatoTarefa.objects.all().delete()
    date_cache = get_date_cache(df, ['data'])
    
    objs = [
        FatoTarefa(
            id=row['id'],
            usuario=row['usuario'],
            horas_trabalhadas=row['horas_trabalhadas'],
            tarefa_id=row['tarefa_id'],
            data=date_cache.get(row['data'])
        ) for _, row in df.iterrows()
    ]
    FatoTarefa.objects.bulk_create(objs)
    logger.info(f"[Loader] FatoTarefa carregado: {len(objs)} registros.")

def load_fato_empenho(df: pd.DataFrame):
    logger.info("[Loader] Carregando FatoEmpenho...")
    df = filter_valid_ids(df, DimProjeto, 'projeto_id')
    df = filter_valid_ids(df, DimMaterial, 'material_id')
    
    FatoEmpenho.objects.all().delete()
    date_cache = get_date_cache(df, ['data_empenho'])
    
    objs = [
        FatoEmpenho(
            id=row['id'],
            quantidade_empenhada=row['quantidade_empenhada'],
            projeto_id=row['projeto_id'],
            material_id=row['material_id'],
            data_empenho=date_cache.get(row['data_empenho'])
        ) for _, row in df.iterrows()
    ]
    FatoEmpenho.objects.bulk_create(objs)
    logger.info(f"[Loader] FatoEmpenho carregado: {len(objs)} registros.")

def load_fato_compra(df: pd.DataFrame):
    logger.info("[Loader] Carregando FatoCompra...")
    df = filter_valid_ids(df, DimSolicitacao, 'solicitacao_id')
    df = filter_valid_ids(df, DimFornecedor, 'fornecedor_id')
    
    FatoCompra.objects.all().delete()
    date_cache = get_date_cache(df, ['data_pedido', 'data_previsao_entrega'])
    
    objs = [
        FatoCompra(
            id=row['id'],
            numero_pedido=row['numero_pedido'],
            valor_total=row['valor_total'],
            status=row['status'],
            solicitacao_id=row['solicitacao_id'],
            fornecedor_id=row['fornecedor_id'],
            data_pedido=date_cache.get(row['data_pedido']),
            data_previsao_entrega=date_cache.get(row['data_previsao_entrega'])
        ) for _, row in df.iterrows()
    ]
    FatoCompra.objects.bulk_create(objs)
    logger.info(f"[Loader] FatoCompra carregado: {len(objs)} registros.")
