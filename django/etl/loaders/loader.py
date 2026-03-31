import pandas as pd
from datetime import datetime
from api.models import (
    DimData, DimPrograma, DimProjeto, DimTarefa, DimMaterial,
    DimFornecedor, DimSolicitacao, FatoTarefa, FatoEmpenho, FatoCompra
)
from etl.utils.logger import get_logger

logger = get_logger(__name__)


def get_or_create_dim_data(date_str: str) -> DimData:
    """
    Converte uma string de data em um registro DimData.
    Cria o registro se ainda não existir.
    """
    date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
    obj, _ = DimData.objects.get_or_create(
        dia=date.day,
        mes=date.month,
        ano=date.year
    )
    return obj


def load_programas(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimPrograma...")
    DimPrograma.objects.all().delete()
    for _, row in df.iterrows():
        DimPrograma.objects.create(
            id=row['id'],
            codigo_programa=row['codigo_programa'],
            nome_programa=row['nome_programa'],
            gerente_programa=row['gerente_programa'],
            gerente_tecnico=row['gerente_tecnico'],
            data_inicio=get_or_create_dim_data(row['data_inicio']),
            data_fim_prevista=get_or_create_dim_data(row['data_fim_prevista']),
            status=row['status']
        )
    logger.info(f"[Loader] DimPrograma carregado: {len(df)} registros.")


def load_projetos(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimProjeto...")
    DimProjeto.objects.all().delete()
    for _, row in df.iterrows():
        DimProjeto.objects.create(
            id=row['id'],
            codigo_projeto=row['codigo_projeto'],
            nome_projeto=row['nome_projeto'],
            programa_id=row['programa_id'],
            responsavel=row['responsavel'],
            custo_hora=row['custo_hora'],
            data_inicio=get_or_create_dim_data(row['data_inicio']),
            data_fim_prevista=get_or_create_dim_data(row['data_fim_prevista']),
            status=row['status']
        )
    logger.info(f"[Loader] DimProjeto carregado: {len(df)} registros.")


def load_tarefas(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimTarefa...")
    DimTarefa.objects.all().delete()
    for _, row in df.iterrows():
        DimTarefa.objects.create(
            id=row['id'],
            codigo_tarefa=row['codigo_tarefa'],
            projeto_id=row['projeto_id'],
            titulo=row['titulo'],
            responsavel=row['responsavel'],
            estimativa=row['estimativa_horas'],
            data_inicio=get_or_create_dim_data(row['data_inicio']),
            data_fim_prevista=get_or_create_dim_data(row['data_fim_prevista']),
            status=row['status']
        )
    logger.info(f"[Loader] DimTarefa carregado: {len(df)} registros.")


def load_materiais(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimMaterial...")
    DimMaterial.objects.all().delete()
    for _, row in df.iterrows():
        DimMaterial.objects.create(
            id=row['id'],
            codigo_material=row['codigo_material'],
            descricao=row['descricao'],
            categoria=row['categoria'],
            fabricante=row['fabricante'],
            custo_estimado=row['custo_estimado'],
            status=row['status']
        )
    logger.info(f"[Loader] DimMaterial carregado: {len(df)} registros.")


def load_fornecedores(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimFornecedor...")
    DimFornecedor.objects.all().delete()
    for _, row in df.iterrows():
        DimFornecedor.objects.create(
            id=row['id'],
            codigo_fornecedor=row['codigo_fornecedor'],
            razao_social=row['razao_social'],
            cidade=row['cidade'],
            estado=row['estado'],
            categoria=row['categoria'],
            status=row['status']
        )
    logger.info(f"[Loader] DimFornecedor carregado: {len(df)} registros.")


def load_solicitacoes(df: pd.DataFrame):
    logger.info("[Loader] Carregando DimSolicitacao...")
    DimSolicitacao.objects.all().delete()
    for _, row in df.iterrows():
        DimSolicitacao.objects.create(
            id=row['id'],
            numero_solicitacao=row['numero_solicitacao'],
            projeto_id=row['projeto_id'],
            material_id=row['material_id'],
            quantidade=row['quantidade'],
            data_solicitacao=get_or_create_dim_data(row['data_solicitacao']),
            prioridade=row['prioridade'],
            status=row['status']
        )
    logger.info(f"[Loader] DimSolicitacao carregado: {len(df)} registros.")


def load_fato_tarefa(df: pd.DataFrame):
    logger.info("[Loader] Carregando FatoTarefa...")
    FatoTarefa.objects.all().delete()
    for _, row in df.iterrows():
        FatoTarefa.objects.create(
            id=row['id'],
            usuario=row['usuario'],
            horas_trabalhadas=row['horas_trabalhadas'],
            tarefa_id=row['tarefa_id'],
            data=get_or_create_dim_data(row['data'])
        )
    logger.info(f"[Loader] FatoTarefa carregado: {len(df)} registros.")


def load_fato_empenho(df: pd.DataFrame):
    logger.info("[Loader] Carregando FatoEmpenho...")
    FatoEmpenho.objects.all().delete()
    for _, row in df.iterrows():
        FatoEmpenho.objects.create(
            id=row['id'],
            quantidade_empenhada=row['quantidade_empenhada'],
            projeto_id=row['projeto_id'],
            material_id=row['material_id'],
            data_empenho=get_or_create_dim_data(row['data_empenho'])
        )
    logger.info(f"[Loader] FatoEmpenho carregado: {len(df)} registros.")


def load_fato_compra(df: pd.DataFrame):
    logger.info("[Loader] Carregando FatoCompra...")
    FatoCompra.objects.all().delete()
    for _, row in df.iterrows():
        FatoCompra.objects.create(
            id=row['id'],
            numero_pedido=row['numero_pedido'],
            valor_total=row['valor_total'],
            status=row['status'],
            solicitacao_id=row['solicitacao_id'],
            fornecedor_id=row['fornecedor_id'],
            data_pedido=get_or_create_dim_data(row['data_pedido']),
            data_previsao_entrega=get_or_create_dim_data(row['data_previsao_entrega'])
        )
    logger.info(f"[Loader] FatoCompra carregado: {len(df)} registros.")