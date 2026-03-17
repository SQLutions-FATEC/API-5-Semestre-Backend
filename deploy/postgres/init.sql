CREATE SCHEMA IF NOT EXISTS schema_api;
-- Aqui usamos o mesmo nome de usuário que vai estar no .env
GRANT ALL PRIVILEGES ON SCHEMA schema_api TO api_user;
ALTER ROLE api_user
SET search_path TO schema_api,
    public;