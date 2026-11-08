#!/usr/bin/env python3
"""Reproduz a tabela de convergencia do Caso 1 (a = b = 0).

Le as series de saida do exemplo da raiz (pastas output_malha_*), compara a
solucao numerica com a solucao analitica de d'Alembert em um instante
escolhido e calcula os erros nas normas L2 discreta e uniforme, junto da ordem
observada entre malhas sucessivas. Gera um CSV e um grafico log-log, e confere
os valores contra os documentados na monografia.

O caso a = b = 0 tem solucao analitica conhecida, com

    u(x,t)  = 1/2 g(x - ct) + 1/2 g(x + ct),   g(xi) = exp(-beta xi^2)
    u_t(x,t) = beta c [(x - ct) g(x - ct) - (x + ct) g(x + ct)]
    u_x(x,t) = -beta [(x - ct) g(x - ct) + (x + ct) g(x + ct)]

As componentes q1, q2 e q3 do estado correspondem, respectivamente, a u, u_t e
u_x. Como o termo fonte desse caso atua apenas sobre q1, as componentes q2 e q3
sao atualizadas exclusivamente pelo esquema hiperbolico, de modo que as ordens
obtidas para elas isolam a etapa de propagacao.

Uso:
    python3 convergencia_caso1.py                       # t = 0,4
    python3 convergencia_caso1.py --tempo 0.8
    python3 convergencia_caso1.py --dirs output_malha_128 output_malha_512
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

PADRAO_SERIE = re.compile(r"^output_malha_(\d+)$")

# Valores da Tabela 6.1 da monografia, para conferencia no caso documentado.
# A coluna de erro usa a norma L2 discreta ponderada por dx, em t = 0,4,
# comparando q1 com a solucao exata avaliada no centro da celula.
REFERENCIA = {
    "e_l2_u": {
        128: 4.54747e-2,
        256: 1.84765e-2,
        512: 9.45958e-3,
        1024: 5.07321e-3,
        2048: 2.55883e-3,
    },
    "p_l2_u": {256: 1.299, 512: 0.966, 1024: 0.899, 2048: 0.987},
}

TOL_TEMPO = 1e-10


def numero(texto: str) -> float:
    """Aceita também expoentes Fortran D/d, sem arredondar os valores."""
    return float(texto.replace("D", "E").replace("d", "e"))


def ler_parametros(pasta: Path) -> tuple[float, float]:
    """Le rho, K e beta do setprob.data e devolve (c, beta)."""
    valores = []
    for linha in (pasta / "setprob.data").read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        valores.append(numero(linha.split("=")[0]))
    if len(valores) != 3 or not all(math.isfinite(v) and v > 0 for v in valores):
        raise ValueError(f"{pasta}: esperados rho, K e beta positivos e finitos")
    rho, K, beta = valores[0], valores[1], valores[2]
    return math.sqrt(K / rho), beta


def indices_disponiveis(pasta: Path) -> list[int]:
    indices = []
    for arquivo in pasta.glob("fort.t*"):
        sufixo = arquivo.name[len("fort.t"):]
        if sufixo.isdigit():
            indices.append(int(sufixo))
    return sorted(indices)


def ler_tempo(pasta: Path, indice: int) -> float:
    tempo = numero((pasta / f"fort.t{indice:04d}").read_text().split()[0])
    if not math.isfinite(tempo):
        raise ValueError(f"{pasta}: tempo nao finito no quadro {indice}")
    return tempo


def ler_quadro(pasta: Path, indice: int):
    """Le um arquivo fort.qNNNN e devolve (mx, xlow, dx, q1, q2, q3)."""
    linhas = (pasta / f"fort.q{indice:04d}").read_text(encoding="utf-8").splitlines()
    mx = int(linhas[2].split()[0])
    xlow = numero(linhas[3].split()[0])
    dx = numero(linhas[4].split()[0])
    if mx < 1 or not math.isfinite(xlow) or not math.isfinite(dx) or dx <= 0:
        raise ValueError(f"{pasta}: geometria invalida no quadro {indice}")
    dados = [[numero(v) for v in linha.split()] for linha in linhas[6:] if linha.strip()]
    if len(dados) != mx or any(len(row) != 3 or not all(map(math.isfinite, row)) for row in dados):
        raise ValueError(f"{pasta}: quadro {indice} deve ter {mx} celulas e tres componentes finitas")
    cabecalho = (pasta / f"fort.t{indice:04d}").read_text().splitlines()
    if ([int(cabecalho[i].split()[0]) for i in (1, 2, 3, 4)] != [3, 1, 0, 1]
            or cabecalho[6].split()[0] != "ascii"):
        raise ValueError(f"{pasta}: esperado Classic 1D, uma malha e tres componentes ASCII")
    return mx, xlow, dx, [linha[0] for linha in dados], \
        [linha[1] for linha in dados], [linha[2] for linha in dados]


def quadro_mais_proximo(pasta: Path, tempo: float) -> int:
    if not math.isfinite(tempo):
        raise ValueError("o tempo solicitado deve ser finito")
    indices = indices_disponiveis(pasta)
    if not indices:
        raise SystemExit(f"nenhum arquivo fort.t* encontrado em {pasta}")
    indice = min(indices, key=lambda i: abs(ler_tempo(pasta, i) - tempo))
    if not math.isclose(ler_tempo(pasta, indice), tempo, rel_tol=0., abs_tol=TOL_TEMPO):
        raise ValueError(f"{pasta}: nao existe quadro em t={tempo} (tolerancia {TOL_TEMPO:g})")
    return indice


def g(xi: float, beta: float) -> float:
    return math.exp(-beta * xi * xi)


def primitiva_g(xi: float, beta: float) -> float:
    return 0.5 * math.sqrt(math.pi / beta) * math.erf(math.sqrt(beta) * xi)


def u_exata(x, t, c, beta):
    return 0.5 * g(x - c * t, beta) + 0.5 * g(x + c * t, beta)


def ut_exata(x, t, c, beta):
    return beta * c * ((x - c * t) * g(x - c * t, beta)
                       - (x + c * t) * g(x + c * t, beta))


def ux_exata(x, t, c, beta):
    return -beta * ((x - c * t) * g(x - c * t, beta)
                    + (x + c * t) * g(x + c * t, beta))


def media_celular_u(esquerda, direita, t, c, beta, dx):
    """Media exata de u na celula [esquerda, direita] no instante t."""
    return 0.5 * (primitiva_g(direita - c * t, beta)
                  - primitiva_g(esquerda - c * t, beta)
                  + primitiva_g(direita + c * t, beta)
                  - primitiva_g(esquerda + c * t, beta)) / dx


def erros(pasta: Path, tempo: float):
    """Calcula os erros de uma serie no instante pedido."""
    c, beta = ler_parametros(pasta)
    indice = quadro_mais_proximo(pasta, tempo)
    tempo_lido = ler_tempo(pasta, indice)
    mx, xlow, dx, q1, q2, q3 = ler_quadro(pasta, indice)
    centros = [xlow + (i + 0.5) * dx for i in range(mx)]
    resultado = {"N": mx, "dx": dx, "tempo": tempo_lido,
                 "c": c, "beta": beta, "lower": xlow, "upper": xlow + mx * dx}
    for nome, numerico, exata in (
        ("u", q1, u_exata),
        ("ut", q2, ut_exata),
        ("ux", q3, ux_exata),
    ):
        diferencas = [n - exata(x, tempo_lido, c, beta)
                      for n, x in zip(numerico, centros)]
        resultado[f"e_l2_{nome}"] = math.sqrt(
            dx * sum(d * d for d in diferencas))
        resultado[f"e_inf_{nome}"] = max(abs(d) for d in diferencas)
    meios = [xlow + i * dx for i in range(mx + 1)]
    resultado["e_l2_u_media"] = math.sqrt(dx * sum(
        (numerico - media_celular_u(meios[i], meios[i + 1], tempo_lido, c, beta, dx)) ** 2
        for i, numerico in enumerate(q1)))
    return resultado


def ordem(erro_grosso: float, erro_fino: float, razao: float = 2.0) -> float:
    """Usa a razão efetiva dos espaçamentos; zero/não finito não define ordem."""
    if not math.isfinite(razao) or razao <= 1:
        raise ValueError("a razao de refinamento deve ser finita e maior que um")
    if not all(math.isfinite(e) and e > 0 for e in (erro_grosso, erro_fino)):
        return math.nan
    quociente = erro_grosso / erro_fino
    if not math.isfinite(quociente) or quociente <= 0:
        return math.nan
    return math.log(quociente) / math.log(razao)


def calcular_ordens(linhas: list[dict]) -> None:
    """Rejeita séries incompatíveis antes de comparar seus erros."""
    linhas.sort(key=lambda linha: linha["N"])
    if len({linha["N"] for linha in linhas}) != len(linhas):
        raise ValueError("ha malhas repetidas na comparacao")
    for anterior, atual in zip(linhas, linhas[1:]):
        for chave in ("c", "beta", "lower", "upper", "tempo"):
            if not math.isclose(anterior[chave], atual[chave], rel_tol=0., abs_tol=TOL_TEMPO):
                raise ValueError(f"series com {chave} diferentes nao podem ser comparadas")
        razao = anterior["dx"] / atual["dx"]
        atual["N_anterior"] = anterior["N"]
        for componente in ("u", "ut", "ux"):
            atual[f"p_l2_{componente}"] = ordem(
                anterior[f"e_l2_{componente}"], atual[f"e_l2_{componente}"], razao)


def series_disponiveis(base: Path) -> list[Path]:
    pastas = []
    for caminho in sorted(base.iterdir()):
        if caminho.is_dir() and PADRAO_SERIE.match(caminho.name):
            pastas.append(caminho)
    return pastas


def escrever_csv(caminho: Path, linhas: list[dict]) -> None:
    colunas = [
        "N", "dx", "tempo",
        "e_l2_u", "e_l2_u_media", "e_inf_u", "p_l2_u",
        "e_l2_ut", "e_inf_ut", "p_l2_ut",
        "e_l2_ux", "e_inf_ux", "p_l2_ux",
    ]
    with caminho.open("w", newline="", encoding="utf-8") as destino:
        escritor = csv.DictWriter(destino, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def gerar_figura(caminho: Path, linhas: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dx = [linha["dx"] for linha in linhas]
    figura, eixos = plt.subplots(figsize=(6.0, 4.2))
    for chave, rotulo in (
        ("e_l2_u", "$u$"),
        ("e_l2_ut", "$u_t$"),
        ("e_l2_ux", "$u_x$"),
    ):
        eixos.loglog(dx, [linha[chave] for linha in linhas], "o-", label=rotulo)
    referencia = [linha["e_l2_u"] for linha in linhas]
    for expoente, estilo in ((1, ":"), (2, "--")):
        eixos.loglog(dx, [referencia[0] * (d / dx[0]) ** expoente for d in dx],
                     "k" + estilo, linewidth=1, label=f"declive {expoente}")
    eixos.set_xlabel(r"$\Delta x$")
    eixos.set_ylabel(r"erro $L^2$ discreto")
    eixos.grid(True, which="both", alpha=0.3)
    eixos.legend()
    figura.tight_layout()
    figura.savefig(caminho.with_suffix(".png"), dpi=200)
    figura.savefig(caminho.with_suffix(".pdf"))
    plt.close(figura)


def imprimir_tabela(linhas: list[dict]) -> None:
    print(f"{'N':>6} {'dx':>10} {'E_L2(u)':>12} {'p(u)':>7} "
          f"{'E_L2(ut)':>12} {'p(ut)':>7} {'E_L2(ux)':>12} {'p(ux)':>7}")
    for linha in linhas:
        def numero(chave, formato="12.5e"):
            valor = linha.get(chave)
            return "     --     " if valor is None else f"{valor:{formato}}"

        def ordem_txt(chave):
            valor = linha.get(chave)
            return "     --" if valor is None else f"{valor:7.3f}"

        print(f"{linha['N']:6d} {linha['dx']:10.6f} {numero('e_l2_u')} "
              f"{ordem_txt('p_l2_u')} {numero('e_l2_ut')} {ordem_txt('p_l2_ut')} "
              f"{numero('e_l2_ux')} {ordem_txt('p_l2_ux')}")


def conferir(linhas: list[dict]) -> int:
    linhas = [linha for linha in linhas
              if all(math.isclose(linha[chave], valor, rel_tol=0., abs_tol=TOL_TEMPO)
                     for chave, valor in (("tempo", .4), ("c", 2.), ("beta", 200.),
                                          ("lower", -2.), ("upper", 2.)))]
    if not linhas:
        print("\nConferencia da monografia nao se aplica a este tempo/parametros/dominio.")
        return 0
    print("\nConferencia com os valores da monografia (t = 0,4):")
    pendencias = 0
    for linha in linhas:
        N = linha["N"]
        esperado = REFERENCIA["e_l2_u"].get(N)
        if esperado is None:
            continue
        calculado = linha["e_l2_u"]
        desvio = abs(calculado - esperado) / esperado
        marca = "ok" if desvio < 1e-3 else "DIVERGE"
        if marca == "DIVERGE":
            pendencias += 1
        print(f"  N={N:5d}  E_L2(u) calculado={calculado:.6e}  "
              f"documentado={esperado:.6e}  desvio relativo={desvio:.2e}  {marca}")
    for linha in linhas:
        N = linha["N"]
        esperado = REFERENCIA["p_l2_u"].get(N)
        if (esperado is None or linha.get("p_l2_u") is None
                or linha.get("N_anterior") != N // 2):
            continue
        desvio = abs(linha["p_l2_u"] - esperado)
        marca = "ok" if desvio < 5e-3 else "DIVERGE"
        if marca == "DIVERGE":
            pendencias += 1
        print(f"  N={N:5d}  p(u) calculado={linha['p_l2_u']:.4f}  "
              f"documentado={esperado:.4f}  desvio={desvio:.2e}  {marca}")
    print("  Nenhuma divergencia." if not pendencias
          else f"  {pendencias} divergencia(s) a investigar.")
    return pendencias


def main() -> None:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--tempo", type=float, default=0.4,
                            help="instante de comparacao (padrao: 0.4)")
    analisador.add_argument("--dirs", nargs="+", type=Path,
                            help="series a analisar (padrao: output_malha_*)")
    analisador.add_argument("--saida", type=Path,
                            default=Path("resultados/convergencia_caso1"),
                            help="pasta de saida do CSV e da figura")
    analisador.add_argument("--sem-figura", action="store_true",
                            help="nao gerar o grafico log-log")
    argumentos = analisador.parse_args()

    pastas = argumentos.dirs or series_disponiveis(Path.cwd())
    if not pastas:
        raise SystemExit("nenhuma serie output_malha_* encontrada")

    try:
        linhas = [erros(pasta, argumentos.tempo) for pasta in pastas]
        calcular_ordens(linhas)
    except (OSError, ValueError, IndexError) as exc:
        analisador.error(str(exc))

    argumentos.saida.mkdir(parents=True, exist_ok=True)
    escrever_csv(argumentos.saida / "convergencia_caso1.csv", linhas)
    if not argumentos.sem_figura:
        gerar_figura(argumentos.saida / "convergencia_caso1_loglog", linhas)

    imprimir_tabela(linhas)
    pendencias = conferir(linhas)
    print(f"\nArquivos gravados em {argumentos.saida}")
    if pendencias:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
