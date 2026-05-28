import pandas as pd


def extrair_csv(arquivo):

    try:

        df = pd.read_csv(arquivo)

        if df.empty:

            raise Exception(
                "Arquivo .CSV vazio. Verifique o arquivo e tente novamente."
            )

        return df

    except Exception:

        raise Exception(
            "Erro ao ler arquivo CSV. Verifique o arquivo e tente novamente."
        )