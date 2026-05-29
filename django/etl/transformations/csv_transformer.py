import pandas as pd


def transformar_csv(df, tipo_csv):

    try:

        df = df.copy()

        if tipo_csv == "projeto":

            df["custo_hora"] = pd.to_numeric(
                df["custo_hora"]
            )

            df["data_inicio"] = pd.to_datetime(
                df["data_inicio"]
            ).dt.date

            df["data_fim_prevista"] = pd.to_datetime(
                df["data_fim_prevista"]
            ).dt.date

        return df

    except ValueError:

        raise ValueError(
            "Erro: Os dados importados estão no formato incorreto. Verifique o arquivo e tente novamente."
        )