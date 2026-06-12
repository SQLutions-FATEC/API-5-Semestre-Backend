FROM prom/mysqld-exporter:v0.19.0

# Copia o seu arquivo de credenciais para dentro do Linux do container
COPY mysql-exporter.cnf /etc/.my.cnf

# Força o exporter a iniciar lendo este arquivo
ENTRYPOINT ["/bin/mysqld_exporter", "--config.my-cnf=/etc/.my.cnf"]