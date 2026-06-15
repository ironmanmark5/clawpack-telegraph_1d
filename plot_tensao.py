import matplotlib.pyplot as plt
import numpy as np
import os

# =========================================================
# PARÂMETROS DO PROBLEMA (devem bater com setprob.data)
# =========================================================
c = 2.0          # velocidade de propagação (sqrt(bulk/rho) = sqrt(4/1))
beta = 200.0     # largura da gaussiana inicial
x_lower, x_upper = -2.0, 2.0   # domínio espacial

# =========================================================
# PARÂMETROS DA SIMULAÇÃO (devem bater com setrun.py)
# =========================================================
tfinal = 0.8
num_output_times = 64
output_t0 = True   # se True, o primeiro frame é em t=0

# =========================================================
# CONFIGURAÇÕES DO GRÁFICO
# =========================================================
t_compare = 0.4          # tempo que você quer visualizar
mesh_sizes = [128, 256, 512, 1024, 2048]   # malhas que você rodou

# =========================================================
# FUNÇÃO SOLUÇÃO EXATA
# =========================================================
def u_exata(x, t):
    """Tensão exata para a equação do telegrafista homogênea"""
    return 0.5 * np.exp(-beta * (x - c*t)**2) + 0.5 * np.exp(-beta * (x + c*t)**2)

# =========================================================
# CÁLCULO DO NÚMERO DO FRAME A PARTIR DO TEMPO
# =========================================================
if output_t0:
    # frames: 0 (t=0), 1, 2, ..., num_output_times (t=tfinal)
    frame_index = int(round(t_compare / tfinal * num_output_times))
else:
    frame_index = int(round(t_compare / tfinal * (num_output_times - 1)))
frame_str = f"{frame_index:04d}"

print(f"Procurando frame {frame_str} (tempo aproximado {t_compare})")

# =========================================================
# LEITURA E PLOTAGEM
# =========================================================
plt.figure(figsize=(10, 6))

# Lista para guardar os valores de tensão (útil para ajuste automático do eixo Y)
all_tensoes = []

for mx in mesh_sizes:
    caminho = f"output_malha_{mx}/fort.q{frame_str}"
    if not os.path.exists(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        continue

    # Carrega os dados (ignora cabeçalho de 6 linhas)
    dados = np.loadtxt(caminho, skiprows=6)

    # Extrai apenas a primeira coluna: tensão u (q1)
    tensao = dados[:, 0]

    # Monta o eixo x (centros das células)
    dx = (x_upper - x_lower) / mx
    x_centros = np.linspace(x_lower + dx/2, x_upper - dx/2, mx)

    # Armazena para ajuste de eixo
    all_tensoes.extend(tensao)

    # Plota a tensão numérica
    plt.plot(x_centros, tensao, linewidth=1.5, label=f'Malha {mx}')

# =========================================================
# SOLUÇÃO EXATA (MALHA FINA)
# =========================================================
x_fino = np.linspace(x_lower, x_upper, 2000)
u_ex = u_exata(x_fino, t_compare)
plt.plot(x_fino, u_ex, 'k--', linewidth=2, label='Solução exata')

# =========================================================
# AJUSTE AUTOMÁTICO DOS LIMITES DOS EIXOS
# =========================================================
# Limite x: onde a solução exata é maior que uma tolerância
tol = 1e-3
mask = u_ex > tol
if mask.any():
    x_min = x_fino[mask][0] - 0.3
    x_max = x_fino[mask][-1] + 0.3
    plt.xlim(x_min, x_max)

# Limite y: baseado no máximo da exata e dos dados numéricos
ymax = max(u_ex.max(), max(all_tensoes) if all_tensoes else 0)
plt.ylim(-0.05 * ymax, ymax * 1.05)

# =========================================================
# FORMATAÇÃO E SALVAMENTO
# =========================================================
plt.title(f'Tensão na equação do telegrafista (t = {t_compare:.2f})', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('u (tensão)', fontsize=12)
plt.legend(loc='upper right')
plt.grid(alpha=0.3)

os.makedirs('resultados', exist_ok=True)
plt.savefig(f'resultados/tensao_t_{t_compare:.2f}.png', dpi=300)
plt.show()