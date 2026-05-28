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

        with self.assertRaises(ValueError) as context:
            validar_csv(df)

        self.assertEqual(
            str(context.exception),
            "Arquivo .CSV não foi reconhecido. Verifique o formato do arquivo e tente novamente."
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

        with self.assertRaises(ValueError) as context:
            validar_csv(df)

        self.assertEqual(
            str(context.exception),
            "Erro: Existem dados vazios no arquivo .CSV. Verifique o arquivo e tente novamente."
        )