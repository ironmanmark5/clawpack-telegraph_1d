# Autoconvergência — experimento combinado

## Metodologia

Foram executadas somente as sete malhas N=32,64,128,256,512,1024,2048. N conta células físicas. Parâmetros: c=2, a=1, b=1, beta=200, x0=0; domínio [-2,2], dx=4/N, tempo final 0,8 e 64 intervalos de saída mais o estado inicial. A equação é u_tt+a*u_t=c²*u_xx+b*u, com sinal positivo de b. q=(u,u_t,u_x); u_t é lido da segunda componente, sem diferenças temporais entre snapshots.

As saídas ASCII contêm exatamente N linhas físicas (out1.f escreve i=1,...,mx), sem células fantasma. Foram conferidos todos os tempos registrados, a geometria, parâmetros efetivos, finitude e condição inicial. A interpretação é de médias celulares. A inicialização por valores no centro foi preservada, inclusive nas malhas grossas.

Antes de comparar, R(q_2N)[i]=(q_2N[2i]+q_2N[2i+1])/2. As fronteiras coincidem, o refinamento é dois e o domínio físico é o mesmo. E(N)=sqrt(mean((R(q_2N)-q_N)²)) é o erro L2 discreto normalizado entre malhas; não é desvio padrão nem erro em relação à solução exata. p(N)=log(E(N)/E(2N))/log(2) usa três soluções.

A referência da orientadora discute pontos/interpolação e mostra E(N) na linha 2N. Aqui a adaptação para volumes finitos usa restrição conservativa e a própria linha N contém E(N) e p(N), conforme o escopo autorizado. Existem seis erros e cinco ordens por componente; E(2048), p(1024) e p(2048) são indisponíveis. CSV usa NaN e LaTeX usa --. Razões e limiares estão em ordens_diagnostico.json.

## Resultados efetivamente calculados

| N | dx | E_u(N) | p_u(N) | E_ut(N) | p_ut(N) |
|---:|---:|---:|---:|---:|---:|
| 32 | 0.125 | 7.441192e-02 | 1.2388 | 2.466716e-01 | -1.9362 |
| 64 | 0.0625 | 3.153010e-02 | 1.1962 | 9.439708e-01 | 0.4824 |
| 128 | 0.03125 | 1.376038e-02 | 1.6681 | 6.756928e-01 | 1.4129 |
| 256 | 0.015625 | 4.329820e-03 | 1.5398 | 2.537534e-01 | 2.0576 |
| 512 | 0.0078125 | 1.489155e-03 | 0.8454 | 6.095455e-02 | 2.1573 |
| 1024 | 0.00390625 | 8.288204e-04 | -- | 1.366411e-02 | -- |
| 2048 | 0.001953125 | -- | -- | -- | -- |

A última trinca disponível é 512→1024→2048: p_u=0.8454 e p_ut=2.1573. São ordens locais observadas entre soluções numéricas, sem imposição de ordem dois.
E_ut(32)=2.466716e-01 é menor que E_ut(64)=9.439708e-01; a primeira ordem de u_t é negativa. Isso registra a ausência de redução monotônica das diferenças nesse intervalo grosseiro, não uma taxa assintótica. O perfil de u em N=32 também apresenta uma região central negativa e pulsos deformados; esses artefatos foram mantidos e podem ser vistos na figura. A resolução inicial insuficiente é relevante para interpretar esse comportamento; sua causa não foi isolada por experimentos adicionais.
Nas duas últimas trincas, u_t apresenta ordens próximas de dois, enquanto u tem ordens diferentes e variáveis. Esses dados não autorizam atribuir segunda ordem ao esquema completo nem afirmar que todos os componentes chegaram ao regime assintótico. O efeito de cada etapa não é isolado por este estudo.

## Passos temporais e verificação de execução

| N | passos aceitos | tentativas rejeitadas | dt mínimo aceito (log) | dt máximo aceito (log) | CFL mínimo | CFL máximo | max u inicial |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 64 | 0 | 1.250000e-02 | 1.250000e-02 | 0.200 | 0.200 | 0.457833 |
| 64 | 64 | 0 | 1.250000e-02 | 1.250000e-02 | 0.400 | 0.400 | 0.822578 |
| 128 | 64 | 0 | 1.250000e-02 | 1.250000e-02 | 0.800 | 0.800 | 0.952345 |
| 256 | 128 | 1 | 5.469000e-03 | 7.031000e-03 | 0.700 | 0.900 | 0.987867 |
| 512 | 256 | 1 | 1.953000e-03 | 3.516000e-03 | 0.500 | 0.900 | 0.996953 |
| 1024 | 512 | 1 | 1.953000e-04 | 1.758000e-03 | 0.100 | 0.900 | 0.999237 |
| 2048 | 960 | 1 | 1.953000e-04 | 8.789000e-04 | 0.200 | 0.900 | 0.999809 |

CFL desejado=0,9; CFL máximo permitido=1. O tempo é variável. O intervalo entre saídas (0,0125) limita o passo nas malhas grossas. O log distingue tentativas rejeitadas de passos aceitos. dt e t do stdout têm cinco algarismos significativos e CFL tem três casas decimais: os diagnósticos efetivos aqui são arredondados, não valores internos de precisão plena. fort.info foi preservado; seus campos dt incluem candidatos ao passo seguinte e a inicialização dt=0,1, e não devem ser confundidos com os dt efetivamente usados.

A única mudança de configuração é verbosity=1 para registrar passos; isso não altera o algoritmo. Fonte, solver, limitadores e inicialização permanecem iguais. Cada execução registra status, tempo atingido, parâmetros, checksum das saídas, tempo de parede e diagnósticos em execucao.json e passos.csv. As sete saídas alcançaram t=0,8 (tolerância 1e-11), com info=0 e código de saída zero.

## Interpretação e limitações

A correção hiperbólica é de segunda ordem com MC; o splitting de Godunov é de primeira ordem e a fonte usa Euler explícito simultâneo, a partir de q1 e q2 antigos. Assim, este estudo mede o esquema completo com refinamento espacial e temporal acoplados pela CFL e pelas saídas. Não isola exclusivamente o erro espacial. Nenhuma alteração foi feita para obter uma ordem desejada.

A largura à meia altura da gaussiana é 0.117741. Em N=32, dx=0,125 é maior que essa largura; a gaussiana estreita é mal resolvida e seu pico contínuo em x=0 fica entre centros de células. Os máximos iniciais na tabela evidenciam esse efeito. Ordens nas malhas grossas podem ser pré-assintóticas. As diferenças de inicialização e os limitadores também fazem parte do experimento.

O domínio e os contornos por extrapolação foram preservados. O estudo não demonstra independência do contorno nem mede erro contra uma solução analítica. Não foram executados N=4096, outros parâmetros físicos ou uma nova bateria de casos.

## Testes sintéticos e proveniência

Os três testes sintéticos exigidos passaram e estão separados em testes_sinteticos.json: diferença unitária→erro 1; restrição constante→mesma constante; redução por quatro→ordem 2. Esses valores não são resultados do solver.

experimento.json registra commit/branch, estado sujo, versão do Clawpack, compilador, flags, lista dos fontes realmente compilados, hashes e comando de build. O executável foi recompilado à força a partir de snapshots dos fontes atuais do Makefile desta aplicação, em build/, sem usar os fontes antigos da raiz. A árvore de trabalho já tinha alterações não commitadas; hashes e snapshots identificam o código efetivo, além do commit. Arquivos antigos dos Casos 2–8 foram preservados.

## Reprodução

A partir de arquivos-roteiro-simulacoes/:

```bash
python3 -m unittest -v test_autoconvergencia.py
python3 autoconvergencia.py
python3 autoconvergencia.py --somente-analisar
```

Use --claw /caminho/para/clawpack ou CLAW quando necessário. A descoberta consulta essa configuração, o pacote instalado e instalações nos diretórios ancestrais. --saida é relativo a esta pasta; use outra pasta para um build/configuração incompatível com execuções existentes. Não é preciso instalar dependências ou criar ambiente virtual.

Pendências: não há bloqueio de execução. Os materiais não foram incorporados à monografia e não houve publicação, commit, push ou PR.
