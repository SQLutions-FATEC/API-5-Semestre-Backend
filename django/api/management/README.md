# Guia de Uso - Script de Seed do Banco de Dados

Este script popula o banco de dados com dados fictícios para testes.

---

## 1. Subir o Docker

Navegue até a pasta `deploy` e inicie os containers:

```bash
cd ../../../deploy
docker-compose up -d
```

**⚠️ Importante:** Se você já tem PostgreSQL instalado na sua máquina, ele usa a porta **5432**. Para evitar conflito, edite o arquivo `docker-compose.yaml` e altere:

```yaml
# Altere de:
- "5432:5432"

# Para:
- "5433:5432"
```

Dessa forma, o banco do Docker estará na porta 5433.

---

## 2. Rodar o Script de Seed

Com os containers rodando, execute o comando para popular o banco:

```bash
docker exec -it django-app python manage.py seed_db
```

Você verá a mensagem de sucesso:
> `Dados inseridos com sucesso! Relacionamentos de chaves estritamente mantidos.`

---

## 3. Conectar no DBeaver

Para visualizar os dados de forma gráfica, use o DBeaver:

1. Abra o DBeaver e clique em **Nova Conexão** (ou Database > New Database Connection)
2. Selecione **PostgreSQL** e clique em **Next**
3. Preencha com os dados abaixo e clique em **Test Connection**:

   - **Host:** `localhost`
   - **Port:** `5432` (ou `5433` se alterou no docker-compose)
   - **Database:** `api_db`
   - **Username:** `api_user`
   - **Password:** `senha_padrao`

4. Clique em **Finish** para salvar
5. Expanda a conexão no painel esquerdo e navegue até **Databases > api_db > Schemas > schema_api > Tables**
6. Dê duplo clique em qualquer tabela para visualizar os dados inseridos
