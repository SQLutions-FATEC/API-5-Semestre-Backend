MAPEAMENTO_CSV = {

    ("codigo_projeto", 9): "projeto",

    ("descricao", 5): "material",

    ("razao_social", 5): "fornecedor",
}


def validar_csv(df):

    if len(df.columns) < 2:

        raise ValueError(
            "Arquivo .CSV não foi reconhecido. Verifique o formato do arquivo e tente novamente."
        )

    segunda_coluna = df.columns[1].lower()

    numero_colunas = len(df.columns)

    chave = (
        segunda_coluna,
        numero_colunas
    )

    tipo_csv = MAPEAMENTO_CSV.get(chave)

    if not tipo_csv:

        raise ValueError(
            "Arquivo .CSV não foi reconhecido. Verifique o formato do arquivo e tente novamente."
        )

    if df.isnull().values.any():

        raise ValueError(
            "Erro: Existem dados vazios no arquivo .CSV. Verifique o arquivo e tente novamente."
        )

    return tipo_csv