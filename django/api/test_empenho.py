from django.test import TestCase
from api.models import *

class EmpenhoTest(TestCase):

    def setUp(self):
        self.data = DimData.objects.create(dia=1, mes=6, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="P1",
            nome_programa="Programa A",
            gerente_programa="X",
            gerente_tecnico="Y",
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="Ativo"
        )

        self.projeto = DimProjeto.objects.create(
            codigo_projeto="PR1",
            nome_projeto="Projeto A",
            programa=self.programa,
            responsavel="João",
            custo_hora=100,
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="Ativo"
        )

        self.material = DimMaterial.objects.create(
            codigo_material="M1",
            descricao="Cimento",
            categoria="Construção",
            fabricante="X",
            custo_estimado=50,
            status="Ativo"
        )

        self.empenho = FatoEmpenho.objects.create(
            quantidade_empenhada=10,
            projeto=self.projeto,
            material=self.material,
            data_empenho=self.data
        )

    def test_vinculo_programa(self):
        self.assertEqual(
            self.empenho.projeto.programa.nome_programa,
            "Programa A"
        )

    def test_valor_empenhado(self):
        valor = self.empenho.quantidade_empenhada * self.material.custo_estimado
        self.assertEqual(valor, 500)

    def test_endpoint(self):
        response = self.client.get('/api/empenhos-programa/?programa_id=1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Projeto A")  