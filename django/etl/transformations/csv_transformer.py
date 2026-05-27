import pandas as pd


def transformar_csv(df, tipo_csv):

    try:

        if tipo_csv == "projeto":

            df["custo_hora"] = pd.to_numeric(
                df["custo_hora"]
            )

        return df

    except Exception:

        raise Exception(
            "Erro na importação: Os dados estão no formato incorreto"
        )