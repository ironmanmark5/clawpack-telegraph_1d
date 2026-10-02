#!/usr/bin/env python3
"""Autoconvergência do experimento combinado, sem modificar os Casos 2–8."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time

from executar_casos import read_frame
from setrun import setrun

ROOT = Path(__file__).resolve().parent
MESHES = (32, 64, 128, 256, 512, 1024, 2048)
PHYSICS = dict(c=2.0, a=1.0, b=1.0, beta=200.0, x0=0.0)
DOMAIN = (-2.0, 2.0)
FINAL_TIME = 0.8
LOCAL_FORTRAN = ('qinit.f90', 'setprob.f90', 'src1.f90', 'rp1_telegraph.f90')
NUMERICS = dict(domain=list(DOMAIN), tfinal=FINAL_TIME, cfl_desired=0.9,
                cfl_max=1.0, dt_variable=True, dt_initial=0.1, dt_max=1e99,
                order=2, limiter=['mc'] * 3, source_split=1,
                boundary=['extrap', 'extrap'], num_output_times=64,
                output_t0=True, num_ghost=2, num_eqn=3, num_waves=3)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                   allow_nan=False) + '\n')


def command(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def optional_command(args):
    try:
        return command(args)
    except (OSError, subprocess.CalledProcessError):
        return None


def restrict(values):
    """Restrição conservativa de duas médias finas para uma média grossa."""
    if not values or len(values) % 2:
        raise ValueError('A restrição requer uma quantidade par de células.')
    if not all(math.isfinite(x) for x in values):
        raise ValueError('Valores não finitos na restrição.')
    return [(values[i] + values[i + 1]) / 2 for i in range(0, len(values), 2)]


def normalized_l2(coarse, restricted):
    if not coarse or len(coarse) != len(restricted):
        raise ValueError('Contagens incompatíveis no erro normalizado.')
    delta = [b - a for a, b in zip(coarse, restricted)]
    if not all(math.isfinite(x) for x in delta):
        raise ValueError('Diferença não finita.')
    return math.sqrt(math.fsum(x * x for x in delta) / len(delta))


def observed_order(error, next_error, floor=100 * sys.float_info.epsilon):
    if not all(math.isfinite(x) for x in (error, next_error)):
        return math.nan, 'erro não finito'
    if error <= 0 or next_error <= 0:
        return math.nan, 'erro nulo ou negativo'
    if min(error, next_error) <= floor:
        return math.nan, f'erro próximo da precisão numérica (limiar {floor:.6e})'
    return (math.log(error) - math.log(next_error)) / math.log(2), ''


def synthetic_checks():
    checks = [
        ('diferença constante unitária', normalized_l2([0.] * 8, [1.] * 8), 1.),
        ('restrição preserva constante', max(abs(x - 7.) for x in restrict([7.] * 8)), 0.),
        ('redução por fator quatro', observed_order(0.016, 0.004)[0], 2.),
    ]
    records = []
    for name, actual, expected in checks:
        if not math.isclose(actual, expected, rel_tol=1e-14, abs_tol=1e-14):
            raise RuntimeError(f'Teste sintético falhou: {name}')
        records.append(dict(teste=name, obtido=actual, esperado=expected, status='passou'))
    return records


def locate_claw(explicit=None):
    def valid(path):
        return ((path / 'classic/src/1d/claw1.f').is_file()
                and (path / 'clawutil/src/python/clawutil/data.py').is_file())
    requested = explicit or os.environ.get('CLAW')
    if requested:
        path = Path(requested).expanduser().resolve()
        if not valid(path):
            raise RuntimeError(f'Instalação Clawpack inválida: {path}')
        return path, '--claw' if explicit else 'variável CLAW'
    candidates = []
    spec = importlib.util.find_spec('clawpack')
    if spec and spec.origin:
        candidates.append(Path(spec.origin).resolve().parent.parent)
    candidates.extend(ROOT.parents)
    for path in candidates:
        if valid(path):
            return path, 'pacote Python instalado' if path in candidates[:1] and spec else 'busca de instalação nos diretórios ancestrais'
    raise RuntimeError('Clawpack não localizado. Informe --claw ou a variável CLAW; nenhuma dependência será instalada.')


def build(output, claw, discovery, compiler, flags):
    """Usa o Makefile original, com snapshots de TODOS os fontes e build isolado."""
    fc = shutil.which(compiler)
    if not fc or not shutil.which('make'):
        raise RuntimeError('Compilador Fortran ou make indisponível.')
    sys.path.insert(0, str(claw))
    import clawpack
    from clawpack.clawutil import data as clawdata
    if not Path(clawdata.__file__).resolve().is_relative_to(claw):
        raise RuntimeError('O módulo Python clawutil não pertence à instalação Clawpack selecionada.')
    dry_args = ['make', '-n', '-B', '.exe', f'CLAW={claw}', f'FC={fc}', f'FFLAGS={flags}']
    dry = command(dry_args)
    lines = [shlex.split(line) for line in dry.splitlines() if '-o xclaw' in line]
    if len(lines) != 1:
        raise RuntimeError('Não foi possível identificar uma única compilação xclaw no Makefile.')
    sources = [Path(p) if Path(p).is_absolute() else ROOT / p
               for p in lines[0] if Path(p).suffix.lower() in ('.f', '.f90')]
    local = [p.resolve() for p in sources if p.resolve().parent == ROOT]
    if set(local) != {ROOT / name for name in LOCAL_FORTRAN}:
        raise RuntimeError('Os fontes locais do Makefile divergem das quatro rotinas autorizadas.')
    core = [p.resolve() for p in sources if p.resolve() not in local]
    if not core or any(p.parent != claw / 'classic/src/1d' for p in core):
        raise RuntimeError('O Makefile usa fontes fora da aplicação ou de Classic 1D.')
    tracked = {f'local/{p.name}': p for p in local}
    tracked.update({f'classic/{p.name}': p for p in core})
    tracked.update({f'local/{name}': ROOT / name for name in
                    ('Makefile', 'setrun.py', 'executar_casos.py', 'autoconvergencia.py')})
    tracked['python/clawutil_data.py'] = Path(clawdata.__file__)
    tracked['python/clawpack_init.py'] = Path(clawpack.__file__)
    hashes = {key: digest(path) for key, path in sorted(tracked.items())}
    version = optional_command([fc, '--version']) or 'versão não identificada'
    provenance = dict(project_commit=command(['git', 'rev-parse', 'HEAD']),
                      project_branch=command(['git', 'branch', '--show-current']),
                      working_tree_status=command(['git', 'status', '--porcelain']),
                      clawpack_version=getattr(clawpack, '__version__', 'não identificada'),
                      clawpack_installation=str(claw), clawpack_discovery=discovery,
                      classic_commit=optional_command(['git', '-C', str(claw / 'classic'), 'rev-parse', 'HEAD']),
                      compiler=fc, compiler_version=version, flags=flags,
                      source_sha256=hashes, python_version=sys.version)
    # Mudanças somente no relatório/leitor não invalidam uma solução do mesmo esquema.
    # Todas são arquivadas; a compatibilidade numérica depende dos fontes do solver,
    # Makefile, setrun, serialização Clawpack, compilador e configuração verificada.
    numerical_hashes = {key: value for key, value in hashes.items()
                        if key not in ('local/autoconvergencia.py', 'local/executar_casos.py')}
    signature = hashlib.sha256(json.dumps(dict(hashes=numerical_hashes, compiler=version, flags=flags,
                                               physics=PHYSICS, numerics=NUMERICS),
                                         sort_keys=True).encode()).hexdigest()
    build_dir = output / 'build' / (signature[:16] + '_' + hashes['local/autoconvergencia.py'][:8])
    build_dir.mkdir(parents=True, exist_ok=True)
    for key, path in tracked.items():
        target = build_dir / key
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    # O Makefile é executado na pasta local do snapshot, preservando o xclaw original.
    args = ['make', '-B', '.exe', f'CLAW={claw}', f'FC={fc}', f'FFLAGS={flags}',
            'CLASSIC=' + ' '.join('../classic/' + p.name for p in core)]
    with (build_dir / 'compilacao.log').open('w') as log:
        log.write(shlex.join(args) + '\n')
        log.flush()
        result = subprocess.run(args, cwd=build_dir / 'local', stdout=log,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        raise RuntimeError(f'Compilação falhou (código {result.returncode}); veja {build_dir / "compilacao.log"}')
    if any(digest(path) != hashes[key] for key, path in tracked.items()):
        raise RuntimeError('Um fonte foi alterado durante a compilação; execução interrompida.')
    executable = build_dir / 'local/xclaw'
    provenance.update(signature=signature, executable_sha256=digest(executable),
                      build_directory=str(build_dir.relative_to(output)), build_command=args,
                      make_dry_run=dry)
    (build_dir / 'alteracoes_locais.patch').write_text(command(['git', 'diff', '--', str(ROOT)]))
    return executable, provenance


def numeric(text):
    return float(text.replace('D', 'E').replace('d', 'e'))


def read_data(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        if '=:' in line:
            value, name = line.split('=:', 1)
            result[name.split()[0]] = value.split()
    return result


def check_input(directory, n):
    data = read_data(directory / 'claw.data')
    expected = dict(num_cells=[n], lower=[-2], upper=[2], num_eqn=[3], num_waves=[3],
                    num_aux=[0], tfinal=[.8], num_output_times=[64], cfl_desired=[.9],
                    cfl_max=[1], dt_initial=[.1], dt_max=[1e99], order=[2],
                    source_split=[1], limiter=[4, 4, 4], bc_lower=[1], bc_upper=[1],
                    num_ghost=[2], verbosity=[1])
    for key, values in expected.items():
        actual = list(map(numeric, data[key]))
        if len(actual) != len(values) or any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                                             for a, b in zip(actual, values)):
            raise RuntimeError(f'Parâmetro divergente em {directory.name}: {key}={actual}')
    for key in ('dt_variable', 'output_t0'):
        if data[key] != ['T']:
            raise RuntimeError(f'{key} não está ativo.')
    prob = read_data(directory / 'setprob.data')
    if list(prob) != list(PHYSICS) or any(numeric(prob[k][0]) != v for k, v in PHYSICS.items()):
        raise RuntimeError('Parâmetros físicos ou sua ordem de leitura divergem.')
    return data


def frame(directory, number):
    t, x, q = read_frame(directory, number)
    header = (directory / f'fort.q{number:04d}').read_text().splitlines()
    th = (directory / f'fort.t{number:04d}').read_text().splitlines()
    if [int(th[i].split()[0]) for i in (1, 2, 3, 4, 5)] != [3, 1, 0, 1, 2]:
        raise RuntimeError('Saída não corresponde a uma malha Classic 1D com três componentes.')
    if th[6].split()[0] != 'ascii':
        raise RuntimeError('Formato de saída diferente de ASCII.')
    lower, dx = numeric(header[3].split()[0]), numeric(header[4].split()[0])
    return dict(n=len(q), time=t, lower=lower, dx=dx, upper=lower + len(q) * dx,
                x=x, u=[row[0] for row in q], ut=[row[1] for row in q], q=q,
                frame=number)


def check_grid_pair(coarse, fine):
    if fine['n'] != 2 * coarse['n']:
        raise ValueError('Refinamento diferente de dois.')
    for key in ('lower', 'upper', 'time'):
        if not math.isclose(coarse[key], fine[key], rel_tol=0., abs_tol=1e-11):
            raise ValueError(f'Malhas não alinhadas: {key}')
    if not math.isclose(coarse['dx'], 2 * fine['dx'], rel_tol=0., abs_tol=1e-12):
        raise ValueError('Espaçamentos incompatíveis.')
    for i in range(coarse['n'] + 1):
        if abs(coarse['lower'] + i * coarse['dx'] - (fine['lower'] + 2*i*fine['dx'])) > 1e-11:
            raise ValueError('Fronteiras das células não coincidem.')


def parse_steps(text):
    pattern = re.compile(r'CLAW1\.\.\. Step\s*(\d+)\s+Courant number =\s*([\d.EeDd+-]+)'
                         r'\s+dt =\s*([\d.EeDd+-]+)\s+t =\s*([\d.EeDd+-]+)')
    records, interval = [], 1
    for line in text.splitlines():
        match = pattern.search(line)
        if match:
            step, cfl, dt, t = match.groups()
            records.append(dict(intervalo_saida=interval, passo_no_intervalo=int(step),
                                dt_log=numeric(dt), cfl_log=numeric(cfl),
                                tempo_final_log=numeric(t), aceito=True))
        elif 'CLAW1 rejecting step' in line:
            if not records:
                raise ValueError('Rejeição sem registro do passo.')
            records[-1]['aceito'] = False
        elif 'CLAW1EZ: Frame' in line:
            interval = int(re.search(r'Frame\s*(\d+)', line).group(1)) + 1
    return records


def validate_run(directory, n):
    input_data = check_input(directory, n)
    if len(list(directory.glob('fort.q[0-9][0-9][0-9][0-9]'))) != 65:
        raise RuntimeError(f'Número de frames incorreto em N={n}.')
    if len(list(directory.glob('fort.t[0-9][0-9][0-9][0-9]'))) != 65:
        raise RuntimeError(f'Número de arquivos de tempo incorreto em N={n}.')
    final = None
    for k in range(65):
        f = frame(directory, k)
        if f['n'] != n or not math.isclose(f['time'], k * FINAL_TIME / 64, abs_tol=1e-11):
            raise RuntimeError(f'Células/tempo divergentes em N={n}, frame {k}.')
        if any(abs(f[key] - value) > 1e-11 for key, value in
               [('lower', -2.), ('upper', 2.), ('dx', 4/n)]):
            raise RuntimeError(f'Domínio/espaçamento divergente em N={n}.')
        if k == 0:
            for x, row in zip(f['x'], f['q']):
                u = math.exp(-200 * x*x)
                expected = (u, 0., -400*x*u)
                if any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(row, expected)):
                    raise RuntimeError(f'Inicialização divergente em N={n}.')
        if math.isclose(f['time'], FINAL_TIME, rel_tol=0., abs_tol=1e-11):
            if final is not None:
                raise RuntimeError('Mais de um frame no tempo de comparação.')
            final = f
    if final is None:
        raise RuntimeError(f'Tempo final não alcançado em N={n}.')
    info = (directory / 'fort.info').read_text()
    status = re.findall(r'info\s*=\s*(\d+)', info)
    if len(status) != 64 or any(int(s) != 0 for s in status):
        raise RuntimeError(f'fort.info sinalizou falha em N={n}.')
    return final, input_data


def output_hashes(directory):
    paths = [*directory.glob('fort.q[0-9]*'), *directory.glob('fort.t[0-9]*')]
    paths += [directory / name for name in ('claw.data', 'setprob.data', 'fort.info', 'execucao.log')]
    return {p.name: digest(p) for p in sorted(paths)}


def run_mesh(output, n, executable, provenance):
    directory = output / 'simulacoes' / f'N{n:04d}_a1_b1_beta200_x0'
    spec = dict(N=n, dx=4/n, physics=PHYSICS, numerics=NUMERICS,
                source_signature=provenance['signature'],
                executable_sha256=provenance['executable_sha256'])
    if directory.exists():
        old = json.loads((directory / 'execucao.json').read_text())
        if old.get('status') != 'concluida' or old.get('spec') != spec:
            raise RuntimeError(f'Execução existente incompatível/incompleta: {directory}; use outra --saida.')
        if old['output_sha256'] != output_hashes(directory):
            raise RuntimeError(f'Checksums divergentes em {directory}.')
        validate_run(directory, n)
        print(f'Reutilizando saída verificada: N={n}', flush=True)
        return old
    directory.mkdir(parents=True)
    meta = dict(spec=spec, provenance=provenance, status='iniciada',
                started_utc=datetime.now(timezone.utc).isoformat())
    write_json(directory / 'execucao.json', meta)
    start = time.perf_counter()
    try:
        rundata = setrun(**PHYSICS, num_cells=n)
        # Apenas instrumentação de stdout; nenhum parâmetro do esquema é alterado.
        rundata.clawdata.verbosity = 1
        rundata.write(out_dir=str(directory))
        check_input(directory, n)
        print(f'Executando N={n}, dx={4/n:g}', flush=True)
        with (directory / 'execucao.log').open('w') as log:
            result = subprocess.run([str(executable)], cwd=directory, stdout=log,
                                    stderr=subprocess.STDOUT, check=False)
        meta['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'Solver terminou com código {result.returncode} em N={n}.')
        final, effective = validate_run(directory, n)
        steps = parse_steps((directory / 'execucao.log').read_text())
        accepted = [s for s in steps if s['aceito']]
        count = sum(map(int, re.findall(r'steps taken\s*=\s*(\d+)', (directory / 'fort.info').read_text())))
        if not accepted or len(accepted) != count:
            raise RuntimeError('Diagnóstico de passos não coincide com fort.info.')
        for s in steps:
            s['cfl_de_dt_log'] = 2*s['dt_log']/(4/n)
        with (directory / 'passos.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(steps[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(steps)
        meta.update(status='concluida', reached_time=final['time'], final_frame=final['frame'],
                    effective_input=effective, accepted_steps=len(accepted),
                    rejected_attempts=len(steps)-len(accepted),
                    dt_accepted_min=min(s['dt_log'] for s in accepted),
                    dt_accepted_max=max(s['dt_log'] for s in accepted),
                    cfl_accepted_min=min(s['cfl_log'] for s in accepted),
                    cfl_accepted_max=max(s['cfl_log'] for s in accepted),
                    diagnostic_precision='dt e t: 5 algarismos significativos; CFL: 3 casas decimais no stdout',
                    output_sha256=output_hashes(directory))
    except Exception as exc:
        meta.update(status='falhou', reason=str(exc))
        times = [numeric(p.read_text().split()[0]) for p in directory.glob('fort.t[0-9]*')]
        meta['reached_time'] = max(times) if times else None
        raise
    finally:
        meta['wall_seconds'] = time.perf_counter()-start
        write_json(directory / 'execucao.json', meta)
    return meta


def analyse(output):
    frames, runs = {}, {}
    for n in MESHES:
        d = output / 'simulacoes' / f'N{n:04d}_a1_b1_beta200_x0'
        meta = json.loads((d / 'execucao.json').read_text())
        if meta['status'] != 'concluida' or meta['output_sha256'] != output_hashes(d):
            raise RuntimeError(f'Execução N={n} inválida ou modificada.')
        frames[n], _ = validate_run(d, n)
        runs[n] = meta
    if len({runs[n]['spec']['source_signature'] for n in MESHES}) != 1:
        raise RuntimeError('Malhas usam fontes/configurações de builds diferentes.')
    rows, reasons = [], {}
    for i, n in enumerate(MESHES):
        row = dict(N=n, dx=frames[n]['dx'], tempo=frames[n]['time'],
                   E_u=math.nan, p_u=math.nan, E_ut=math.nan, p_ut=math.nan)
        reasons[n] = {}
        if i+1 < len(MESHES):
            fine = frames[MESHES[i+1]]
            check_grid_pair(frames[n], fine)
            for variable in ('u', 'ut'):
                try:
                    error = normalized_l2(frames[n][variable], restrict(fine[variable]))
                    if not math.isfinite(error):
                        raise ValueError('erro de refinamento não finito')
                    row['E_'+variable] = error
                except (ValueError, OverflowError) as exc:
                    reasons[n]['E_'+variable] = str(exc)
        else:
            reasons[n]['E'] = 'malha 2N não disponível (4096 não executada)'
        rows.append(row)
    for i, row in enumerate(rows):
        for variable in ('u', 'ut'):
            if i+2 >= len(rows):
                reasons[row['N']]['p_'+variable] = 'trinca N, 2N, 4N não disponível'
                continue
            scale = max(1., *(abs(x) for n in MESHES[i:i+3] for x in frames[n][variable]))
            floor = 100*sys.float_info.epsilon*scale
            p, reason = observed_order(row['E_'+variable], rows[i+1]['E_'+variable], floor)
            row['p_'+variable] = p
            if reason:
                reasons[row['N']]['p_'+variable] = reason
    write_json(output / 'ordens_diagnostico.json', reasons)
    with (output / 'autoconvergencia.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: 'NaN' if isinstance(v, float) and math.isnan(v) else v
                          for k, v in row.items()} for row in rows)
    table_latex(output, rows)
    plots(output, rows, frames)
    report(output, rows, runs, frames)
    return rows


def sci(value):
    if not math.isfinite(value):
        return '--'
    coefficient, exponent = f'{value:.6e}'.split('e')
    return rf'${coefficient}\times 10^{{{int(exponent)}}}$'


def table_latex(output, rows):
    lines = [r'\begin{table}[htbp]', r'\centering', r'\small',
             r'\caption{Autoconvergência em $t=0{,}8$: erro $L^2$ discreto normalizado entre malhas.}',
             r'\label{tab:autoconvergencia_combinado}',
             r'\setlength{\tabcolsep}{3pt}', r'\begin{tabular}{rrrrrrr}', r'\hline',
             r'$N$ & $\Delta x$ & $t$ & $E_u(N)$ & $p_u(N)$ & $E_{u_t}(N)$ & $p_{u_t}(N)$ \\', r'\hline']
    for r in rows:
        p = lambda k: '--' if math.isnan(r[k]) else f'{r[k]:.4f}'
        lines.append(f"{r['N']} & {r['dx']:.7g} & {r['tempo']:.1f} & {sci(r['E_u'])} & {p('p_u')} & {sci(r['E_ut'])} & {p('p_ut')} " + r'\\')
    lines += [r'\hline', r'\end{tabular}', r'\par\smallskip',
              r'\parbox{0.98\linewidth}{\footnotesize Na linha $N$, $E(N)$ compara $N$ e $2N$,',
              r'e $p(N)$ usa a trinca $N,2N,4N$. A restrição usa a média de duas células finas.',
              r'Os valores indisponíveis são indicados por --.}', r'\end{table}']
    (output / 'tabela_autoconvergencia.tex').write_text('\n'.join(lines)+'\n')


def plots(output, rows, frames):
    os.environ.setdefault('MPLCONFIGDIR', str(output / '.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def save(fig, name):
        fig.savefig(output / f'{name}.png', dpi=220)
        fig.savefig(output / f'{name}.pdf', metadata={'CreationDate': None, 'ModDate': None})
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout='constrained')
    for ax, variable, title in zip(axes, ('u', 'ut'), ('$u$', '$u_t$')):
        available = [r for r in rows[:-1] if math.isfinite(r['E_'+variable]) and r['E_'+variable] > 0]
        ax.loglog([r['dx'] for r in available], [r['E_'+variable] for r in available], 'o-', lw=1.5)
        if len(available) != len(rows)-1:
            ax.text(.02, .04, 'Erros nulos/indisponíveis omitidos do log-log', transform=ax.transAxes, fontsize=8)
        ax.set(xlabel=r'$\Delta x$', ylabel='Erro de refinamento normalizado', title=title+r' em $t=0{,}8$')
        ax.grid(which='both', alpha=.25)
    fig.suptitle('Autoconvergência do esquema completo: c=2, a=1, b=1, beta=200')
    save(fig, 'erros_loglog')
    for variable, label in [('u', '$u$'), ('ut', '$u_t$')]:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
        for i, n in enumerate(MESHES):
            for ax in axes:
                ax.plot(frames[n]['x'], frames[n][variable], label=f'N={n}',
                        color=plt.cm.viridis(i/6), lw=1.4)
        axes[0].set(xlim=DOMAIN, title='Domínio físico completo')
        axes[1].set(xlim=(1.25, 1.95), title='Detalhe do pulso direito')
        for ax in axes:
            ax.set(xlabel='$x$', ylabel=label)
            ax.grid(alpha=.25)
        axes[0].legend(fontsize=8, ncols=2)
        fig.suptitle(f'{label}: médias celulares em t=0,8, c=2, a=1, b=1, beta=200')
        save(fig, 'perfis_'+variable)


def report(output, rows, runs, frames):
    text = [
        '# Autoconvergência — experimento combinado\n',
        '## Metodologia\n',
        'Foram executadas somente as sete malhas N=32,64,128,256,512,1024,2048. '
        'N conta células físicas. Parâmetros: c=2, a=1, b=1, beta=200, x0=0; domínio [-2,2], '
        'dx=4/N, tempo final 0,8 e 64 intervalos de saída mais o estado inicial. '
        'A equação é u_tt+a*u_t=c²*u_xx+b*u, com sinal positivo de b. '
        'q=(u,u_t,u_x); u_t é lido da segunda componente, sem diferenças temporais entre snapshots.\n',
        'As saídas ASCII contêm exatamente N linhas físicas (out1.f escreve i=1,...,mx), '
        'sem células fantasma. Foram conferidos todos os tempos registrados, a geometria, '
        'parâmetros efetivos, finitude e condição inicial. A interpretação é de médias celulares. '
        'A inicialização por valores no centro foi preservada, inclusive nas malhas grossas.\n',
        'Antes de comparar, R(q_2N)[i]=(q_2N[2i]+q_2N[2i+1])/2. '
        'As fronteiras coincidem, o refinamento é dois e o domínio físico é o mesmo. '
        'E(N)=sqrt(mean((R(q_2N)-q_N)²)) é o erro L2 discreto normalizado entre malhas; '
        'não é desvio padrão nem erro em relação à solução exata. '
        'p(N)=log(E(N)/E(2N))/log(2) usa três soluções.\n',
        'A referência da orientadora discute pontos/interpolação e mostra E(N) na linha 2N. '
        'Aqui a adaptação para volumes finitos usa restrição conservativa e a própria linha N '
        'contém E(N) e p(N), conforme o escopo autorizado. Existem seis erros e cinco ordens '
        'por componente; E(2048), p(1024) e p(2048) são indisponíveis. '
        'CSV usa NaN e LaTeX usa --. Razões e limiares estão em ordens_diagnostico.json.\n',
        '## Resultados efetivamente calculados\n',
        '| N | dx | E_u(N) | p_u(N) | E_ut(N) | p_ut(N) |',
        '|---:|---:|---:|---:|---:|---:|',
    ]
    for r in rows:
        value = lambda k: '--' if math.isnan(r[k]) else (f'{r[k]:.6e}' if k.startswith('E') else f'{r[k]:.4f}')
        text.append(f"| {r['N']} | {r['dx']:.7g} | {value('E_u')} | {value('p_u')} | {value('E_ut')} | {value('p_ut')} |")
    last = rows[-3]
    text += ['', f"A última trinca disponível é 512→1024→2048: p_u={last['p_u']:.4f} e p_ut={last['p_ut']:.4f}. "
             'São ordens locais observadas entre soluções numéricas, sem imposição de ordem dois.',
             f"E_ut(32)={rows[0]['E_ut']:.6e} é menor que E_ut(64)={rows[1]['E_ut']:.6e}; "
             'a primeira ordem de u_t é negativa. Isso registra a ausência de redução monotônica '
             'das diferenças nesse intervalo grosseiro, não uma taxa assintótica. O perfil de u '
             'em N=32 também apresenta uma região central negativa e pulsos deformados; esses '
             'artefatos foram mantidos e podem ser vistos na figura. A resolução inicial insuficiente '
             'é relevante para interpretar esse comportamento; sua causa não foi isolada por '
             'experimentos adicionais.',
             'Nas duas últimas trincas, u_t apresenta ordens próximas de dois, enquanto u tem '
             'ordens diferentes e variáveis. Esses dados não autorizam atribuir segunda ordem '
             'ao esquema completo nem afirmar que todos os componentes chegaram ao regime '
             'assintótico. O efeito de cada etapa não é isolado por este estudo.',
             '\n## Passos temporais e verificação de execução\n',
             '| N | passos aceitos | tentativas rejeitadas | dt mínimo aceito (log) | dt máximo aceito (log) | CFL mínimo | CFL máximo | max u inicial |',
             '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n in MESHES:
        m = runs[n]
        initial = frame(output / 'simulacoes' / f'N{n:04d}_a1_b1_beta200_x0', 0)
        text.append(f"| {n} | {m['accepted_steps']} | {m['rejected_attempts']} | {m['dt_accepted_min']:.6e} | {m['dt_accepted_max']:.6e} | {m['cfl_accepted_min']:.3f} | {m['cfl_accepted_max']:.3f} | {max(initial['u']):.6f} |")
    text += ['', 'CFL desejado=0,9; CFL máximo permitido=1. O tempo é variável. '
             'O intervalo entre saídas (0,0125) limita o passo nas malhas grossas. '
             'O log distingue tentativas rejeitadas de passos aceitos. dt e t do stdout têm '
             'cinco algarismos significativos e CFL tem três casas decimais: os diagnósticos '
             'efetivos aqui são arredondados, não valores internos de precisão plena. '
             'fort.info foi preservado; seus campos dt incluem candidatos ao passo seguinte '
             'e a inicialização dt=0,1, e não devem ser confundidos com os dt efetivamente usados.\n',
             'A única mudança de configuração é verbosity=1 para registrar passos; isso não altera '
             'o algoritmo. Fonte, solver, limitadores e inicialização permanecem iguais. '
             'Cada execução registra status, tempo atingido, parâmetros, checksum das saídas, '
             'tempo de parede e diagnósticos em execucao.json e passos.csv. '
             'As sete saídas alcançaram t=0,8 (tolerância 1e-11), com info=0 e código de saída zero.\n',
             '## Interpretação e limitações\n',
             'A correção hiperbólica é de segunda ordem com MC; o splitting de Godunov é de '
             'primeira ordem e a fonte usa Euler explícito simultâneo, a partir de q1 e q2 antigos. '
             'Assim, este estudo mede o esquema completo com refinamento espacial e temporal '
             'acoplados pela CFL e pelas saídas. Não isola exclusivamente o erro espacial. '
             'Nenhuma alteração foi feita para obter uma ordem desejada.\n',
             f'A largura à meia altura da gaussiana é {2*math.sqrt(math.log(2)/200):.6f}. '
             'Em N=32, dx=0,125 é maior que essa largura; a gaussiana estreita é mal resolvida '
             'e seu pico contínuo em x=0 fica entre centros de células. Os máximos iniciais '
             'na tabela evidenciam esse efeito. Ordens nas malhas grossas podem ser pré-assintóticas. '
             'As diferenças de inicialização e os limitadores também fazem parte do experimento.\n',
             'O domínio e os contornos por extrapolação foram preservados. O estudo não demonstra '
             'independência do contorno nem mede erro contra uma solução analítica. '
             'Não foram executados N=4096, outros parâmetros físicos ou uma nova bateria de casos.\n',
             '## Testes sintéticos e proveniência\n',
             'Os três testes sintéticos exigidos passaram e estão separados em testes_sinteticos.json: '
             'diferença unitária→erro 1; restrição constante→mesma constante; redução por quatro→ordem 2. '
             'Esses valores não são resultados do solver.\n',
             'experimento.json registra commit/branch, estado sujo, versão do Clawpack, compilador, '
             'flags, lista dos fontes realmente compilados, hashes e comando de build. '
             'O executável foi recompilado à força a partir de snapshots dos fontes atuais do '
             'Makefile desta aplicação, em build/, sem usar os fontes antigos da raiz. '
             'A árvore de trabalho já tinha alterações não commitadas; hashes e snapshots identificam '
             'o código efetivo, além do commit. Arquivos antigos dos Casos 2–8 foram preservados.\n',
             '## Reprodução\n',
             'A partir de arquivos-roteiro-simulacoes/:\n',
             '```bash\npython3 -m unittest -v test_autoconvergencia.py\n'
             'python3 autoconvergencia.py\n'
             'python3 autoconvergencia.py --somente-analisar\n```\n',
             'Use --claw /caminho/para/clawpack ou CLAW quando necessário. '
             'A descoberta consulta essa configuração, o pacote instalado e instalações nos diretórios '
             'ancestrais. --saida é relativo a esta pasta; use outra pasta para um build/configuração '
             'incompatível com execuções existentes. Não é preciso instalar dependências ou criar ambiente virtual.\n',
             'Pendências: não há bloqueio de execução. Os materiais não foram incorporados à monografia '
             'e não houve publicação, commit, push ou PR.']
    (output / 'RELATORIO.md').write_text('\n'.join(text)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claw', type=Path)
    parser.add_argument('--fc', default=os.environ.get('FC', 'gfortran'))
    parser.add_argument('--fflags', default='-O2')
    parser.add_argument('--saida', type=Path, default=Path('resultados_autoconvergencia'))
    parser.add_argument('--somente-analisar', action='store_true')
    parser.add_argument('--testes', action='store_true')
    args = parser.parse_args()
    checks = synthetic_checks()
    if args.testes:
        print(json.dumps(checks, indent=2, ensure_ascii=False))
        return
    if command(['git', 'branch', '--show-current']) != 'tcc-simulacoes':
        parser.error('Este experimento deve ser executado na branch tcc-simulacoes.')
    output = args.saida.expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'testes_sinteticos.json', checks)
    (output / '.gitignore').write_text('build/\nsimulacoes/\n.mplconfig/\n')
    try:
        if not args.somente_analisar:
            claw, discovery = locate_claw(args.claw)
            executable, provenance = build(output, claw, discovery, args.fc, args.fflags)
            study = dict(meshes=list(MESHES), physics=PHYSICS, numerics=NUMERICS,
                         provenance=provenance, diagnostic_verbosity=1)
            # Não sobrescrever a proveniência de uma bateria incompatível.
            path = output / 'experimento.json'
            if path.exists() and json.loads(path.read_text())['provenance']['signature'] != provenance['signature']:
                raise RuntimeError('A pasta pertence a outros fontes/configuração; escolha outra --saida.')
            write_json(path, study)
            for n in MESHES:
                run_mesh(output, n, executable, provenance)
        rows = analyse(output)
        print(f'Resultados em {output}')
        print('Última trinca: p_u=%.6f; p_ut=%.6f' % (rows[-3]['p_u'], rows[-3]['p_ut']))
    except Exception as exc:
        write_json(output / 'bloqueio.json', dict(status='bloqueado', reason=str(exc)))
        (output / 'RELATORIO_BLOQUEIO.md').write_text(
            '# Bloqueio de execução/análise\n\n' + str(exc) + '\n\n'
            'Nenhum resultado ausente foi preenchido. Logs e execuções parciais foram preservados.\n')
        print(f'BLOQUEIO: {exc}', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
