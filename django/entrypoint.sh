#!/bin/bash
# Removemos o set -e daqui para termos controle manual do erro

echo "=================================================="
echo "🛠️ INICIANDO DATABASE MIGRATIONS..."
echo "=================================================="

# Executa o comando e captura o resultado
if python manage.py smart_migrate; then
    echo "✅ SUCESSO: Migrations aplicadas perfeitamente."
    echo "=================================================="
else
    echo "❌ FATAL ERROR: Falha ao aplicar as migrations!"
    echo "O container não pode subir com o banco desatualizado/quebrado."
    
    # Opcional: Se você usa Slack, Discord ou Teams, pode disparar um alerta aqui!
    # curl -X POST -H 'Content-type: application/json' --data '{"text":"🚨 Erro de Migration na API!"}' SEU_WEBHOOK_URL
    
    echo "=================================================="
    # Força o container a "morrer" informando código de erro para a AWS
    exit 1
fi

# ... (aqui continua a sua lógica do RUN_SEED) ...

echo "🚀 Iniciando servidor Gunicorn..."
exec "$@"