# Dados, nomes e correspondência com a monografia

Este documento explica como ler os arquivos de resultado e como cada
configuração de simulação se liga às seções, figuras e tabelas da monografia.

## 1. Nomes das configurações

Cada diretório de caso em `arquivos-roteiro-simulacoes/resultados/` recebe um
identificador com os parâmetros usados, no formato
`a<valor>_b<valor>_beta<valor>_x0<valor>`. A convenção é a seguinte:

| Trecho | Significado | Exemplos |
| --- | --- | --- |
| `a0`, `a0p5`, `a1`, `a2` | valor do coeficiente de amortecimento $a$; `p` indica a vírgula decimal | `a0p5` = $a = 0{,}5$ |
| `b0`, `b0p5`, `b1`, `bm1` | valor do coeficiente de reação $b$; `m` indica sinal negativo | `bm1` = $b = -1$ |
| `beta25`, `beta50`, `beta100`, `beta200` | largura da gaussiana inicial | `beta200` = $\beta = 200$ |
| `x00`, `x00p5` | centro inicial do pulso | `x00p5` = $x_0 = 0{,}5$ |

Assim, `a1_bm1_beta200_x00` é o Caso 5: $a = 1$, $b = -1$, $\beta = 200$ e
$x_0 = 0$.

## 2. Arquivos de cada configuração

| Arquivo | Conteúdo |
| --- | --- |
| `fort.qNNNN` e `fort.tNNNN` | Estado e tempo de cada instante de saída, no formato ASCII do Clawpack; 65 pares por execução |
| `claw.data` e `setprob.data` | Parâmetros efetivamente usados na execução, gerados a partir do `setrun.py` |
| `parametros.json` | Registro da execução, com a malha, os tempos e os identificadores |
| `amplitude.csv` | `frame, t, A_max_abs_u`: amplitude máxima $A(t) = \max_i |u_i(t)|$ em cada quadro |
| `perfis.csv` | `frame, t, x, u, u_t, u_x`: as três componentes do estado em cada célula |
| `execucao.log` | Saída do solver, útil para diagnóstico |

## 3. Arquivos agregados

| Arquivo | Colunas ou formato | Para que serve |
| --- | --- | --- |
| `resultados/resumo.csv` | `caso, id, c, a, b, beta, x0, N, tfinal, A_t0p4, A_t0p8` | Índice de todas as configurações, com a amplitude máxima em $t = 0{,}4$ e $t = 0{,}8$ |
| `resultados/casos.json` | Caso → lista de identificadores | Relaciona cada caso do roteiro às configurações executadas |
| `resultados/figuras_comparativas/amplitudes_tempos_comuns.csv` | `caso, id, a, b, beta, x0, t, A_max_abs_u` | Amplitude nos instantes comuns 0,2; 0,4; 0,6 e 0,8, base das tabelas dos Casos 2, 3 e 7 |
| `resultados/figuras_comparativas/caso_8_t0p4_matriz.csv` e `caso_8_t0p8_matriz.csv` | Matriz com $a$ nas linhas e $b$ nas colunas | Tabelas do Caso 8 nos dois instantes |
| `resultados_autoconvergencia/autoconvergencia.csv` | `N, dx, tempo, E_u, p_u, E_ut, p_ut` | Erros de refinamento e ordens observadas |
| `resultados_autoconvergencia/experimento.json` | JSON | Parâmetros, versões, compilador e hashes dos fontes da execução |
| `resultados_autoconvergencia/testes_sinteticos.json` | JSON | Resultado dos testes da rotina de erro, independentes do solver |
| `resultados_autoconvergencia/ordens_diagnostico.json` | JSON | Razões registradas para erros ou ordens indisponíveis |
| `resultados/convergencia_caso1/convergencia_caso1.csv` | `N, dx, tempo, e_l2_u, e_l2_u_media, e_inf_u, p_l2_u, e_l2_ut, e_inf_ut, p_l2_ut, e_l2_ux, e_inf_ux, p_l2_ux` | Erros e ordens do Caso 1, incluindo $u_t$ e $u_x$ |
| `resultados/convergencia_caso1/convergencia_caso1_loglog.png` e `.pdf` | Figura | Erro $L^2$ em função de $\Delta x$, com declives de referência 1 e 2 |

## 3.1 Scripts de pós-processamento

| Script | Função |
| --- | --- |
| `convergencia_caso1.py` | Erros e ordens do Caso 1, com CSV e gráfico log–log; confere os valores contra os da monografia |
| `arquivos-roteiro-simulacoes/executar_casos.py` | Executa os Casos 2 a 8 e registra parâmetros, amplitudes e perfis |
| `arquivos-roteiro-simulacoes/gerar_figuras_comparativas.py` | Monta as figuras e tabelas comparativas dos Casos 2 a 8 |
| `arquivos-roteiro-simulacoes/autoconvergencia.py` | Estudo de refinamento com o termo fonte ativo |

Os scripts `comparar_malhas.py`, `plot_tensao.py`, `plot_evolucao_temporal.py`
e `derivada_e_tensao.py`, na raiz, são material exploratório das primeiras
etapas do trabalho. Eles geraram as figuras de verificação
(`resultados/telegrafista_t_0.20.png`, `0.40` e `0.60`, e as comparações de
malhas), mas têm uma limitação conhecida: estimam $u_t$ por diferença entre
snapshots consecutivos, o que introduz erro de primeira ordem no tempo. A
componente $u_t$ usada na monografia é a **segunda componente do estado**
(`q2`), lida diretamente dos arquivos de saída, como fazem
`convergencia_caso1.py` e o script de autoconvergência.

## 4. Correspondência com a monografia

| Caso | Configurações | Seção | Figuras e tabelas |
| --- | --- | --- | --- |
| 1 — verificação, $a = b = 0$ | séries da raiz, $N = 128$ a $2048$ | 5.1 | Figuras 2 e 3, Tabela 4 |
| 2 — amortecimento, $b = 0$ | `a0`, `a0p5`, `a1`, `a2` | 5.2 | Figura 4, Tabela 5 |
| 3 — termo reativo, $a = 0$ | `b0`, `b0p5`, `b1` | 5.3 | Figura 5, Tabela 6 |
| 4 — combinado, $a = b = 1$ | `a1_b1_beta200_x00` | 5.4 | Figura 6, Tabela 7 |
| 5 — restaurador, $a = 1$, $b = -1$ | `a1_bm1_beta200_x00` | 5.5 | Figura 7, Tabela 7 |
| 6 — pulso deslocado | `a0p5_bm1_beta25_x00p5` e a auxiliar `a1_bm1_beta200_x00p5` | 5.6 | Figuras 8, 9 e 10 |
| 7 — largura da condição inicial | `a1_bm1_beta25/50/100/200_x00` | 5.7 | Figuras 11 e 12, Tabela 8 |
| 8 — grade $a \times b$ | nove configurações com $a \in \{0;1;2\}$ e $b \in \{-1;0;1\}$ | 5.8 | Figuras 13 e 14, Tabelas 9 e 10 |
| Autoconvergência | sete malhas, $a = b = 1$ | 5.9 | Figuras 15, 16 e 17, Tabela 11 |

A numeração de figuras e tabelas acima é a da versão provisória do texto; na
versão montada sobre o template oficial da UFLA, figuras e tabelas recebem
numeração por seção, como "Figura 5.3".

## 5. Configuração numérica

Os parâmetros comuns às execuções são: domínio $[-2, 2]$, tempo final $0{,}8$,
64 intervalos de saída mais o estado inicial, CFL desejado $0{,}9$, correção
hiperbólica de segunda ordem com limitador MC configurado como $(4,4,4)$,
separação de Godunov para o termo fonte (`source_split = 1`) e contornos por
extrapolação nas duas extremidades.

A ordem de leitura do `setprob.data` é `c`, `a`, `b`, `beta`, `x0` na bateria
do roteiro. No exemplo da raiz, que resolve o caso $a = b = 0$, a ordem é
`rho`, `K`, `beta`, com $c = \sqrt{K/\rho}$.

## 6. Duas variantes do solucionador

O repositório contém duas variantes da mesma rotina de Riemann:

- `arquivos-roteiro-simulacoes/rp1_telegraph.f90`, usada na bateria e no estudo
  de refinamento, lê $c$, $a$ e $b$ no bloco comum `/cparam/`;
- `solver-referencia/rp1_telegraph.f90`, usada nos resultados de verificação,
  lê $\rho$ e $K$ e calcula $c = \sqrt{K/\rho}$.

A segunda precisa ser copiada para `$CLAW/riemann/src/`, que é o local previsto
pelo `Makefile` da raiz para os solucionadores compartilhados.
