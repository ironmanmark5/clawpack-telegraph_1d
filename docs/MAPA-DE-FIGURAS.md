# Mapa das figuras e tabelas da monografia

Este documento responde a uma pergunta prática: **qual script gera cada
figura e cada tabela do texto, a partir de qual arquivo de dados, e com qual
comando**. A numeração da primeira coluna é a que aparece na monografia.

As figuras saem em PDF (vetorial, usado no texto) e PNG (prévia). No texto da
monografia, cada uma aparece com um nome próprio — `fig_caso2_a_t040.pdf`,
por exemplo —, diferente do nome gerado pelo script. A segunda coluna dá o
nome usado no texto e a terceira, o arquivo gerado por este repositório.

## Os três canais de geração

| Canal | Script | Entrada | Saída |
| --- | --- | --- | --- |
| Caso 1 (verificação, $a=b=0$) | `gerar_figuras_caso1.py` | `output_malha_{128,256,512,1024,2048}/` e a solução de d'Alembert | `resultados/figuras/` |
| Casos 2 a 8 | `arquivos-roteiro-simulacoes/gerar_figuras_comparativas.py` | `arquivos-roteiro-simulacoes/resultados/<caso>/` | `arquivos-roteiro-simulacoes/resultados/figuras_comparativas/` |
| Autoconvergência | `arquivos-roteiro-simulacoes/autoconvergencia.py` | as sete malhas `resultados_autoconvergencia/malha_*` | `arquivos-roteiro-simulacoes/resultados_autoconvergencia/` |

## Figuras

| Figura | Arquivo na monografia | Gerado em | Script | Dados de entrada |
| --- | --- | --- | --- | --- |
| 6.1 | `fig_caso1_t020.pdf` | `resultados/figuras/fig_caso1_t020.pdf` | `gerar_figuras_caso1.py` | cinco séries `output_malha_*` |
| 6.2 | `fig_caso1_t040.pdf` | `resultados/figuras/fig_caso1_t040.pdf` | `gerar_figuras_caso1.py` | idem |
| 6.3 | `fig_caso2_a_t040.pdf` | `figuras_comparativas/caso_2_t0p4.pdf` | `gerar_figuras_comparativas.py` | `a0_b0`, `a0p5_b0`, `a1_b0`, `a2_b0` |
| 6.4 | `fig_caso3_b_t040.pdf` | `figuras_comparativas/caso_3_t0p4.pdf` | `gerar_figuras_comparativas.py` | `a0_b0`, `a0_b0p5`, `a0_b1` |
| 6.5 | `fig_caso4_quatro_t040.pdf` | `figuras_comparativas/caso_4_quatro_configuracoes_t0p4.pdf` | `gerar_figuras_comparativas.py` | `(0,0)`, `(1,0)`, `(0,1)`, `(1,1)` |
| 6.6 | `fig_caso5_b_t040.pdf` | `figuras_comparativas/caso_5_comparacao_b_t0p4.pdf` | `gerar_figuras_comparativas.py` | `a1_bm1`, `a1_b0`, `a1_b1` |
| 6.7 | `fig_caso6_ci.pdf` | `figuras_comparativas/caso_6_condicoes_iniciais.pdf` | `gerar_figuras_comparativas.py` | condição A e condição B |
| 6.8 | `fig_caso6_evolucao.pdf` | `figuras_comparativas/caso_6_evolucao.pdf` | `gerar_figuras_comparativas.py` | `a0p5_bm1_beta25_x00p5`, quadros 0 a 64 |
| 6.9 | `fig_caso6_vs_caso5_t040.pdf` | `figuras_comparativas/caso_6_versus_caso_5_t0p4.pdf` | `gerar_figuras_comparativas.py` | `a1_bm1_beta200_x0` com $x_0=0$ e $0{,}5$ |
| 6.10 | `fig_caso7_ci.pdf` | `figuras_comparativas/caso_7_condicoes_iniciais.pdf` | `gerar_figuras_comparativas.py` | quatro valores de $\beta$ |
| 6.11 | `fig_caso7_beta_t040.pdf` | `figuras_comparativas/caso_7_beta_t0p4.pdf` | `gerar_figuras_comparativas.py` | `a1_bm1` com $\beta=25,50,100,200$ |
| 6.12 | `fig_caso8_por_a_t040.pdf` | `figuras_comparativas/caso_8_por_a_t0p4.pdf` | `gerar_figuras_comparativas.py` | grade $a \times b$ |
| 6.13 | `fig_caso8_dif_vs_b0.pdf` | `figuras_comparativas/caso_8_diferencas_vs_b0.pdf` | `gerar_figuras_comparativas.py` | mesmos casos do Caso 8 |
| 6.14 | `fig_autoconv_loglog.pdf` | `resultados_autoconvergencia/erros_loglog.pdf` | `autoconvergencia.py` | sete malhas, $a=1$, $b=1$ |
| 6.15 | `fig_autoconv_perfis_u.pdf` | `resultados_autoconvergencia/perfis_u.pdf` | `autoconvergencia.py` | idem |
| 6.16 | `fig_autoconv_perfis_ut.pdf` | `resultados_autoconvergencia/perfis_ut.pdf` | `autoconvergencia.py` | idem |

## Tabelas

| Tabela | Conteúdo | Gerado por | Arquivo de dados |
| --- | --- | --- | --- |
| 6.1 | erro e ordem do Caso 1, $t=0{,}40$ | `convergencia_caso1.py` | `resultados/convergencia_caso1/convergencia_caso1.csv` |
| 6.2 | amplitude máxima do Caso 2 | `executar_casos.py` | `resultados/<caso>/amplitude.csv` |
| 6.3 | amplitude máxima do Caso 3 | `executar_casos.py` | `resultados/<caso>/amplitude.csv` |
| 6.4 | comparação entre configurações | `gerar_figuras_comparativas.py` | `figuras_comparativas/amplitudes_tempos_comuns.csv` |
| 6.5 | amplitude máxima do Caso 7 | `gerar_figuras_comparativas.py` | `figuras_comparativas/amplitudes_tempos_comuns.csv` |
| 6.6 | grade $a\times b$ em $t=0{,}40$ | `gerar_figuras_comparativas.py` | `figuras_comparativas/caso_8_t0p4_matriz.csv` |
| 6.7 | grade $a\times b$ em $t=0{,}80$ | `gerar_figuras_comparativas.py` | `figuras_comparativas/caso_8_t0p8_matriz.csv` |
| 6.8 | autoconvergência com fonte ativa | `autoconvergencia.py` | `resultados_autoconvergencia/autoconvergencia.csv` |

## Comandos

```bash
# Figuras do Caso 1 (precisa das séries output_malha_* na raiz)
python3 gerar_figuras_caso1.py

# Figuras e tabelas dos Casos 2 a 8 (precisa das simulações já executadas)
cd arquivos-roteiro-simulacoes
python3 gerar_figuras_comparativas.py

# Autoconvergência: executa as sete malhas e gera figuras, CSV e tabela LaTeX
python3 autoconvergencia.py --claw "$CLAW"

# Se as malhas já existem, apenas analisar e gerar as figuras
python3 autoconvergencia.py --somente-analisar
```

## Observações

- Os nomes dos arquivos gerados e os nomes usados na monografia diferem
  porque as figuras foram copiadas e renomeadas ao serem integradas ao
  texto. A tabela acima é o mapa entre os dois.
- As figuras 6.1 e 6.2 usam as séries de refinamento da raiz do repositório,
  e não a pasta `arquivos-roteiro-simulacoes`, porque o Caso 1 é o caso de
  verificação, com solução exata.
- As figuras 6.14 a 6.16 vêm do estudo de autoconvergência, que executa as
  sete malhas e compara soluções entre malhas — não há solução analítica
  nesse caso.
- `convergencia_caso1.py` também produz `convergencia_caso1_loglog.pdf`, que
  não é usada no texto; a figura em escala logarítmica que aparece na
  monografia (6.14) é a do estudo com o termo fonte ativo.
