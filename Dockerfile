FROM python:3.6.4-alpine3.7

RUN ["pip", "install", "prometheus_client"]

COPY ynab_exporter.py /

ENTRYPOINT ["python3", "ynab_exporter.py"]
