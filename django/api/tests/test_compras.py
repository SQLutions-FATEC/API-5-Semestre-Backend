from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData,
    DimPrograma,
    DimProjeto,
    DimMaterial,
    DimSolicitacao,
    FatoCompra,
    DimFornecedor,
)


class ComprasProjetoViewTest(TestCase):
    fixtures = ['compras_golden.json']

    def setUp(self):
        self.client = Client()

        # Recuperando objetos da fixture que são usados nos testes
        self.projeto_com_dados = DimProjeto.objects.get(codigo_projeto="PRJ01")
        self.projeto_vazio = DimProjeto.objects.get(codigo_projeto="PRJ02")

    def test_compras_success_with_data(self):
        response = self.client.get(
            f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/compras/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['tempo_medio_entrega_dias'], 15.0)
        self.assertEqual(len(data['pedidos']), 2)

        pedido_1 = next(p for p in data['pedidos'] if p['numero'] == 'PED01')
        self.assertEqual(pedido_1['fornecedor'], "Forn Teste")
        self.assertEqual(pedido_1['nome_material'], "Mat 1")
        self.assertEqual(pedido_1['status'], "Entregue")
        self.assertEqual(pedido_1['dias_previstos_entrega'], 10)

    def test_compras_success_without_data(self):
        response = self.client.get(
            f'/api/projetos/{self.projeto_vazio.codigo_projeto}/compras/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['tempo_medio_entrega_dias'], 0.0)
        self.assertEqual(data['pedidos'], [])

    def test_compras_not_found(self):
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/compras/')
        self.assertEqual(response.status_code, 404)

    def test_compras_wrong_method(self):
        response = self.client.post(
            f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/compras/'
        )
        self.assertEqual(response.status_code, 405)


class EvolucaoGastosProjetoViewTest(TestCase):
    fixtures = ['evolucao_gastos_golden.json']

    def setUp(self):
        self.client = Client()

        # Recuperando objetos da fixture que são usados nos testes
        self.projeto_com_dados = DimProjeto.objects.get(codigo_projeto="PEVO01")
        self.projeto_vazio = DimProjeto.objects.get(codigo_projeto="PEVO02")
        self.material = DimMaterial.objects.get(codigo_material="M02")
        self.fornecedor = DimFornecedor.objects.get(codigo_fornecedor="F02")
        self.data_mar = DimData.objects.get(dia=1, mes=3, ano=2024)

    def test_evolucao_gastos_success_with_data(self):
        response = self.client.get(
            f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/gastos/evolucao/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 3)  # Jan, Feb, Mar

        self.assertEqual(data[0]['data'], '2024-01')
        self.assertEqual(data[0]['total_gasto'], 150.00)  # Only ENTREGUE counted

        self.assertEqual(data[1]['data'], '2024-02')  # The gap should be filled with 0
        self.assertEqual(data[1]['total_gasto'], 0.0)

        self.assertEqual(data[2]['data'], '2024-03')
        self.assertEqual(data[2]['total_gasto'], 200.00)

    def test_evolucao_gastos_success_without_data(self):
        response = self.client.get(
            f'/api/projetos/{self.projeto_vazio.codigo_projeto}/gastos/evolucao/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data, [])

    def test_evolucao_gastos_debug_mode(self):
        response = self.client.get(
            f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/gastos/evolucao/?debug=true'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('debug', data)
        self.assertIn('resultado', data)
        self.assertEqual(data['debug']['total_compras_geral'], 3)

    def test_evolucao_gastos_debug_mode_without_data(self):
        response = self.client.get(
            f'/api/projetos/{self.projeto_vazio.codigo_projeto}/gastos/evolucao/?debug=true'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('debug', data)
        self.assertEqual(data['resultado'], [])

    def test_evolucao_gastos_not_found(self):
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/gastos/evolucao/')
        self.assertEqual(response.status_code, 404)

    def test_evolucao_gastos_wrong_method(self):
        response = self.client.post(
            f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/gastos/evolucao/'
        )
        self.assertEqual(response.status_code, 405)

    def test_evolucao_gastos_min_date_before_project(self):
        data_old = DimData.objects.create(dia=1, mes=12, ano=2023)
        solicitacao_old = DimSolicitacao.objects.create(
            numero_solicitacao="S03",
            projeto=self.projeto_com_dados,
            material=self.material,
            quantidade=2,
            data_solicitacao=data_old,
            prioridade="Alta",
            status="Ativo",
        )
        FatoCompra.objects.create(
            numero_pedido="PEOLD",
            valor_total=Decimal('50.00'),
            status="ENTREGUE",
            solicitacao=solicitacao_old,
            fornecedor=self.fornecedor,
            data_pedido=data_old,
            data_previsao_entrega=self.data_mar,
        )
        response = self.client.get(
            f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/gastos/evolucao/'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 4)  # Dec 23, Jan 24, Feb 24, Mar 24
        self.assertEqual(data[0]['data'], '2023-12')
        self.assertEqual(data[0]['total_gasto'], 50.00)
