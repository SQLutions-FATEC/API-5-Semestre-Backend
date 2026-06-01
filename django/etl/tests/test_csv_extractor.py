import io

from django.test import TestCase

from etl.extractors.csv_extractor import extrair_csv


class CsvExtractorTest(TestCase):

    def test_extrair_csv_valido(self):

        arquivo = io.BytesIO(b"codigo_material,descricao\nMAT001,Material A")

        arquivo.size = len(arquivo.getvalue())

        df = extrair_csv(arquivo)

        self.assertEqual(len(df), 1)

    def test_extrair_csv_vazio(self):

        arquivo = io.BytesIO(b"")

        arquivo.size = len(arquivo.getvalue())

        with self.assertRaises(ValueError):
            extrair_csv(arquivo)

    def test_extrair_csv_maior_que_limite(self):

        arquivo = io.BytesIO(b"codigo_material,descricao\nMAT001,Material A")

        arquivo.size = 6 * 1024 * 1024

        with self.assertRaises(ValueError):
            extrair_csv(arquivo)
