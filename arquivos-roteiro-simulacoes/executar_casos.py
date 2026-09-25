#!/usr/bin/env python3
"""Executa e analisa os Casos 2–8 descritos na mensagem da orientadora.

O Caso 1 fica fora desta bateria. Cada conjunto (a,b,beta,x0) é executado
uma única vez e pode ser referenciado por vários casos.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
CLAW = ROOT.parents[3]
sys.path.insert(0, str(CLAW))

from setrun import setrun


def label(value: float) -> str:
    return f"{value:g}".replace('-', 'm').replace('.', 'p')


def run_id(p: tuple[float, float, float, float]) -> str:
    a, b, beta, x0 = p
    return f"a{label(a)}_b{label(b)}_beta{label(beta)}_x0{label(x0)}"


def cases() -> dict[int, list[tuple[float, float, float, float]]]:
    return {
        2: [(a, 0, 200, 0) for a in (0, 0.5, 1, 2)],
        3: [(0, b, 200, 0) for b in (0, 0.5, 1)],
        4: [(1, 1, 200, 0)],
        5: [(1, -1, 200, 0)],
        6: [(0.5, -1, 25, 0.5)],
        7: [(1, -1, beta, 0) for beta in (25, 50, 100, 200)],
        8: [(a, b, 200, 0) for a in (0, 1, 2) for b in (-1, 0, 1)],
    }


def ensure_executable() -> Path:
    executable = ROOT / 'xclaw'
    result = subprocess.run(['make', '.exe'], cwd=ROOT, check=False)
    if result.returncode != 0 or not executable.is_file():
        raise RuntimeError('Falha na compilação do executável Classic Clawpack.')
    return executable


def read_frame(directory: Path, number: int):
    qpath = directory / f'fort.q{number:04d}'
    tpath = directory / f'fort.t{number:04d}'
    if not qpath.is_file() or not tpath.is_file():
        raise RuntimeError(f'Frame {number} ausente em {directory}')
    lines = qpath.read_text().splitlines()
    mx = int(lines[2].split()[0])
    xlow = float(lines[3].split()[0].replace('D', 'E'))
    dx = float(lines[4].split()[0].replace('D', 'E'))
    rows = []
    for line in lines[6:]:
        if not line.strip():
            continue
        values = [float(value.replace('D', 'E')) for value in line.split()]
        if len(values) != 3 or not all(math.isfinite(value) for value in values):
            raise RuntimeError(f'Dado inválido em {qpath}')
        rows.append(values)
    if len(rows) != mx:
        raise RuntimeError(f'Esperadas {mx} células em {qpath}; lidas {len(rows)}')
    time = float(tpath.read_text().split()[0].replace('D', 'E'))
    return time, [xlow + (i + 0.5) * dx for i in range(mx)], rows


def export_csv(directory: Path, n: int) -> None:
    with (directory / 'amplitude.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['frame', 't', 'A_max_abs_u'])
        for frame in range(n + 1):
            time, _, rows = read_frame(directory, frame)
            writer.writerow([frame, f'{time:.16g}', f'{max(abs(q[0]) for q in rows):.16g}'])

    with (directory / 'perfis.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['frame', 't', 'x', 'u', 'u_t', 'u_x'])
        for frame in (0, 16, 32, 48, 64):
            time, centers, rows = read_frame(directory, frame)
            for x, q in zip(centers, rows):
                writer.writerow([frame, f'{time:.16g}', f'{x:.16g}',
                                 *[f'{value:.16g}' for value in q]])


def complete(directory: Path, params: tuple[float, float, float, float]) -> bool:
    manifest = directory / 'parametros.json'
    if not manifest.is_file() or not (directory / 'amplitude.csv').is_file():
        return False
    data = json.loads(manifest.read_text())
    if [data[k] for k in ('a', 'b', 'beta', 'x0')] != list(params):
        return False
    return all((directory / f'fort.q{i:04d}').is_file() and
               (directory / f'fort.t{i:04d}').is_file() for i in range(65))


def simulate(executable: Path, output_root: Path,
             params: tuple[float, float, float, float]) -> Path:
    directory = output_root / run_id(params)
    if directory.exists():
        if complete(directory, params):
            print(f'Reutilizando {directory.name}', flush=True)
            return directory
        raise RuntimeError(f'Saída incompleta ou divergente: {directory}. '
                           'Examine-a antes de executar novamente.')

    a, b, beta, x0 = params
    with tempfile.TemporaryDirectory(prefix=f'.{run_id(params)}-', dir=output_root) as scratch:
        work = Path(scratch)
        rundata = setrun(c=2.0, a=a, b=b, beta=beta, x0=x0, num_cells=400)
        rundata.write(out_dir=str(work))
        manifest = {
            'id': run_id(params), 'c': 2.0, 'a': a, 'b': b,
            'beta': beta, 'x0': x0, 'num_cells': 400,
            'domain': [-2.0, 2.0], 'tfinal': 0.8,
            'num_output_times': 64, 'order': 2,
            'limiter': ['mc', 'mc', 'mc'], 'source_split': 1,
            'boundary': ['extrap', 'extrap'],
            'note': 'Caso 6: pulso deslocado alcança a fronteira direita perto de t=0,75.'
                    if x0 == 0.5 else '',
        }
        (work / 'parametros.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'Executando {directory.name}', flush=True)
        with (work / 'execucao.log').open('w') as log:
            subprocess.run([str(executable)], cwd=work, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        export_csv(work, 64)
        work.rename(directory)
    return directory


def read_amplitudes(directory: Path):
    with (directory / 'amplitude.csv').open(newline='') as stream:
        return [(float(row['t']), float(row['A_max_abs_u']))
                for row in csv.DictReader(stream)]


def plot_results(selected: dict[int, list[tuple[float, float, float, float]]],
                 output_root: Path) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plots = output_root / 'figuras'
    plots.mkdir(exist_ok=True)
    for number, parameters in selected.items():
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        for p in parameters:
            directory = output_root / run_id(p)
            a, b, beta, x0 = p
            legend = f'a={a:g}, b={b:g}, β={beta:g}, x₀={x0:g}'
            _, x, rows = read_frame(directory, 32)
            axes[0].plot(x, [q[0] for q in rows], label=legend)
            amplitude = read_amplitudes(directory)
            axes[1].plot([row[0] for row in amplitude],
                         [row[1] for row in amplitude], label=legend)
        axes[0].set(xlabel='x', ylabel='u(x, 0,4)', title=f'Caso {number}: perfis em t=0,4')
        axes[1].set(xlabel='t', ylabel='A(t) = max |u|', title='Amplitude máxima')
        for ax in axes:
            ax.grid(alpha=0.25)
            ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(plots / f'caso_{number}.png', dpi=160)
        plt.close(fig)

        for frame in (16, 32, 48, 64):
            fig, ax = plt.subplots(figsize=(8, 4.5))
            for p in parameters:
                a, b, beta, x0 = p
                time, x, rows = read_frame(output_root / run_id(p), frame)
                legend = f'a={a:g}, b={b:g}, β={beta:g}, x₀={x0:g}'
                ax.plot(x, [q[0] for q in rows], label=legend)
            ax.set(xlabel='x', ylabel='u(x,t)',
                   title=f'Caso {number}: perfis em t={time:.1f}')
            ax.grid(alpha=0.25)
            ax.legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(plots / f'caso_{number}_t{label(time)}.png', dpi=160)
            plt.close(fig)


def write_index(selected: dict[int, list[tuple[float, float, float, float]]],
                output_root: Path) -> None:
    rows = []
    for case, parameters in selected.items():
        for p in parameters:
            directory = output_root / run_id(p)
            amplitude = read_amplitudes(directory)
            rows.append([case, run_id(p), 2, *p, 400, 0.8,
                         f'{amplitude[32][1]:.16g}', f'{amplitude[64][1]:.16g}'])
    with (output_root / 'resumo.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['caso', 'id', 'c', 'a', 'b', 'beta', 'x0', 'N', 'tfinal',
                         'A_t0p4', 'A_t0p8'])
        writer.writerows(rows)
    (output_root / 'casos.json').write_text(json.dumps({
        str(case): [run_id(p) for p in parameters]
        for case, parameters in selected.items()}, indent=2) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--casos', nargs='+', type=int, default=list(range(2, 9)),
                        help='Selecione casos entre 2 e 8; padrão: todos.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar as configurações sem compilar ou executar.')
    parser.add_argument('--saida', type=Path, default=ROOT / 'resultados',
                        help='Diretório novo para os resultados.')
    args = parser.parse_args()
    all_cases = cases()
    invalid = set(args.casos) - set(all_cases)
    if invalid:
        parser.error(f'Casos inválidos: {sorted(invalid)}; use 2 a 8.')
    selected = {case: all_cases[case] for case in sorted(set(args.casos))}
    unique = list(dict.fromkeys(p for group in selected.values() for p in group))
    print(f'{len(selected)} casos, {len(unique)} configurações únicas:', flush=True)
    for p in unique:
        print(f'  {run_id(p)}', flush=True)
    if args.dry_run:
        return

    output_root = args.saida.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    executable = ensure_executable()
    for p in unique:
        simulate(executable, output_root, p)
    available = {case: parameters for case, parameters in all_cases.items()
                 if all(complete(output_root / run_id(p), p) for p in parameters)}
    write_index(available, output_root)
    os.environ.setdefault('MPLCONFIGDIR', str(output_root / '.mplconfig'))
    plot_results(selected, output_root)
    print(f'Resultados completos em {output_root}', flush=True)


if __name__ == '__main__':
    main()
