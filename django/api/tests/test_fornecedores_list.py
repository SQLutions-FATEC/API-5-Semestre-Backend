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

        # 1. Criação das Dimensões base para satisfazer as Foreign Keys (NOT NULL)
        # Atenção: Ajuste os campos (como ano, mes, dia) caso sua model de DimData exija outros campos.
        self.data_mock = DimData.objects.create(
            id=20260524, 
            ano=2026, 
            mes=5, 
            dia=24
        )
        
        self.material_mock = DimMaterial.objects.create(
            codigo_material='M001',
            descricao='Material Genérico de Teste',
            status='Ativo'
        )

        # 2. Criação de Programas e Projetos (agora recebendo a data obrigatória)
        self.programa_alfa = DimPrograma.objects.create(
            nome_programa='Programa Alfa',
            data_inicio=self.data_mock  # <-- Conserto do erro aqui
        )
        self.programa_beta = DimPrograma.objects.create(
            nome_programa='Programa Beta',
            data_inicio=self.data_mock
        )

        self.projeto_x = DimProjeto.objects.create(
            nome_projeto='Projeto X', 
            programa=self.programa_alfa,
            # Se DimProjeto também exigir datas obrigatórias, adicione aqui:
            # data_inicio=self.data_mock 
        )
        self.projeto_y = DimProjeto.objects.create(
            nome_projeto='Projeto Y', 
            programa=self.programa_beta
        )

        # 3. Criação de Fornecedores
        self.fornecedor_1 = DimFornecedor.objects.create(
            codigo_fornecedor='F001',
            razao_social='RTech Distribuidora 1 Ltda',
            cidade='Jundiaí',
            categoria='Materiais de Solda',
            codigo_categoria='CAT01',
            status='Ativo'
        )
        self.fornecedor_2 = DimFornecedor.objects.create(
            codigo_fornecedor='F002',
            razao_social='Tech Corp Eletrônicos',
            cidade='São Paulo',
            categoria='Eletrônica',
            codigo_categoria='CAT02',
            status='Inativo'
        )

        # 4. Criação de Solicitações e Vínculos com Compras
        # Passando a data e material para satisfazer possíveis constraints da Fato e da Solicitação
        self.solicitacao_1 = DimSolicitacao.objects.create(
            projeto=self.projeto_x,
            material=self.material_mock,
            data_solicitacao=self.data_mock
        )
        self.solicitacao_2 = DimSolicitacao.objects.create(
            projeto=self.projeto_y,
            material=self.material_mock,
            data_solicitacao=self.data_mock
        )

        FatoCompra.objects.create(
            solicitacao=self.solicitacao_1, 
            fornecedor=self.fornecedor_1,
            data_pedido=self.data_mock,
            data_previsao_entrega=self.data_mock
        )
        FatoCompra.objects.create(
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

    def test_filtro_por_categoria_nome_e_codigo(self):
        """Filtro deve funcionar tanto passando o nome quanto o código da categoria (Q objects)"""
        # Testando pelo nome
        res_nome = self.client.get(self.url, {'categoria': 'Materiais de Solda'})
        self.assertEqual(len(res_nome.json()), 1)
        self.assertEqual(res_nome.json()[0]['razao_social'], 'RTech Distribuidora 1 Ltda')

        # Testando pelo código
        res_codigo = self.client.get(self.url, {'categoria': 'CAT02'})
        self.assertEqual(len(res_codigo.json()), 1)
        self.assertEqual(res_codigo.json()[0]['razao_social'], 'Tech Corp Eletrônicos')

    def test_filtro_relacional_por_projeto(self):
        """Filtro que exige os JOINs (select_related/filter) até a tabela DimProjeto"""
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
            'projeto_nome': 'Projeto Y' # Projeto Y não é de Jundiaí
        })
        data = response.json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)