import pandas as pd

from django.test import TestCase
from etl.loaders.csv_loader import carregar_csv
from datetime import date
from api.models import (
    DimPrograma,
    DimData,
    DimProjeto
)


class CsvLoaderTest(TestCase):

    def setUp(self):

        self.data_inicio = DimData.objects.create(
            dia=1,
            mes=1,
            ano=2026
        )

        self.data_fim = DimData.objects.create(
            dia=31,
            mes=12,
            ano=2026
        )

        self.programa = DimPrograma.objects.create(
            codigo_programa="TESTE",
            nome_programa="Programa Teste",
            gerente_programa="Gerente A",
            gerente_tecnico="Gerente Técnico A",
            data_inicio=self.data_inicio,
            data_fim_prevista=self.data_fim,
            status="EM ANDAMENTO"
        )

    def test_carregar_projeto(self):

        df = pd.DataFrame({
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "codigo_programa": ["TESTE"],
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
            "Código de programa não foi localizado: INVALIDO",
            str(context.exception)
        )