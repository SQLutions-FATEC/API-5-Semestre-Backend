import pandas as pd


def transformar_csv(df, tipo_csv):

    try:

        df = df.copy()

        if tipo_csv == "projeto":

            df["custo_hora"] = pd.to_numeric(
                df["custo_hora"]
            )

        return df

    except ValueError:

        raise ValueError(
            "Erro: Os dados importados estão no formato incorreto. Verifique o arquivo e tente novamente."
        )