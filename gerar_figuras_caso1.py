#!/usr/bin/env python3
"""Gera as figuras de comparação de malhas do Caso 1.

Reproduz as figuras do Caso 1 da monografia (t = 0,20 e t = 0,40) a partir
das séries de refinamento em output_malha_*/, comparando cada malha com a
solução exata de d'Alembert. As duas figuras usam os mesmos limites de eixo,
cores e marcadores, de modo que possam ser comparadas diretamente. Uma
janela amplia o pico direito em x = c*t, sem interpolar as curvas numéricas.
Salva PDF (vetorial) e PNG.

Uso:
    python3 gerar_figuras_caso1.py [--destino resultados/figuras]

Não executa simulações: lê apenas os arquivos fort.qNNNN já gravados.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

from convergencia_caso1 import (
    ler_parametros,
    ler_quadro,
    ler_tempo,
    quadro_mais_proximo,
)

RAIZ = Path(__file__).resolve().parent
TEMPOS = ((0.20, "t020"), (0.40, "t040"))
X_LIMITES = (-1.2, 1.2)
Y_LIMITES = (-0.02, 0.70)
ESTILOS = {
    128: ("#B85C38", "o"),
    256: ("#99702F", "s"),
    512: ("#287D72", "^"),
    1024: ("#356FA3", "D"),
    2048: ("#72558C", "x"),
}
COR_EXATA = "#222222"
ZOOM_MEIA_LARGURA = 0.065
ZOOM_Y_LIMITES = (0.33, 0.52)


@dataclass(frozen=True)
class Serie:
    """Valores gravados nos centros das células, sem reamostragem."""

    n: int
    x: np.ndarray
    u: np.ndarray
    c: float
    beta: float
    tempo: float


def series():  # noqa: D103
    pastas = []
    for caminho in RAIZ.glob("output_malha_*"):
        sufixo = caminho.name.rsplit("_", 1)[-1]
        if caminho.is_dir() and sufixo.isdigit() and int(sufixo) in ESTILOS:
            pastas.append((int(sufixo), caminho))
    faltantes = set(ESTILOS) - {n for n, _ in pastas}
    if faltantes:
        raise ValueError(f"séries de malha ausentes: {sorted(faltantes)}")
    return [caminho for _, caminho in sorted(pastas)]


def estilo() -> None:
    plt.rcParams.update({
        "font.size": 13,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 11,
        "axes.linewidth": 0.8,
        "figure.dpi": 160,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
    })


def u_exata(x, t: float, c: float, beta: float):
    """Solução de d'Alembert do caso a = b = 0, vetorizada em x.

    Mesma expressão de convergencia_caso1.u_exata, que é escalar.
    """
    return 0.5 * np.exp(-beta * (x - c * t) ** 2) + 0.5 * np.exp(-beta * (x + c * t) ** 2)


def carregar_series(pastas, tempo: float) -> list[Serie]:
    """Confere os quadros antes de desenhar dados numéricos e referência."""
    dados = []
    for pasta in pastas:
        c, beta = ler_parametros(pasta)
        quadro = quadro_mais_proximo(pasta, tempo)
        tempo_lido = ler_tempo(pasta, quadro)
        if not np.isclose(tempo_lido, tempo, rtol=0, atol=1e-10):
            raise ValueError(f"{pasta}: quadro em t={tempo_lido}, esperado t={tempo}")
        mx, xlow, dx, u, _, _ = ler_quadro(pasta, quadro)
        if mx != int(pasta.name.rsplit("_", 1)[-1]) or mx not in ESTILOS:
            raise ValueError(f"{pasta}: número de células inesperado: {mx}")
        x = xlow + (np.arange(mx) + 0.5) * dx
        u = np.asarray(u)
        if not np.all(np.isfinite(u)) or c <= 0 or beta <= 0:
            raise ValueError(f"{pasta}: dados ou parâmetros inválidos")
        dados.append(Serie(mx, x, u, c, beta, tempo_lido))
    if len({(d.c, d.beta, d.tempo) for d in dados}) != 1:
        raise ValueError("as séries devem compartilhar c, beta e o instante")
    return dados


def desenhar_curvas(ax, dados: list[Serie], xlim, *, detalhe=False) -> None:
    """Mantém todos os pontos nas linhas; só os marcadores são esparsos."""
    for ordem, dado in enumerate(dados):
        cor, marcador = ESTILOS[dado.n]
        dx = dado.x[1] - dado.x[0]
        espacamento = 0.012 if detalhe else 0.095
        passo = max(1, round(espacamento / dx))
        # Alterna apenas os índices que recebem símbolos, nunca os dados.
        inicio = round(ordem * passo / len(dados)) % passo
        indices = np.arange(inicio, dado.n, passo)
        if not detalhe:
            # Evita uma faixa de símbolos sobrepostos na região quase nula.
            # As linhas continuam incluindo todos os valores, inclusive o resíduo.
            indices = indices[np.abs(dado.u[indices]) > 0.025]
        ax.plot(
            dado.x, dado.u, color=cor, lw=1.25,
            marker=marcador, markevery=indices.tolist(),
            markersize=3.3 if detalhe else 4.0,
            markerfacecolor="white", markeredgewidth=0.85,
            label=rf"$N = {dado.n}$",
        )
    ref = dados[0]
    x = np.linspace(*xlim, 1600)
    ax.plot(
        x, u_exata(x, ref.tempo, ref.c, ref.beta),
        color=COR_EXATA, ls="--", lw=1.45,
        label="Solução exata", zorder=3,
    )


def figura(pastas, tempo: float, destino: Path, nome: str) -> None:
    dados = carregar_series(pastas, tempo)
    fig, ax = plt.subplots(figsize=(7.5, 3.7))
    desenhar_curvas(ax, dados, X_LIMITES)
    ax.set(xlabel="$x$", ylabel="$u(x,t)$", xlim=X_LIMITES, ylim=Y_LIMITES)
    ax.grid(alpha=0.16, linewidth=0.6)
    ax.legend(loc="upper center", ncol=3, framealpha=0.95, borderpad=0.4,
              columnspacing=1.4, handlelength=2.0, numpoints=1)
    fig.tight_layout()

    # Mesmo tamanho e escala vertical nas duas figuras; o centro acompanha ct.
    centro = dados[0].c * dados[0].tempo
    limites_zoom = (centro - ZOOM_MEIA_LARGURA, centro + ZOOM_MEIA_LARGURA)
    zoom = ax.inset_axes([0.405, 0.32, 0.23, 0.40], zorder=4)
    desenhar_curvas(zoom, dados, limites_zoom, detalhe=True)
    zoom.set(xlim=limites_zoom, ylim=ZOOM_Y_LIMITES)
    zoom.set_xticks([centro - 0.05, centro, centro + 0.05])
    zoom.set_yticks([0.35, 0.40, 0.45, 0.50])
    zoom.tick_params(labelsize=8.5, length=2.5, pad=2)
    zoom.set_title("Pico direito", fontsize=9, pad=2)
    zoom.grid(alpha=0.16, linewidth=0.5)
    for borda in zoom.spines.values():
        borda.set_color("#606060")
        borda.set_linewidth(0.7)
    mark_inset(ax, zoom, loc1=1, loc2=4, fc="none", ec="#606060",
               lw=0.65, zorder=1.8)

    destino.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino / f"{nome}.pdf")
    fig.savefig(destino / f"{nome}.png", dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=RAIZ / "resultados" / "figuras")
    args = parser.parse_args()
    destino = args.destino.expanduser().resolve()

    estilo()
    pastas = series()
    if not pastas:
        raise SystemExit("nenhuma série output_malha_* encontrada")
    print("Malhas:", ", ".join(p.name for p in pastas))
    for tempo, sufixo in TEMPOS:
        figura(pastas, tempo, destino, f"fig_caso1_{sufixo}")
        print(f"t = {tempo:.2f} -> {destino / ('fig_caso1_' + sufixo)}.pdf")


if __name__ == "__main__":
    main()
