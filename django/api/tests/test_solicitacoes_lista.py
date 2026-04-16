from api.models import DimFornecedor, FatoCompra, DimPrograma, DimProjeto, DimMaterial, DimSolicitacao, DimData
from decimal import Decimal
from django.test import TestCase, Client

class SolicitacoesDetalhesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.data_obj = DimData.objects.create(dia=10, mes=5, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PRG02", nome_programa="Prog Detalhes",
            gerente_programa="Gerente D", gerente_tecnico="Tecnico D",
            data_inicio=self.data_obj, data_fim_prevista=self.data_obj, status="Ativo"
        )

        self.projeto = DimProjeto.objects.create(
            codigo_projeto="PRJ03", nome_projeto="Proj Detalhes",
            programa=self.programa, responsavel="Resp", custo_hora=Decimal('100.00'),
            data_inicio=self.data_obj, data_fim_prevista=self.data_obj, status="Ativo"
        )

        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ04", nome_projeto="Proj Vazio",
            programa=self.programa, responsavel="Resp", custo_hora=Decimal('100.00'),
            data_inicio=self.data_obj, data_fim_prevista=self.data_obj, status="Ativo"
        )

        self.material = DimMaterial.objects.create(
            codigo_material="MAT02", descricao="Placa Mãe", categoria="Eletronicos",
            fabricante="Asus", custo_estimado=Decimal('150.00'), status="Ativo"
        )

        self.fornecedor = DimFornecedor.objects.create(
            codigo_fornecedor="FOR01", razao_social="Fornecedor X", cidade="SP",
            estado="SP", categoria="Eletronicos", status="Ativo"
        )

        self.sol_com_pedido = DimSolicitacao.objects.create(
            numero_solicitacao="S10", projeto=self.projeto, material=self.material,
            quantidade=2, data_solicitacao=self.data_obj, prioridade="Normal", status="Aprovada"
        )
        FatoCompra.objects.create(
            numero_pedido="PED10", valor_total=Decimal('300.00'), status="Enviado",
            solicitacao=self.sol_com_pedido, fornecedor=self.fornecedor,
            data_pedido=self.data_obj, data_previsao_entrega=self.data_obj
        )

        self.sol_sem_pedido = DimSolicitacao.objects.create(
            numero_solicitacao="S11", projeto=self.projeto, material=self.material,
            quantidade=5, data_solicitacao=self.data_obj, prioridade="Alta", status="Pendente"
        )

    def test_detalhes_success_with_data(self):
        """Garante que a matemática da view funcione e que o join com pedido seja feito/omitido corretamente"""
        response = self.client.get(f'/api/projetos/{self.projeto.codigo_projeto}/solicitacoes/detalhes/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto'], "PRJ03")
        
        solicitacoes = data['solicitacoes']
        self.assertEqual(len(solicitacoes), 2)

        sol_1 = next(s for s in solicitacoes if s['numero_solicitacao'] == 'S10')
        self.assertEqual(sol_1['numero_pedido'], 'PED10')
        self.assertEqual(sol_1['valor_total_estimado'], 300.00)
        self.assertEqual(sol_1['nome_material'], 'Placa Mãe')

        sol_2 = next(s for s in solicitacoes if s['numero_solicitacao'] == 'S11')
        self.assertIsNone(sol_2['numero_pedido'])
        self.assertEqual(sol_2['valor_total_estimado'], 750.00) 