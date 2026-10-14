# Como reproduzir este trabalho

Este guia acompanha a monografia. Ele descreve, na mesma ordem do texto, o que
executar para refazer cada resultado, o que esperar de cada execução e o que
não está no repositório de propósito. Para o mapa das alterações feitas no
Clawpack, veja [`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md);
para o significado dos arquivos e dos nomes, veja
[`docs/DADOS-E-NOMENCLATURA.md`](docs/DADOS-E-NOMENCLATURA.md).

## 1. Preparar o ambiente

O trabalho foi executado com **Clawpack 5.14.0**, `gfortran` 16.2.1, Python
3.14.7 e a opção de compilação `-O2`. O Clawpack não está incluído neste
repositório: ele é uma dependência externa e precisa ser obtido separadamente.

```bash
# ferramentas
sudo dnf install gcc-gfortran make        # Fedora/Nobara; use apt em Debian/Ubuntu
python3 -m pip install -r requirements.txt

# Clawpack 5.14.0
git clone --branch v5.14.0 https://github.com/clawpack/clawpack.git
export CLAW=$PWD/clawpack
export PYTHONPATH=$CLAW:$PYTHONPATH
```

Antes de qualquer execução, rode a verificação de ambiente deste repositório:

```bash
./verificar-ambiente.sh
```

O script confere se `gfortran`, `make`, Python e os pacotes de Python estão
disponíveis, se a variável `CLAW` aponta para uma árvore válida do Clawpack e se
o solucionador de Riemann está no lugar esperado pelo `Makefile`.

## 2. Caso 1 — verificação da implementação ($a = b = 0$)

Esta é a etapa de verificação, em que a equação se reduz à equação da onda e a
solução de referência é a de d'Alembert. Corresponde à Seção 5.1 da monografia.

```bash
# o Makefile espera o solucionador em $CLAW/riemann/src/
cp solver-referencia/rp1_telegraph.f90 $CLAW/riemann/src/

make .exe
make .output OUTDIR=output_malha_512    # uma malha; repita com outros valores de mx
```

O número de células é definido em `setrun.py` (`clawdata.num_cells[0]`). As
séries usadas na monografia têm $N = 128$, $256$, $512$, $1024$ e $2048$.

**O que esperar.** Cada execução grava pares `fort.qNNNN`/`fort.tNNNN` no
diretório de saída: 65 arquivos de cada tipo, com o intervalo de saída de
0,0125 e tempo final 0,8. Em `t = 0,4`, o perfil deve mostrar dois pulsos de
amplitude próxima de 0,5, separando-se da origem com velocidade $\pm 2$. As
figuras de comparação com a solução exata do repositório
(`fig_caso1_t020.png` e `fig_caso1_t040.png`) foram geradas dessas saídas.

**Erros e ordem.** A tabela de convergência da monografia usa a norma discreta
$E_{L^2} = [\Delta x \sum_i (u_i - u_{ex}(x_i,t))^2]^{1/2}$ em $t = 0{,}4$ e a
ordem $p = \log(E_h/E_{h/2})/\log 2$. Os valores estão registrados na
Seção 5.1 e podem ser recalculados a partir dos `fort.qNNNN` com a expressão
acima. O script que automatiza esse cálculo ainda não faz parte do
repositório; enquanto isso, a leitura dos arquivos e o cálculo manual seguem a
metodologia descrita na Seção 4.4 da monografia.

## 3. Casos 2 a 8 — bateria de experimentos

Cada caso altera um parâmetro do modelo ou a condição inicial. A definição dos
casos está na Seção 4.3 da monografia e a correspondência entre caso,
configuração e figura está em
[`docs/DADOS-E-NOMENCLATURA.md`](docs/DADOS-E-NOMENCLATURA.md).

```bash
cd arquivos-roteiro-simulacoes
python3 executar_casos.py --dry-run     # confere quais casos serão executados
python3 executar_casos.py               # executa os Casos 2 a 8 (16 configurações)
python3 gerar_figuras_comparativas.py   # monta as figuras comparativas
```

Opções úteis: `--casos 2` executa apenas um caso; `--celulas 1024` muda a
malha; `--saida outra_pasta` separa uma bateria nova. A primeira execução
compila o `xclaw`; as seguintes apenas rodam.

**O que esperar.** Para cada configuração o script cria um diretório em
`resultados/` com os pares `fort.qNNNN`/`fort.tNNNN`, os arquivos
`claw.data`/`setprob.data` efetivos, `parametros.json`, `amplitude.csv`,
`perfis.csv` e `execucao.log`. O índice `resultados/casos.json` relaciona cada
caso às configurações e `resultados/resumo.csv` registra a amplitude máxima em
$t = 0{,}4$ e $t = 0{,}8$. A etapa final produz
`resultados/figuras_comparativas/`, com as figuras e as tabelas usadas na
Seção 5 da monografia.

**Conferência rápida.** Em `resultados/resumo.csv`, a configuração
`a1_bm1_beta200_x00` (Caso 5) deve apresentar $A(0{,}4) = 0{,}41288$ e
$A(0{,}8) = 0{,}33414$; a `a0_b0_beta200_x00` (referência, $a = b = 0$) deve
apresentar $0{,}49835$ e $0{,}49490$. Se os seus valores coincidirem, a
reprodução está correta.

## 4. Estudo de autoconvergência

Executa sete malhas com o termo fonte ativo ($c = 2$, $a = 1$, $b = 1$,
$\beta = 200$, $x_0 = 0$) e compara as soluções por restrição conservativa.
Corresponde à Seção 5.9 da monografia.

```bash
cd arquivos-roteiro-simulacoes
python3 -m unittest -v test_autoconvergencia.py   # testes da rotina de erro
python3 autoconvergencia.py                       # executa as sete malhas
python3 autoconvergencia.py --somente-analisar    # recalcula tabelas e figuras
```

**O que esperar.** Sete simulações de $N = 32$ a $2048$ em
`resultados_autoconvergencia/simulacoes/`, o arquivo `autoconvergencia.csv` com
os erros de refinamento e as ordens observadas, as figuras `erros_loglog`,
`perfis_u` e `perfis_ut`, o relatório `RELATORIO.md` e os arquivos de
proveniência. A trinca mais fina disponível deve fornecer $p_u \approx 0{,}85$
e $p_{u_t} \approx 2{,}16$; as malhas grossas apresentam ordens
pré-assintóticas, como discutido no relatório.

## 5. O que não está no repositório

Por tamanho, e porque podem ser regenerados pelos scripts acima, ficaram fora
do controle de versão:

- as saídas brutas das simulações (`fort.qNNNN`, `fort.tNNNN`, `xclaw`) das
  duas baterias, que somam dezenas de megabytes;
- os arquivos `perfis.csv` de cada configuração, que contêm as médias
  celulares quadro a quadro e são a matéria-prima das figuras;
- os resultados da bateria repetida com 1024 células.

O que está versionado é o conjunto que permite conferir os números da
monografia sem executar nada: as figuras comparativas, os CSVs agregados
(`resumo.csv`, `amplitudes_tempos_comuns.csv`, as matrizes do Caso 8 e o
`autoconvergencia.csv`) e os metadados de proveniência
(`experimento.json`, `testes_sinteticos.json`, `ordens_diagnostico.json`).

## 6. Se algo der errado

| Sintoma | Causa provável e solução |
| --- | --- |
| `fatal error: opendatafile` ou erro de link no `make` | O solucionador não está em `$CLAW/riemann/src/`. Rode a cópia indicada na Seção 2 |
| `ModuleNotFoundError: clawpack` | `PYTHONPATH` não inclui a raiz do Clawpack. Exporte novamente e confirme com `python3 -c "import clawpack; print(clawpack.__version__)"` |
| `gfortran: command not found` | Instale o compilador (Seção 1) |
| `ModuleNotFoundError: matplotlib` | `python3 -m pip install -r requirements.txt` |
| O script reclama de saída incompleta | Ele se recusa a reaproveitar execuções duvidosas, de propósito. Use `--saida` para um diretório novo |
| Resultados diferentes dos da monografia | Confira `setprob.data` e `claw.data` gerados em cada caso: eles registram os parâmetros efetivamente usados |

## 7. Se você quer apenas conferir os números

Não é preciso compilar nada. O caminho mais curto é ler os CSVs agregados
indicados na Seção 5 e compará-los com as tabelas da monografia, usando a
correspondência entre caso e configuração descrita em
[`docs/DADOS-E-NOMENCLATURA.md`](docs/DADOS-E-NOMENCLATURA.md).
