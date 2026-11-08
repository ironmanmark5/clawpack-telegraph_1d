# Arquivos originais do Clawpack

Esta pasta guarda **cópias não modificadas** dos arquivos do Clawpack usados
como ponto de partida, para que qualquer leitor possa comparar com os
arquivos deste repositório sem precisar instalar o pacote.

| Pasta | Origem | Conteúdo |
| --- | --- | --- |
| `acoustics_1d_example1/` | `$CLAW/classic/examples/acoustics_1d_example1/` | `setrun.py`, `setprob.f90`, `qinit.f90`, `setplot.py`, `Makefile` |
| `classic-src-1d/` | `$CLAW/classic/src/1d/` | `src1.f90` (rotina vazia de termo fonte distribuída com o pacote) |
| `riemann-src/` | `$CLAW/riemann/src/` | `rp1_acoustics.f90` (solucionador do exemplo acústico) |

Versão utilizada: **Clawpack 5.14.0**, árvore em
`v5.14.0-17-gc5b4fbe`. O exemplo unidimensional de acústica dessa versão
chama-se `acoustics_1d_example1`; em versões antigas o mesmo exemplo aparece
como `acoustics_1d`.

O Clawpack é distribuído sob licença BSD de três cláusulas; o texto completo
está em [`LICENSE`](../LICENSE) e em
[`arquivos-roteiro-simulacoes/LICENSE-CLAWPACK.txt`](../arquivos-roteiro-simulacoes/LICENSE-CLAWPACK.txt).
Estes arquivos são reproduzidos aqui apenas para fins de comparação e
documentação, sem alteração.

As diferenças linha a linha entre estes originais e os arquivos do trabalho
estão em [`docs/DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff`](../docs/DIFERENCAS-EM-RELACAO-AO-UPSTREAM.diff).
