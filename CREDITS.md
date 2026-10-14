# Créditos e atribuições

Este repositório reúne o material computacional do Trabalho de Conclusão de
Curso de graduação de **Diogo Barbosa Ferreira da Silva**, da Universidade
Federal de Lavras (UFLA), orientado pela **Profa. DSc. Juliana Bertoco**. O
trabalho formula a equação do telegrafista como um sistema de primeira ordem,
resolve a parte hiperbólica com um solucionador de Riemann próprio no
*Clawpack* e analisa numericamente os casos descritos no roteiro de
simulações.

## Clawpack

Toda a parte numérica está construída sobre o **Clawpack** (*Conservation Laws
Package*), biblioteca de código aberto para a solução de leis de conservação
hiperbólicas por métodos de volumes finitos com solucionadores de Riemann. Os
créditos do pacote pertencem aos Clawpack Developers, e o trabalho não teria
sido possível sem essa base.

- CLAWPACK DEVELOPMENT TEAM. **Clawpack**: Conservation Laws Package. 2026.
  DOI: 10.17605/osf.io/kmw6h. Disponível em: https://www.clawpack.org.
- A implementação partiu do exemplo `classic/examples/acoustics_1d`,
  distribuído com o pacote, que foi adaptado para o sistema do telegrafista.
- As rotinas numéricas do solver clássico unidimensional (`claw1.f`,
  `step1.f90`, `inlinelimiter.f90`, `bc1.f`, `out1.f` e demais arquivos de
  `classic/src/1d`) são de autoria dos Clawpack Developers e **não foram
  modificadas** neste trabalho.
- Versão utilizada: **5.14.0**, com os fontes do *Classic* no commit
  `6b3dfe6419d9b389e2d04a372a7880c9e9c8349d` do repositório oficial,
  disponível em https://github.com/clawpack/clawpack.
- Licença: BSD de três cláusulas, reproduzida no arquivo `LICENSE` e também em
  `arquivos-roteiro-simulacoes/LICENSE-CLAWPACK.txt`.

### Como citar o Clawpack

- LEVEQUE, R. J. **Finite Volume Methods for Hyperbolic Problems**. Cambridge:
  Cambridge University Press, 2002.
- KETCHESON, D. I.; LEVEQUE, R. J.; DEL RAZO, M. J. **Riemann Problems and
  Jupyter Solutions**: Theory and Approximate Solvers for Hyperbolic PDEs.
  Philadelphia: SIAM, 2020. DOI: 10.1137/1.9781611976212.
- Documentação oficial, incluindo as rotinas de usuário e as condições de
  contorno: https://www.clawpack.org.

## Autoria deste repositório

- **Rotinas, scripts, experimentos e resultados**: Diogo Barbosa Ferreira da
  Silva.
- **Orientação** e roteiro de simulações: Profa. DSc. Juliana Bertoco.

As alterações feitas em relação ao Clawpack estão documentadas em
[`docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md`](docs/ALTERACOES-EM-RELACAO-AO-CLAWPACK.md)
e reproduzidas nos apêndices da monografia.

## Ferramentas utilizadas

- `gfortran` 16.2.1, com a opção `-O2`;
- Python 3.14.7, com `matplotlib`;
- Clawpack 5.14.0 (Classic);
- `make` e a árvore de fontes do Clawpack para compilação.
