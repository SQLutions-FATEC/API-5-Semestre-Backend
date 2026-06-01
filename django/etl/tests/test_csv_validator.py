import pandas as pd

from django.test import TestCase

from etl.validators.csv_validator import validar_csv


class CsvValidatorTest(TestCase):

    def test_validar_csv_projeto(self):

        df = pd.DataFrame(columns=["id", "codigo_projeto"])

        resultado = validar_csv(df)

        self.assertEqual(resultado, "projeto")

    def test_validar_csv_material(self):

        df = pd.DataFrame(columns=["id", "descricao"])

        resultado = validar_csv(df)

        self.assertEqual(resultado, "material")

    def test_validar_csv_fornecedor(self):

        df = pd.DataFrame(columns=["id", "razao_social"])

        resultado = validar_csv(df)

        self.assertEqual(resultado, "fornecedor")

    def test_validar_csv_programa(self):

        df = pd.DataFrame(columns=["id", "nome_programa"])

        resultado = validar_csv(df)

        self.assertEqual(resultado, "programa")

    def test_validar_csv_invalido(self):

        df = pd.DataFrame(columns=["id", "teste"])

        with self.assertRaises(ValueError):

            validar_csv(df)

    def test_validar_csv_com_nulos(self):

        df = pd.DataFrame([{"codigo_projeto": None}])

        with self.assertRaises(ValueError):

            validar_csv(df)
