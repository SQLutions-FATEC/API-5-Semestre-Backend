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

        DimData.objects.create(
            dia=1,
            mes=1,
            ano=2025
        )

        self.programa = DimPrograma.objects.create(
            id=1,
            nome_programa="Programa Teste",
            data_inicio=data_inicio
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
                "programa_id": 1,
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31"
            }
        ])

        carregar_csv(df, "projetos")

        self.assertEqual(
            DimProjeto.objects.count(),
            1
        )

        projeto = DimProjeto.objects.first()

        self.assertEqual(
            projeto.nome_projeto,
            "Projeto A"
        )

        self.assertEqual(
            projeto.programa.id,
            1
        )

    def test_carregar_csv_tipo_invalido(self):

        df = pd.DataFrame()

        carregar_csv(df, "tipo_invalido")

        self.assertEqual(
            DimProjeto.objects.count(),
            0
        )