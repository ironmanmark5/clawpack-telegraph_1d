#!/usr/bin/env bash
# Verifica se o ambiente tem o necessario para reproduzir o trabalho.
# Nao altera nada: apenas informa o que esta pronto e o que falta.

set -u

falhas=0

relatar_ok()   { printf '  [ok]    %s\n' "$1"; }
relatar_falta() { printf '  [falta] %s\n' "$1"; falhas=$((falhas + 1)); }

echo "Ferramentas"
for ferramenta in gfortran make python3; do
    if command -v "$ferramenta" >/dev/null 2>&1; then
        relatar_ok "$ferramenta: $(command -v "$ferramenta")"
    else
        relatar_falta "$ferramenta nao encontrado no PATH"
    fi
done

echo
echo "Pacotes de Python"
if command -v python3 >/dev/null 2>&1; then
    for pacote in numpy matplotlib; do
        if python3 -c "import $pacote" >/dev/null 2>&1; then
            versao=$(python3 -c "import $pacote; print(getattr($pacote, '__version__', 'versao desconhecida'))")
            relatar_ok "$pacote $versao"
        else
            relatar_falta "$pacote nao instalado (use: python3 -m pip install -r requirements.txt)"
        fi
    done
    if python3 -c "import clawpack" >/dev/null 2>&1; then
        relatar_ok "clawpack na PYTHONPATH: $(python3 -c "import clawpack; print(clawpack.__version__)" 2>/dev/null)"
    else
        relatar_falta "clawpack nao esta no PYTHONPATH (export PYTHONPATH=\$CLAW:\$PYTHONPATH)"
    fi
fi

echo
echo "Arvore do Clawpack"
if [ -n "${CLAW:-}" ] && [ -d "${CLAW}/classic/src/1d" ]; then
    relatar_ok "CLAW = $CLAW"
    solver="${CLAW}/riemann/src/rp1_telegraph.f90"
    if [ -f "$solver" ]; then
        relatar_ok "solucionador presente em riemann/src"
    else
        relatar_falta "solucionador ausente: copie solver-referencia/rp1_telegraph.f90 para $solver"
    fi
else
    relatar_falta "CLAW nao aponta para uma arvore do Clawpack (veja COMO-REPRODUZIR.md)"
fi

echo
echo "Arquivos deste repositorio"
for arquivo in Makefile setrun.py qinit.f90 setprob.f90 src1.f90 \
               solver-referencia/rp1_telegraph.f90 \
               arquivos-roteiro-simulacoes/executar_casos.py \
               arquivos-roteiro-simulacoes/autoconvergencia.py; do
    if [ -f "$arquivo" ]; then
        relatar_ok "$arquivo"
    else
        relatar_falta "$arquivo"
    fi
done

echo
if [ "$falhas" -eq 0 ]; then
    echo "Ambiente pronto: siga o guia COMO-REPRODUZIR.md."
else
    echo "$falhas item(ns) a resolver antes de executar as simulacoes."
fi

exit 0
