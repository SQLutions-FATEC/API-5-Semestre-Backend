FROM grafana/grafana:12.5.2

# Remove os dashboards padrão
RUN rm -rf /var/lib/grafana/dashboards/*

# Copia as configurações de provisionamento (YAMLs)
COPY ./provisioning/dashboards /etc/grafana/provisioning/dashboards
COPY ./provisioning/datasources /etc/grafana/provisioning/datasources

# Copia os arquivos JSON dos dashboards para o local correto
COPY ./dashboards_models/*.json /var/lib/grafana/dashboards/

# Ajuste de permissões (MUDANÇA AQUI: grafana:root)
USER root
RUN chown -R grafana:root /etc/grafana/provisioning/ /var/lib/grafana/dashboards/
USER grafana