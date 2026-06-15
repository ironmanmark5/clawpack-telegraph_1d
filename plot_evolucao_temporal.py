import matplotlib.pyplot as plt
import numpy as np
import os

# =========================================================
# PARÂMETROS (mesmos do setprob.data e setrun.py)
# =========================================================
c = 2.0
beta = 200.0
x_lower, x_upper = -2.0, 2.0
tfinal = 0.8
num_output_times = 64
output_t0 = True
malha = 2048
pasta = f"output_malha_{malha}"

# Tempos para os quais gerar arquivos individuais
tempos = [0.0, 0.1, 0.2]

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def u_exata(x, t):
    return 0.5 * np.exp(-beta * (x - c*t)**2) + 0.5 * np.exp(-beta * (x + c*t)**2)

def frame_para_tempo(t):
    if output_t0:
        idx = int(round(t / tfinal * num_output_times))
    else:
        idx = int(round(t / tfinal * (num_output_times - 1)))
    return f"{idx:04d}"

def carregar_u(t, malha):
    frame = frame_para_tempo(t)
    arquivo = os.path.join(pasta, f"fort.q{frame}")
    if not os.path.exists(arquivo):
        return None, None
    dados = np.loadtxt(arquivo, skiprows=6)
    u = dados[:, 0]
    dx = (x_upper - x_lower) / malha
    x = np.linspace(x_lower + dx/2, x_upper - dx/2, malha)
    return x, u

def derivada_temporal(t, malha, dt=None):
    if dt is None:
        dt = tfinal / num_output_times   # ≈ 0.0125
    x1, u1 = carregar_u(t, malha)
    x2, u2 = carregar_u(t + dt, malha)
    if x1 is None or x2 is None:
        return None, None
    u_t = (u2 - u1) / dt
    return x1, u_t

# =========================================================
# GERA UM ARQUIVO PARA CADA TEMPO
# =========================================================
os.makedirs('resultados', exist_ok=True)
dt = tfinal / num_output_times

for t in tempos:
    # Cria uma nova figura com 2 linhas e 1 coluna (empilhados)
    fig, (ax_u, ax_ut) = plt.subplots(2, 1, figsize=(6, 7), sharex=True)
    
    # ---- Gráfico superior: u ----
    x, u_num = carregar_u(t, malha)
    if x is not None:
        u_ex = u_exata(x, t)
        ax_u.plot(x, u_num, 'b-', lw=1.5, label='Numérica')
        ax_u.plot(x, u_ex, 'r--', lw=1.5, label='Exata')
        ax_u.set_ylabel(r'$u$ (tensão)')
        ax_u.grid(alpha=0.3)
        ax_u.legend(loc='upper right')
        # Ajuste de limites x (baseado na região onde exata é relevante)
        mask = u_ex > 1e-3
        if mask.any():
            x_min = x[mask][0] - 0.2
            x_max = x[mask][-1] + 0.2
            ax_u.set_xlim(x_min, x_max)
        ymax = max(u_ex.max(), u_num.max())
        ax_u.set_ylim(-0.05*ymax, ymax*1.05)
    else:
        ax_u.set_title("Dados não encontrados")
    
    # ---- Gráfico inferior: u_t ----
    x, u_t_num = derivada_temporal(t, malha, dt)
    if x is not None:
        ax_ut.plot(x, u_t_num, 'g-', lw=1.5, label=r'$u_t$ numérica')
        ax_ut.set_xlabel(r'$x$')
        ax_ut.set_ylabel(r'$\partial u / \partial t$')
        ax_ut.grid(alpha=0.3)
        ax_ut.legend(loc='upper right')
        # Repete os limites x do gráfico superior (se existirem)
        if ax_u.get_xlim() != (0, 1):
            ax_ut.set_xlim(ax_u.get_xlim())
        ymax = np.abs(u_t_num).max()
        ax_ut.set_ylim(-1.1*ymax, 1.1*ymax)
    else:
        ax_ut.set_title("Dados insuficientes para derivada")
    
    # Título geral da figura (opcional)
    fig.suptitle(f't = {t:.2f}', fontsize=14)
    plt.tight_layout()
    
    # Salvar arquivo individual
    nome_arquivo = f'resultados/u_e_ut_t_{t:.2f}.eps'.replace('.', '_')
    plt.savefig(nome_arquivo, format='eps')
    print(f"Salvo: {nome_arquivo}")
    plt.close(fig)  # fecha a figura para liberar memória