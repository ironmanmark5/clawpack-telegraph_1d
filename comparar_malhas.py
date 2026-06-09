import matplotlib.pyplot as plt
import numpy as np
import os

# Configurações do Problema
mesh_sizes = [32, 64, 128, 256, 512, 1024]
x_lower, x_upper = -2.0, 2.0
t_final = 0.0
u = 1.0  # velocidade de advecção

def q_exata(x, t):
    """ Equação em uso : exp(-100*(x-0.4)^2)/10 """
    # Considera a translação x -> x - ut
    x0 = x - u*t
    # Ajuste simples para o domínio (periódico ou infinito)
    return np.exp(-100.0 * (x0 - 0.4)**2) / 10.0

plt.figure(figsize=(10, 6))

# Loop para ler cada pasta de output
for m in mesh_sizes:
    path = f"output_malha_{m}/fort.q0000" # lendo o frame 20 (t=0.2)
    
    if os.path.exists(path):
        # O Clawpack ASCII tem 6 linhas de cabeçalho, então pulamos elas
        data = np.loadtxt(path, skiprows=6)
        
        # Reconstrói o eixo X (centros das células)
        dx = (x_upper - x_lower) / m
        x = np.linspace(x_lower + dx/2, x_upper - dx/2, m)
        
        plt.plot(x, data, label=f'Malha {m}')
    else:
        print(f"Aviso: Pasta {path} não encontrada.")

# Plotar a Solução Exata para comparação (Linha contínua)
x_fino = np.linspace(x_lower, x_upper, 1600)
plt.plot(x_fino, q_exata(x_fino, t_final), 'r--', linewidth=2, label='Solução Exata')

# Estética do Gráfico
plt.title(f'Comparação de Convergência de Malha (t = {t_final})', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('q', fontsize=12)
plt.xlim([-0.5, 1.5]) # Focar na região onde a onda está (x=0.6)
plt.ylim([-0.01, 0.12])
plt.legend()
plt.grid(alpha=0.3)

# Salvar o resultado
os.makedirs('resultados', exist_ok=True) # Cria pasta 'resultados' se ela não existir

plt.savefig('resultados/frame01.png', dpi=1000)
print("Sucesso! O gráfico 'comparativo_malhas.png' foi gerado.")
plt.show()
