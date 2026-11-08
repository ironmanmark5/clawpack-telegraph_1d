#!/usr/bin/env python3
"""Executa o Caso 1 sem editar setrun.py nem sobrescrever resultados existentes.

rodar.sh e a interface curta. Os arquivos .data sao gerados em uma pasta
temporaria; a saida recebe seu nome definitivo somente depois de validada.
Os parametros e o metodo numerico continuam definidos em setrun.py.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from convergencia_caso1 import ler_quadro, ler_tempo

ROOT = Path(__file__).resolve().parent


def locate_claw() -> Path:
    requested = os.environ.get('CLAW')
    candidates = [Path(requested).expanduser().resolve()] if requested else ROOT.parents
    for path in candidates:
        if ((path / 'classic/src/1d/claw1.f').is_file()
                and (path / 'clawutil/src/Makefile.common').is_file()):
            return path
    raise ValueError('Clawpack nao localizado. Defina CLAW para a raiz da instalacao completa.')


def configure(num_cells: int, claw: Path):
    # Carregamento pelo caminho evita confundir os dois arquivos setrun.py.
    sys.path.insert(0, str(claw))
    spec = importlib.util.spec_from_file_location('caso1_setrun', ROOT / 'setrun.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.setrun(num_cells=num_cells)


def validate(directory: Path, data) -> None:
    """Codigo de saida zero nao basta: o Classic tambem informa erros em fort.info."""
    n = data.num_cells[0]
    for k in range(data.num_output_times + 1):
        t = ler_tempo(directory, k)
        mx, lower, dx, *_ = ler_quadro(directory, k)
        expected_time = data.t0 + k * (data.tfinal - data.t0) / data.num_output_times
        if (mx != n or not math.isclose(t, expected_time, rel_tol=0., abs_tol=1e-10)
                or not math.isclose(lower, data.lower[0], rel_tol=0., abs_tol=1e-10)
                or not math.isclose(lower + mx*dx, data.upper[0], rel_tol=0., abs_tol=1e-8)):
            raise ValueError(f'Malha/tempo inesperado no quadro {k}.')
    statuses = re.findall(r'info\s*=\s*(-?\d+)', (directory / 'fort.info').read_text())
    if len(statuses) != data.num_output_times or any(int(s) != 0 for s in statuses):
        raise ValueError('fort.info indica falha ou execucao incompleta.')


def run(num_cells: int, destination: Path, *, plots: bool = True, dry_run: bool = False) -> Path:
    if type(num_cells) is not int or num_cells < 2:
        raise ValueError('o numero de celulas deve ser pelo menos 2')
    destination = destination.expanduser().resolve()
    output = destination / f'output_malha_{num_cells}'
    plotdir = destination / f'plots_malha_{num_cells}'
    for path in (output, plotdir) if plots else (output,):
        if path.exists() or path.is_symlink():
            raise ValueError(f'Destino ja existe e foi preservado: {path}. Use outro --destino.')
    claw = locate_claw()
    solver = claw / 'riemann/src/rp1_telegraph.f90'
    if not solver.is_file():
        raise ValueError(f'Solver ausente: {solver}. Consulte COMO-REPRODUZIR.md.')
    print(f'Caso 1: N={num_cells}; CLAW={claw}; saida={output}', flush=True)
    if dry_run:
        print('Planejamento apenas: nenhuma compilacao, simulacao ou escrita de dados.')
        return output

    env = dict(os.environ, CLAW=str(claw), PYTHONDONTWRITEBYTECODE='1')
    make_settings = [f'CLAW={claw}', f'CLAW_PYTHON={sys.executable}']
    subprocess.run(['make', '.exe', *make_settings], cwd=ROOT, env=env, check=True)
    rundata = configure(num_cells, claw)
    destination.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f'.caso1-N{num_cells}-', dir=destination))
    try:
        rundata.write(out_dir=str(work))
        with (work / 'execucao.log').open('w') as log:
            subprocess.run([str(ROOT / 'xclaw')], cwd=work, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        validate(work, rundata.clawdata)
        if output.exists() or output.is_symlink():
            raise ValueError(f'O destino foi criado durante a execucao: {output}')
        work.rename(output)
    except Exception:
        print(f'Execucao interrompida; dados de diagnostico preservados em {work}', file=sys.stderr)
        raise
    print(f'Simulacao validada: {output}', flush=True)
    if plots:
        # Sem ponto: a etapa de graficos nao deve disparar outra simulacao.
        if plotdir.exists() or plotdir.is_symlink():
            raise ValueError(f'Destino de graficos ja existe: {plotdir}; dados preservados em {output}')
        # Chamada direta ao VisClaw: preserva argumentos com espacos e nao
        # passa pela dependencia .output do alvo make .plots.
        subprocess.run([sys.executable, '-B',
                        str(claw / 'visclaw/src/python/visclaw/plotclaw.py'),
                        str(output), str(plotdir), str(ROOT / 'setplot.py')],
                       cwd=ROOT, env=env, check=True)
        print(f'Graficos: {plotdir}', flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('celulas', type=int, help='numero de celulas fisicas (pelo menos 2)')
    parser.add_argument('--destino', type=Path, default=ROOT,
                        help='pasta-base para output_malha_N e plots_malha_N')
    parser.add_argument('--sem-plots', action='store_true', help='nao chamar o VisClaw')
    parser.add_argument('--dry-run', action='store_true', help='validar caminhos sem executar ou gravar')
    args = parser.parse_args()
    try:
        run(args.celulas, args.destino, plots=not args.sem_plots, dry_run=args.dry_run)
    except (OSError, ValueError, IndexError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Erro: {exc}\n')


if __name__ == '__main__':
    main()
