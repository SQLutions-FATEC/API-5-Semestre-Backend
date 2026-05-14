from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Executa migrações de forma inteligente: do zero se o banco estiver vazio, ou normal caso contrário.'

    def handle(self, *args, **kwargs):
        tables = connection.introspection.table_names()
        
        is_empty = len(tables) == 0 or tables == ['django_migrations']
        
        if is_empty:
            self.stdout.write(self.style.WARNING("Banco de dados vazio detectado. Executando migração única 'from scratch'..."))
            
            # A migração "from scratch" está em um arquivo de migração do Django na pasta api/sql.
            # Precisamos apontar temporariamente o módulo de migrações do app 'api' para essa pasta.
            sql_dir = os.path.join(settings.BASE_DIR, 'api', 'from_scratch')
            init_file = os.path.join(sql_dir, '__init__.py')
            
            # Garante que a pasta sql seja um pacote Python válido
            if os.path.exists(sql_dir):
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        pass
                    
                self.stdout.write("Configurando o Django para usar a migração 'from scratch'...")
                
                # Altera em memória o caminho das migrações do app 'api'
                if not hasattr(settings, 'MIGRATION_MODULES') or settings.MIGRATION_MODULES is None:
                    settings.MIGRATION_MODULES = {}
                settings.MIGRATION_MODULES['api'] = 'api.from_scratch'
                
                # Aplica o from_scratch
                self.stdout.write("Aplicando migrações no banco de dados...")
                call_command('migrate')
                
                # Desfaz a alteração para que o Django volte a ler da pasta api/migrations/
                settings.MIGRATION_MODULES.pop('api')
                
                self.stdout.write("Marcando o restante das migrações regulares do app 'api' como concluídas (fake)...")
                # Finge aplicar as migrações regulares de 'api' para que o banco seja considerado atualizado
                call_command('migrate', 'api', fake=True)
                
                self.stdout.write(self.style.SUCCESS("Migração 'from scratch' concluída com sucesso!"))
            else:
                self.stdout.write(self.style.ERROR(f"Diretório não encontrado: {sql_dir}"))
                self.stdout.write(self.style.WARNING("Crie o diretório api/sql/ com a sua Migration inicial para usar essa funcionalidade."))
        else:
            self.stdout.write(self.style.SUCCESS("Banco de dados já contém tabelas. Executando migração normal..."))
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS("Migração normal concluída com sucesso!"))

