#!/usr/bin/env python3
"""Monta as comparações dos Casos 2–8 a partir de simulações já concluídas.

Cria uma pasta independente em resultados/figuras_comparativas. Não executa
simulações e não inclui o estudo de convergência do Caso 1.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from executar_casos import ROOT, cases, complete, read_amplitudes, read_frame, run_id


ZERO = (0, 0, 200, 0)
CASE4 = [ZERO, (1, 0, 200, 0), (0, 1, 200, 0), (1, 1, 200, 0)]
CASE5 = [(1, b, 200, 0) for b in (-1, 0, 1)]
CASE6 = (0.5, -1, 25, 0.5)
FRAMES = (16, 32, 48, 64)


def path_for(data_dir: Path, params: tuple[float, float, float, float]) -> Path:
    return data_dir / run_id(params)


def frame_data(data_dir: Path, params: tuple[float, float, float, float], frame: int):
    time, x, q = read_frame(path_for(data_dir, params), frame)
    return time, x, [row[0] for row in q]


def run_label(params: tuple[float, float, float, float], *, detail: str = 'ab') -> str:
    a, b, beta, x0 = params
    if detail == 'full':
        return rf'$a={a:g},\ b={b:g},\ \beta={beta:g},\ x_0={x0:g}$'
    if detail == 'beta':
        return rf'$\beta={beta:g}$'
    if detail == 'initial':
        return rf'$\beta={beta:g},\ x_0={x0:g}$'
    return rf'$a={a:g},\ b={b:g}$'


def save(fig, destination: Path, name: str) -> None:
    fig.savefig(destination / f'{name}.png', dpi=220, bbox_inches='tight')
    fig.savefig(destination / f'{name}.pdf', bbox_inches='tight')
    import matplotlib.pyplot as plt
    plt.close(fig)


def decorate(ax, *, xlabel: str, ylabel: str, title: str) -> None:
    ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
    ax.grid(alpha=0.25)


def comparison(data_dir: Path, destination: Path, group, *, case: int,
               frame: int, name: str, detail: str = 'ab', note: str = '') -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout='constrained')
    for params in group:
        time, x, u = frame_data(data_dir, params, frame)
        amplitude = read_amplitudes(path_for(data_dir, params))
        label = run_label(params, detail=detail)
        axes[0].plot(x, u, label=label, lw=1.8)
        axes[1].plot([item[0] for item in amplitude],
                     [item[1] for item in amplitude], label=label, lw=1.8)
    decorate(axes[0], xlabel='$x$', ylabel='$u(x,t)$',
             title=f'Caso {case}: perfis em $t={time:.1f}$')
    decorate(axes[1], xlabel='$t$', ylabel=r'$A(t)=\max_i |u_i(t)|$',
             title='Amplitude máxima nos centros das células')
    axes[0].set_xlim(-2, 2)
    for ax in axes:
        ax.legend(fontsize=9)
    if note:
        fig.suptitle(note, fontsize=10)
    save(fig, destination, name)


def initial_profiles(data_dir: Path, destination: Path, group, *, name: str,
                     title: str, detail: str) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5), layout='constrained')
    for params in group:
        _, x, u = frame_data(data_dir, params, 0)
        ax.plot(x, u, lw=1.8, label=run_label(params, detail=detail))
    decorate(ax, xlabel='$x$', ylabel='$u(x,0)$', title=title)
    ax.set_xlim(-2, 2)
    ax.legend()
    save(fig, destination, name)


def case6_evolution(data_dir: Path, destination: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5), sharex=True, sharey=True,
                             layout='constrained')
    for ax, frame in zip(axes.flat, (0, *FRAMES)):
        time, x, u = frame_data(data_dir, CASE6, frame)
        ax.plot(x, u, color='#0072B2', lw=1.8)
        decorate(ax, xlabel='$x$', ylabel='$u$', title=f'$t={time:.1f}$')
        ax.set(xlim=(-2, 2), ylim=(-0.05, 1.05))
        if frame == 64:
            ax.axvline(2, color='#D55E00', ls='--', lw=1.2)
            ax.text(0.02, 0.05, 'Pulso junto ao contorno direito',
                    transform=ax.transAxes, fontsize=9, color='#A04000')
    axes.flat[-1].axis('off')
    fig.suptitle('Caso 6: propagação do pulso largo e deslocado; '
                 r'o pico direito chega perto de $x=2$ em $t\approx 0{,}75$')
    save(fig, destination, 'caso_6_evolucao')


def case8_panels(data_dir: Path, destination: Path, frame: int) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharex='col',
                             layout='constrained')
    for row, a in enumerate((0, 1, 2)):
        for b in (-1, 0, 1):
            params = (a, b, 200, 0)
            time, x, u = frame_data(data_dir, params, frame)
            amplitude = read_amplitudes(path_for(data_dir, params))
            color = {-1: '#0072B2', 0: '#E69F00', 1: '#009E73'}[b]
            axes[row, 0].plot(x, u, color=color, lw=1.7,
                              label=rf'$b={b:g}$')
            axes[row, 1].plot([item[0] for item in amplitude],
                              [item[1] for item in amplitude],
                              color=color, lw=1.7, label=rf'$b={b:g}$')
        decorate(axes[row, 0], xlabel='$x$', ylabel='$u$',
                 title=rf'$a={a:g}$: perfis em $t={time:.1f}$')
        decorate(axes[row, 1], xlabel='$t$', ylabel=r'$A(t)$',
                 title=rf'$a={a:g}$: amplitude máxima')
        axes[row, 0].set_xlim(-2, 2)
        axes[row, 0].legend(fontsize=9)
        axes[row, 1].legend(fontsize=9)
    fig.suptitle('Caso 8: comparação dos três valores de $b$ para cada $a$')
    save(fig, destination, f'caso_8_por_a_t{time:.1f}'.replace('.', 'p'))


def differences_from_b0(data_dir: Path, destination: Path) -> None:
    """Evidencia o efeito pequeno de b quando curvas completas se sobrepõem."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True,
                             layout='constrained')
    for row, a in enumerate((0, 1, 2)):
        for col, frame in enumerate((32, 64)):
            time, x, baseline = frame_data(data_dir, (a, 0, 200, 0), frame)
            for b, color in ((-1, '#0072B2'), (1, '#009E73')):
                _, _, u = frame_data(data_dir, (a, b, 200, 0), frame)
                axes[row, col].plot(x, [value - base for value, base in zip(u, baseline)],
                                    label=rf'$b={b:g}$', color=color, lw=1.8)
            axes[row, col].axhline(0, color='0.35', lw=0.8)
            decorate(axes[row, col], xlabel='$x$',
                     ylabel=r'$u_{a,b}(x,t)-u_{a,0}(x,t)$',
                     title=rf'$a={a:g},\ t={time:.1f}$')
            axes[row, col].set_xlim(-2, 2)
            axes[row, col].legend()
    fig.suptitle('Caso 8: alteração do perfil causada por mudar $b$ com $a$ fixo')
    save(fig, destination, 'caso_8_diferencas_vs_b0')


def amplitude_rows(data_dir: Path, group, *, case: int):
    rows = []
    for params in group:
        a, b, beta, x0 = params
        amplitudes = read_amplitudes(path_for(data_dir, params))
        for frame in FRAMES:
            time, amplitude = amplitudes[frame]
            rows.append([case, run_id(params), a, b, beta, x0,
                         f'{time:.1f}', f'{amplitude:.16g}'])
    return rows


def write_amplitudes(data_dir: Path, destination: Path, groups: dict[int, list]) -> None:
    with (destination / 'amplitudes_tempos_comuns.csv').open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['caso', 'id', 'a', 'b', 'beta', 'x0', 't', 'A_max_abs_u'])
        for case, group in groups.items():
            writer.writerows(amplitude_rows(data_dir, group, case=case))

    for frame in (32, 64):
        time = 0.8 * frame / 64
        filename = f'caso_8_t{str(time).replace(".", "p")}_matriz.csv'
        with (destination / filename).open('w', newline='') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(['a \\ b', -1, 0, 1])
            for a in (0, 1, 2):
                writer.writerow([a, *(
                    f'{read_amplitudes(path_for(data_dir, (a, b, 200, 0)))[frame][1]:.16g}'
                    for b in (-1, 0, 1)
                )])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados', type=Path, default=ROOT / 'resultados',
                        help='Pasta com as simulações completas.')
    args = parser.parse_args()
    data_dir = args.dados.expanduser().resolve()
    groups = cases()
    required = dict.fromkeys([p for group in groups.values() for p in group])
    missing = [run_id(p) for p in required if not complete(path_for(data_dir, p), p)]
    if missing:
        parser.error('Simulações ausentes ou incompletas: ' + ', '.join(missing))

    destination = data_dir / 'figuras_comparativas'
    destination.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(data_dir / '.mplconfig'))

    for case in (2, 3):
        for frame in (32, 64):
            comparison(data_dir, destination, groups[case], case=case, frame=frame,
                       name=f'caso_{case}_t{str(frame * 0.0125).replace(".", "p")}')

    for frame in (32, 64):
        suffix = str(frame * 0.0125).replace('.', 'p')
        comparison(data_dir, destination, CASE4, case=4, frame=frame,
                   name=f'caso_4_quatro_configuracoes_t{suffix}')
        comparison(data_dir, destination, CASE5, case=5, frame=frame,
                   name=f'caso_5_comparacao_b_t{suffix}')

    initial_profiles(data_dir, destination, [ZERO, CASE6],
                     name='caso_6_condicoes_iniciais',
                     title='Caso 6: pulso deslocado e condição de referência',
                     detail='initial')
    case6_evolution(data_dir, destination)
    comparison(data_dir, destination, [(1, -1, 200, 0), CASE6], case=6,
               frame=32, name='caso_6_versus_caso_5_t0p4', detail='full',
               note='Os dois testes diferem em a, largura e centro do pulso; '
                    'a comparação não isola um único efeito.')

    initial_profiles(data_dir, destination, groups[7],
                     name='caso_7_condicoes_iniciais',
                     title='Caso 7: larguras iniciais com a=1 e b=-1',
                     detail='beta')
    for frame in (32, 64):
        comparison(data_dir, destination, groups[7], case=7, frame=frame,
                   name=f'caso_7_beta_t{str(frame * 0.0125).replace(".", "p")}',
                   detail='beta')

    for frame in (32, 64):
        case8_panels(data_dir, destination, frame)
    differences_from_b0(data_dir, destination)
    write_amplitudes(data_dir, destination, groups)
    (destination / 'LEIA-ME.md').write_text(
        '# Figuras comparativas dos Casos 2–8\n\n'
        'Geradas por `python3 gerar_figuras_comparativas.py` a partir dos dados '
        'de `resultados/`. Cada figura tem versões PNG e PDF. '
        'A tabela `amplitudes_tempos_comuns.csv` usa t=0,2; 0,4; 0,6; 0,8. '
        'As duas matrizes do Caso 8 organizam A(t) por linha a e coluna b.\n\n'
        'O Caso 6 usa o domínio original [-2,2]. Seu pico direito alcança '
        'o contorno perto de t=0,75; a figura final pode refletir esse efeito. '
        'A comparação com o Caso 5 altera a, beta e x0 simultaneamente e '
        'não permite atribuir a diferença a apenas um desses parâmetros.\n\n'
        'O Caso 1 permanece reservado para o estudo de validação e convergência.\n'
    )
    print(f'Figuras e tabelas salvas em {destination}')


if __name__ == '__main__':
    main()
