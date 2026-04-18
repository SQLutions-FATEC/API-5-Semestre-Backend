from decimal import Decimal
from django.test import TestCase, Client
from api.models import DimData, DimPrograma, DimProjeto


class ProgramaProjetosViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.data = DimData.objects.create(dia=1, mes=1, ano=2024)

        self.programa_com_projetos = DimPrograma.objects.create(
            codigo_programa='PROG10',
            nome_programa='Programa 10',
            gerente_programa='Gerente 10',
            gerente_tecnico='Tecnico 10',
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Ativo',
        )

        self.programa_sem_projetos = DimPrograma.objects.create(
            codigo_programa='PROG11',
            nome_programa='Programa 11',
            gerente_programa='Gerente 11',
            gerente_tecnico='Tecnico 11',
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Planejado',
        )

        DimProjeto.objects.create(
            codigo_projeto='PRJ10',
            nome_projeto='Projeto 10',
            programa=self.programa_com_projetos,
            responsavel='Resp 10',
            custo_hora=Decimal('100.00'),
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Ativo',
        )
        DimProjeto.objects.create(
            codigo_projeto='PRJ11',
            nome_projeto='Projeto 11',
            programa=self.programa_com_projetos,
            responsavel='Resp 11',
            custo_hora=Decimal('80.00'),
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Concluido',
        )

    def test_programa_projetos_success(self):
        response = self.client.get('/api/programas/projetos/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('programas', data)
        self.assertEqual(len(data['programas']), 2)

        programa_10 = next(
            p for p in data['programas'] if p['codigo_programa'] == 'PROG10'
        )
        self.assertEqual(programa_10['nome_programa'], 'Programa 10')
        self.assertEqual(programa_10['status'], 'Ativo')
        self.assertEqual(programa_10['gerente'], 'Gerente 10')
        self.assertEqual(programa_10['gerente_tecnico'], 'Tecnico 10')
        self.assertNotIn('projetos', programa_10)

        programa_11 = next(
            p for p in data['programas'] if p['codigo_programa'] == 'PROG11'
        )
        self.assertEqual(programa_11['nome_programa'], 'Programa 11')
        self.assertEqual(programa_11['status'], 'Planejado')
        self.assertEqual(programa_11['gerente'], 'Gerente 11')
        self.assertEqual(programa_11['gerente_tecnico'], 'Tecnico 11')
        self.assertNotIn('projetos', programa_11)

    def test_programa_projetos_wrong_method(self):
        response = self.client.post('/api/programas/projetos/')
        self.assertEqual(response.status_code, 405)

class BuscaProjetosViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.data = DimData.objects.create(dia=1, mes=1, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa='PROG10',
            nome_programa='Programa 10',
            gerente_programa='Gerente 10',
            gerente_tecnico='Tecnico 10',
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Ativo',
        )
        
        self.programa_outro = DimPrograma.objects.create(
            codigo_programa='PROG11',
            nome_programa='Programa 11',
            gerente_programa='Gerente 11',
            gerente_tecnico='Tecnico 11',
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Planejado',
        )

        DimProjeto.objects.create(
            codigo_projeto='PRJ10',
            nome_projeto='Projeto Alpha',
            programa=self.programa,
            responsavel='Resp 10',
            custo_hora=Decimal('100.00'),
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Ativo',
        )
        DimProjeto.objects.create(
            codigo_projeto='PRJ11',
            nome_projeto='Projeto Beta',
            programa=self.programa,
            responsavel='Resp 11',
            custo_hora=Decimal('80.00'),
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Concluido',
        )
        DimProjeto.objects.create(
            codigo_projeto='PRJ33',
            nome_projeto='Projeto Alpha Dois',
            programa=self.programa_outro,
            responsavel='Resp 33',
            custo_hora=Decimal('90.00'),
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status='Ativo',
        )

    def test_busca_projetos_por_nome(self):
        response = self.client.get('/api/PROG10/projetos/busca/?q=alpha')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['codigo_projeto'], 'PRJ10')
        self.assertEqual(data[0]['nome_projeto'], 'Projeto Alpha')
        self.assertEqual(data[0]['status'], 'Ativo')
        self.assertEqual(data[0]['responsavel'], 'Resp 10')
        
    def test_busca_projetos_case_insensitive_codigo(self):
        response = self.client.get('/api/PROG10/projetos/busca/?q=prj11')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['codigo_projeto'], 'PRJ11')
        
    def test_busca_projetos_sem_termo(self):
        response = self.client.get('/api/PROG10/projetos/busca/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data), 2)
        
    def test_busca_projetos_limita_ao_programa(self):
        response = self.client.get('/api/PROG11/projetos/busca/?q=alpha')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['codigo_projeto'], 'PRJ33')
