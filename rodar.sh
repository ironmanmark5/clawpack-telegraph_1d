#!/bin/bash

# Configura o ambiente do Clawpack (ajuste o caminho se necessário)
export CLAW=$(realpath ../../../) 
export PYTHONPATH=$CLAW:$PYTHONPATH

# Verifica se o usuário forneceu o tamanho da malha
if [ -z "$1" ]
  then
    echo "Erro: Digite o número de células (malha). Exemplo: ./rodar_telegrafista.sh 400"
    exit 1
fi

MALHA=$1
OUT="output_malha_$MALHA"
PLOT="plots_malha_$MALHA"

echo "--- Alterando a malha para $MALHA células no setrun.py ---"

# Ajusta o número de células no arquivo setrun.py
# Procura pela linha 'clawdata.num_cells[0] =' e substitui pelo novo valor
sed -i "s/clawdata.num_cells\[0\] = .*/clawdata.num_cells\[0\] = $MALHA/" setrun.py

echo "--- Compilando o código (make .exe) ---"
make .exe

echo "--- Executando a simulação ---"
make .output OUTDIR=$OUT

echo "--- Gerando os gráficos ---"
make .plots OUTDIR=$OUT PLOTDIR=$PLOT

echo "--- Finalizado! ---"
echo "Dados salvos em: $OUT"
echo "Gráficos salvos em: $PLOT"