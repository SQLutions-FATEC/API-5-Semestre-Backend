import pandas as pd


def extrair_csv(arquivo):

    try:

        df = pd.read_csv(arquivo)

        if df.empty:

            raise Exception(
                "CSV vazio"
            )

        return df

    except Exception:

        raise Exception(
            "Erro ao ler arquivo CSV"
        )