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

    data = DimData.objects.first()

    if not data:

        raise LookupError(
            "Nenhuma data cadastrada no sistema."
        )

    for _, row in df.iterrows():

        try:

            programa = DimPrograma.objects.get(
                id=int(row["programa_id"])
            )

        except DimPrograma.DoesNotExist:

            raise LookupError(
                f"Código de programa não foi localizado: {row['programa_id']}"
            )

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