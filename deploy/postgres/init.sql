-- Cria um schema específico para a sua aplicação
CREATE SCHEMA IF NOT EXISTS schema_api;
-- Define que o usuário padrão tenha acesso total a esse schema
GRANT ALL PRIVILEGES ON SCHEMA schema_api TO api_user;
-- Define o schema padrão para pesquisas
ALTER ROLE api_user
SET search_path TO schema_api,
    public;