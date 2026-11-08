# Revisão conservadora de robustez e documentação

**Data:** 8 de novembro de 2026.

**Estado de partida:** commit `9102c1b`, tag `v1.1.0`, árvore de trabalho limpa.

**Objetivo:** tornar o material do TCC mais claro e seguro para reprodução,
sem mudar o método nem os resultados numéricos já apresentados.

## 1. Restrições adotadas

- Não modificar fórmulas, sinais, autovetores, velocidades, atualizações da
  fonte, inicialização ou integração temporal do solver.
- Não mudar malhas, domínio, coeficientes, CFL, limitadores ou instantes de saída
  dos experimentos documentados.
- Não executar novas simulações, regenerar figuras históricas ou editar o texto
  e os PDFs da monografia.
- Não alterar saídas brutas, CSVs publicados, relatórios históricos, metadados
  de execução ou snapshots dos builds antigos.
- Não reorganizar fisicamente os arquivos existentes: a organização didática
  foi melhorada pelos guias, preservando os caminhos usados no texto.

Esta revisão melhora **clareza, validação e segurança operacional**, não aumenta
a precisão numérica do método. A integração explícita e o splitting originais
foram mantidos.

## 2. O que foi feito e por quê

### Comentários científicos e distinção entre as duas versões

Foram corrigidos os cabeçalhos de `qinit.f90` da raiz e da bateria, que ainda
anunciavam uma rotina padrão que emitiria erro. Agora explicam a inicialização
de `(u,u_t,u_x)` nos centros como aproximação das médias celulares. Experimentos
antigos comentados foram retirados do `qinit.f90` da raiz e a indentação dos
dois laços de inicialização foi uniformizada, sem mudar suas instruções.

Os dois solvers de Riemann tiveram corrigidos os comentários sobre:

- o salto direita menos esquerda;
- os índices `qr(:,i-1)` e `ql(:,i)`;
- os três autovetores e a velocidade nula da onda intermediária.

Não se inverteu o salto do código para acompanhar o comentário antigo errado.
As duas fontes receberam explicações sobre o passo posterior à propagação e
sobre a atualização simultânea com valores guardados. Não se trocaram
declarações, `COMMON`, tipos, expressões ou instruções Fortran.

Os auxiliares exploratórios receberam avisos sobre parâmetros fixos e sobre
a estimativa de derivadas entre quadros. Comentários que anunciavam diferença
centrada ou arquivo EPS foram corrigidos para refletir o que o código faz.
O `setplot.py` da raiz explicita os parâmetros fixos da referência analítica.

O `setprob.f90` da raiz permanece sem alterações em relação à cópia original
armazenada no repositório. `referencia-upstream/` e o diff histórico também
foram preservados. `Makefile_ptwise` foi identificado como legado acústico,
não como alternativa para o sistema de três componentes do trabalho.

### Caso 1: execução sem editar o fonte

`rodar.sh` passou a ser uma interface curta para `executar_caso1.py`:

- valida o número de células e respeita `CLAW_PYTHON`;
- funciona a partir de outro diretório;
- configura `num_cells` em memória, sem usar `sed` sobre `setrun.py`;
- gera entradas em pasta temporária e recusa destinos já existentes;
- confere malha, tempos, finitude e `fort.info` antes de publicar a saída;
- conserva dados temporários e log se uma execução falhar;
- chama o VisClaw diretamente para plotar, sem dependência que possa simular
  novamente;
- oferece `--dry-run`, `--sem-plots` e `--destino`.

O novo argumento opcional `num_cells` de `setrun.py` mantém **2048 como padrão**.
Não houve mudança dos demais parâmetros. O executor não reescreve os `.data`
da raiz nem substitui resultados de uma malha existente.

### Configuração e identificação do ambiente

O Makefile da raiz passou a usar `CLAW_PYTHON`, variável efetivamente consultada
pelo `Makefile.common` do Clawpack. Não foram alteradas flags de compilação.

`verificar-ambiente.sh` agora verifica a importação de `clawutil`/`visclaw`,
a correspondência com `CLAW`, a presença dos componentes necessários e retorna
erro quando há dependências ausentes. Os padrões históricos de configuração
foram mantidos; entradas obviamente inválidas passam a ser rejeitadas.

### Análise de convergência do Caso 1

`convergencia_caso1.py` recebeu validações para geometria, três componentes
finitas, formato ASCII, tempo disponível, domínio e parâmetros comuns.
Expoentes Fortran `D/d` são aceitos.

A ordem usa a razão efetiva dos espaçamentos. Na sequência histórica de
refinamento por dois, a fórmula e os números permanecem os mesmos. Selecionar,
por exemplo, apenas 128 e 512 células não divide mais incorretamente por
`log(2)`. Erros nulos ou não finitos não definem ordem.

A referência da monografia só é aplicada no caso documentado: `t=0,4`,
`c=2`, `beta=200`, domínio `[-2,2]`. As ordens de referência são conferidas
somente nos pares correspondentes. Assim, `--tempo 0.8` não produz falsas
divergências contra uma tabela de outro instante. Divergências reais no caso
de referência passam a produzir código de saída diferente de zero.

### Casos 2–8: validação e reutilização conservadora

`executar_casos.py` passou a verificar entradas efetivas, malha, 65 tempos,
finitude, amplitudes CSV e conclusão em `fort.info`, em vez de conferir apenas
a existência dos arquivos. JSONs/CSVs inválidos não são tratados como saídas
completas.

Para **novas** simulações, são registrados os hashes dos fontes enumerados
pelo Makefile, configuração Python/serialização, binário, comando de build e
checksums das saídas. O build é forçado para não depender de datas quando
flags ou compilador forem diferentes.

A reutilização de uma execução exige identificação compatível. Dados antigos
sem esses campos continuam disponíveis para análise, mas não são presumidos
como produzidos pelos fontes atuais. O executor solicita outra `--saida`.
Não foram inseridos hashes retrospectivos nos manifestos históricos.

O gerador de figuras comparativas valida resolução comum e alinhamento antes
de subtrair curvas, configura o backend `Agg` antes do pyplot e oferece
`--destino` para preservar os produtos publicados. Não se alteraram estilos,
escalas ou valores das curvas históricas e não se regeneraram as figuras.

### Autoconvergência e branches

Foi retirada a exigência literal da branch `tcc-simulacoes`. O nome da branch
continua registrado como procedência do build, sem participar do método.
O gerador de relatório deixou de afirmar automaticamente que a monografia
ainda não incorpora os resultados ou que o repositório não foi publicado.
Os relatórios antigos não foram reescritos.

Após a remoção do bloqueio e a aprovação dos testes, verificou-se no servidor
que `main` e `tcc-simulacoes` apontavam para o mesmo commit `9102c1b`.
A branch redundante foi excluída localmente e no GitHub. A exclusão remota
usou uma condição sobre o hash esperado, para não apagar uma atualização
concorrente. `main`, a tag `v1.1.0` e todos os commits foram preservados.
Referências históricas à branch nos metadados continuam intactas.

### Documentação didática

Foram revisados `README.md`, `COMO-REPRODUZIR.md`, os guias da bateria e os
documentos em `docs/`, com estas distinções explícitas:

- Classic Fortran não é o solver PyClaw;
- instalação por Git exige os submódulos;
- localização dentro de `$CLAW` e cópia do solver para `riemann/src` são
  escolhas deste projeto, não exigências universais do pacote;
- `OUTDIR` nomeia a saída, não configura a malha;
- intervalo entre saídas não é o passo interno adaptativo;
- `make .plots` pode executar o solver; `make plots` apenas plota;
- análise sem simulação ainda pode escrever CSVs, relatórios e figuras;
- dados históricos e uma nova reprodução devem usar destinos distintos;
- numeração e caminhos foram alinhados ao mapa atual do template UFLA.

A versão nominal `5.14.0` foi distinguida dos commits efetivos. Os 11 fontes
Classic utilizados e `clawutil/data.py` foram comparados aos da tag `v5.14.0`
e estavam iguais. Não se atualizou nem substituiu a instalação existente.

## 3. Verificações realizadas

Todas as verificações abaixo foram feitas **sem compilar ou executar Fortran**:

1. **32 testes novos de robustez**, com quadros sintéticos e subprocessos
   substituídos por mocks; passaram.
2. **8 testes sintéticos existentes** de autoconvergência; passaram.
3. Sintaxe dos arquivos Python da aplicação e `bash -n` dos dois scripts shell.
4. Comparação das instruções de **8 rotinas Fortran** antes/depois, removendo
   apenas comentários e diferenças de espaços: instruções idênticas.
5. Comparação dos arquivos `.data` gerados antes/depois para cinco malhas de
   cada versão e para as 16 configurações e sete malhas do estudo: idênticos.
6. Recálculo em memória dos erros do Caso 1: idênticos ao estado anterior;
   quatro ordens conferidas com a referência da monografia.
7. Nova validação dos **1.040 quadros das 16 configurações** históricas: aprovada.
8. Validação dos **455 quadros da autoconvergência**, checksums e recálculo
   dos erros e ordens: idênticos aos CSVs existentes.
9. CLIs conferidas em `--dry-run`, ajuda e reanálises do Caso 1 em `t=0,4`,
   `t=0,8` e com razão de refinamento quatro. Os produtos de teste ficaram
   somente em diretórios temporários externos ao projeto.
10. Hashes SHA-256 de **6.888 arquivos preexistentes protegidos**, incluindo
    saídas, dados agregados, figuras, monografia e materiais de publicação:
    permaneceram idênticos.

Os testes sintéticos verificam a infraestrutura, não substituem validação
física nem uma nova execução completa do solver. A preservação foi sustentada
pela identidade das instruções e das entradas e pela comparação dos arquivos
e cálculos existentes; não se tentou obter uma nova ordem de convergência.

Para executar os testes sem simular:

```bash
# Na raiz:
python3 -B -m unittest discover -s tests -v

# Na pasta da bateria:
cd arquivos-roteiro-simulacoes
python3 -B -m unittest -v test_autoconvergencia.py
```

## 4. O que permanece deliberadamente para depois

- Modernização estrutural do Fortran, unificação das duas versões do solver
  e refatorações extensas.
- Mudanças na integração da fonte, médias iniciais exatas ou novos testes
  físicos/experimentos de contorno.
- Remoção ou movimentação de scripts exploratórios e de dados históricos.
- Nova versão pública, commit e publicação das melhorias. Nesta intervenção
  não foi criado commit nem feito push de código: apenas a exclusão da branch
  remota redundante foi publicada.

**Atenção aos hashes:** alterar comentários também altera a identidade de um
fonte. A assinatura numérica da autoconvergência continua conservadora;
uma nova bateria com os fontes revisados pode exigir outra `--saida`, mesmo
sem mudança das instruções. Isso protege a procedência, não indica mudança
dos resultados antigos. `--somente-analisar` continua aceitando o arquivo
histórico validado, mas reescreve seus produtos derivados se for executado.

## 5. Fontes oficiais consultadas

Documentação Clawpack **5.14.x**, consultada em 8 de novembro de 2026:

- [Instalação Fortran](https://www.clawpack.org/installing_fortcodes.html)
- [Variáveis de ambiente](https://www.clawpack.org/setenv.html)
- [Makefiles](https://www.clawpack.org/makefiles.html) e
  [substituição de rotinas de biblioteca](https://www.clawpack.org/makefiles_library.html)
- [Rotinas de usuário](https://www.clawpack.org/user_routines.html)
- [Solucionadores de Riemann](https://www.clawpack.org/riemann.html)
- [Algoritmos de propagação de ondas](https://www.clawpack.org/wp_algorithms.html)
- [Contornos](https://www.clawpack.org/bc.html)
- [Formato de saída](https://www.clawpack.org/output_styles.html)
- [Nova aplicação](https://www.clawpack.org/newapp.html)
- [Identificação de versões](https://www.clawpack.org/git_versions.html)

A tabela de limitadores da página `setrun.html` consultada apresentava os
códigos 3/4 invertidos. Foram confrontados com os fontes efetivos:
`clawutil/data.py` e `classic/src/1d/inlinelimiter.f90` usam **3 = van Leer,
4 = MC**. A configuração histórica `['mc','mc','mc']`, serializada como
`(4,4,4)`, foi preservada; não se alterou o método para acompanhar esse erro
de documentação externa.
