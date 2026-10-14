# Equação do Telegrafista no Clawpack

Material computacional do Trabalho de Conclusão de Curso de graduação de
**Diogo Barbosa Ferreira da Silva** (Universidade Federal de Lavras),
orientado pela **Profa. DSc. Juliana Bertoco**.

O trabalho formula a equação do telegrafista como um sistema de primeira ordem,
resolve a parte hiperbólica com um solucionador de Riemann próprio no
[Clawpack](https://www.clawpack.org) e analisa numericamente o efeito dos
coeficientes de amortecimento e de reação, da condição inicial e do
refinamento da malha. Este repositório é o material externo vinculado à
monografia: reúne os códigos, os scripts de automação e os resultados
agregados.

<!-- TODO: incluir aqui o link do PDF da monografia quando estiver publicado. -->

## Comece por aqui

Se você chegou pelo texto da monografia e quer conferir ou refazer os
resultados, o caminho é este:

1. **Verifique o ambiente**: `./verificar-ambiente.sh` diz o que já está pronto
   e o que falta (compilador, Python, pacotes e árvore do Clawpack).
2. **Siga o guia passo a passo**: [`COMO-REPRODUZIR.md`](COMO-REPRODUZIR.md)
   descreve, na ordem da monografia, o que executar em cada etapa, o que
   esperar de cada execução e o que não está versionado de propósito.
3. **Para entender o que foi alterado no Clawpack**:
   [`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md),
   arquivo por arquivo, com o motivo de cada mudança.
4. **Para ler os dados sem executar nada**:
   [`docs/DADOS-E-NOMENCLATURA.md`](docs/DADOS-E-NOMENCLATURA.md) explica a
   convenção dos nomes das configurações, as colunas de cada CSV e a
   correspondência entre cada caso e as seções, figuras e tabelas do texto.

## A equação e o sistema resolvido

$$u_{tt} + a\,u_t = c^2 u_{xx} + b\,u$$

com as variáveis auxiliares $q_1 = u$, $q_2 = u_t$ e $q_3 = u_x$, resulta no
sistema

$$q_t + A q_x = \psi(q), \qquad
A = \begin{pmatrix} 0 & 0 & 0 \\ 0 & 0 & -c^2 \\ 0 & -1 & 0 \end{pmatrix},
\qquad
\psi(q) = \begin{pmatrix} q_2 \\ b q_1 - a q_2 \\ 0 \end{pmatrix}.$$

Os autovalores de $A$ são $-c$, $0$ e $c$. O solucionador de Riemann decompõe o
salto nas interfaces nessa base e o termo fonte $\psi(q)$ é aplicado por
separação fracionária, após a etapa hiperbólica.

## Duas versões do programa

| Versão | Pasta | Caso resolvido | Onde aparecem os resultados |
| --- | --- | --- | --- |
| Verificação | raiz do repositório | $a = b = 0$, equivalente à equação da onda | séries de refinamento com $N = 128$ a $2048$ |
| Bateria do roteiro | `arquivos-roteiro-simulacoes/` | equação completa, com $c$, $a$, $b$, $\beta$ e $x_0$ configuráveis | Casos 2 a 8 e estudo de autoconvergência |

## Onde cada arquivo deve ficar

Este repositório **é** uma pasta de exemplo do Clawpack. Para compilar, o
conteúdo dele deve estar em `$CLAW/classic/examples/telegraph_1d/`, onde
`$CLAW` é a raiz da árvore do Clawpack instalada na sua máquina. A partir daí,
o Clawpack espera uma organização própria: parte dos arquivos fica **dentro
dessa pasta** e um deles precisa ficar **fora dela**, na pasta de
solucionadores de Riemann. É o erro mais comum na primeira tentativa de
compilar.

| Arquivo | Onde deve ficar | Papel |
| --- | --- | --- |
| `setrun.py` | `$CLAW/classic/examples/telegraph_1d/` | configura malha, tempo final, CFL, instantes de saída e o termo fonte |
| `setprob.f90` | idem | lê os parâmetros do modelo em `setprob.data` |
| `qinit.f90` | idem | define a condição inicial gaussiana e sua derivada espacial |
| `src1.f90` | idem | trata o termo fonte, com amortecimento e reação |
| `setplot.py` | idem | gera os gráficos a partir das saídas |
| `Makefile` | idem | compila e executa, e aponta para o solucionador |
| **`rp1_telegraph.f90`** | **`$CLAW/riemann/src/`** | solucionador de Riemann da parte hiperbólica; é o único arquivo que vive **fora** da pasta do exemplo |

```bash
mkdir -p $CLAW/riemann/src
cp solver-referencia/rp1_telegraph.f90 $CLAW/riemann/src/
```

Dois detalhes que costumam confundir. Os arquivos `claw.data` e `setprob.data`
são **gerados** pelo `setrun.py` a cada execução e não devem ser editados à
mão: para mudar um parâmetro, altere o `setrun.py` e rode `make .data`. E a
bateria dos Casos 2 a 8 não precisa dessa cópia, porque tem o próprio
`rp1_telegraph.f90` dentro de `arquivos-roteiro-simulacoes/`, com o `Makefile`
apontando para ele.

As rotinas efetivamente modificadas em relação ao exemplo acústico do Clawpack
são cinco: `setprob.f90`, `setrun.py`, `qinit.f90`, `rp1_telegraph.f90` e
`src1.f90`. O que cada uma mudou, e por quê, está em
[`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md).


## Como reproduzir

Pré-requisitos: `make`, `gfortran`, Python 3 com `numpy` e `matplotlib`
(veja `requirements.txt`) e a árvore de fontes do Clawpack. O projeto foi
executado com Clawpack 5.14.0, `gfortran` 16.2.1 e Python 3.14.7. O Clawpack é
uma dependência externa e não está incluído neste repositório:

```bash
git clone --branch v5.14.0 https://github.com/clawpack/clawpack.git
export CLAW=$PWD/clawpack
export PYTHONPATH=$CLAW:$PYTHONPATH
```

Bateria de casos (Casos 2 a 8), que gera as figuras comparativas:

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run     # lista o que será executado
python3 executar_casos.py
python3 gerar_figuras_comparativas.py
```

Estudo de refinamento, com sete malhas de 32 a 2048 células:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py
python3 autoconvergencia.py --somente-analisar
```

Verificação da implementação (Caso 1, $a = b = 0$), na raiz do repositório:

```bash
cp solver-referencia/rp1_telegraph.f90 $CLAW/riemann/src/
make .exe
make .output OUTDIR=output_malha_512
```

A tabela de convergência e o gráfico log–log desse caso são calculados pelo
script `convergencia_caso1.py`, que lê as séries, compara com a solução exata,
confere os valores contra os documentados na monografia e também mede a ordem
de $u_t$ e $u_x$:

```bash
python3 convergencia_caso1.py            # t = 0,4
python3 convergencia_caso1.py --tempo 0.8
```

O detalhamento de cada arquivo alterado e o motivo de cada alteração estão em
[`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md).

## Estrutura do repositório

```text
.
├── Makefile, setrun.py, setplot.py     # exemplo da raiz (a = b = 0)
├── setprob.f90, qinit.f90, src1.f90    # rotinas do exemplo da raiz
├── arquivos-roteiro-simulacoes/        # bateria de casos e autoconvergência
│   ├── executar_casos.py
│   ├── gerar_figuras_comparativas.py
│   ├── autoconvergencia.py
│   ├── setrun.py, setprob.f90, qinit.f90, src1.f90, rp1_telegraph.f90
│   ├── resultados/                     # CSVs, figuras e metadados dos Casos 2 a 8
│   ├── resultados_autoconvergencia/     # erros, ordens e figuras do refinamento
│   └── resumo_autoconvergencia/         # resumo expandido para a orientação
├── solver-referencia/                  # solucionador usado no Caso 1
├── COMO-REPRODUZIR.md                  # guia passo a passo da reprodução
├── verificar-ambiente.sh               # confere compilador, Python e Clawpack
├── requirements.txt                    # dependências em Python
├── docs/                               # alterações feitas e dicionário de dados
│   ├── ALTERACOES-EM-RELACAO-AO-CLAWPACK.md
│   └── DADOS-E-NOMENCLATURA.md
├── CREDITS.md                          # créditos e atribuições
├── LICENSE                             # licença BSD de três cláusulas
└── CITATION.cff                        # como citar este material
```

## Parâmetros

No exemplo da raiz, `setprob.data` traz $\rho = 1{,}0$ e $K = 4{,}0$, de modo
que $c = \sqrt{K/\rho} = 2$, com $\beta = 200$. Na bateria do roteiro, os
parâmetros são $c = 2$, $a$, $b$, $\beta$ e $x_0$, definidos caso a caso:
Caso 2 varia $a$ com $b = 0$; Caso 3 varia $b$ com $a = 0$; Caso 4 usa
$a = b = 1$; Caso 5 usa $a = 1$ e $b = -1$; Caso 6 usa a condição inicial
deslocada, com $\beta = 25$ e $x_0 = 0{,}5$; Caso 7 varia $\beta$; e o Caso 8
percorre a grade $a \in \{0;\,1;\,2\}$ por $b \in \{-1;\,0;\,1\}$.

A configuração numérica comum é o domínio $[-2, 2]$, tempo final $0{,}8$, CFL
desejado $0{,}9$, correção hiperbólica de segunda ordem com limitador MC,
separação da fonte no esquema de Godunov e contornos por extrapolação.

## Resultados

Os resultados principais estão descritos na monografia e resumidos nos
arquivos de cada pasta de saída:

- `arquivos-roteiro-simulacoes/resultados/resumo.csv`: amplitude máxima de cada
  configuração nos instantes 0,4 e 0,8;
- `arquivos-roteiro-simulacoes/resultados/figuras_comparativas/`: comparações
  entre casos, em PDF e PNG;
- `arquivos-roteiro-simulacoes/resultados_autoconvergencia/autoconvergencia.csv`:
  erros de refinamento e ordens observadas, com
  `RELATORIO.md` descrevendo a metodologia e os limites da interpretação.

## Publicações

- SILVA, D. B. F. da; BERTOCO, J. Implementação numérica da equação do
  telegrafista no Clawpack utilizando métodos de volumes finitos. In: **Anais
  do VII Congresso Brasileiro Interdisciplinar em Ciência e Tecnologia**, 2026.
  Resumo expandido, reproduzido em [`publicacoes/`](publicacoes/).
- O estudo de autoconvergência com o termo fonte ativo tem relatório e resumo
  expandido próprios, em
  [`arquivos-roteiro-simulacoes/`](arquivos-roteiro-simulacoes/).

## Créditos e licença

Toda a parte numérica é construída sobre o Clawpack, distribuído sob a licença
BSD de três cláusulas. Os créditos ao pacote, à sua documentação e às
referências que devem ser citadas estão em
[`CREDITS.md`](CREDITS.md); o texto da licença está em [`LICENSE`](LICENSE).

## Como citar

Consulte [`CITATION.cff`](CITATION.cff). Se este material contribuir para um
trabalho acadêmico, cite também o Clawpack e as referências indicadas em
`CREDITS.md`.
