from unittest.mock import patch, MagicMock
from django.test import TestCase
import api.management.commands.setup_to_fixture as cmd_mod
from api.management.commands.setup_to_fixture import Command


class SetupToFixtureCommandTest(TestCase):
    @patch.object(cmd_mod, 'setup_databases')
    @patch.object(cmd_mod, 'teardown_databases')
    @patch.object(cmd_mod, 'importlib')
    @patch.object(cmd_mod, 'call_command')
    def test_command_success(
        self, mock_call_command, mock_importlib, mock_teardown, mock_setup
    ):
        mock_setup.return_value = 'old_config'

        mock_module = MagicMock()
        mock_test_class = MagicMock()
        mock_test_instance = MagicMock()

        setattr(mock_module, 'MockTestCase', mock_test_class)
        mock_importlib.import_module.return_value = mock_module
        mock_test_class.return_value = mock_test_instance

        cmd = Command()
        cmd.handle(
            test_class_path='fake.module.MockTestCase', fixture_name='test_fixture.json'
        )

        mock_importlib.import_module.assert_called_once_with('fake.module')
        mock_setup.assert_called_once_with(verbosity=1, interactive=False)
        mock_test_class.assert_called_once()
        mock_test_instance._pre_setup.assert_called_once()
        mock_test_instance.setUp.assert_called_once()
        mock_call_command.assert_called_once_with('generate_fixture', 'test_fixture')
        mock_teardown.assert_called_once_with('old_config', verbosity=1)

    @patch.object(cmd_mod, 'setup_databases')
    @patch.object(cmd_mod, 'teardown_databases')
    @patch.object(cmd_mod, 'importlib')
    @patch.object(cmd_mod, 'call_command')
    def test_command_without_json_extension(
        self, mock_call_command, mock_importlib, mock_teardown, mock_setup
    ):
        mock_setup.return_value = 'old_config'
        mock_module = MagicMock()
        mock_test_class = MagicMock()
        mock_test_instance = MagicMock()

        setattr(mock_module, 'MockTestCase', mock_test_class)
        mock_importlib.import_module.return_value = mock_module
        mock_test_class.return_value = mock_test_instance

        cmd = Command()
        cmd.handle(
            test_class_path='fake.module.MockTestCase', fixture_name='test_fixture'
        )

        mock_call_command.assert_called_once_with('generate_fixture', 'test_fixture')

    @patch.object(cmd_mod, 'setup_databases')
    @patch.object(cmd_mod, 'teardown_databases')
    @patch.object(cmd_mod, 'importlib')
    def test_command_exception_handling(
        self, mock_importlib, mock_teardown, mock_setup
    ):
        mock_setup.return_value = 'old_config'
        mock_module = MagicMock()
        mock_test_class = MagicMock()

        setattr(mock_module, 'MockTestCase', mock_test_class)
        mock_importlib.import_module.return_value = mock_module
        mock_test_class.return_value.setUp.side_effect = Exception("Erro forçado")

        with self.assertRaises(Exception):
            cmd = Command()
            cmd.handle(
                test_class_path='fake.module.MockTestCase', fixture_name='test_fixture'
            )

        mock_teardown.assert_called_once_with('old_config', verbosity=1)

    @patch.object(cmd_mod, 'setup_databases')
    @patch.object(cmd_mod, 'teardown_databases')
    @patch.object(cmd_mod, 'importlib')
    @patch.object(cmd_mod, 'call_command')
    def test_command_without_pre_setup(
        self, mock_call_command, mock_importlib, mock_teardown, mock_setup
    ):
        mock_setup.return_value = 'old_config'
        mock_module = MagicMock()
        mock_test_class = MagicMock()

        mock_test_instance = MagicMock(spec=['setUp'])

        setattr(mock_module, 'MockTestCase', mock_test_class)
        mock_importlib.import_module.return_value = mock_module
        mock_test_class.return_value = mock_test_instance

        cmd = Command()
        cmd.handle(
            test_class_path='fake.module.MockTestCase', fixture_name='test_fixture'
        )

        mock_test_instance.setUp.assert_called_once()
        mock_call_command.assert_called_once_with('generate_fixture', 'test_fixture')
