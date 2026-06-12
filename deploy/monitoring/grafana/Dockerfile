FROM grafana/grafana-oss:latest
COPY ./provisioning /etc/grafana/provisioning
# Garanta que a pasta dashboards exista ou ajuste o caminho conforme sua estrutura
COPY ./dashboards_models /var/lib/grafana/dashboards