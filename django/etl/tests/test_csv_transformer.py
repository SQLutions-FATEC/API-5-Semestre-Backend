import pandas as pd

from django.test import TestCase

from etl.transformations.csv_transformer import transformar_csv


class CsvTransformerTest(TestCase):

    def test_transformar_csv_valido(self):

        df = pd.DataFrame({
            "custo_hora": ["150"]
        })

        resultado = transformar_csv(
            df,
            "projeto"
        )

        self.assertEqual(
            resultado["custo_hora"][0],
            150
        )

    def test_transformar_csv_invalido(self):

        df = pd.DataFrame({
            "custo_hora": ["abc"]
        })

        with self.assertRaises(ValueError) as context:
            transformar_csv(df, "projeto")

        self.assertEqual(
            str(context.exception),
            "Erro: Os dados importados estão no formato incorreto. Verifique o arquivo e tente novamente."
        )