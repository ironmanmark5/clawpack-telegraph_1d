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

> **Sobre o PDF da monografia.** A versão final do texto será publicada neste
> repositório depois da defesa e da entrega no SIP/UFLA, quando não houver
> mais correções pendentes da banca. Até lá, este repositório documenta o
> material computacional e os resultados, e a citação do software está em
> [`CITATION.cff`](CITATION.cff).

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
5. **Para saber qual script gera cada figura**:
   [`docs/MAPA-DE-FIGURAS.md`](docs/MAPA-DE-FIGURAS.md) lista, figura por
   figura, o script responsável, o comando e o arquivo de dados de entrada.
6. **Para entender a revisão de robustez sem mudar o método**:
   [`docs/REVISAO-DE-ROBUSTEZ.md`](docs/REVISAO-DE-ROBUSTEZ.md) registra as
   decisões, os testes e o que foi deliberadamente preservado.

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

## Escopo

Este repositório cobre o que está na monografia: a verificação no caso
$a=b=0$, os Casos 2 a 8 da bateria paramétrica e o estudo de autoconvergência
com o termo fonte ativo. Experimentos exploratórios que não entraram no texto
não fazem parte do caminho de reprodução dos resultados finais. Alguns
scripts antigos permanecem identificados como material exploratório.

## Onde cada arquivo deve ficar

Este repositório é uma **aplicação do Classic 1D**, com cálculo em Fortran e
configuração/análise em Python; não usa o solver PyClaw para avançar a solução.
A disposição adotada no trabalho é `$CLAW/classic/examples/telegraph_1d/`,
onde `$CLAW` aponta para a raiz da instalação. Ela facilita a localização
automática das dependências, mas não é uma exigência universal do Clawpack:
fora dessa árvore, configure `CLAW` e `PYTHONPATH` explicitamente.

O `Makefile` da raiz escolheu procurar o solver em `$CLAW/riemann/src/`.
Essa é uma escolha desta aplicação, não uma obrigação para todo solver próprio.

| Arquivo | Onde deve ficar | Papel |
| --- | --- | --- |
| `setrun.py` | `$CLAW/classic/examples/telegraph_1d/` | configura malha, tempo final, CFL, instantes de saída e o termo fonte |
| `setprob.f90` | idem | lê os parâmetros do modelo em `setprob.data` |
| `qinit.f90` | idem | define a condição inicial gaussiana e sua derivada espacial |
| `src1.f90` | idem | no Caso 1, atualiza somente $u$ por meio de $u_t$ |
| `setplot.py` | idem | configura a visualização direta no VisClaw; as figuras finais têm scripts próprios |
| `Makefile` | idem | compila e executa, e aponta para o solucionador |
| **`rp1_telegraph.f90`** | **`$CLAW/riemann/src/`** | solucionador de Riemann da parte hiperbólica; é o único arquivo que vive **fora** da pasta do exemplo |

```bash
cp solver-referencia/rp1_telegraph.f90 "$CLAW/riemann/src/"
```

Confira o destino antes da cópia se já existir um solver próprio com esse nome.
Os arquivos `claw.data` e `setprob.data` são **gerados** pelo `setrun.py` e não
devem ser editados à mão. No fluxo Makefile, `make .data` verifica dependências;
`make data` força a geração. O `rodar.sh` gera dados isolados por execução,
sem editar `setrun.py` nem os arquivos `.data` da raiz. Já a
bateria dos Casos 2 a 8 não precisa dessa cópia, porque tem o próprio
`rp1_telegraph.f90` dentro de `arquivos-roteiro-simulacoes/`, com o `Makefile`
apontando para ele.

As rotinas efetivamente modificadas em relação ao exemplo acústico do Clawpack
são quatro: `setrun.py`, `qinit.f90`, `rp1_telegraph.f90` e `src1.f90`. O
`setprob.f90` da raiz é usado **sem alteração**, porque o caso da raiz mantém
a leitura de $\rho$ e $K$ do exemplo acústico. O que cada arquivo mudou, e por
quê, está em
[`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md).


## Como reproduzir

Pré-requisitos: `make`, `gfortran`, Python 3.9+ com `numpy` e `matplotlib` 3.6+
(veja `requirements.txt`) e a árvore de fontes do Clawpack. O projeto foi
executado com Clawpack 5.14.0, `gfortran` 16.2.1 e Python 3.14.7. O Clawpack é
uma dependência externa e não está incluído neste repositório:

```bash
git clone --recurse-submodules --branch v5.14.0 https://github.com/clawpack/clawpack.git
export CLAW="$PWD/clawpack"
export FC=gfortran
export CLAW_PYTHON=python3
export PYTHONPATH="$CLAW${PYTHONPATH:+:$PYTHONPATH}"
```

Esse bloco instala a dependência; volte à raiz deste projeto antes dos
comandos seguintes. O guia explica também onde clonar esta aplicação e como
conferir se o Python importa a mesma instalação indicada por `CLAW`.

Bateria de casos (Casos 2 a 8), que gera as figuras comparativas:

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run     # lista o que será executado
python3 executar_casos.py --saida resultados/reproducao_nova
python3 gerar_figuras_comparativas.py --dados resultados/reproducao_nova
```

Estudo de refinamento, com sete malhas de 32 a 2048 células:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py --saida resultados_autoconvergencia_nova
python3 autoconvergencia.py --somente-analisar --saida resultados_autoconvergencia_nova
```

Verificação da implementação (Caso 1, $a = b = 0$), na raiz do repositório:

```bash
cp solver-referencia/rp1_telegraph.f90 "$CLAW/riemann/src/"
./rodar.sh 512 --sem-plots
```

O argumento `512` define a malha sem editar o fonte. Saídas existentes são
recusadas: use `--destino outra_pasta` para preservá-las. `--dry-run` confere
os caminhos sem compilar ou simular. O nome de um `OUTDIR`, sozinho, nunca
configura o número de células. Para apenas desenhar dados existentes pelo
VisClaw, use `make plots` (sem ponto); `make .plots` pode executar o solver.

A tabela de convergência e o gráfico log–log desse caso são calculados pelo
script `convergencia_caso1.py`, que lê as séries, compara com a solução exata,
confere os valores contra os documentados na monografia e também mede a ordem
de $u_t$ e $u_x$:

```bash
python3 convergencia_caso1.py --saida resultados/reanalise_caso1
python3 convergencia_caso1.py --tempo 0.8 --saida resultados/reanalise_caso1_t08
```

O detalhamento de cada arquivo alterado e o motivo de cada alteração estão em
[`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md).

## Estrutura do repositório

```text
.
├── Makefile, setrun.py, setplot.py     # exemplo da raiz (a = b = 0)
├── rodar.sh, executar_caso1.py         # execução isolada do Caso 1
├── setprob.f90, qinit.f90, src1.f90    # rotinas do exemplo da raiz
├── convergencia_caso1.py               # erros e ordens do Caso 1 (Tabela 6.1)
├── gerar_figuras_caso1.py              # figuras 6.1 e 6.2
├── arquivos-roteiro-simulacoes/        # bateria de casos e autoconvergência
│   ├── executar_casos.py
│   ├── gerar_figuras_comparativas.py
│   ├── autoconvergencia.py
│   ├── test_autoconvergencia.py
│   ├── setrun.py, setprob.f90, qinit.f90, src1.f90, rp1_telegraph.f90
│   ├── resultados/                     # CSVs, figuras e metadados dos Casos 2 a 8
│   ├── resultados_autoconvergencia/     # erros, ordens e figuras do refinamento
│   └── resumo_autoconvergencia/         # resumo expandido para a orientação
├── solver-referencia/                  # solucionador usado no Caso 1
├── referencia-upstream/                # originais do Clawpack, sem alteração
├── resultados/                         # séries e figuras do Caso 1
├── COMO-REPRODUZIR.md                  # guia passo a passo da reprodução
├── verificar-ambiente.sh               # confere compilador, Python e Clawpack
├── requirements.txt                    # dependências em Python
├── tests/                              # testes de robustez sem simular
├── docs/                               # alterações, diff e mapa das figuras
│   ├── ALTERACOES-EM-RELACAO-AO-CLAWPACK.md
│   ├── DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff
│   ├── MAPA-DE-FIGURAS.md
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

Para citar este material no texto da monografia ou em outro trabalho:

> SILVA, D. B. F. da. **Equação do telegrafista no Clawpack**: material
> computacional do Trabalho de Conclusão de Curso. 2026. Repositório de
> software. Disponível em:
> <https://github.com/ironmanmark5/clawpack-telegraph_1d>. Acesso em: data.

O arquivo [`CITATION.cff`](CITATION.cff) traz os mesmos dados em formato
legível por máquina e uma versão do material para citação. Se este material
contribuir para um trabalho acadêmico, cite também o Clawpack
(DOI 10.17605/osf.io/kmw6h) e as referências indicadas em
[`CREDITS.md`](CREDITS.md).
