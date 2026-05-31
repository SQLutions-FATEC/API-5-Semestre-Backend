from django.test import TestCase, Client
from django.urls import reverse
from api.models import (
    DimFornecedor, DimPrograma, DimProjeto, DimSolicitacao, FatoCompra,
    DimData, DimMaterial
)

class ListagemFornecedoresIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('api-listagem-fornecedores') 

        self.data_mock = DimData.objects.create(
            dia=24, 
            mes=5, 
            ano=2026
        )
        
        self.material_mock = DimMaterial.objects.create(
            codigo_material='M001',
            descricao='Material Genérico de Teste',
            categoria='Componentes',
            fabricante='SIATT',
            custo_estimado=100.00,
            status='Ativo'
        )

        self.programa_alfa = DimPrograma.objects.create(
            codigo_programa='PRG001',
            nome_programa='Programa Alfa',
            gerente_programa='João',
            gerente_tecnico='Maria',
            data_inicio=self.data_mock,
            data_fim_prevista=self.data_mock,
            status='Ativo'
        )
        self.programa_beta = DimPrograma.objects.create(
            codigo_programa='PRG002',
            nome_programa='Programa Beta',
            gerente_programa='Pedro',
            gerente_tecnico='Ana',
            data_inicio=self.data_mock,
            data_fim_prevista=self.data_mock,
            status='Ativo'
        )

        self.projeto_x = DimProjeto.objects.create(
            codigo_projeto='PRJ001',
            nome_projeto='Projeto X', 
            programa=self.programa_alfa,
            responsavel='Carlos',
            custo_hora=150.00,
            data_inicio=self.data_mock,
            data_fim_prevista=self.data_mock,
            status='Ativo'
        )
        self.projeto_y = DimProjeto.objects.create(
            codigo_projeto='PRJ002',
            nome_projeto='Projeto Y', 
            programa=self.programa_beta,
            responsavel='Julia',
            custo_hora=200.00,
            data_inicio=self.data_mock,
            data_fim_prevista=self.data_mock,
            status='Ativo'
        )

        self.fornecedor_1 = DimFornecedor.objects.create(
            codigo_fornecedor='F001',
            razao_social='RTech Distribuidora 1 Ltda',
            cidade='Jundiaí',
            estado='SP',
            categoria='Materiais de Solda',
            status='Ativo'
        )
        self.fornecedor_2 = DimFornecedor.objects.create(
            codigo_fornecedor='F002',
            razao_social='Tech Corp Eletrônicos',
            cidade='São Paulo',
            estado='SP',
            categoria='Eletrônica',
            status='Inativo'
        )

        self.solicitacao_1 = DimSolicitacao.objects.create(
            numero_solicitacao='SOL001',
            projeto=self.projeto_x,
            material=self.material_mock,
            quantidade=50,
            data_solicitacao=self.data_mock,
            prioridade='Alta',
            status='Aprovada'
        )
        self.solicitacao_2 = DimSolicitacao.objects.create(
            numero_solicitacao='SOL002',
            projeto=self.projeto_y,
            material=self.material_mock,
            quantidade=100,
            data_solicitacao=self.data_mock,
            prioridade='Média',
            status='Aprovada'
        )

        FatoCompra.objects.create(
            numero_pedido='PED001',
            valor_total=5000.00,
            status='Concluído',
            solicitacao=self.solicitacao_1, 
            fornecedor=self.fornecedor_1,
            data_pedido=self.data_mock,
            data_previsao_entrega=self.data_mock
        )
        FatoCompra.objects.create(
            numero_pedido='PED002',
            valor_total=10000.00,
            status='Pendente',
            solicitacao=self.solicitacao_2, 
            fornecedor=self.fornecedor_2,
            data_pedido=self.data_mock,
            data_previsao_entrega=self.data_mock
        )

    def test_listagem_sem_filtros_retorna_todos_fornecedores(self):
        """Garante que a rota pura retorna 100% dos registros"""
        response = self.client.get(self.url)
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_filtro_por_nome_fornecedor(self):
        """Filtro de busca por nome (razao_social) com icontains"""
        response = self.client.get(self.url, {'fornecedor_nome': 'RTech'})
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['razao_social'], 'RTech Distribuidora 1 Ltda')

    def test_filtro_por_cidade(self):
        """Filtro de busca exata/parcial por cidade"""
        response = self.client.get(self.url, {'fornecedor_cidade': 'São Paulo'})
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['cidade'], 'São Paulo')

    def test_filtro_por_categoria(self):
        """Filtro de busca pela categoria do material fornecido"""
        res_nome = self.client.get(self.url, {'categoria': 'Materiais de Solda'})
        self.assertEqual(len(res_nome.json()), 1)
        self.assertEqual(res_nome.json()[0]['razao_social'], 'RTech Distribuidora 1 Ltda')

    def test_filtro_relacional_por_projeto(self):
        """Filtro que exige os JOINs até a tabela DimProjeto"""
        response = self.client.get(self.url, {'projeto_nome': 'Projeto Y'})
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['razao_social'], 'Tech Corp Eletrônicos')

    def test_filtro_relacional_por_programa(self):
        """Filtro profundo que exige os JOINs até a tabela DimPrograma"""
        response = self.client.get(self.url, {'programa_nome': 'Programa Alfa'})
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['razao_social'], 'RTech Distribuidora 1 Ltda')

    def test_filtros_combinados(self):
        """Garante que passar múltiplos filtros reduz o escopo corretamente"""
        response = self.client.get(self.url, {
            'fornecedor_cidade': 'Jundiaí',
            'projeto_nome': 'Projeto X'
        })
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['codigo_fornecedor'], 'F001')
        
    def test_filtros_combinados_sem_resultado(self):
        """Garante que a combinação impossível retorna array vazio em vez de erro"""
        response = self.client.get(self.url, {
            'fornecedor_cidade': 'Jundiaí',
            'projeto_nome': 'Projeto Y'
        })
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)