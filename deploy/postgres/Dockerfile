# Usamos a versão Alpine por ser muito mais leve
FROM postgres:15-alpine

# Copia o nosso script de criação do Schema para a pasta de inicialização nativa
COPY init.sql /docker-entrypoint-initdb.d/
