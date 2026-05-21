from unittest.mock import patch, mock_open, call
from django.test import TestCase
from django.core.management import call_command
from io import StringIO
import os


class SmartMigrateCommandTest(TestCase):

    @patch('api.management.commands.smart_migrate.connection')
    @patch('api.management.commands.smart_migrate.call_command')
    @patch('api.management.commands.smart_migrate.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_database_empty_with_from_scratch_dir(
        self, mock_file, mock_exists, mock_call_command, mock_connection
    ):
        # Configurar mocks
        mock_connection.introspection.table_names.return_value = []  # Banco vazio

        # Simula que o diretório api/from_scratch existe, e o __init__.py NÃO existe (para testar a criação)
        def exists_side_effect(path):
            if path.endswith('from_scratch'):
                return True
            if path.endswith('__init__.py'):
                return False
            return False

        mock_exists.side_effect = exists_side_effect

        # Executar comando
        out = StringIO()
        call_command('smart_migrate', stdout=out)

        # Asserções
        output = out.getvalue()
        self.assertIn("Banco de dados vazio detectado", output)
        self.assertIn(
            "Configurando o Django para usar a migração 'from scratch'", output
        )

        # Verifica se tentou criar o __init__.py
        mock_file.assert_called_once()

        # Verifica as chamadas do call_command (migrate)
        expected_calls = [call('migrate'), call('migrate', 'api', fake=True)]
        mock_call_command.assert_has_calls(expected_calls, any_order=False)

    @patch('api.management.commands.smart_migrate.connection')
    @patch('api.management.commands.smart_migrate.call_command')
    @patch('api.management.commands.smart_migrate.os.path.exists')
    def test_database_empty_without_from_scratch_dir(
        self, mock_exists, mock_call_command, mock_connection
    ):
        # Configurar mocks
        mock_connection.introspection.table_names.return_value = [
            'django_migrations'
        ]  # Considerado vazio

        # Simula que o diretório não existe
        mock_exists.return_value = False

        # Executar comando
        out = StringIO()
        call_command('smart_migrate', stdout=out)

        # Asserções
        output = out.getvalue()
        self.assertIn("Diretório não encontrado", output)

        # Verifica que o call_command interno NÃO foi chamado
        mock_call_command.assert_not_called()

    @patch('api.management.commands.smart_migrate.connection')
    @patch('api.management.commands.smart_migrate.call_command')
    def test_database_not_empty(self, mock_call_command, mock_connection):
        # Configurar mocks para banco com tabelas
        mock_connection.introspection.table_names.return_value = [
            'django_migrations',
            'api_projeto',
        ]

        # Executar comando
        out = StringIO()
        call_command('smart_migrate', stdout=out)

        # Asserções
        output = out.getvalue()
        self.assertIn("Banco de dados já contém tabelas", output)

        # Verifica se executou o migrate normal apenas uma vez
        mock_call_command.assert_called_once_with('migrate')
