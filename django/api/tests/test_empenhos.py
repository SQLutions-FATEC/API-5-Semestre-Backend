from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, 
    DimMaterial, FatoEmpenho
)

class ProjetoEmpenhoViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.data_1 = DimData.objects.create(dia=1, mes=2, ano=2024)
        self.data_2 = DimData.objects.create(dia=15, mes=3, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG03", nome_programa="Prog 3",
            gerente_programa="Gerente P3", gerente_tecnico="Gerente T3",
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ20", nome_projeto="Projeto Empenho",
            programa=self.programa, responsavel="Resp Empenho",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ21", nome_projeto="Projeto Sem Empenho",
            programa=self.programa, responsavel="Resp Sem Dados",
            custo_hora=Decimal('80.00'),
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.material_1 = DimMaterial.objects.create(
            codigo_material="MAT01", descricao="Cimento", categoria="Construcao",
            fabricante="Votorantim", custo_estimado=Decimal('35.50'), status="Ativo"
        )
        self.material_2 = DimMaterial.objects.create(
            codigo_material="MAT02", descricao="Tinta", categoria="Acabamento",
            fabricante="Suvinil", custo_estimado=Decimal('120.00'), status="Ativo"
        )
        self.material_3 = DimMaterial.objects.create(
            codigo_material="MAT03", descricao="Tijolo", categoria="Construcao",
            fabricante="Olaria", custo_estimado=Decimal('1.50'), status="Ativo"
        )

        FatoEmpenho.objects.create(
            quantidade_empenhada=10, projeto=self.projeto_com_dados, 
            material=self.material_1, data_empenho=self.data_1
        )
        FatoEmpenho.objects.create(
            quantidade_empenhada=5, projeto=self.projeto_com_dados, 
            material=self.material_2, data_empenho=self.data_1
        )
        FatoEmpenho.objects.create(
            quantidade_empenhada=1000, projeto=self.projeto_com_dados, 
            material=self.material_3, data_empenho=self.data_2
        )

    def test_empenho_success_with_data(self):
        response = self.client.get(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/empenhos/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['empenho_total'], 2455.00)

        categorias = {c['categoria']: c['total_custo'] for c in data['empenho_por_categoria']}
        self.assertEqual(categorias['Construcao'], 1855.00)
        self.assertEqual(categorias['Acabamento'], 600.00)

        materiais = {m['codigo_material']: m for m in data['empenho_por_material']}
        self.assertEqual(materiais['MAT01']['total_custo'], 355.00)
        self.assertEqual(materiais['MAT02']['total_custo'], 600.00)
        self.assertEqual(materiais['MAT03']['total_custo'], 1500.00)

        tempo = {t['data']: t for t in data['empenho_por_tempo']}
        self.assertEqual(tempo['2024-02-01']['total_custo'], 955.00)
        self.assertEqual(tempo['2024-03-15']['total_custo'], 1500.00)

    def test_empenho_success_without_data(self):
        response = self.client.get(f'/api/projetos/{self.projeto_vazio.codigo_projeto}/empenhos/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['empenho_total'], 0.0)
        self.assertEqual(data['empenho_por_categoria'], [])
        self.assertEqual(data['empenho_por_material'], [])
        self.assertEqual(data['empenho_por_tempo'], [])

    def test_empenho_not_found(self):
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/empenhos/')
        self.assertEqual(response.status_code, 404)

    def test_empenho_wrong_method(self):
        response = self.client.post(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/empenhos/')
        self.assertEqual(response.status_code, 405)


class EmpenhoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.data = DimData.objects.create(dia=1, mes=6, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="P1", nome_programa="Programa A",
            gerente_programa="X", gerente_tecnico="Y",
            data_inicio=self.data, data_fim_prevista=self.data, status="Ativo"
        )

        self.projeto = DimProjeto.objects.create(
            codigo_projeto="PR1", nome_projeto="Projeto A",
            programa=self.programa, responsavel="João",
            custo_hora=100, data_inicio=self.data, data_fim_prevista=self.data, status="Ativo"
        )

        self.material = DimMaterial.objects.create(
            codigo_material="M1", descricao="Cimento", categoria="Construção",
            fabricante="X", custo_estimado=50, status="Ativo"
        )

        self.empenho = FatoEmpenho.objects.create(
            quantidade_empenhada=10, projeto=self.projeto,
            material=self.material, data_empenho=self.data
        )

    def test_vinculo_programa(self):
        self.assertEqual(self.empenho.projeto.programa.nome_programa, "Programa A")

    def test_valor_empenhado(self):
        valor = self.empenho.quantidade_empenhada * self.material.custo_estimado
        self.assertEqual(valor, 500)

    def test_endpoint(self):
        url = f'/api/empenhos-programa/?programa_id={self.programa.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Projeto A")