CREATE SCHEMA IF NOT EXISTS schema_api;
-- Aqui usamos o mesmo nome de usuário que vai estar no .env
GRANT ALL PRIVILEGES ON SCHEMA schema_api TO sqlutions;
ALTER ROLE sqlutions
SET search_path TO schema_api,
    public;