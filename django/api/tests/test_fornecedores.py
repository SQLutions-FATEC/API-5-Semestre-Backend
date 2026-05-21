from decimal import Decimal
from datetime import date
from unittest.mock import patch
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


class FornecedoresPedidosApiTest(TestCase):
    fixtures = ['fornecedores.json']

    def setUp(self):
        self.client = Client()
        self.fornecedor = DimFornecedor.objects.get(codigo_fornecedor="F1")
        self.fornecedor_sem_pedidos = DimFornecedor.objects.get(codigo_fornecedor="F2")

        # Mocka a data atual para 2024-05-15 (para ficar entre as datas da fixture)
        patcher = patch('api.views.fornecedores.date')
        self.mock_date = patcher.start()
        self.mock_date.today.return_value = date(
            2024, 5, 15
        )  # Essa função é usada no views/fornecedores.py
        self.addCleanup(patcher.stop)

    def test_fornecedor_pedidos_success(self):
        response = self.client.get(
            f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["fornecedor"], "Forn 1")
        self.assertEqual(data["quantidade_pedidos_totais"], 3)
        self.assertEqual(data["quantidade_atrasos"], 1)
        self.assertEqual(len(data["pedidos"]), 3)

    def test_fornecedor_pedidos_filtro_projeto_codigo(self):
        response = self.client.get(
            f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/?id_projeto=PRJA'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["quantidade_pedidos_totais"], 2)
        self.assertEqual(data["quantidade_atrasos"], 1)

    def test_fornecedor_pedidos_filtro_projeto_nome(self):
        response = self.client.get(
            f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/?id_projeto=Projeto B'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["quantidade_pedidos_totais"], 1)
        self.assertEqual(data["quantidade_atrasos"], 0)

    def test_fornecedor_pedidos_sem_dados(self):
        response = self.client.get(
            f'/api/fornecedores/{self.fornecedor_sem_pedidos.codigo_fornecedor}/pedidos/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["quantidade_pedidos_totais"], 0)
        self.assertEqual(data["quantidade_atrasos"], 0)
        self.assertEqual(len(data["pedidos"]), 0)

    def test_fornecedor_not_found(self):
        response = self.client.get('/api/fornecedores/INVALIDO/pedidos/')
        self.assertEqual(response.status_code, 404)

    def test_fornecedor_pedidos_wrong_method(self):
        response = self.client.post(
            f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/'
        )
        self.assertEqual(response.status_code, 405)
