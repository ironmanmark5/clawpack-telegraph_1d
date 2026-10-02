# Resumo expandido de autoconvergência

Documento independente para discussão com a orientação do TCC. Sintetiza somente o estudo combinado de autoconvergência, não toda a bateria dos Casos 2–8. Nenhum resultado novo foi simulado para redigir este material.

- `resumo_expandido_autoconvergencia.pdf`: versão para leitura e envio.
- `resumo_expandido_autoconvergencia.tex`: fonte editável.
- `figuras/`: três gráficos originais em PDF vetorial.
- `dados/`: CSV, relatório, metadados e testes do estudo. A tabela LaTeX foi gerada diretamente do CSV; não há valores estimados ou preenchimentos com zero.

## Compilar o documento

A partir desta pasta, com uma instalação LaTeX que já disponha dos pacotes usados:

```bash
pdflatex -interaction=nonstopmode -halt-on-error resumo_expandido_autoconvergencia.tex
pdflatex -interaction=nonstopmode -halt-on-error resumo_expandido_autoconvergencia.tex
```

Envie o PDF para leitura. Para editar em outro computador ou no Overleaf, use o ZIP de fontes ao lado desta pasta, mantendo `figuras/` e `dados/` junto ao `.tex`; escolha esse `.tex` como documento principal. O pacote não contém as saídas brutas das sete simulações.

## Reproduzir os resultados numéricos

No repositório, a partir de `arquivos-roteiro-simulacoes/`:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py
python3 autoconvergencia.py --somente-analisar
```

Se necessário, indique `--claw /caminho/para/clawpack` ou configure `CLAW`. Os requisitos, as verificações de compatibilidade e a estrutura das execuções estão descritos em [AUTOCONVERGENCIA.md](../../../AUTOCONVERGENCIA.md), na pasta da aplicação. Esse documento permanece no repositório e não é incluído no ZIP de fontes.

Este resumo mantém os resultados reais, inclusive a ordem negativa de `u_t` nas malhas grossas e as ordens distintas na última trinca. Testes sintéticos e expectativas sobre os componentes do método são identificados separadamente.
