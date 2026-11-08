# Como reproduzir este trabalho

Este guia separa **instalar**, **simular** e **analisar dados existentes**.
O cálculo é feito pelo **Classic 1D em Fortran**; Python configura entradas,
automatiza execuções e analisa/visualiza saídas. Não é uma aplicação do solver
PyClaw. Os três caminhos de resultados estão em
[`docs/MAPA-DE-FIGURAS.md`](docs/MAPA-DE-FIGURAS.md).

> Os comandos de simulação abaixo são para reprodução. Não é necessário
> executá-los para consultar os CSVs e as figuras publicados. Preserve uma
> cópia dos resultados antes de qualquer reanálise que escreva arquivos.

## 1. Preparar a dependência e o projeto

Requisitos: Git, `make`, compilador Fortran 90 (o trabalho usa `gfortran`),
Python 3.9 ou superior, NumPy e Matplotlib 3.6 ou superior. As versões
**efetivamente usadas** foram Clawpack 5.14.0, gfortran 16.2.1 e Python 3.14.7;
isso é um registro do ambiente, não a exigência de instalar exatamente esses
compiladores. Outras combinações não foram todas testadas.

Instale as ferramentas pelo gerenciador do sistema. Por exemplo, em
Fedora/Nobara: `sudo dnf install git make gcc-gfortran python3-pip`.

Obtenha o Clawpack **com seus submódulos**:

```bash
git clone --recurse-submodules --branch v5.14.0 https://github.com/clawpack/clawpack.git
export CLAW="$PWD/clawpack"
export FC=gfortran
export CLAW_PYTHON=python3
export PYTHONPATH="$CLAW${PYTHONPATH:+:$PYTHONPATH}"
```

Se o clone já existe sem os submódulos, execute
`git -C "$CLAW" submodule update --init --recursive` após selecionar a versão
desejada. Não atualize a instalação usada por resultados antigos sem registrar
a mudança. Configure novamente as variáveis ao abrir outro terminal.

Em uma instalação nova, clone esta aplicação na disposição adotada pelo trabalho:

```bash
git clone https://github.com/ironmanmark5/clawpack-telegraph_1d.git "$CLAW/classic/examples/telegraph_1d"
cd "$CLAW/classic/examples/telegraph_1d"
python3 -m pip install -r requirements.txt
```

Se já está neste repositório, não precisa cloná-lo novamente. O Clawpack admite
aplicações fora de sua árvore; nesse caso `CLAW` e `PYTHONPATH` precisam apontar
explicitamente para a dependência correta. Não misture esta instalação com
outra importada pelo Python. Para conferir:

```bash
python3 -B -c 'import clawpack; from clawpack.clawutil import data; print(clawpack.__version__); print(data.__file__)'
```

O `Makefile.common` usa `CLAW_PYTHON`, não `PYTHON`. Para escolher outro
interpretador, configure `CLAW_PYTHON=/caminho/para/python3` e use esse mesmo
interpretador nos comandos Python do guia.

### Versão nominal e fontes efetivos

A instalação original identifica-se como `5.14.0`, na árvore
`v5.14.0-17-gc5b4fbe`, com Classic no commit
`6b3dfe6419d9b389e2d04a372a7880c9e9c8349d`. Não é exatamente o checkout da tag
do superprojeto. Na revisão de robustez, os 11 arquivos Classic compilados e
`clawutil/data.py` foram comparados aos da tag `v5.14.0` e estavam iguais.
Os metadados de autoconvergência registram hashes para identificar os arquivos
efetivamente utilizados; eles não foram reescritos após a revisão.

### Solver próprio e verificação do ambiente

**Somente para o Caso 1**, o Makefile da raiz procura o solver fora do projeto:

```bash
cp solver-referencia/rp1_telegraph.f90 "$CLAW/riemann/src/"
./verificar-ambiente.sh
```

Antes da cópia, compare/guarde o destino caso já exista um solver com esse
nome. Essa localização é uma escolha do nosso Makefile, não uma obrigação do
Clawpack. A bateria compila seu solver local e não requer essa cópia.

O verificador examina as dependências do fluxo completo, incluindo VisClaw e
o solver do Caso 1; retorna código diferente de zero quando encontra faltas.
Ele não compila nem simula.

## 2. Caso 1 — verificação com solução de d'Alembert

Na raiz deste projeto, para uma **saída ainda inexistente**:

```bash
./rodar.sh 512 --sem-plots
```

O script usa `executar_caso1.py`: configura `num_cells=512` em memória, compila
se necessário e gera as entradas em uma pasta temporária. Não edita
`setrun.py`, não altera os `.data` da raiz e não sobrescreve saídas existentes.
Valida os quadros e `fort.info` antes de publicar `output_malha_512/`.
Uma falha conserva a pasta temporária com o log para diagnóstico.

```bash
./rodar.sh 512 --dry-run --destino reproducoes/nova
./rodar.sh 512 --destino reproducoes/nova
```

Sem `--sem-plots`, a última etapa chama o VisClaw diretamente, sem disparar
outra simulação. A segunda chamada acima **executa**; a primeira apenas confere
os caminhos. O destino relativo é interpretado a partir do diretório de chamada.

Para reproduzir as cinco séries na raiz, em um clone novo:

```bash
for N in 128 256 512 1024 2048; do
    ./rodar.sh "$N" --sem-plots
done
```

Cada saída contém 65 pares `fort.qNNNN`/`fort.tNNNN`, entradas efetivas e log.
São 64 intervalos de saída até `t=0,8`, com estado inicial. **0,0125 é o
intervalo entre saídas, não um passo interno fixo do solver.**

O fluxo manual `make .exe`, `make .data`, `make .output OUTDIR=...` continua
disponível. Nesse fluxo, a malha é a configurada em `setrun.py` (2048 por
padrão): o nome `output_malha_512` não a modifica. Os alvos com ponto verificam
dependências por datas; mudar apenas `OUTDIR` pode não forçar nova execução.

### Análise do Caso 1, sem simular

```bash
python3 -B convergencia_caso1.py --saida resultados/reanalise_caso1
python3 -B gerar_figuras_caso1.py --destino resultados/figuras_reanalise_caso1
```

São lidas as séries `output_malha_*` da raiz. Se as séries foram gravadas em
outro local, use `--dirs` no script de convergência. Os scripts escrevem CSVs
ou figuras, mas não executam Fortran; os destinos alternativos acima preservam
os produtos publicados. Os destinos padrão originais continuam disponíveis.

O erro usa `sqrt(dx*sum((u_i-u_ex(x_i,t))**2))`, além da comparação com a média
celular exata. A ordem usa a razão efetiva dos espaçamentos, inclusive se uma
malha intermediária não for selecionada. Os tempos, domínios e parâmetros
das séries precisam ser compatíveis. A conferência com a Tabela 6.1 aplica-se
somente ao caso documentado em `t=0,4`; ordens de referência são conferidas
apenas nos pares de malhas correspondentes.

Para outro instante disponível:

```bash
python3 -B convergencia_caso1.py --tempo 0.8 --saida resultados/reanalise_caso1_t08
```

Um tempo ausente não é silenciosamente trocado pelo quadro mais próximo.

## 3. Casos 2 a 8 — 16 configurações únicas

A partir da raiz:

```bash
cd arquivos-roteiro-simulacoes
python3 -B executar_casos.py --dry-run
python3 -B executar_casos.py --saida resultados/reproducao_nova
python3 -B gerar_figuras_comparativas.py --dados resultados/reproducao_nova
```

O executor usa **400 células por padrão**; `--celulas 1024` muda explicitamente
a resolução, e `--casos 2` seleciona um caso. O `setrun.py` da bateria, quando
chamado diretamente, mantém o padrão 1024. Não confunda esses dois padrões.

Novas execuções registram fontes, comando de compilação, hash do binário e
checksums das saídas. Uma saída só é reutilizada para simulação se essa
proveniência coincidir. Dados históricos sem esses campos não são apagados
nem recebem hashes retrospectivos: podem ser analisados, mas uma nova
simulação deve usar outra `--saida`. Comentários nos fontes também alteram
seus hashes e, conservadoramente, impedem essa reutilização automática.

A análise valida entradas efetivas, geometria, tempos, finitude, `fort.info`
e amplitudes CSV. Não mistura resoluções nas comparações. Para analisar a
bateria original sem substituir as figuras publicadas:

```bash
python3 -B gerar_figuras_comparativas.py --dados resultados --destino resultados/figuras_reanalise
```

As 16 configurações históricas principais têm 400 células. Como conferência
parcial, no Caso 5: `A(0,4) ≈ 0,41288`, `A(0,8) ≈ 0,33414`; na referência
`a=b=0`: `0,49835` e `0,49490`. Coincidir nesses quatro valores é um indício,
não uma prova completa de reprodução. O Caso 6 pode sofrer influência da
fronteira perto de `t=0,75`; o domínio original foi mantido.

## 4. Autoconvergência com fonte ativa

A partir de `arquivos-roteiro-simulacoes/`:

```bash
python3 -B -m unittest -v test_autoconvergencia.py
python3 -B autoconvergencia.py --claw "$CLAW" --saida resultados_autoconvergencia_nova
```

São sete malhas de 32 a 2048 células; `c=2, a=1, b=1, beta=200, x0=0`.
Não é necessário um nome específico de branch. A branch efetiva continua
registrada como procedência. Builds e saídas antigos permanecem preservados.

Para dados brutos já existentes na pasta padrão:

```bash
python3 -B autoconvergencia.py --somente-analisar
```

Esse comando não compila nem simula, **mas reescreve os relatórios, CSVs e
figuras derivados**. Não o execute sobre o arquivo histórico se quiser apenas
consultar os resultados publicados. Em um clone novo, as saídas brutas devem
ser produzidas antes: não estão no Git. Mais detalhes em
[`AUTOCONVERGENCIA.md`](arquivos-roteiro-simulacoes/AUTOCONVERGENCIA.md).

## 5. O que está e o que não está no Git

Estão versionados: fontes, scripts, documentação, figuras finais, CSVs
agregados e metadados de procedência. Não estão: binários, objetos, saídas
brutas completas, caches e a bateria auxiliar de 1024 células. Os nomes e
colunas estão em [`docs/DADOS-E-NOMENCLATURA.md`](docs/DADOS-E-NOMENCLATURA.md).

Para apenas conferir números, leia os CSVs e o mapa de figuras: não é preciso
instalar ou executar o Clawpack. Os testes de robustez, também sem simular:

```bash
# Na raiz do projeto:
python3 -B -m unittest discover -s tests -v
```

## 6. Segurança e diagnóstico

- `make plots` apenas plota; `make .plots` pode recompilar e simular.
- `make output` não verifica dependências: exige binário e `.data` atualizados.
- O fluxo manual tem `OVERWRITE=True` por padrão. Não aponte para dados que
  deseja preservar. `rodar.sh` recusa destinos existentes.
- Mudar `FFLAGS` não força recompilação no fluxo Makefile. Não troque flags
  para revisar resultados históricos. Novas baterias recompilam explicitamente.
- A CFL controla a propagação hiperbólica; não garante estabilidade de uma
  fonte explícita com coeficientes arbitrariamente rígidos.
- Em falhas, confira o caminho do solver, os submódulos, a instalação importada,
  o log e `fort.info`. Um erro em `opendatafile` aponta primeiro para arquivos
  de entrada ausentes/inválidos, não necessariamente para falta do solver.

Referências oficiais consultadas: [instalação Fortran](https://www.clawpack.org/installing_fortcodes.html),
[ambiente](https://www.clawpack.org/setenv.html), [Makefiles](https://www.clawpack.org/makefiles.html),
[rotinas de usuário](https://www.clawpack.org/user_routines.html),
[contornos](https://www.clawpack.org/bc.html) e [formato de saída](https://www.clawpack.org/output_styles.html).
