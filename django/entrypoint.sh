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
    echo "❌ FATAL ERROR: Falha ao aplicar as migrations!" >&2
    echo "O container não pode subir com o banco desatualizado/quebrado." >&2
    
    echo "==================================================" >&2
    exit 1
fi

# ... (aqui continua a sua lógica do RUN_SEED) ...

echo "🚀 Iniciando servidor Gunicorn..."
exec "$@"