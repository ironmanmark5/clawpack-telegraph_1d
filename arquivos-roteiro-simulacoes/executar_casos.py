#!/usr/bin/env python3
"""Executa e analisa os Casos 2–8 descritos na mensagem da orientadora.

O Caso 1 fica fora desta bateria. Cada conjunto (a,b,beta,x0) é executado
uma única vez e pode ser referenciado por vários casos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
CLAW = Path(os.environ.get('CLAW', ROOT.parents[3])).expanduser().resolve()
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
        # Configuração do roteiro e execução auxiliar para isolar o efeito de x0.
        6: [(0.5, -1, 25, 0.5), (1, -1, 200, 0.5)],
        7: [(1, -1, beta, 0) for beta in (25, 50, 100, 200)],
        8: [(a, b, 200, 0) for a in (0, 1, 2) for b in (-1, 0, 1)],
    }


def ensure_executable() -> Path:
    executable = ROOT / 'xclaw'
    # Flags e compilador nao sao dependencias temporais do make: recompilar
    # evita associar os fontes atuais a um binario antigo por engano.
    result = subprocess.run(['make', '-B', '.exe', f'CLAW={CLAW}'], cwd=ROOT, check=False)
    if result.returncode != 0 or not executable.is_file():
        raise RuntimeError('Falha na compilação do executável Classic Clawpack.')
    return executable


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_provenance(executable: Path) -> dict:
    """Identifica o binário e os fontes enumerados pelo Makefile efetivo."""
    dry = subprocess.check_output(
        ['make', '-n', '-B', '.exe', f'CLAW={CLAW}'], cwd=ROOT, text=True)
    commands = [shlex.split(line) for line in dry.splitlines() if '-o xclaw' in line]
    if len(commands) != 1:
        raise RuntimeError('Nao foi possivel identificar a compilacao unica do Makefile.')
    paths = [Path(p) if Path(p).is_absolute() else ROOT / p
             for p in commands[0] if Path(p).suffix.lower() in ('.f', '.f90')]
    paths.extend(ROOT / name for name in ('Makefile', 'setrun.py'))
    import clawpack
    from clawpack.clawutil import data as clawdata
    paths.extend((Path(clawpack.__file__), Path(clawdata.__file__)))
    hashes = {str(p.resolve()): digest(p) for p in paths}
    return {'source_sha256': hashes, 'executable_sha256': digest(executable),
            'build_command': commands[0]}


def output_checksums(directory: Path) -> dict:
    paths = [*directory.glob('fort.q[0-9]*'), *directory.glob('fort.t[0-9]*')]
    paths += [directory / name for name in
              ('claw.data', 'setprob.data', 'fort.info', 'amplitude.csv', 'perfis.csv')]
    return {p.name: digest(p) for p in sorted(paths)}


def numeric(value: str) -> float:
    return float(value.replace('D', 'E').replace('d', 'e'))


def read_input(path: Path) -> dict:
    return {name.split()[0]: value.split()
            for line in path.read_text().splitlines() if '=:' in line
            for value, name in [line.split('=:', 1)]}


def read_frame(directory: Path, number: int):
    qpath = directory / f'fort.q{number:04d}'
    tpath = directory / f'fort.t{number:04d}'
    if not qpath.is_file() or not tpath.is_file():
        raise RuntimeError(f'Frame {number} ausente em {directory}')
    lines = qpath.read_text().splitlines()
    mx = int(lines[2].split()[0])
    xlow = numeric(lines[3].split()[0])
    dx = numeric(lines[4].split()[0])
    th = tpath.read_text().splitlines()
    time = numeric(th[0].split()[0])
    if (mx < 1 or dx <= 0 or not all(map(math.isfinite, (xlow, dx, time)))
            or [int(th[i].split()[0]) for i in (1, 2, 3, 4)] != [3, 1, 0, 1]
            or th[6].split()[0] != 'ascii'):
        raise RuntimeError(f'Esperada uma malha Classic 1D ASCII valida em {directory}')
    rows = []
    for line in lines[6:]:
        if not line.strip():
            continue
        values = [numeric(value) for value in line.split()]
        if len(values) != 3 or not all(math.isfinite(value) for value in values):
            raise RuntimeError(f'Dado inválido em {qpath}')
        rows.append(values)
    if len(rows) != mx:
        raise RuntimeError(f'Esperadas {mx} células em {qpath}; lidas {len(rows)}')
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


def validate_output(directory: Path, params: tuple[float, float, float, float],
                    num_cells: int | None = None) -> dict:
    """Valida dados históricos sem exigir ou inventar proveniência ausente."""
    data = json.loads((directory / 'parametros.json').read_text())
    expected = dict(c=2., a=params[0], b=params[1], beta=params[2], x0=params[3],
                    domain=[-2., 2.], tfinal=.8, num_output_times=64,
                    order=2, limiter=['mc'] * 3, source_split=1,
                    boundary=['extrap'] * 2)
    if any(data.get(k) != v for k, v in expected.items()):
        raise ValueError(f'Manifesto divergente em {directory}')
    n = data['num_cells']
    if type(n) is not int or n < 2 or (num_cells is not None and n != num_cells):
        raise ValueError(f'Resolucao divergente em {directory}')
    physical = read_input(directory / 'setprob.data')
    if list(physical) != ['c', 'a', 'b', 'beta', 'x0']:
        raise ValueError(f'Ordem de leitura dos parametros divergente em {directory}')
    for key in ('c', 'a', 'b', 'beta', 'x0'):
        if numeric(physical[key][0]) != expected[key]:
            raise ValueError(f'Parametro fisico {key} divergente em {directory}')
    inputs = read_input(directory / 'claw.data')
    wanted = dict(num_dim=[1], num_cells=[n], lower=[-2.], upper=[2.],
                  num_eqn=[3], num_waves=[3], num_aux=[0], t0=[0],
                  output_style=[1], num_output_times=[64], tfinal=[.8],
                  output_format=[1], order=[2], limiter=[4]*3, source_split=[1],
                  num_ghost=[2], bc_lower=[1], bc_upper=[1], capa_index=[0],
                  cfl_desired=[.9], cfl_max=[1.], dt_initial=[.1], dt_max=[1e99])
    if any(list(map(numeric, inputs[key])) != value for key, value in wanted.items()):
        raise ValueError(f'Configuracao numerica divergente em {directory}')
    if any(inputs[key] != value for key, value in
           (('dt_variable', ['T']), ('output_t0', ['T']), ('use_fwaves', ['F']))):
        raise ValueError(f'Opcoes numericas divergentes em {directory}')
    amplitudes = read_amplitudes(directory)
    if len(amplitudes) != 65:
        raise ValueError(f'Esperadas 65 amplitudes em {directory}')
    for prefix in ('q', 't'):
        if len(list(directory.glob(f'fort.{prefix}[0-9][0-9][0-9][0-9]'))) != 65:
            raise ValueError(f'Esperados 65 arquivos fort.{prefix} em {directory}')
    for k in range(65):
        time, x, rows = read_frame(directory, k)
        if (len(rows) != n or not math.isclose(time, k*.8/64, rel_tol=0., abs_tol=1e-11)
                or any(not math.isclose(xi, -2+(i+.5)*4/n, rel_tol=0., abs_tol=1e-8)
                       for i, xi in enumerate(x))):
            raise ValueError(f'Malha/tempo divergente em {directory}, quadro {k}')
        t_csv, a_csv = amplitudes[k]
        if (not math.isclose(t_csv, time, rel_tol=0., abs_tol=1e-11)
                or not math.isclose(a_csv, max(abs(q[0]) for q in rows),
                                    rel_tol=1e-14, abs_tol=1e-14)):
            raise ValueError(f'Amplitude CSV divergente em {directory}, quadro {k}')
    statuses = re.findall(r'info\s*=\s*(-?\d+)', (directory / 'fort.info').read_text())
    if len(statuses) != 64 or any(int(s) != 0 for s in statuses):
        raise ValueError(f'fort.info indica execucao incompleta em {directory}')
    if 'output_sha256' in data and data['output_sha256'] != output_checksums(directory):
        raise ValueError(f'Checksums divergentes em {directory}')
    return data


def complete(directory: Path, params: tuple[float, float, float, float],
             num_cells: int | None = None) -> bool:
    try:
        validate_output(directory, params, num_cells)
    except (OSError, ValueError, KeyError, IndexError, TypeError, RuntimeError):
        return False
    return True


def simulate(executable: Path, output_root: Path,
             params: tuple[float, float, float, float], num_cells: int,
             provenance: dict | None = None) -> Path:
    provenance = provenance if provenance is not None else build_provenance(executable)
    directory = output_root / run_id(params)
    if directory.exists():
        try:
            data = validate_output(directory, params, num_cells)
        except (OSError, ValueError, KeyError, IndexError, TypeError, RuntimeError) as exc:
            raise RuntimeError(f'Saida incompleta ou divergente em {directory}: {exc}. '
                               'Dados preservados; use --saida com uma pasta nova.') from exc
        if data.get('provenance') == provenance and 'output_sha256' in data:
            print(f'Reutilizando {directory.name}', flush=True)
            return directory
        raise RuntimeError(f'Saida historica ou de outros fontes/binario: {directory}. '
                           'Os dados foram preservados; use --saida com uma pasta nova. '
                           'A analise dos dados historicos continua disponivel separadamente.')

    a, b, beta, x0 = params
    with tempfile.TemporaryDirectory(prefix=f'.{run_id(params)}-', dir=output_root) as scratch:
        work = Path(scratch)
        rundata = setrun(c=2.0, a=a, b=b, beta=beta, x0=x0, num_cells=num_cells)
        rundata.write(out_dir=str(work))
        manifest = {
            'id': run_id(params), 'c': 2.0, 'a': a, 'b': b,
            'beta': beta, 'x0': x0, 'num_cells': num_cells,
            'domain': [-2.0, 2.0], 'tfinal': 0.8,
            'num_output_times': 64, 'order': 2,
            'limiter': ['mc', 'mc', 'mc'], 'source_split': 1,
            'boundary': ['extrap', 'extrap'],
            'provenance': provenance,
            'note': 'Caso 6: pulso deslocado alcança a fronteira direita perto de t=0,75.'
                    if x0 == 0.5 else '',
        }
        (work / 'parametros.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'Executando {directory.name}', flush=True)
        with (work / 'execucao.log').open('w') as log:
            subprocess.run([str(executable)], cwd=work, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        export_csv(work, 64)
        validate_output(work, params, num_cells)
        manifest['output_sha256'] = output_checksums(work)
        (work / 'parametros.json').write_text(json.dumps(manifest, indent=2) + '\n')
        work.rename(directory)
    return directory


def read_amplitudes(directory: Path):
    with (directory / 'amplitude.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    values = [(numeric(row['t']), numeric(row['A_max_abs_u'])) for row in rows]
    if (any(int(row['frame']) != k for k, row in enumerate(rows))
            or any(not math.isfinite(t) or not math.isfinite(a) or a < 0 for t, a in values)):
        raise ValueError(f'CSV de amplitudes invalido em {directory}')
    return values


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
                output_root: Path, num_cells: int) -> None:
    rows = []
    for case, parameters in selected.items():
        for p in parameters:
            directory = output_root / run_id(p)
            amplitude = read_amplitudes(directory)
            rows.append([case, run_id(p), 2, *p, num_cells, 0.8,
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
    parser.add_argument('--celulas', type=int, default=400,
                        help='Número de células espaciais (padrão: 400).')
    args = parser.parse_args()
    if args.celulas < 2:
        parser.error('--celulas deve ser pelo menos 2.')
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
    provenance = build_provenance(executable)
    for p in unique:
        simulate(executable, output_root, p, args.celulas, provenance)
    available = {case: parameters for case, parameters in all_cases.items()
                 if all(complete(output_root / run_id(p), p, args.celulas)
                        for p in parameters)}
    write_index(available, output_root, args.celulas)
    os.environ.setdefault('MPLCONFIGDIR', str(output_root / '.mplconfig'))
    plot_results(selected, output_root)
    print(f'Resultados completos em {output_root}', flush=True)


if __name__ == '__main__':
    main()
