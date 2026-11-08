#!/usr/bin/env bash
# Caso 1: delega a configuracao isolada ao executor, sem editar setrun.py.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PYTHON=${CLAW_PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Erro: interpretador indisponivel: $PYTHON (configure CLAW_PYTHON)." >&2
    exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" -B "$SCRIPT_DIR/executar_caso1.py" "$@"
