from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, 
    DimMaterial, DimSolicitacao, FatoCompra, DimFornecedor
)

class FornecedoresPedidosApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        amanha = hoje + timedelta(days=1)
        
        self.data_hoje = DimData.objects.create(dia=hoje.day, mes=hoje.month, ano=hoje.year)
        self.data_passada = DimData.objects.create(dia=ontem.day, mes=ontem.month, ano=ontem.year)
        self.data_futura = DimData.objects.create(dia=amanha.day, mes=amanha.month, ano=amanha.year)

        self.programa = DimPrograma.objects.create(
            codigo_programa="P1", nome_programa="Prog 1", data_inicio=self.data_passada, data_fim_prevista=self.data_futura
        )
        self.projeto_A = DimProjeto.objects.create(
            codigo_projeto="PRJA", nome_projeto="Projeto A", programa=self.programa, custo_hora=10,
            data_inicio=self.data_passada, data_fim_prevista=self.data_futura
        )
        self.projeto_B = DimProjeto.objects.create(
            codigo_projeto="PRJB", nome_projeto="Projeto B", programa=self.programa, custo_hora=10,
            data_inicio=self.data_passada, data_fim_prevista=self.data_futura
        )
        
        self.material = DimMaterial.objects.create(codigo_material="M1", descricao="Mat 1", custo_estimado=10)
        self.fornecedor = DimFornecedor.objects.create(codigo_fornecedor="F1", razao_social="Forn 1")
        self.fornecedor_sem_pedidos = DimFornecedor.objects.create(codigo_fornecedor="F2", razao_social="Forn 2")
        
        self.solicitacao_A = DimSolicitacao.objects.create(
            numero_solicitacao="S1", projeto=self.projeto_A, material=self.material, quantidade=1, data_solicitacao=self.data_passada
        )
        self.solicitacao_B = DimSolicitacao.objects.create(
            numero_solicitacao="S2", projeto=self.projeto_B, material=self.material, quantidade=1, data_solicitacao=self.data_passada
        )

        self.compra_atrasada = FatoCompra.objects.create(
            numero_pedido="PED1", valor_total=100.0, status="aberto", solicitacao=self.solicitacao_A,
            fornecedor=self.fornecedor, data_pedido=self.data_passada, data_previsao_entrega=self.data_passada
        )
        
        self.compra_prazo = FatoCompra.objects.create(
            numero_pedido="PED2", valor_total=200.0, status="aberto", solicitacao=self.solicitacao_B,
            fornecedor=self.fornecedor, data_pedido=self.data_passada, data_previsao_entrega=self.data_futura
        )

        self.compra_entregue = FatoCompra.objects.create(
            numero_pedido="PED3", valor_total=300.0, status="entregue", solicitacao=self.solicitacao_A,
            fornecedor=self.fornecedor, data_pedido=self.data_passada, data_previsao_entrega=self.data_passada
        )

    def test_fornecedor_pedidos_success(self):
        response = self.client.get(f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["fornecedor"], "Forn 1")
        self.assertEqual(data["quantidade_pedidos_totais"], 3)
        self.assertEqual(data["quantidade_atrasos"], 1)
        self.assertEqual(len(data["pedidos"]), 3)

    def test_fornecedor_pedidos_filtro_projeto_codigo(self):
        response = self.client.get(f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/?id_projeto=PRJA')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["quantidade_pedidos_totais"], 2)
        self.assertEqual(data["quantidade_atrasos"], 1)

    def test_fornecedor_pedidos_filtro_projeto_nome(self):
        response = self.client.get(f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/?id_projeto=Projeto B')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["quantidade_pedidos_totais"], 1)
        self.assertEqual(data["quantidade_atrasos"], 0)

    def test_fornecedor_pedidos_sem_dados(self):
        response = self.client.get(f'/api/fornecedores/{self.fornecedor_sem_pedidos.codigo_fornecedor}/pedidos/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["quantidade_pedidos_totais"], 0)
        self.assertEqual(data["quantidade_atrasos"], 0)
        self.assertEqual(len(data["pedidos"]), 0)

    def test_fornecedor_not_found(self):
        response = self.client.get('/api/fornecedores/INVALIDO/pedidos/')
        self.assertEqual(response.status_code, 404)

    def test_fornecedor_pedidos_wrong_method(self):
        response = self.client.post(f'/api/fornecedores/{self.fornecedor.codigo_fornecedor}/pedidos/')
        self.assertEqual(response.status_code, 405)
