from datetime import datetime

from api.models import (
    DimPrograma,
    DimData,
    DimProjeto,
    DimMaterial,
    DimFornecedor
)
from etl.transformations.transformers import standardize_strings

def carregar_csv(df, tipo):

    if tipo == "projeto":
        carregar_projetos(df)

    elif tipo == "material":
        carregar_materiais(df)

    elif tipo == "fornecedor":
        carregar_fornecedores(df)    


def obter_ou_criar_data(data_str):

    if not data_str:
        return None

    try:
        data = datetime.strptime(str(data_str), "%Y-%m-%d")

        data_obj, _ = DimData.objects.get_or_create(
            ano=data.year,
            mes=data.month,
            dia=data.day
        )

        return data_obj

    except Exception as e:
        print(f"Erro ao processar data {data_str}: {e}")
        return None


def carregar_projetos(df):
    df = standardize_strings(df, ['status', 'categoria', 'prioridade', 'cidade', 'estado', 'nome', 'responsavel'])
    for _, row in df.iterrows():

        programa = DimPrograma.objects.get(
            id=int(row["programa_id"])
        )

        data_inicio = obter_ou_criar_data(
            row["data_inicio"]
        )

        data_fim = obter_ou_criar_data(
            row["data_fim_prevista"]
        )
  

        DimProjeto.objects.create(
            codigo_projeto=row["codigo_projeto"],
            nome_projeto=row["nome_projeto"],
            status=row["status"],
            programa=programa,
            responsavel=row["responsavel"],
            custo_hora=row["custo_hora"],
            data_inicio=data_inicio,
            data_fim_prevista=data_fim,
            lead_time_dias=row.get("lead_time_dias", 0),
            is_atrasado=row.get("is_atrasado", False)
        )

    print("Projetos carregados com sucesso.")

def carregar_materiais(df):

    df = standardize_strings(df, ['status', 'categoria', 'prioridade', 'cidade', 'estado', 'nome', 'responsavel'])
    for _, row in df.iterrows():

        DimMaterial.objects.create(
            codigo_material=row["codigo_material"],
            descricao=row["descricao"],
            categoria=row["categoria"],
            fabricante=row["fabricante"],
            custo_estimado=row["custo_estimado"],
            status=row["status"]
        )

    print("Materiais carregados com sucesso.")

def carregar_fornecedores(df):

    df = standardize_strings(df, ['status', 'categoria', 'prioridade', 'cidade', 'estado', 'nome', 'responsavel'])
    for _, row in df.iterrows():

        DimFornecedor.objects.create(
            codigo_fornecedor=row["codigo_fornecedor"],
            razao_social=row["razao_social"],
            cidade=row["cidade"],
            estado=row["estado"],
            categoria=row["categoria"],
            status=row["status"]
        )

    print("Fornecedores carregados com sucesso.")    