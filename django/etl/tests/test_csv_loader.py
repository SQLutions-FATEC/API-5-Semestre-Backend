import pandas as pd
from django.test import TestCase

from api.models import (
    DimPrograma,
    DimProjeto,
    DimData
)

from etl.loaders.csv_loader import (
    carregar_csv,
    obter_ou_criar_data
)


class CsvLoaderTest(TestCase):

    def setUp(self):

        # Datas necessárias como DimData (FK do modelo)
        self.data_inicio = DimData.objects.create(
            dia=1,
            mes=1,
            ano=2025
        )

        self.data_fim_prevista = DimData.objects.create(
            dia=31,
            mes=12,
            ano=2025
        )

        # Programa com todas as FKs obrigatórias
        self.programa = DimPrograma.objects.create(
            nome_programa="Programa Teste",
            data_inicio=self.data_inicio,
            data_fim_prevista=self.data_fim_prevista
        )

    def test_obter_ou_criar_data(self):

        data = obter_ou_criar_data("2025-01-10")

        self.assertIsNotNone(data)
        self.assertEqual(data.ano, 2025)
        self.assertEqual(data.mes, 1)
        self.assertEqual(data.dia, 10)

    def test_obter_ou_criar_data_invalida(self):

        data = obter_ou_criar_data("data-invalida")

        self.assertIsNone(data)

    def test_carregar_csv_projetos(self):

        df = pd.DataFrame([
            {
                "nome_projeto": "Projeto A",
                "descricao": "Descricao A",
                "status": "Ativo",
                "programa_id": self.programa.id,
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31"
            }
        ])

        carregar_csv(df, "projetos")

        self.assertEqual(DimProjeto.objects.count(), 1)

        projeto = DimProjeto.objects.first()

        self.assertEqual(projeto.nome_projeto, "Projeto A")
        self.assertEqual(projeto.programa.id, self.programa.id)

    def test_carregar_csv_tipo_invalido(self):

        df = pd.DataFrame()

        carregar_csv(df, "tipo_invalido")

        self.assertEqual(DimProjeto.objects.count(), 0)