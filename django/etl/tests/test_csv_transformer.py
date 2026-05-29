import pandas as pd

from django.test import TestCase

from etl.transformations.csv_transformer import (
    transformar_csv
)


class CsvTransformerTest(TestCase):

    def test_transformar_csv_projeto(self):

        df = pd.DataFrame([
            {
                "custo_hora": "150",
                "data_inicio": "2025-01-01",
                "data_fim_prevista": "2025-12-31"
            }
        ])

        resultado = transformar_csv(
            df,
            "projeto"
        )

        self.assertEqual(
            resultado["custo_hora"][0],
            150
        )

    def test_transformar_csv_tipo_diferente(self):

        df = pd.DataFrame([
            {
                "nome": "Teste"
            }
        ])

        resultado = transformar_csv(
            df,
            "material"
        )

        self.assertEqual(
            resultado["nome"][0],
            "Teste"
        )

    def test_transformar_csv_valor_invalido(self):

        df = pd.DataFrame([
            {
                "custo_hora": "abc",
                "data_inicio": "2025-01-01",
                "data_fim_prevista": "2025-12-31"
            }
        ])

        with self.assertRaises(ValueError):

            transformar_csv(
                df,
                "projeto"
            )