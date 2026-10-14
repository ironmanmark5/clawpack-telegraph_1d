# O que foi feito, onde e por quê

Este documento descreve, arquivo por arquivo, o que foi alterado em relação ao
*Clawpack*, para que qualquer leitor da monografia consiga reproduzir o
trabalho. Ele corresponde, em forma resumida, ao Apêndice A da monografia.

## Ponto de partida

O trabalho parte do exemplo `classic/examples/acoustics_1d`, distribuído com o
*Clawpack*, que resolve um sistema acústico linear de duas ondas com um
solucionador de Riemann próprio. Esse exemplo foi adaptado para a equação do
telegrafista, escrita como um sistema de primeira ordem com três componentes e
três ondas (velocidades $-c$, $0$ e $c$).

## Duas versões do mesmo programa

| Versão | Onde está | O que resolve | Resultados |
| --- | --- | --- | --- |
| Raiz do repositório | `./` | caso $a = b = 0$, equivalente à equação da onda | verificação e séries de refinamento com $N = 128$ a $2048$ |
| Bateria do roteiro | `arquivos-roteiro-simulacoes/` | equação completa, com $a$, $b$, $\beta$ e $x_0$ configuráveis | Casos 2 a 8 e estudo de autoconvergência |

As duas compartilham as rotinas numéricas do *Clawpack* e diferem na leitura de
parâmetros, na condição inicial, no termo fonte e no solucionador de Riemann,
conforme a tabela a seguir.

## Alterações, arquivo por arquivo

| Arquivo | Origem | Alteração | Motivo |
| --- | --- | --- | --- |
| `setrun.py` (raiz) | `acoustics_1d/setrun.py` | número de equações e de ondas igual a três; limitador MC; separação da fonte; 64 instantes de saída | adequar o exemplo acústico ao sistema do telegrafista |
| `setprob.f90` (raiz) | `acoustics_1d/setprob.f90` | leitura de $\rho$, $K$ e $\beta$, com $c = \sqrt{K/\rho}$; bloco comum `/cparam/ rho,bulk,cc,zz` | manter a formulação acústica, em que $a = b = 0$ |
| `qinit.f90` (raiz) | `acoustics_1d/qinit.f90` | $q_1 = e^{-\beta x^2}$, $q_2 = 0$, $q_3 = -2\beta x\,e^{-\beta x^2}$ | definir a condição inicial gaussiana centrada na origem |
| `src1.f90` (raiz) | `acoustics_1d/src1.f90` | somente $q_1 \leftarrow q_1 + \Delta t\,q_2$ | avançar $u$ por meio de $u_t$, já que o termo $b q_1 - a q_2$ se anula |
| `solver-referencia/rp1_telegraph.f90` | `riemann/src/rp1_acoustics.f90` | três ondas, com autovalores $-c$, $0$ e $c$, e autovetores do sistema do telegrafista; parâmetros $\rho$ e $K$ | resolver o problema de Riemann do sistema; precisa ser copiado para `$CLAW/riemann/src/` |
| `arquivos-roteiro-simulacoes/setprob.f90` | versão da raiz | leitura de $c$, $a$, $b$, $\beta$ e $x_0$; bloco comum `/cparam/ c,a,b` | incorporar amortecimento, reação e o centro do pulso |
| `arquivos-roteiro-simulacoes/qinit.f90` | versão da raiz | $z = x - x_0$ na gaussiana e em sua derivada | permitir o pulso deslocado (Caso 6) e a variação de largura (Caso 7) |
| `arquivos-roteiro-simulacoes/src1.f90` | versão da raiz | guarda $q_1$ e $q_2$ anteriores e atualiza as duas componentes: $q_2 \leftarrow q_2 + \Delta t\,(b q_1 - a q_2)$ | resolver a equação completa, com os dois termos do modelo |
| `arquivos-roteiro-simulacoes/rp1_telegraph.f90` | `solver-referencia` | parâmetros $c$, $a$ e $b$ no lugar de $\rho$ e $K$ | alinhar o solucionador à formulação do telegrafista |
| `arquivos-roteiro-simulacoes/setrun.py` | `setrun.py` da raiz | parâmetros $c$, $a$, $b$, $\beta$, $x_0$ e número de células como argumentos, com valores padrão | executar os casos do roteiro sem editar o arquivo |
| `arquivos-roteiro-simulacoes/executar_casos.py` | novo | executa cada configuração de parâmetros, verifica as saídas e registra os metadados | automatizar e tornar reprodutível a bateria de casos |
| `arquivos-roteiro-simulacoes/gerar_figuras_comparativas.py` | novo | comparações lado a lado entre configurações e casos | produzir as figuras dos Casos 2 a 8 |
| `arquivos-roteiro-simulacoes/autoconvergencia.py` | novo | executa as sete malhas, restringe a solução fina à grossa e calcula erros e ordens | estudar a convergência com o termo fonte ativo |
| `arquivos-roteiro-simulacoes/test_autoconvergencia.py` | novo | testes sintéticos da rotina de erro e ordem | verificar a automação independentemente do solver |

## O que não foi modificado

As rotinas numéricas do *Clawpack* (`classic/src/1d/*`), as rotinas de
condição de contorno, o formato dos arquivos de saída e a estrutura de
`data`/`setrun`/`setplot` foram utilizados como distribuídos pelo pacote. As
figuras dos resultados foram produzidas por scripts próprios, a partir das
saídas em texto do solver.

## Como reproduzir

Pré-requisitos: `make`, `gfortran`, Python 3 com `matplotlib` e a árvore de
fontes do Clawpack. Com a árvore em `$CLAW`:

```bash
export CLAW=/caminho/para/clawpack
export PYTHONPATH=$CLAW:$PYTHONPATH
```

Para a bateria de casos (Casos 2 a 8):

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run     # confere a lista antes de executar
python3 executar_casos.py               # executa e registra os resultados
python3 gerar_figuras_comparativas.py   # gera as figuras comparativas
```

Para o estudo de refinamento, que executa as sete malhas:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py
python3 autoconvergencia.py --somente-analisar   # recalcula tabelas e figuras
```

Para a verificação da implementação (Caso 1, $a = b = 0$), na raiz do
repositório, copie antes o solucionador para o local previsto pelo `Makefile`:

```bash
cp solver-referencia/rp1_telegraph.f90 $CLAW/riemann/src/
make .exe
make .output OUTDIR=output_malha_512
```

As séries do Caso 1 nascem da repetição dessa última etapa com diferentes
números de células, conforme o roteiro descrito na Seção 4 da monografia.

## Observações sobre reprodutibilidade

1. O `Makefile` da raiz espera o solucionador em `$CLAW/riemann/src/`. O arquivo
   correspondente está versionado em `solver-referencia/` e precisa ser
   copiado, como indicado acima.
2. As saídas brutas das simulações não estão todas versionadas: os resultados
   agregados (CSV, figuras e metadados) estão, e as séries completas podem ser
   regeneradas com os scripts.
3. O número de células não é o mesmo em todos os conjuntos: a bateria
   paramétrica usa 400 células por padrão e o estudo de refinamento usa de 32 a
   2048, conforme registrado em `resultados/resumo.csv` e
   `resultados_autoconvergencia/autoconvergencia.csv`.
