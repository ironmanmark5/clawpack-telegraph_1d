# Autoconvergência do experimento combinado

O estudo usa exclusivamente os fontes desta pasta. A versão antiga na raiz não participa da compilação. A equação é `u_tt + a*u_t = c²*u_xx + b*u`, com `q=(u,u_t,u_x)` e fonte `(q2,b*q1-a*q2,0)`. `setprob.f90` lê `c,a,b,beta,x0` nessa ordem. `qinit.f90` avalia a gaussiana e sua derivada no centro da célula; essa inicialização foi preservada.

São executadas somente `N=32,64,128,256,512,1024,2048`, com `c=2,a=1,b=1,beta=200,x0=0`. O domínio é `[-2,2]`, `tfinal=0.8`, CFL desejado `0.9`, passo variável, `order=2`, limitadores MC, `source_split=1`, contornos por extrapolação e 64 intervalos de saída com estado inicial. A fonte existente permanece ativa.

## Executar e reproduzir

A partir desta pasta:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py
```

O Clawpack é localizado por `--claw`, pela variável `CLAW`, pelo pacote Python instalado ou por uma instalação válida em diretórios ancestrais. Para indicar uma instalação explicitamente:

```bash
python3 autoconvergencia.py --claw /caminho/para/clawpack
```

Os requisitos são Python 3, matplotlib, make, gfortran e a árvore de fontes do Clawpack Classic. O script usa somente o ambiente existente. `--fc` seleciona o compilador; `--fflags=-O2` registra as flags usadas. Não cria ambientes virtuais nem instala dependências.

As saídas ficam em `resultados_autoconvergencia/`, com diretórios `simulacoes/N0032_a1_b1_beta200_x0`, etc. `--saida outra_pasta` é relativo à localização desta aplicação. Identificadores incluem N. O script recompila à força em `build/`, usando cópias dos fontes locais e de todos os fontes Classic enumerados pelo Makefile. Não sobrescreve o executável nem as saídas dos Casos 2–8.

Uma execução só é reutilizada após conferir parâmetros, hashes dos fontes/executável/saídas, dimensões, inicialização, todos os tempos e finitude. Saídas incompletas ou incompatíveis causam erro e são preservadas; use outra `--saida` para uma nova implementação. Para recalcular apenas as tabelas e figuras dos dados já existentes:

```bash
python3 autoconvergencia.py --somente-analisar
```

`--testes` executa apenas os três testes sintéticos exigidos, sem compilar ou simular. Falhas de build ou execução ficam em `bloqueio.json`, `RELATORIO_BLOQUEIO.md` e nos logs; dados ausentes não são preenchidos.

## Medida e convenção da tabela

O arquivo `calculo_erro_ordem.tex` recebido da orientadora fornece a referência metodológica. Neste solver de volumes finitos, N conta células físicas e as saídas são aproximações de médias celulares. `out1.f` escreve somente `i=1,...,mx`; o campo `nghost` no cabeçalho não indica linhas fantasma nos dados. São recuperados `mx`, `xlow`, `dx` de `fort.qNNNN` e o tempo de `fort.tNNNN`, aproveitando o leitor de `executar_casos.py`.

A solução fina é restrita com `R(q)[i]=(q[2*i]+q[2*i+1])/2`, separadamente para u e u_t. As fronteiras de células devem coincidir, o fator de refinamento é dois e os dados são comparados no mesmo tempo registrado, `t=0.8`. Não há seleção de pontos alternados nem comparação direta de arrays de tamanhos diferentes.

`E(N)=sqrt(mean((R(q_2N)-q_N)**2))` é o erro L2 discreto normalizado entre malhas, sem subtrair a média das diferenças. `p(N)=log(E(N)/E(2N))/log(2)` exige N,2N,4N. A linha N contém E(N) e p(N). A referência mostra os erros na linha seguinte; aqui a convenção é explicitamente a solicitada pelo autor.

Há seis erros (N=32,...,1024) e cinco ordens (N=32,...,512), por componente. E(2048), p(1024) e p(2048) ficam indisponíveis. O CSV usa `NaN` e a tabela LaTeX usa `--`. Erros nulos, não finitos ou abaixo de `100*epsilon*max(1,|q|)` tornam a ordem indisponível com razão registrada. Esse limiar usa a escala das soluções da trinca. Nenhum dado ausente é substituído por zero.

## Produtos e diagnósticos

O [resumo expandido para a orientação](resumo_autoconvergencia/README.md) está em `resumo_autoconvergencia/`, com PDF, fonte LaTeX e pacote para Overleaf. O [relatório completo](resultados_autoconvergencia/RELATORIO.md) e os [dados tabulados](resultados_autoconvergencia/autoconvergencia.csv) estão em `resultados_autoconvergencia/`.

São versionados os resultados agregados, as figuras e os metadados do estudo. As pastas `build/`, `simulacoes/` e `.mplconfig/` são ignoradas pelo Git e permanecem locais. Em um clone novo, execute primeiro `python3 autoconvergencia.py` para produzir as sete saídas; `--somente-analisar` requer essas saídas brutas, que não estão incluídas no resumo ou no repositório remoto.

- `autoconvergencia.csv`: `N,dx,tempo,E_u,p_u,E_ut,p_ut`.
- `tabela_autoconvergencia.tex`: tabela para inclusão manual, com notação científica.
- `erros_loglog.png/pdf`, `perfis_u.png/pdf`, `perfis_ut.png/pdf`.
- `RELATORIO.md`: resultados reais, metodologia e limites da interpretação.
- `testes_sinteticos.json`: testes separados dos resultados do solver.
- `ordens_diagnostico.json`: razões para erros/ordens indisponíveis.
- `experimento.json`, snapshots e `compilacao.log`: commit, estado local, Clawpack, compilador e fontes efetivamente usados.
- Em cada execução: `execucao.json`, `execucao.log`, `passos.csv`, `claw.data`, `setprob.data`, `fort.info` e 65 pares `fort.qNNNN`/`fort.tNNNN`.

O único ajuste de diagnóstico é `verbosity=1`, para capturar tentativas e passos aceitos sem alterar o esquema. O stdout arredonda dt/t a cinco algarismos significativos e CFL a três casas decimais. `fort.info` é preservado, mas seus extremos de dt podem incluir candidatos ainda não usados; os extremos efetivos são calculados dos passos aceitos do log. O CFL desejado não é confundido com o observado, especialmente nas malhas grossas limitadas pelo intervalo entre saídas.

O estudo mede o esquema completo com refinamento espacial e temporal acoplados. A correção hiperbólica de segunda ordem, os limitadores, o splitting de primeira ordem e Euler explícito da fonte participam do resultado. A ordem dois não é imposta. Não há incorporação automática à monografia nem publicação dos arquivos.
