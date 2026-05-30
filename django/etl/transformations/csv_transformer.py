import pandas as pd


def transformar_csv(df, tipo_csv):
    try:

        df = df.copy()

        if tipo_csv == "projeto":
            if "custo_hora" in df.columns:
                df["custo_hora"] = pd.to_numeric(df["custo_hora"])

            if "data_inicio" in df.columns:
                df["data_inicio"] = pd.to_datetime(df["data_inicio"]).dt.date

            if "data_fim_prevista" in df.columns:
                df["data_fim_prevista"] = pd.to_datetime(df["data_fim_prevista"]).dt.date

        elif tipo_csv == "material":
            if "custo_estimado" in df.columns:
                df["custo_estimado"] = pd.to_numeric(df["custo_estimado"])

        return df

    except ValueError:
        raise ValueError(
            "Erro: Os dados importados estão no formato incorreto. Verifique o arquivo e tente novamente."
        )