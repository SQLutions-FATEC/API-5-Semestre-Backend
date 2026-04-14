from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, DimMaterial, DimSolicitacao
)

class SolicitacoesStatsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        hoje = date.today()
        passado_5d = hoje - timedelta(days=5)
        passado_2d = hoje - timedelta(days=2)

        self.data_hoje = DimData.objects.create(dia=hoje.day, mes=hoje.month, ano=hoje.year)
        self.data_5d = DimData.objects.create(dia=passado_5d.day, mes=passado_5d.month, ano=passado_5d.year)
        self.data_2d = DimData.objects.create(dia=passado_2d.day, mes=passado_2d.month, ano=passado_2d.year)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG01", nome_programa="Prog Solicitacoes",
            gerente_programa="Gerente S", gerente_tecnico="Tecnico S",
            data_inicio=self.data_5d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ01", nome_projeto="Projeto com Solicitacoes",
            programa=self.programa, responsavel="Resp", custo_hora=Decimal('100.00'),
            data_inicio=self.data_5d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ02", nome_projeto="Projeto Vazio",
            programa=self.programa, responsavel="Resp 2", custo_hora=Decimal('100.00'),
            data_inicio=self.data_5d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        self.material = DimMaterial.objects.create(
            codigo_material="MAT01", descricao="Cabo", categoria="Eletrica",
            fabricante="Fab", custo_estimado=Decimal('10.00'), status="Ativo"
        )

        # Encurtado de "SOL-001" para "S01" (3 chars)
        DimSolicitacao.objects.create(
            numero_solicitacao="S01", projeto=self.projeto_com_dados, material=self.material,
            quantidade=1, data_solicitacao=self.data_5d, prioridade="Normal", status="Aberto"
        )
        
        DimSolicitacao.objects.create(
            numero_solicitacao="S02", projeto=self.projeto_com_dados, material=self.material,
            quantidade=1, data_solicitacao=self.data_5d, prioridade="Urgente", status="Aberto"
        )

        DimSolicitacao.objects.create(
            numero_solicitacao="S03", projeto=self.projeto_com_dados, material=self.material,
            quantidade=1, data_solicitacao=self.data_2d, prioridade="Alta", status="Aberto"
        )

        DimSolicitacao.objects.create(
            numero_solicitacao="S04", projeto=self.projeto_com_dados, material=self.material,
            quantidade=1, data_solicitacao=self.data_5d, prioridade="Urgente", status="Fechado"
        )
    
    def test_stats_success_with_data(self):
        """Valida a contagem de pendentes, os filtros de criticidade e o cálculo de datas"""
        response = self.client.get(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/solicitacoes/stats/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        estatisticas = data['estatisticas']

        self.assertEqual(data['projeto'], "PRJ01")
        self.assertEqual(estatisticas['total_pendentes'], 3)
        self.assertEqual(len(estatisticas['urgentes_criticas']), 2)

        sol_urgente = next(s for s in estatisticas['urgentes_criticas'] if s['numero_solicitacao'] == 'S02')
        self.assertEqual(sol_urgente['status'], 'Aberto')
        self.assertEqual(sol_urgente['prioridade'], 'Urgente')
        self.assertEqual(sol_urgente['dias_desde_criacao'], 5) 

        sol_alta = next(s for s in estatisticas['urgentes_criticas'] if s['numero_solicitacao'] == 'S03')
        self.assertEqual(sol_alta['prioridade'], 'Alta')
        self.assertEqual(sol_alta['dias_desde_criacao'], 2)

    def test_stats_success_without_data(self):
        """Garante que projetos sem solicitações retornem inteiros zerados e listas vazias (Não estoure erro de NoneType)"""
        response = self.client.get(f'/api/projetos/{self.projeto_vazio.codigo_projeto}/solicitacoes/stats/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['projeto'], "PRJ02")
        self.assertEqual(data['estatisticas']['total_pendentes'], 0)
        self.assertEqual(data['estatisticas']['urgentes_criticas'], [])

    def test_stats_not_found(self):
        """Garante a proteção 404 para projetos que não existem"""
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/solicitacoes/stats/')
        self.assertEqual(response.status_code, 404)

    def test_stats_wrong_method(self):
        """Garante a blindagem da rota apenas para métodos GET"""
        response = self.client.post(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/solicitacoes/stats/')
        self.assertEqual(response.status_code, 405)