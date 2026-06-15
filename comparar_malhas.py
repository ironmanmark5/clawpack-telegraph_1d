import matplotlib.pyplot as plt
import numpy as np
import os

# Parâmetros
c = 2.0
beta = 200.0
x_lower, x_upper = -2.0, 2.0
tfinal = 0.8
num_output_times = 64
output_t0 = True
t_compare = 0.2

def u_exata(x, t):
    return 0.5 * np.exp(-beta * (x - c*t)**2) + 0.5 * np.exp(-beta * (x + c*t)**2)

# Frame
if output_t0:
    frame_index = int(round(t_compare / tfinal * num_output_times))
else:
    frame_index = int(round(t_compare / tfinal * (num_output_times - 1)))
frame_str = f"{frame_index:04d}"

mesh_sizes = [128, 256, 512, 1024, 2048]

# Cores adequadas para linhas (evitar vermelho que é da exata)
cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
# Azul, laranja, verde, vermelho escuro (mas exata já é vermelho claro pontilhado), roxo

plt.figure(figsize=(10, 6))
all_y = []

for i, mx in enumerate(mesh_sizes):
    path = f"output_malha_{mx}/fort.q{frame_str}"
    if not os.path.exists(path):
        print(f"Aviso: {path} não encontrado. Pulando malha {mx}.")
        continue
    data = np.loadtxt(path, skiprows=6)
    q1 = data[:, 0]
    dx = (x_upper - x_lower) / mx
    x_centros = np.linspace(x_lower + dx/2, x_upper - dx/2, mx)
    plt.plot(x_centros, q1, color=cores[i % len(cores)], linestyle='-', linewidth=1.5,
             label=f'mx = {mx}')
    all_y.extend(q1)

# Exata (vermelho pontilhado)
x_fino = np.linspace(x_lower, x_upper, 2000)
u_ex = u_exata(x_fino, t_compare)
plt.plot(x_fino, u_ex, 'r--', linewidth=2, label='Solução exata')

# Ajuste de limites
mask = u_ex > 1e-3
if mask.any():
    x_min = x_fino[mask][0] - 0.3
    x_max = x_fino[mask][-1] + 0.3
    plt.xlim(x_min, x_max)
ymax = max(u_ex.max(), max(all_y) if all_y else 0)
plt.ylim(-0.05 * ymax, ymax * 1.05)

plt.title(r'Equação do Telegrafista ($t = {:.2f}$)'.format(t_compare), fontsize=14)
plt.xlabel(r'$x$', fontsize=12)
plt.ylabel(r'$u$ (tensão)', fontsize=12)
plt.legend(loc='upper right')
plt.grid(alpha=0.3)

os.makedirs('resultados', exist_ok=True)
nome_eps = f'resultados/comparacao_malhas_t_{t_compare:.2f}.eps'.replace('.', '_')
plt.savefig(nome_eps, format='eps')
print(f"Salvo: {nome_eps}")
plt.show()