import pandas as pd

from django.test import TestCase

from etl.validators.csv_validator import validar_csv


class CsvValidatorTest(TestCase):

    def test_csv_projeto_valido(self):

        df = pd.DataFrame({
            "id": [1],
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "programa_id": [1],
            "responsavel": ["João"],
            "custo_hora": [100],
            "data_inicio": ["2026-01-01"],
            "data_fim_prevista": ["2026-12-31"],
            "status": ["ATIVO"]
        })

        resultado = validar_csv(df)

        self.assertEqual(
            resultado,
            "projeto"
        )

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
            "id": [1],
            "codigo_projeto": ["P001"],
            "nome_projeto": [None],
            "programa_id": [1],
            "responsavel": ["João"],
            "custo_hora": [100],
            "data_inicio": ["2026-01-01"],
            "data_fim_prevista": ["2026-12-31"],
            "status": ["ATIVO"]
        })

        with self.assertRaises(ValueError) as context:
            validar_csv(df)

        self.assertEqual(
            str(context.exception),
            "Erro: Existem dados vazios no arquivo .CSV. Verifique o arquivo e tente novamente."
        )

    def test_csv_com_menos_de_duas_colunas(self):

        df = pd.DataFrame({
            "codigo_projeto": ["P001"]
        })

        with self.assertRaises(ValueError) as context:
            validar_csv(df)

        self.assertEqual(
            str(context.exception),
            "Arquivo .CSV não foi reconhecido. Verifique o formato do arquivo e tente novamente."
        )