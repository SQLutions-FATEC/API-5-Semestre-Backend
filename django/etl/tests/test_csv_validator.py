import pandas as pd

from django.test import TestCase

from etl.validators.csv_validator import validar_csv


class CsvValidatorTest(TestCase):

    def test_csv_projeto_valido(self):

        df = pd.DataFrame({
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "codigo_programa": ["PR001"],
            "responsavel": ["João"],
            "custo_hora": [100],
            "status": ["ATIVO"]
        })

        resultado = validar_csv(df)

        self.assertEqual(resultado, "projeto")

    def test_csv_nao_reconhecido(self):

        df = pd.DataFrame({
            "a": [1],
            "b": [2]
        })

        with self.assertRaises(Exception) as context:
            validar_csv(df)

        self.assertEqual(
            str(context.exception),
            "CSV não reconhecido"
        )

    def test_csv_com_dados_vazios(self):

        df = pd.DataFrame({
            "codigo_projeto": ["P001"],
            "nome_projeto": [None],
            "codigo_programa": ["PR001"],
            "responsavel": ["João"],
            "custo_hora": [100],
            "status": ["ATIVO"]
        })

        with self.assertRaises(Exception) as context:
            validar_csv(df)

        self.assertEqual(
            str(context.exception),
            "Erro na importação: Existem dados vazios"
        )