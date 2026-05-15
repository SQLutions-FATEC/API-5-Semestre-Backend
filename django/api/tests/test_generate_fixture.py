import os
import tempfile
import shutil
from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch

class GenerateFixtureCommandTest(TestCase):
    
    def setUp(self):
        # Cria um diretório temporário para não sujar as fixtures reais durante o teste
        self.test_dir = tempfile.mkdtemp()
        self.fixture_dir = os.path.join(self.test_dir, 'api', 'fixtures')
        os.makedirs(self.fixture_dir, exist_ok=True)

    def tearDown(self):
        # Limpa tudo
        shutil.rmtree(self.test_dir)

    @patch('api.management.commands.generate_fixture.call_command')
    @patch('os.chown')
    def test_generate_fixture_success(self, mock_chown, mock_call_command):
        """Testa se o comando funciona normalmente criando o arquivo no local correto."""
        out = StringIO()
        
        with patch('api.management.commands.generate_fixture.os.path.dirname') as mock_dirname:
            # Faz o comando salvar no nosso diretório temporário
            mock_dirname.return_value = self.fixture_dir
            
            filename_esperado = os.path.join(self.fixture_dir, 'meu_teste.json')
            
            with patch('api.management.commands.generate_fixture.os.makedirs'):
                # O comando não usa o valor de retorno de open para nada além de stdout
                call_command('generate_fixture', 'meu_teste', stdout=out)
        
        self.assertIn('Sucesso', out.getvalue())
        # O mock call_command('dumpdata') evitou que escrevesse de verdade no arquivo as 15000 linhas
        mock_call_command.assert_called_with('dumpdata', 'api', indent=4, stdout=mock_call_command.call_args[1].get('stdout'))

    @patch('api.management.commands.generate_fixture.call_command')
    @patch('os.chown')
    def test_generate_fixture_with_json_extension(self, mock_chown, mock_call_command):
        """Testa se a extensão .json é removida para evitar arquivos como nome.json.json"""
        out = StringIO()
        with patch('api.management.commands.generate_fixture.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = self.fixture_dir
            call_command('generate_fixture', 'com_extensao.json', stdout=out)
            
        self.assertIn('com_extensao.json', out.getvalue())
        self.assertNotIn('com_extensao.json.json', out.getvalue())

    @patch('api.management.commands.generate_fixture.os.makedirs', side_effect=Exception("Permissão Negada simulada"))
    def test_generate_fixture_exception_handling(self, mock_makedirs):
        """Testa se a exceção é pega amigavelmente pelo bloco try-except."""
        out = StringIO()
        call_command('generate_fixture', 'teste_erro', stdout=out)
        self.assertIn("Erro ao gerar a fixture", out.getvalue())
        self.assertIn("Permissão Negada simulada", out.getvalue())

