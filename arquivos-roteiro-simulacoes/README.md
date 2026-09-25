# Simulações dos Casos 2 a 8

Esta pasta reúne as cinco rotinas recebidas da orientadora e a execução dos casos descritos na mensagem de 18/09. O Caso 1, de validação e convergência, permanece fora desta bateria. O arquivo `Roteiro-simulacoes.tex` não estava disponível nesta pasta; a lista de parâmetros abaixo foi transcrita do contexto fornecido pelo autor.

## Como executar

Entre nesta pasta e rode:

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run
python3 executar_casos.py
```

Requisitos: `gfortran`, `make`, Python 3, `matplotlib` e a árvore do Clawpack na posição atual do projeto. O script usa a versão local do pacote Python do Clawpack. Também é possível compilar separadamente com `make .exe`. Um teste isolado pode ser feito com `python3 executar_casos.py --casos 2`.

A primeira execução compila o executável `xclaw` a partir dos fontes Classic Clawpack e das rotinas desta pasta. Cada conjunto único de parâmetros é executado uma única vez. Execuções completas são reutilizadas em chamadas posteriores; saídas incompletas causam erro para evitar reaproveitar dados duvidosos. Não é necessário editar `setrun.py` entre casos.

Os resultados ficam em `resultados/`, com um diretório por configuração. Cada diretório contém os arquivos `fort.qNNNN` e `fort.tNNNN`, os `claw.data` e `setprob.data` efetivos, `parametros.json`, `amplitude.csv`, `perfis.csv` e `execucao.log`. O índice `casos.json` relaciona cada caso concluído às configurações. `resumo.csv` registra parâmetros e amplitude nos tempos 0,4 e 0,8. As figuras comparativas estão em `resultados/figuras/caso_N.png`, com perfil de u em t=0,4 e amplitude máxima ao longo do tempo. Arquivos `caso_N_t*.png` mostram os perfis em t=0,2, 0,4, 0,6 e 0,8. Os perfis CSV incluem também o frame inicial.

Para gerar uma pasta separada com as comparações do roteiro, rode `python3 gerar_figuras_comparativas.py`. Isso usa as simulações já concluídas e cria `resultados/figuras_comparativas/`, com figuras PNG e PDF, tabelas de amplitude nos tempos comuns e matrizes do Caso 8. A pasta inclui as comparações entre configurações dos Casos 4 e 5 e as condições iniciais dos Casos 6 e 7.

## Parâmetros

Todos os casos usam c=2, domínio [-2,2], N=400, tempo final 0,8, 64 intervalos de saída, correção hiperbólica de segunda ordem com limitador MC, `source_split=1` e contornos por extrapolação. A fonte permanece ativa até quando a=b=0 porque também atualiza u por u_t. Os nomes a, b, beta e x0 aparecem nos diretórios para rastrear cada execução.

| Caso | a | b | beta | x0 |
| --- | --- | --- | --- | --- |
| 2 | 0; 0,5; 1; 2 | 0 | 200 | 0 |
| 3 | 0 | 0; 0,5; 1 | 200 | 0 |
| 4 | 1 | 1 | 200 | 0 |
| 5 | 1 | -1 | 200 | 0 |
| 6 | 0,5 | -1 | 25 | 0,5 |
| 7 | 1 | -1 | 25; 50; 100; 200 | 0 |
| 8 | 0; 1; 2 | -1; 0; 1 | 200 | 0 |

São 15 configurações únicas. O Caso 6 utiliza `z=x-x0` na condição inicial gaussiana e em sua derivada espacial. Seu pulso deslocado se aproxima da fronteira direita por volta de t=0,75; o domínio original foi mantido, portanto os resultados posteriores a esse instante podem incluir influência do contorno. Avalie essa influência antes de interpretá-los como propagação em domínio aberto.

O script mede `A(t)=max_i |u_i(t)|`, isto é, máximo discreto nos centros das células. Não calcula a solução analítica para a e b não nulos. Os gráficos dos casos 4 a 6 mostram uma única curva em cada painel; nos outros casos fazem as comparações pedidas.
