import pandas as pd

def extrair_csv(arquivo):

    try:

        df = pd.read_csv(arquivo)

    except pd.errors.ParserError:

        raise ValueError(
            "Erro ao ler arquivo CSV. Verifique o arquivo e tente novamente."
        )

    if df.empty:

        raise ValueError(
            "Arquivo .CSV vazio. Verifique o arquivo e tente novamente."
        )

    return df