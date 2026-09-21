import matplotlib.pyplot as plt
import numpy as np
import os

# =========================================================
# PARÂMETROS (AJUSTE CONFORME SUA SIMULAÇÃO)
# =========================================================

c = 2.0
beta = 200.0         
x_lower, x_upper = -2.0, 2.0
tfinal = 0.8
num_output_times = 64
output_t0 = True     # True se o frame 0 é em t=0
melhor_malha = 1024  # ou 2048, dependendo da sua melhor malha
pasta = f"output_malha_{melhor_malha}"

# Três instantes de tempo para gerar as figuras (em sequência)
tempos = [0.1, 0.3, 0.5]

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def u_exata(x, t):
    """Solução analítica de d'Alembert para a equação da onda."""
    return 0.5 * np.exp(-beta * (x - c*t)**2) + 0.5 * np.exp(-beta * (x + c*t)**2)

def frame_para_tempo(t):
    """Converte um tempo físico no número do frame (string com 4 dígitos)."""
    if output_t0:
        idx = int(round(t / tfinal * num_output_times))
    else:
        idx = int(round(t / tfinal * (num_output_times - 1)))
    return f"{idx:04d}"

def carregar_u(t):
    """Carrega a tensão u (q1) de um dado instante de tempo."""
    frame = frame_para_tempo(t)
    arquivo = os.path.join(pasta, f"fort.q{frame}")
    if not os.path.exists(arquivo):
        print(f"Erro: arquivo {arquivo} não encontrado.")
        return None, None
    dados = np.loadtxt(arquivo, skiprows=6)
    u = dados[:, 0]  # q1 = u (tensão)
    dx = (x_upper - x_lower) / melhor_malha
    x = np.linspace(x_lower + dx/2, x_upper - dx/2, melhor_malha)
    return x, u

def derivada_temporal(t, dt=None):
    """Calcula u_t por diferença finita centrada ou progressiva."""
    if dt is None:
        dt = tfinal / num_output_times   # passo de tempo entre frames
    x1, u1 = carregar_u(t)
    x2, u2 = carregar_u(t + dt)
    if x1 is None or x2 is None:
        return None, None
    u_t = (u2 - u1) / dt
    return x1, u_t

# =========================================================
# GERA AS 3 FIGURAS (UMA PARA CADA TEMPO)
# =========================================================
os.makedirs('resultados/derivadas', exist_ok=True)
dt = tfinal / num_output_times

for t in tempos:
    print(f"Gerando figura para t = {t:.2f}...")

    # Cria figura com 2 linhas e 1 coluna (2x1)
    fig, (ax_u, ax_ut) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)

    # ---- GRÁFICO SUPERIOR: Tensão u ----
    x, u_num = carregar_u(t)
    if x is not None:
        u_ex = u_exata(x, t)
        ax_u.plot(x, u_num, 'b-', linewidth=1.8, label='Numérica')
        ax_u.plot(x, u_ex, 'r--', linewidth=1.8, label='Exata')
        ax_u.set_ylabel(r'$u$ (tensão)', fontsize=12)
        ax_u.grid(alpha=0.3)
        ax_u.legend(loc='upper right', fontsize=10)

        # Ajuste automático dos limites x (zoom na região do pulso)
        mask = u_ex > 1e-3
        if mask.any():
            x_min = x[mask][0] - 0.2
            x_max = x[mask][-1] + 0.2
            ax_u.set_xlim(x_min, x_max)
        ymax = max(u_ex.max(), u_num.max())
        ax_u.set_ylim(-0.05 * ymax, ymax * 1.05)

    # ---- GRÁFICO INFERIOR: Derivada temporal u_t ----
    x, u_t_num = derivada_temporal(t, dt)
    if x is not None:
        ax_ut.plot(x, u_t_num, 'g-', linewidth=1.8, label=r'$u_t$ numérica')
        ax_ut.set_xlabel(r'$x$', fontsize=12)
        ax_ut.set_ylabel(r'$u_t$ (derivada temporal)', fontsize=12) # (r'$\partial u / \partial t$') -> du/dt
        ax_ut.grid(alpha=0.3)
        ax_ut.legend(loc='upper right', fontsize=10)

        # Repete os limites x do gráfico superior
        if ax_u.get_xlim() != (0, 1):
            ax_ut.set_xlim(ax_u.get_xlim())
        ymax = np.abs(u_t_num).max()
        ax_ut.set_ylim(-1.1 * ymax, 1.1 * ymax)

    # Título geral da figura (opcional)
    fig.suptitle(f'Malha (N = {melhor_malha}) — t = {t:.2f}', fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # ajusta para não sobrepor o título

    # Salva a figura em EPS (vetorial) e também PNG (para visualização rápida)
    nome_base = f'resultados/derivadas/frame_u_ut_t_{t:.2f}'.replace('.', '_')
    plt.savefig(nome_base + '.pdf', format='pdf', bbox_inches='tight', pad_inches=0.02)
    plt.savefig(nome_base + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    print(f"  Salvo: {nome_base}.pdf e {nome_base}.png")

    plt.close(fig)  # fecha a figura para liberar memória

print("\n✅ Todas as figuras foram geradas na pasta 'resultados/derivadas/'.")