# Equação do Telegrafista no Clawpack

Implementação da equação do telegrafista (caso homogêneo → equação da onda) utilizando o ambiente Clawpack. Desenvolvido como parte de Trabalho de Conclusão de Curso (TCC).

## Modelo Matemático

A equação homogênea considerada é:

```math
\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}
```

com condição inicial gaussiana:

```math
u(x,0) = e^{-\beta x^2}
```

```math
\frac{\partial u}{\partial t}(x,0) = 0
```

onde:

* (c = 2)
* (\beta = 200)

A solução exata consiste em duas ondas que se propagam simetricamente:

```math
u_{\text{exata}}(x,t)=
\frac{1}{2}e^{-\beta(x-ct)^2}
+
\frac{1}{2}e^{-\beta(x+ct)^2}
```

O sistema é reescrito como um sistema hiperbólico de primeira ordem:

```math
\mathbf{q}_t + A\mathbf{q}_x = 0
```

com

```math
\mathbf{q}=
\begin{pmatrix}
u\\
u_t\\
u_x
\end{pmatrix}
```

e

```math
A=
\begin{pmatrix}
0 & 0 & 0\\
0 & 0 & -c^2\\
0 & -1 & 0
\end{pmatrix}
```

A discretização é realizada utilizando o solver de Riemann do Clawpack com esquema de segunda ordem e limitadores `mc`.

---

## Estrutura dos Arquivos

| Arquivo                 | Descrição                                                       |
| ----------------------- | --------------------------------------------------------------- |
| `setrun.py`             | Parâmetros da simulação (malha, tempo final, CFL e saídas).     |
| `setprob.f90`           | Leitura dos parâmetros físicos (`rho`, `K`, `beta`).            |
| `qinit.f90`             | Condição inicial gaussiana para (u), (u_t=0) e (u_x) analítico. |
| `rp1_telegraph.f90`     | Solucionador de Riemann (autovalores (-c,0,c)).                 |
| `setplot.py`            | Geração de gráficos da solução numérica e exata.                |
| `Makefile`              | Compilação e execução no padrão Clawpack.                       |
| `rodar_telegrafista.sh` | Automação para diferentes refinamentos de malha.                |
| `comparar_malhas.py`    | Pós-processamento, cálculo de erros e estudo de convergência.   |

---

## Compilação e Execução

Antes de executar qualquer comando `make`, configure as variáveis de ambiente:

```bash
export CLAW=$(realpath ../../..)
export PYTHONPATH=$CLAW:$PYTHONPATH
```

Compile o executável:

```bash
make .exe
```

Execute a simulação:

```bash
make .output OUTDIR=output
```

Gere os gráficos:

```bash
make .plots OUTDIR=output PLOTDIR=plots
```

---

## Estudo de Convergência

Torne o script executável:

```bash
chmod +x rodar_telegrafista.sh
```

Executando uma malha com 200 células:

```bash
./rodar_telegrafista.sh 200
```

Os resultados serão armazenados em:

```text
output_malha_200/
plots_malha_200/
```

Para executar várias malhas:

```bash
for n in 50 100 200 400 800; do
    ./rodar_telegrafista.sh $n
done
```

---

## Pós-Processamento e Análise de Erros

Após gerar as soluções para as diferentes malhas:

```bash
python3 comparar_malhas.py
```

O script:

* Lê os arquivos `fort.qXXXX` no instante desejado.
* Compara a solução numérica com a solução exata.
* Calcula o erro (L^2).
* Gera gráficos de convergência em escala log-log.
* Inclui retas de referência de primeira e segunda ordem.

---

## Personalização de Parâmetros

### Parâmetros Físicos

Os parâmetros são definidos em `setprob.data`:

```text
rho    # densidade
K      # módulo bulk
beta   # largura da gaussiana
```

Valores padrão:

```text
rho  = 1.0
K    = 4.0
beta = 200.0
```

A velocidade da onda é dada por:

```math
c=\sqrt{\frac{K}{\rho}}
```

resultando em:

```math
c=2
```

### Parâmetros Numéricos

No arquivo `setrun.py` podem ser alterados:

* Número de células: `clawdata.num_cells[0]`
* Tempo final: `clawdata.tfinal`
* Número de saídas: `clawdata.num_output_times`
* Limitadores: `clawdata.limiter`
* Condições de contorno:

  * `clawdata.bc_lower[0]`
  * `clawdata.bc_upper[0]`

Exemplos:

```python
clawdata.limiter = ['mc', 'mc', 'mc']
```

```python
clawdata.bc_lower[0] = 'extrap'
clawdata.bc_upper[0] = 'extrap'
```

ou

```python
clawdata.bc_lower[0] = 'periodic'
clawdata.bc_upper[0] = 'periodic'
```

---

## Observações

* A solução exata implementada utiliza os mesmos valores de (c) e (\beta) definidos em `setprob.data`.
* O solver `rp1_telegraph.f90` foi desenvolvido a partir do exemplo `acoustics_1d` do Clawpack.
* A implementação atual considera apenas o caso homogêneo.
* Extensões futuras incluirão termos fonte de amortecimento e reação por meio de técnicas de operator splitting.

---

## Referências

1. Clawpack Documentation: https://www.clawpack.org
2. LeVeque, R. J. *Finite Volume Methods for Hyperbolic Problems*. Cambridge University Press.
3. Material teórico do TCC (*Telegrafista_Clawpack.pdf*).
