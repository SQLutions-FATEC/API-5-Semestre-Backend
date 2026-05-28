import pandas as pd

from django.test import TestCase

from api.models import (
    DimPrograma,
    DimData,
    DimProjeto
)

from etl.loaders.csv_loader import carregar_csv


class CsvLoaderTest(TestCase):

    def setUp(self):

        self.data = DimData.objects.create(
            dia=1,
            mes=1,
            ano=2026
        )

        self.programa = DimPrograma.objects.create(
            codigo_programa="PR001",
            nome_programa="Programa Teste",
            gerente_programa="Gerente A",
            gerente_tecnico="Gerente Técnico A",
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="ATIVO"
        )

    def test_carregar_projeto(self):

        df = pd.DataFrame({
            "id": [1],
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "programa_id": [self.programa.id],
            "responsavel": ["João"],
            "custo_hora": [100],
            "data_inicio": ["2026-01-01"],
            "data_fim_prevista": ["2026-12-31"],
            "status": ["ATIVO"]
        })

        carregar_csv(df, "projeto")

        self.assertEqual(
            DimProjeto.objects.count(),
            1
        )

    def test_programa_nao_encontrado(self):

        df = pd.DataFrame({
            "id": [1],
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "programa_id": [999],
            "responsavel": ["João"],
            "custo_hora": [100],
            "data_inicio": ["2026-01-01"],
            "data_fim_prevista": ["2026-12-31"],
            "status": ["ATIVO"]
        })

        with self.assertRaises(LookupError) as context:
            carregar_csv(df, "projeto")

        self.assertEqual(
            str(context.exception),
            "Código de programa não foi localizado: 999"
        )

    def test_sem_data_cadastrada(self):

        DimData.objects.all().delete()

        df = pd.DataFrame({
            "id": [1],
            "codigo_projeto": ["P001"],
            "nome_projeto": ["Projeto Teste"],
            "programa_id": [self.programa.id],
            "responsavel": ["João"],
            "custo_hora": [100],
            "data_inicio": ["2026-01-01"],
            "data_fim_prevista": ["2026-12-31"],
            "status": ["ATIVO"]
        })

        with self.assertRaises(LookupError) as context:
            carregar_csv(df, "projeto")

        self.assertEqual(
            str(context.exception),
            "Nenhuma data cadastrada no sistema."
        )