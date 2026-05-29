import os
import pandas as pd

LIMITE_MB = 5
LIMITE_BYTES = LIMITE_MB * 1024 * 1024


def extrair_csv(arquivo):

    if os.path.getsize(arquivo) > LIMITE_BYTES:

        raise ValueError(
            f"Arquivo maior que {LIMITE_MB}MB. Verifique o arquivo e tente novamente."
        )

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