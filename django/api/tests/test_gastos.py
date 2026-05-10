from django.test import TestCase, Client
from decimal import Decimal
from api.models import DimProjeto, DimPrograma, DimData, FatoCompra, DimSolicitacao, DimMaterial, DimFornecedor

class GastosProjetoApiTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.data = DimData.objects.create(dia=1, mes=1, ano=2026)

        self.prog = DimPrograma.objects.create(
            codigo_programa="P1",
            nome_programa="Prog 1",
            status="Ativo",
            data_inicio=self.data,
            data_fim_prevista=self.data
        )

        self.proj = DimProjeto.objects.create(
            codigo_projeto="PRJGST",
            nome_projeto="Projeto Teste Gasto",
            programa=self.prog,
            custo_hora=100,
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="EM ANDAMENTO"
        )
        self.mat = DimMaterial.objects.create(codigo_material="M1", descricao="Material X", custo_estimado=50)
        self.forn = DimFornecedor.objects.create(codigo_fornecedor="F1", razao_social="Fornecedor Y")
        self.sol = DimSolicitacao.objects.create(numero_solicitacao="S1", projeto=self.proj, material=self.mat, quantidade=1, data_solicitacao=self.data)

        #cria dois pedidos para somar no consolidado
        FatoCompra.objects.create(numero_pedido="PED-01", valor_total=Decimal("1500.00"), status="Concluido", solicitacao=self.sol, fornecedor=self.forn, data_pedido=self.data, data_previsao_entrega=self.data)
        FatoCompra.objects.create(numero_pedido="PED-02", valor_total=Decimal("500.00"), status="Pendente", solicitacao=self.sol, fornecedor=self.forn, data_pedido=self.data, data_previsao_entrega=self.data)

    def test_detalhamento_gastos_sucesso(self):
        url = f'/api/projetos/{self.proj.codigo_projeto}/gastos/detalhes/'
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['gasto_total_consolidado'], 2000.0)
        self.assertEqual(len(data['pedidos']), 2)
        self.assertEqual(data['pedidos'][0]['numero_pedido'], "PED-01")
