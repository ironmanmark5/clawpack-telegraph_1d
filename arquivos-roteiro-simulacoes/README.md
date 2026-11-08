# Simulações dos Casos 2 a 8

Esta pasta reúne as cinco rotinas recebidas da orientadora e a execução dos casos descritos na mensagem de 18/09. O Caso 1, de validação e convergência, permanece fora desta bateria. O arquivo `Roteiro-simulacoes.tex` não estava disponível nesta pasta; a lista de parâmetros abaixo foi transcrita do contexto fornecido pelo autor.

## Proveniência e licença

`qinit.f90` e `setrun.py` foram adaptados do exemplo Classic correspondente da árvore do [Clawpack](https://github.com/clawpack/clawpack), projeto dos Clawpack Developers. O código-fonte original é distribuído sob a licença BSD 3-Clause; uma cópia dos avisos e termos está em [`LICENSE-CLAWPACK.txt`](LICENSE-CLAWPACK.txt). As rotinas específicas da equação do telégrafo foram fornecidas pela orientadora ou desenvolvidas/adaptadas para este projeto.

## Como executar

Entre nesta pasta e rode:

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run
python3 executar_casos.py --saida resultados/reproducao_nova
```

Requisitos: `gfortran`, `make`, Python 3.9+, `matplotlib` 3.6+ e a árvore completa do Clawpack. Configure `CLAW` e `PYTHONPATH` como no [guia](../COMO-REPRODUZIR.md). A localização dentro da árvore permite descoberta automática. Também é possível compilar separadamente com `make .exe`. Um teste isolado pode ser feito com `python3 executar_casos.py --casos 2 --saida resultados/teste_novo`.

Para repetir todos os casos com 1024 células e preservar a bateria original de 400 células:

```bash
python3 executar_casos.py --celulas 1024 --saida resultados/malha_1024
python3 gerar_figuras_comparativas.py --dados resultados/malha_1024
```

O executor registra a resolução em `parametros.json` e `resumo.csv` e a confere no frame inicial antes de reutilizar uma execução.

O comando direto `python3 setrun.py` usa 1024 células. O executor dos Casos 2–8 mantém 400 como padrão e passa explicitamente o valor escolhido por `--celulas`.

Cada chamada de simulação recompila o executável `xclaw` a partir dos fontes Classic Clawpack e das rotinas desta pasta. Cada conjunto único de parâmetros é executado uma única vez por bateria. Novas saídas registram hashes dos fontes, do binário e dos dados. Uma execução só é reutilizada quando essas identificações e as validações dos quadros coincidem. Saídas históricas sem proveniência suficiente continuam disponíveis para análise, mas o executor exige outra `--saida` em vez de presumir que vieram do código atual. Não se apagam dados nem se completam manifestos antigos retrospectivamente. Não é necessário editar `setrun.py` entre casos.

Os resultados ficam em `resultados/`, com um diretório por configuração. Cada diretório contém os arquivos `fort.qNNNN` e `fort.tNNNN`, os `claw.data` e `setprob.data` efetivos, `parametros.json`, `amplitude.csv`, `perfis.csv` e `execucao.log`. O índice `casos.json` relaciona cada caso concluído às configurações. `resumo.csv` registra parâmetros e amplitude nos tempos 0,4 e 0,8. As figuras comparativas estão em `resultados/figuras/caso_N.png`, com perfil de u em t=0,4 e amplitude máxima ao longo do tempo. Arquivos `caso_N_t*.png` mostram os perfis em t=0,2, 0,4, 0,6 e 0,8. Os perfis CSV incluem também o frame inicial.

Para gerar as comparações do roteiro a partir de dados existentes, rode `python3 gerar_figuras_comparativas.py --dados resultados/reproducao_nova`. O destino padrão é `<dados>/figuras_comparativas/`; use `--destino outra_pasta` para não substituir figuras e CSVs existentes. São conferidos tempos, geometria, resolução comum e amplitudes antes das comparações. A análise não executa o solver.

## Parâmetros

Todos os casos usam c=2, domínio [-2,2], N=400 por padrão (ou o valor de `--celulas`), tempo final 0,8, 64 intervalos de saída, correção hiperbólica de segunda ordem com limitador MC, `source_split=1` e contornos por extrapolação. A fonte permanece ativa até quando a=b=0 porque também atualiza u por u_t. Os nomes a, b, beta e x0 aparecem nos diretórios para rastrear cada execução.

| Caso | a | b | beta | x0 |
| --- | --- | --- | --- | --- |
| 2 | 0; 0,5; 1; 2 | 0 | 200 | 0 |
| 3 | 0 | 0; 0,5; 1 | 200 | 0 |
| 4 | 1 | 1 | 200 | 0 |
| 5 | 1 | -1 | 200 | 0 |
| 6 | 0,5 | -1 | 25 | 0,5 |
| 7 | 1 | -1 | 25; 50; 100; 200 | 0 |
| 8 | 0; 1; 2 | -1; 0; 1 | 200 | 0 |

São 16 configurações únicas, incluindo uma execução auxiliar para comparar Caso 5 e Caso 6 alterando somente o centro: `a=1`, `b=-1`, `beta=200`, `x0=0` e `x0=0,5`. O Caso 6 do roteiro continua com `a=0,5`, `b=-1`, `beta=25`, `x0=0,5`. Ele usa `z=x-x0` na condição inicial gaussiana e em sua derivada espacial. Seu pulso deslocado se aproxima da fronteira direita por volta de t=0,75; o domínio original foi mantido, portanto os resultados posteriores a esse instante podem incluir influência do contorno. Avalie essa influência antes de interpretá-los como propagação em domínio aberto.

O script mede `A(t)=max_i |u_i(t)|`, máximo discreto das aproximações de médias celulares representadas nos centros. Não calcula a solução analítica para a e b não nulos. As figuras diretas e as figuras comparativas têm finalidades distintas; as comparativas também isolam configurações dos Casos 4 a 6.

## Autoconvergência e resumo expandido

O experimento combinado de erros e ordem de convergência possui automação própria, separada dos Casos 2–8. Usa sete malhas (`32,64,128,256,512,1024,2048`) e compara médias celulares por restrição conservativa, com `c=2`, `a=1`, `b=1`, `beta=200` e `x0=0`.

- [Metodologia, verificações e comandos de reprodução](AUTOCONVERGENCIA.md).
- [Relatório com os resultados calculados](resultados_autoconvergencia/RELATORIO.md).
- [Tabela de erros e ordens em CSV](resultados_autoconvergencia/autoconvergencia.csv).
- [Resumo expandido em PDF e LaTeX para a orientação](resumo_autoconvergencia/README.md).

As saídas brutas e os executáveis permanecem locais; o repositório inclui os resultados agregados, figuras e metadados. Em um clone novo, execute a autoconvergência para gerar as sete simulações antes de usar `--somente-analisar`. Qualquer branch pode ser usada; seu nome é apenas registrado como procedência. Comentários revisados mudam os hashes dos fontes: use uma pasta nova para uma nova bateria e preserve o arquivo histórico.
