import os
import pandas as pd
import pytest
from django.test import TestCase
from django.core.management import call_command
from api.models import DimPrograma, DimProjeto, DimTarefa, FatoCompra
from etl.extractors.base import CSV_BASE_PATH

class ETLIntegrationTest(TestCase):
    """
    Testes de integração para validar o fluxo CSV -> DW.
    """

    def setUp(self):
        """
        Verifica se os arquivos CSV existem antes de rodar o comando.
        """
        self.required_files = [
            'programas.csv', 'projetos.csv', 'tarefas_projeto.csv', 
            'pedidos_compra.csv'
        ]
        for f in self.required_files:
            path = os.path.join(CSV_BASE_PATH, f)
            self.assertTrue(os.path.exists(path), f"Arquivo não encontrado: {path}")

    def test_run_etl_command(self):
        """
        Testa se o comando 'run_etl' popula o banco corretamente e aplica transformações.
        """
        # 1. Executa o comando de gerenciamento que criamos
        call_command('run_etl')

        # 2. Valida DimPrograma (Dimensão Base)
        df_programas = pd.read_csv(os.path.join(CSV_BASE_PATH, 'programas.csv'))
        self.assertEqual(DimPrograma.objects.count(), len(df_programas))

        # 3. Valida FatoCompra (Fato com FKs)
        df_pedidos = pd.read_csv(os.path.join(CSV_BASE_PATH, 'pedidos_compra.csv'))
        self.assertEqual(FatoCompra.objects.count(), len(df_pedidos))

        # 4. Valida um dado específico para garantir que o mapeamento de colunas está OK
        primeiro_pedido_csv = df_pedidos.iloc[0]['numero_pedido']
        primeiro_pedido_db = FatoCompra.objects.get(id=df_pedidos.iloc[0]['id'])
        self.assertEqual(primeiro_pedido_db.numero_pedido, primeiro_pedido_csv)

        # 5. Validação das Transformações (Adicionado conforme Comentário do PR)
        projeto = DimProjeto.objects.first()
        self.assertIsNotNone(projeto, "O banco deveria ter pelo menos um projeto carregado.")
        
        #garante que o status ficou tudo em maiúsculo (standardize_strings)
        self.assertEqual(projeto.status, projeto.status.upper())
        
        #garante que o cálculo de métricas rodou corretamente (calculate_project_metrics)
        self.assertGreaterEqual(projeto.lead_time_dias, 0)

    def test_etl_command_idempotency(self):
        """
        Garante que rodar o comando duas vezes não duplica dados (Idempotência).
        """
        call_command('run_etl')
        count_first_run = DimProjeto.objects.count()
        self.assertGreater(count_first_run, 0, "A tabela não deveria estar vazia após a carga.")
        
        call_command('run_etl') # deve apagar os dados antigos e carregar de novo
        self.assertEqual(DimProjeto.objects.count(), count_first_run)