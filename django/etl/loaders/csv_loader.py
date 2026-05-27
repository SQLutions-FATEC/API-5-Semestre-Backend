from django.db import transaction

from api.models import (
    DimProjeto,
    DimPrograma,
    DimData
)


def carregar_csv(df, tipo_csv):

    with transaction.atomic():

        if tipo_csv == "projeto":

            carregar_projetos(df)


def carregar_projetos(df):

    for _, row in df.iterrows():

        programa = DimPrograma.objects.filter(
            codigo_programa=row["codigo_programa"]
        ).first()

        if not programa:

            raise Exception(
                f"Programa não encontrado: {row['codigo_programa']}"
            )

        data = DimData.objects.first()

        DimProjeto.objects.create(
            codigo_projeto=row["codigo_projeto"],
            nome_projeto=row["nome_projeto"],
            programa=programa,
            responsavel=row["responsavel"],
            custo_hora=row["custo_hora"],
            status=row["status"],
            data_inicio=data,
            data_fim_prevista=data
        )