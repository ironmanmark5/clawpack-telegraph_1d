# Equação do Telegrafista no Clawpack

Implementação numérica da Equação do Telegrafista (caso homogêneo, equivalente à equação da onda) utilizando o framework **Clawpack**.

Este projeto foi desenvolvido como parte de um **Trabalho de Conclusão de Curso (TCC)** e tem como objetivo estudar a propagação de ondas, a implementação de solucionadores de Riemann e a análise de convergência de métodos de volumes finitos.

---

## Problema Modelado

O caso homogêneo da Equação do Telegrafista é dado por:

```text
∂²u/∂t² = c² ∂²u/∂x²
```

com condição inicial gaussiana:

```text
u(x,0) = exp(-βx²)
u_t(x,0) = 0
```

onde:

* c = 2 (velocidade de propagação)
* β = 200 (largura da gaussiana)

A solução exata consiste em duas ondas gaussianas que se propagam em sentidos opostos:

```text
u(x,t) =
½ exp[-β(x-ct)²]
+
½ exp[-β(x+ct)²]
```

Para utilização no Clawpack, a equação é reescrita como um sistema hiperbólico de primeira ordem:

```text
q_t + A q_x = 0
```

com:

```text
q = [u, u_t, u_x]ᵀ
```

e matriz de coeficientes:

```text
      | 0   0    0 |
A  =  | 0   0  -c² |
      | 0  -1    0 |
```

A discretização utiliza:

* Método dos Volumes Finitos
* Solver de Riemann personalizado
* Esquema de segunda ordem
* Limitadores MC (Monotonized Central)

---

## Estrutura do Projeto

```text
telegraph_1d/
├── Makefile
├── README.md
├── qinit.f90
├── setprob.f90
├── setrun.py
├── setplot.py
├── src1.f90
├── comparar_malhas.py
├── rodar.sh
└── ...
```

### Arquivos Principais

| Arquivo              | Função                                           |
| -------------------- | ------------------------------------------------ |
| `setrun.py`          | Configuração da malha, tempo final, CFL e saídas |
| `setprob.f90`        | Leitura dos parâmetros físicos                   |
| `qinit.f90`          | Definição da condição inicial                    |
| `src1.f90`           | Implementação do sistema hiperbólico             |
| `setplot.py`         | Geração dos gráficos                             |
| `comparar_malhas.py` | Análise de erros e convergência                  |
| `Makefile`           | Compilação e execução                            |

---

## Requisitos

* Python 3
* Fortran (gfortran)
* Clawpack 5.x

Verifique sua instalação:

```bash
python -c "import clawpack; print(clawpack.__version__)"
```

---

## Configuração do Ambiente

Defina as variáveis de ambiente do Clawpack:

```bash
export CLAW=$(realpath ../../..)
export PYTHONPATH=$CLAW:$PYTHONPATH
```

---

## Compilação

Compile o executável:

```bash
make .exe
```

---

## Execução

Execute a simulação:

```bash
make .output OUTDIR=output
```

Gerar gráficos:

```bash
make .plots OUTDIR=output PLOTDIR=plots
```

---

## Estudo de Convergência

Torne o script executável:

```bash
chmod +x rodar.sh
```

Executar uma única malha:

```bash
./rodar.sh 200
```

Executar várias malhas:

```bash
for n in 50 100 200 400 800; do
    ./rodar.sh $n
done
```

Os resultados serão armazenados em diretórios separados para cada refinamento.

---

## Pós-Processamento

Após gerar as soluções:

```bash
python3 comparar_malhas.py
```

O script realiza:

* Leitura dos arquivos de saída do Clawpack
* Comparação com a solução exata
* Cálculo do erro L²
* Gráfico log-log de convergência
* Comparação visual entre solução numérica e analítica

---

## Parâmetros Físicos

Definidos em `setprob.data`:

```text
rho   = 1.0
K     = 4.0
beta  = 200.0
```

A velocidade da onda é calculada por:

```text
c = sqrt(K/rho)
```

resultando em:

```text
c = 2
```

---

## Parâmetros Numéricos

Podem ser alterados em `setrun.py`:

```python
clawdata.num_cells[0]
clawdata.tfinal
clawdata.num_output_times
clawdata.limiter
clawdata.bc_lower[0]
clawdata.bc_upper[0]
```

Exemplo:

```python
clawdata.limiter = ['mc', 'mc', 'mc']
```

---

## Resultados Esperados

A solução inicial gaussiana divide-se em duas ondas que se propagam simetricamente para a esquerda e para a direita com velocidade constante.

O refinamento sucessivo da malha deve produzir:

* Redução do erro L²
* Aproximação da ordem teórica do método
* Melhor concordância com a solução exata

---

## Trabalhos Futuros

* Inclusão de amortecimento
* Inclusão de termos de reação
* Operator Splitting
* Equação completa do Telegrafista
* Extensão para duas dimensões

---

## Referências

1. Randall J. LeVeque, *Finite Volume Methods for Hyperbolic Problems*, Cambridge University Press.

2. Clawpack Documentation
   https://www.clawpack.org

3. Material teórico desenvolvido para o TCC.
