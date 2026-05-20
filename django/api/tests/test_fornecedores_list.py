from django.test import TestCase, Client
from django.urls import reverse
from api.models import (
    DimFornecedor, DimPrograma, DimProjeto, DimSolicitacao, FatoCompra
)

class ListagemFornecedoresIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('api-listagem-fornecedores') 

        self.programa_alfa = DimPrograma.objects.create(nome_programa='Programa Alfa')
        self.programa_beta = DimPrograma.objects.create(nome_programa='Programa Beta')

        self.projeto_x = DimProjeto.objects.create(nome_projeto='Projeto X', programa=self.programa_alfa)
        self.projeto_y = DimProjeto.objects.create(nome_projeto='Projeto Y', programa=self.programa_beta)

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

        self.solicitacao_1 = DimSolicitacao.objects.create(projeto=self.projeto_x)
        self.solicitacao_2 = DimSolicitacao.objects.create(projeto=self.projeto_y)

        FatoCompra.objects.create(solicitacao=self.solicitacao_1, fornecedor=self.fornecedor_1)
        FatoCompra.objects.create(solicitacao=self.solicitacao_2, fornecedor=self.fornecedor_2)

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