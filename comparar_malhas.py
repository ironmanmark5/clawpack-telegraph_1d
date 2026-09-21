import matplotlib.pyplot as plt
import numpy as np
import os

# =========================================================
# PARÂMETROS (DEVEM BATER COM A SIMULAÇÃO)
# =========================================================
c = 2.0
beta = 200.0          # <-- USE O MESMO VALOR QUE VOCÊ RODOU
x_lower, x_upper = -2.0, 2.0
tfinal = 0.8
num_output_times = 64
output_t0 = True       # True se o frame 0 é t=0
t_compare = 0.4        # tempo em que você quer comparar

# Malhas a serem comparadas (a partir de 256)
mesh_sizes = [256, 512, 1024]   # pode adicionar 2048 se tiver

# =========================================================
# FUNÇÃO SOLUÇÃO EXATA
# =========================================================
def u_exata(x, t):
    return 0.5 * np.exp(-beta * (x - c*t)**2) + 0.5 * np.exp(-beta * (x + c*t)**2)

# =========================================================
# CÁLCULO DO NÚMERO DO FRAME
# =========================================================
if output_t0:
    frame_index = int(round(t_compare / tfinal * num_output_times))
else:
    frame_index = int(round(t_compare / tfinal * (num_output_times - 1)))
frame_str = f"{frame_index:04d}"

# =========================================================
# PLOTAGEM
# =========================================================
plt.figure(figsize=(8, 5))
all_y = []   # para ajuste do eixo y

cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # cores

for i, mx in enumerate(mesh_sizes):
    caminho = f"output_malha_{mx}/fort.q{frame_str}"
    if not os.path.exists(caminho):
        print(f"Aviso: {caminho} não encontrado. Pulando malha {mx}.")
        continue
    dados = np.loadtxt(caminho, skiprows=6)
    q1 = dados[:, 0]   # tensão u
    dx = (x_upper - x_lower) / mx
    x_centros = np.linspace(x_lower + dx/2, x_upper - dx/2, mx)
    plt.plot(x_centros, q1, color=cores[i % len(cores)], linestyle='-', linewidth=1.5,
             label=f'N = {mx}')
    all_y.extend(q1)

# Solução exata (em malha fina para suavidade)
x_fino = np.linspace(x_lower, x_upper, 2000)
u_ex = u_exata(x_fino, t_compare)
plt.plot(x_fino, u_ex, 'r--', linewidth=2, label='Solução exata')

# ---- ZOOM AUTOMÁTICO NA REGIÃO DE INTERESSE ----
tol = 1e-3
mask = u_ex > tol
if mask.any():
    x_min = x_fino[mask][0] - 0.2
    x_max = x_fino[mask][-1] + 0.2
    plt.xlim(x_min, x_max)
else:
    plt.xlim(x_lower, x_upper)

# Ajuste do eixo y
ymax = max(u_ex.max(), max(all_y) if all_y else 0)
plt.ylim(-0.05 * ymax, ymax * 1.05)

# ---- RÓTULOS E LEGENDA ----
plt.title(f'Comparação de malhas – t = {t_compare:.2f}', fontsize=16)
plt.xlabel(r'$x$', fontsize=14)
plt.ylabel(r'$u$ (tensão)', fontsize=14)
plt.legend(loc='upper right')
plt.grid(alpha=0.3)

# ---- SALVAMENTO ----
os.makedirs('resultados', exist_ok=True)
# Salva em PDF (recomendado para pdfLaTeX) e também PNG
plt.savefig('resultados/comparacao_malhas_zoom2.pdf', format='pdf')
plt.savefig('resultados/comparacao_malhas_zoom2.png', dpi=300)
print("✅ Figura salva em 'resultados/comparacao_malhas_zoom2.pdf' e .png")
plt.show()