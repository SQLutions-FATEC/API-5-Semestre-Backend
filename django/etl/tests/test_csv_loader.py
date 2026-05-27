import pandas as pd

from django.test import TestCase

from etl.loaders.csv_loader import carregar_csv

from api.models import (
    DimPrograma,
    DimData,
    DimProjeto
)


class CsvLoaderTest(TestCase):

    def setUp(self):

        self.programa = DimPrograma.objects.create(
            codigo_programa="PR001",
            nome_programa="Programa Teste"
        )

        self.data = DimData.objects.create()

    def test_carregar_projeto(self):

        df = pd.DataFrame({
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "codigo_programa": ["PR001"],
            "responsavel": ["João"],
            "custo_hora": [100],
            "status": ["ATIVO"]
        })

        carregar_csv(df, "projeto")

        self.assertEqual(
            DimProjeto.objects.count(),
            1
        )

    def test_programa_nao_encontrado(self):

        df = pd.DataFrame({
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "codigo_programa": ["INVALIDO"],
            "responsavel": ["João"],
            "custo_hora": [100],
            "status": ["ATIVO"]
        })

        with self.assertRaises(Exception) as context:
            carregar_csv(df, "projeto")

        self.assertIn(
            "Programa não encontrado",
            str(context.exception)
        )