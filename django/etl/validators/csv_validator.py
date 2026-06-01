MAPEAMENTO_CSV = {
    "codigo_projeto": "projeto",
    "descricao": "material",
    "razao_social": "fornecedor",
    "nome_programa": "programa",
}


def validar_csv(df):

    if len(df.columns) < 2:

        raise ValueError(
            "Arquivo .CSV não foi reconhecido. Verifique o formato do arquivo e tente novamente."
        )

    colunas = [col.lower().strip() for col in df.columns]

    tipo_csv = None

    for coluna in colunas:

        if coluna in MAPEAMENTO_CSV:

            tipo_csv = MAPEAMENTO_CSV[coluna]
            break

    if not tipo_csv:

        raise ValueError(
            "Arquivo .CSV não foi reconhecido. Verifique o formato do arquivo e tente novamente."
        )

    if df.isnull().values.any():

        raise ValueError(
            "Erro: Existem dados vazios no arquivo .CSV. Verifique o arquivo e tente novamente."
        )

    return tipo_csv
