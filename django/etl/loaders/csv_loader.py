from datetime import datetime

from api.models import (
    DimPrograma,
    DimData,
    DimProjeto
)


def carregar_csv(df, tipo):

    if tipo == "projetos":
        carregar_projetos(df)


def obter_ou_criar_data(data_str):

    if not data_str:
        return None

    try:

        data = datetime.strptime(
            str(data_str),
            "%Y-%m-%d"
        )

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

    for _, row in df.iterrows():

        programa = DimPrograma.objects.get(
            id=int(row["programa_id"])
        )

        data_inicio = obter_ou_criar_data(
            row["data_inicio"]
        )

        data_fim = obter_ou_criar_data(
            row["data_fim"]
        )

        DimProjeto.objects.create(
            nome_projeto=row["nome_projeto"],
            status=row["status"],
            programa=programa,
            data_inicio=data_inicio,
            data_fim_prevista=data_fim
        )

    print("Projetos carregados com sucesso.")