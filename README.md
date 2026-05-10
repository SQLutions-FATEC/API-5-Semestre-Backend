#  API - 5º Semestre

Este repositório contém o back-end em **Django** e o banco de dados **PostgreSQL** do projeto.  

---

## 📁 Estrutura do Projeto

- `django/`: Código-fonte da API, regras de negócio e `requirements.txt`
- `deploy/`:  
  - `Dockerfiles` dos serviços  
  - `docker-compose.yaml`  
  - Scripts de inicialização (`init.sql`)

---

## ⚙️ Pré-requisitos

Antes de começar, instale:

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (com Docker Compose)

---

## 🛠️ Como rodar o projeto localmente

### 1. Clone o repositório

Este projeto utiliza submódulos, então use `--recursive`:

```bash
git clone --recursive https://github.com/SQLutions-FATEC/API-5-Semestre.git
cd API-5-Semestre

## Atualize os submódulos para a versão mais recente:
git submodule update --remote
```

### 2. Configure as variáveis de ambiente

Acesse a pasta de deploy:

```bash
cd backend/deploy

##Crie o arquivo .env:
cp .env.example .env
```
Agora edite o .env com suas configurações locais (se necessário).

### 3. Suba os contêineres

Ainda dentro da pasta deploy, execute:

```bash
docker compose up -d --build
```

### 4. Execute as migrações do banco
Com os contêineres rodando:

```bash
docker compose exec backend python manage.py migrate
```

### 5. Acesse a aplicação
Se tudo deu certo, o servidor estará disponível em:

http://localhost:8000

---
### Comandos úteis

- Para parar os contêineres:

```bash
docker compose down
```

- Para resetar o banco de dados:

```bash
docker compose down -v
```