# Roteiro do Integrante B — apresentação final

Cada resposta abaixo foi pensada para durar aproximadamente 20 a 30 segundos.
Os números correspondem aos arquivos versionados `results/q1_q2_q3.csv`,
`results/tamanho_amostra.csv` e `data/real/prs.csv`.

## Pergunta 5 — O que cada teste compara?

**Mostrar:** seção 3 do dashboard.

> O t de Welch compara as médias dos tempos de merge e não exige variâncias
> iguais entre os grupos. O Mann-Whitney compara os postos: ele avalia se os
> tempos de um grupo tendem a ser maiores que os do outro. Por isso, o Welch
> responde diretamente sobre médias, enquanto Mann-Whitney é uma alternativa
> baseada na ordenação dos valores.

## Pergunta 6 — Como interpretar o G2?

**Mostrar:** seção 3, gráfico G2.

> O G2 mostra a distribuição esperada da estatística se H0 fosse verdadeira.
> Para Welch, usamos a distribuição t com os graus de liberdade de
> Welch-Satterthwaite; para Mann-Whitney, a aproximação normal da estatística U
> padronizada. Como a hipótese é bicaudal, as regiões de rejeição ficam nas duas
> caudas, além dos limites definidos por alfa igual a 5%.

## Pergunta 7 — O que significa o p-valor?

**Mostrar:** seção 3, estatísticas e áreas do G2.

> O p-valor é a probabilidade, supondo H0 verdadeira, de observar uma estatística
> tão extrema quanto a obtida ou mais extrema. No G2, essa probabilidade aparece
> como a área sombreada nas duas caudas. Ele não é a probabilidade de H0 ser
> verdadeira e, sozinho, não mede a importância prática de uma diferença.

## Pergunta 9 — Algum teste se afastou de 5%?

**Mostrar:** seção 4, gráfico G3, com alfa igual a 5%.

> Na situação base, Mann-Whitney rejeitou H0 em 4,74% das simulações, perto dos
> 5% esperados; nas situações da Q3, ficou entre 4,42% e 4,92%. Welch foi
> conservador em todas: variou de 1,69% na base a 0,42% com assimetria extrema,
> além de 1,60% com outliers e 0,84% com amostras pequenas. Isso indica que, neste
> cenário de cauda longa, Welch rejeitou H0 verdadeira menos do que o nível
> nominal.

## Pergunta 10 — Qual teste teve mais poder?

**Mostrar:** seção 5, gráfico G4.

> Mann-Whitney teve maior poder que Welch em todos os efeitos e cenários
> simulados. Na situação base e no maior efeito avaliado, 0,9, o poder foi 96,95%
> para Mann-Whitney e 36,56% para Welch. A vantagem não se inverteu nas
> situações simuladas; uma checagem exploratória indica que Welch só pode empatar
> ou superar Mann-Whitney com dados quase simétricos.

## Pergunta 14 — Os testes concordaram nos dados reais?

**Mostrar:** seção 6 do dashboard.

> Sim. Com 30 PRs em cada grupo, Welch obteve p = 0,593 e Mann-Whitney p = 0,355;
> nenhum rejeitou H0 a 5%. A mediana observada foi 37,1 horas com bot e 51,8 horas
> sem bot, uma diferença de cerca de 14,7 horas, mas a amostra teve pouco poder
> para distinguir esse efeito do acaso. Além disso, os PRs com bot eram menores,
> então não podemos atribuir a diferença somente ao bot.

## Pergunta 15 — Qual é a recomendação e quando ela mudaria?

**Mostrar:** seções 5, 6 e 7 do dashboard.

> Para tempos de merge muito assimétricos como os deste estudo, recomendamos
> Mann-Whitney, que manteve a taxa de erro tipo I mais próxima de 5% e teve maior
> poder nas simulações realizadas. Se os dados fossem quase simétricos e a
> pergunta de interesse fosse especificamente sobre médias, Welch poderia ser
> mais adequado. A principal limitação é que este é um estudo observacional de
> um único repositório: o uso do bot não foi sorteado e os grupos diferem também
> no tamanho dos PRs.
