import pandas as pd

LIMITE_BYTES = 5 * 1024 * 1024


def extrair_csv(arquivo):
    
    if not hasattr(arquivo, "read"):
        raise ValueError("Tipo de arquivo inválido.")

    tamanho = getattr(arquivo, "size", None)

    if tamanho is None:
        pos = arquivo.tell()
        arquivo.seek(0, 2) 
        tamanho = arquivo.tell()
        arquivo.seek(pos) 

    if tamanho > LIMITE_BYTES:
        raise ValueError("Arquivo muito grande")

    try:
        arquivo.seek(0)
        df = pd.read_csv(arquivo)

    except pd.errors.ParserError:
        raise ValueError("Erro ao ler arquivo CSV. Verifique o arquivo e tente novamente.")

    if df.empty:
        raise ValueError("Arquivo .CSV vazio. Verifique o arquivo e tente novamente.")

    return df