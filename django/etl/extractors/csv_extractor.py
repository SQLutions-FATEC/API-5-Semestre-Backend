import pandas as pd

LIMITE_BYTES = 5 * 1024 * 1024


def extrair_csv(arquivo):

    tamanho = arquivo.size

    if tamanho > LIMITE_BYTES:
        raise ValueError("Arquivo muito grande")

    try:
        arquivo.seek(0)
        df = pd.read_csv(arquivo)

    except pd.errors.ParserError:
        raise ValueError(
            "Erro ao ler arquivo CSV. Verifique o arquivo e tente novamente."
        )

    if df.empty:
        raise ValueError("Arquivo CSV vazio. Verifique o arquivo e tente novamente.")

    return df
