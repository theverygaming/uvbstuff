#!/usr/bin/env bash

set -e

# Cria o ambiente virtual, se não existir
if [ ! -d "autoreload_venv" ]; then
  python3 -m venv autoreload_venv || { echo "Erro ao criar o venv"; exit 1; }
fi

# Ativa o ambiente virtual
source autoreload_venv/bin/activate || { echo "Erro ao ativar o venv"; exit 1; }

# Instala os pacotes
pip install git+https://github.com/theverygaming/silly.git@050482f272af4fab564c15238bd7b17ecf22197d || { echo "Erro ao instalar silly"; exit 1; }
pip install requests || { echo "Erro ao instalar requests"; exit 1; }

# Loop de execução
while true; do
  python main.py >> autoreload.log 2>&1
done

