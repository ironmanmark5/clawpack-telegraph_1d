# O que foi feito, onde e por quê

Este documento descreve, arquivo por arquivo, o que foi alterado em relação ao
*Clawpack*, para que qualquer leitor da monografia consiga reproduzir o
trabalho. Ele corresponde, em forma resumida, ao Apêndice A da monografia.

## Ponto de partida

O trabalho parte do exemplo `classic/examples/acoustics_1d_example1`,
distribuído com o *Clawpack* (versão 5.14.0, árvore `v5.14.0-17-gc5b4fbe`),
que resolve um sistema acústico linear de duas ondas com um solucionador de
Riemann próprio. Esse exemplo foi adaptado para a equação do telegrafista,
escrita como um sistema de primeira ordem com três componentes e três ondas
(velocidades $-c$, $0$ e $c$).

As cópias não modificadas dos arquivos de origem estão em
[`referencia-upstream/`](../referencia-upstream/LEIA-ME.md), e as diferenças
linha a linha estão em
[`docs/DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff`](DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff).

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
| `setprob.f90` (raiz) | `acoustics_1d_example1/setprob.f90` | **sem alteração**: lê $\rho$, $K$ e $\beta$ e calcula $c = \sqrt{K/\rho}$ | manter a formulação acústica, em que $a = b = 0$ |
| `qinit.f90` (raiz) | `acoustics_1d/qinit.f90` | $q_1 = e^{-\beta x^2}$, $q_2 = 0$, $q_3 = -2\beta x\,e^{-\beta x^2}$ | definir a condição inicial gaussiana centrada na origem |
| `src1.f90` (raiz) | `acoustics_1d/src1.f90` | somente $q_1 \leftarrow q_1 + \Delta t\,q_2$ | avançar $u$ por meio de $u_t$, já que o termo $b q_1 - a q_2$ se anula |
| `solver-referencia/rp1_telegraph.f90` | `riemann/src/rp1_acoustics.f90` | três ondas, com autovalores $-c$, $0$ e $c$, e autovetores do sistema do telegrafista; parâmetros $\rho$ e $K$ | resolver o problema de Riemann do sistema; precisa ser copiado para `$CLAW/riemann/src/` |
| `arquivos-roteiro-simulacoes/setprob.f90` | versão da raiz | leitura de $c$, $a$, $b$, $\beta$ e $x_0$; bloco comum `/cparam/ c,a,b` | incorporar amortecimento, reação e o centro do pulso |
| `arquivos-roteiro-simulacoes/qinit.f90` | versão da raiz | $z = x - x_0$ na gaussiana e em sua derivada | permitir o pulso deslocado (Caso 6) e a variação de largura (Caso 7) |
| `arquivos-roteiro-simulacoes/src1.f90` | versão da raiz | guarda $q_1$ e $q_2$ anteriores e atualiza as duas componentes: $q_2 \leftarrow q_2 + \Delta t\,(b q_1 - a q_2)$ | resolver a equação completa, com os dois termos do modelo |
| `arquivos-roteiro-simulacoes/rp1_telegraph.f90` | `solver-referencia` | parâmetros $c$, $a$ e $b$ no lugar de $\rho$ e $K$ | alinhar o solucionador à formulação do telegrafista; o `Makefile` da bateria compila esta cópia **na própria pasta**, sem precisar copiá-la para `$CLAW/riemann/src/` |
| `arquivos-roteiro-simulacoes/setrun.py` | `setrun.py` da raiz | parâmetros $c$, $a$, $b$, $\beta$, $x_0$ e número de células como argumentos, com valores padrão | executar os casos do roteiro sem editar o arquivo |
| `arquivos-roteiro-simulacoes/executar_casos.py` | novo | executa cada configuração de parâmetros, verifica as saídas e registra os metadados | automatizar e tornar reprodutível a bateria de casos |
| `arquivos-roteiro-simulacoes/gerar_figuras_comparativas.py` | novo | comparações lado a lado entre configurações e casos | produzir as figuras dos Casos 2 a 8 |
| `arquivos-roteiro-simulacoes/autoconvergencia.py` | novo | executa as sete malhas, restringe a solução fina à grossa e calcula erros e ordens | estudar a convergência com o termo fonte ativo |
| `arquivos-roteiro-simulacoes/test_autoconvergencia.py` | novo | testes sintéticos da rotina de erro e ordem | verificar a automação independentemente do solver |

## Resumo histórico das diferenças linha a linha

As contagens e o diff arquivado abaixo descrevem a adaptação anterior à
revisão de robustez. Foram preservados como referência, não regenerados para
reescrever a história. Os ajustes posteriores, sem mudança das instruções
Fortran, estão em [`REVISAO-DE-ROBUSTEZ.md`](REVISAO-DE-ROBUSTEZ.md).

| Arquivo | Linhas alteradas | O que muda, em resumo |
| --- | --- | --- |
| `setrun.py` | +8 / −8 | domínio de $[-1,1]$ para $[-2,2]$; 2048 células; três equações e três ondas; limitador MC nas três famílias; 64 instantes de saída; `source_split = 1` |
| `setprob.f90` | 0 / 0 | nenhuma alteração; o caso da raiz mantém a leitura de $\rho$, $K$ e $\beta$ |
| `qinit.f90` | +11 / −2 | preenche as três componentes com a gaussiana e sua derivada |
| `setplot.py` | +30 / −6 | rótulos e visualização direta de $u$ e $u_t$ |
| `Makefile` | +6 / −2 | aponta para `rp1_telegraph.f90` em vez de `rp1_acoustics.f90`; a revisão posterior corrige o interpretador para `CLAW_PYTHON ?= python3` |
| `src1.f90` | +12 / −11 | substitui a rotina vazia do pacote pela atualização de $u$ |
| `solver-referencia/rp1_telegraph.f90` | +57 / −34 | solucionador de três ondas, com autovalores $-c$, $0$ e $c$, e cabeçalho comentado atualizado |

O diff unificado completo, com o número de cada linha alterada, está em
[`docs/DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff`](DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff).

## Arquivos adicionados ao repositório

Além das adaptações acima, o trabalho reúne arquivos que **não existem** no
pacote original:

| Arquivo | Onde deve ficar | Por quê |
| --- | --- | --- |
| `solver-referencia/rp1_telegraph.f90` | `$CLAW/riemann/src/` | o `Makefile` procura o solucionador fora da pasta do exemplo |
| `gerar_figuras_caso1.py` | raiz | gera as figuras 6.1 e 6.2 a partir das séries `output_malha_*` |
| `convergencia_caso1.py` | raiz | calcula erros e ordens do Caso 1 contra a solução de d'Alembert |
| `arquivos-roteiro-simulacoes/setrun.py` | pasta da bateria | recebe $c$, $a$, $b$, $\beta$ e $x_0$ como argumentos |
| `arquivos-roteiro-simulacoes/{qinit,setprob,src1}.f90` | pasta da bateria | condição inicial deslocada e fonte com os dois coeficientes |
| `arquivos-roteiro-simulacoes/rp1_telegraph.f90` | permanece na pasta da bateria | mesma solução de Riemann, com $c$, $a$ e $b$ lidos do modelo; o `Makefile` local compila este arquivo |
| `arquivos-roteiro-simulacoes/executar_casos.py` | pasta da bateria | executa os Casos 2 a 8 e registra metadados |
| `arquivos-roteiro-simulacoes/gerar_figuras_comparativas.py` | pasta da bateria | gera as figuras 6.3 a 6.13 e as tabelas 6.2 a 6.7 |
| `arquivos-roteiro-simulacoes/autoconvergencia.py` | pasta da bateria | executa as sete malhas e gera as figuras 6.14 a 6.16 e a tabela 6.8 |
| `arquivos-roteiro-simulacoes/test_autoconvergencia.py` | pasta da bateria | testes sintéticos da automação |

O mapa entre cada figura e tabela da monografia e o script que a gera está em
[`docs/MAPA-DE-FIGURAS.md`](MAPA-DE-FIGURAS.md).

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
export PYTHONPATH="$CLAW${PYTHONPATH:+:$PYTHONPATH}"
```

Para a bateria de casos (Casos 2 a 8):

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run     # confere a lista antes de executar
python3 executar_casos.py --saida resultados/reproducao_nova
python3 gerar_figuras_comparativas.py --dados resultados/reproducao_nova
```

Para o estudo de refinamento, que executa as sete malhas:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py --saida resultados_autoconvergencia_nova
python3 autoconvergencia.py --somente-analisar --saida resultados_autoconvergencia_nova
```

Para a verificação da implementação (Caso 1, $a = b = 0$), na raiz do
repositório, copie antes o solucionador para o local previsto pelo `Makefile`:

```bash
cp solver-referencia/rp1_telegraph.f90 "$CLAW/riemann/src/"
./rodar.sh 512 --sem-plots
```

As séries do Caso 1 nascem da repetição dessa última etapa com diferentes
números de células. O executor configura a malha em memória sem editar o
fonte; o nome do diretório, sozinho, não determina a resolução. Saídas
existentes são recusadas; use `--destino` para preservar a bateria original.

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
