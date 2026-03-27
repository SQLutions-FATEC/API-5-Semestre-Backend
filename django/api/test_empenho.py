from django.test import TestCase
from api.models import *

class EmpenhoTest(TestCase):

    def setUp(self):
        self.data = DimData.objects.create(dia=1, mes=6, ano=2024)

        self.material = DimMaterial.objects.create(
            descricao="Cimento",
            categoria="Construção",
            custo_estimado=50,
            codigo_material="MAT1",
            fabricante="X",
            status="Ativo"
        )

        self.projeto = DimProjeto.objects.create(
            nome_projeto="Obra A",
            codigo_projeto="P1",
            responsavel="João",
            custo_hora=100,
            programa=DimPrograma.objects.create(
                codigo_programa="PRG",
                nome_programa="Prog",
                gerente_programa="A",
                gerente_tecnico="B",
                data_inicio=self.data,
                data_fim_prevista=self.data,
                status="Ativo"
            ),
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="Ativo"
        )

        self.empenho = FatoEmpenho.objects.create(
            quantidade_empenhada=10,
            projeto=self.projeto,
            material=self.material,
            data_empenho=self.data
        )

    def test_vinculo_projeto(self):
        self.assertEqual(self.empenho.projeto.nome_projeto, "Obra A")

    def test_custo_total(self):
        custo = self.empenho.quantidade_empenhada * self.material.custo_estimado
        self.assertEqual(custo, 500)