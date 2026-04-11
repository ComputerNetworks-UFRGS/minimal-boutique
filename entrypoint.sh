#!/bin/bash
# Inicia o Postgres
service postgresql start

# Espera alguns segundos para Postgres inicializar
sleep 5

# Roda sua aplicação Flask
exec python app.py
