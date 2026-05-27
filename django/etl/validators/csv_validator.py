MAPEAMENTO_CSV = {

    ("nome_projeto", 6): "projeto",

    ("descricao", 5): "material",

    ("razao_social", 5): "fornecedor",
}


def validar_csv(df):

    segunda_coluna = df.columns[1].lower()

    numero_colunas = len(df.columns)

    chave = (
        segunda_coluna,
        numero_colunas
    )

    tipo_csv = MAPEAMENTO_CSV.get(chave)

    if not tipo_csv:

        raise Exception(
            "CSV não reconhecido"
        )

    if df.isnull().values.any():

        raise Exception(
            "Erro na importação: Existem dados vazios"
        )

    return tipo_csv