# Resultados das simulações (Q1, Q2, Q3 e tamanho da amostra)

Notas do Integrante A para as issues S2-A1 a S2-A4 e F-A3 e para os textos das seções 4, 5 e 7.
Todos os números saem de `python -m src.experimentos` e `python -m src.tamanho_amostra` (seed 42,
10.000 repetições por ponto, n = 30 por grupo, lognormal com mediana 55,7 h e sigma 2,23).

## Formato do arquivo de resultados (S2-A1)

```
results/q1_q2_q3.csv            (α = 0,05)
results/q1_q2_q3_alpha001.csv   (α = 0,01, mesmo formato; usado na pergunta 12)
colunas: pergunta, situacao, teste, efeito, n_por_grupo, n_rep, taxa_rejeicao, ic95_inf, ic95_sup
pergunta: Q1 | Q2 | Q3
situacao: base | assimetria_extrema | com_outliers | amostra_pequena
teste:    welch | mann_whitney
```

- O IC 95% é o de Wald: `taxa ± 1,96·sqrt(taxa(1 − taxa)/n_rep)`.
- Em cada ponto (situação × efeito), os dois testes são aplicados **aos mesmos 10.000 conjuntos**. Assim a diferença entre eles não vem de sorteios diferentes.
- O motor é vetorizado. Ele gera `size=(n_rep, n)` de uma vez e chama os testes com `axis=-1`, e só divide em blocos quando n é grande. A grade inteira, com α = 0,05 e α = 0,01, roda em cerca de 5 s.

## Q1: erro tipo I com H0 verdadeira (S2-A2)

| Teste | Taxa de rejeição | IC 95% | Dentro de 5% ± 0,4 p.p.? |
|---|---|---|---|
| t de Welch | 1,69% | 1,44% a 1,94% | **Não. Conservador** |
| Mann-Whitney | 4,74% | 4,32% a 5,16% | Sim |

- O Welch rejeita H0 verdadeira três vezes menos que o nominal. Com cauda pesada, a variância amostral cresce junto com a média amostral: o conjunto que tem um PR enorme tem média alta e desvio alto ao mesmo tempo. Por isso |t| quase nunca fica grande.
- No ponto efeito = 0 da Q2, que é uma segunda rodada independente, o Mann-Whitney deu 4,30%. Numa checagem com 200.000 repetições, o tamanho real do Mann-Whitney é **4,85%** (IC 4,76% a 4,95%), um pouco abaixo de 5% por causa da correção de continuidade da aproximação normal. O 4,30% é variação amostral, cerca de 2,7 erros-padrão. O Welch deu 1,63% com 200.000 repetições.

## Q2: curvas de poder (S2-A3)

Grade de efeitos: `[0, 0,1, …, 0,9]`, com o efeito sendo a redução relativa da mediana. A grade do plano, `[0, …, 0,5]`, foi
estendida porque com sigma = 2,23 o poder em 0,5 fica perto de 21% (Mann-Whitney) e 5% (Welch), e
a curva não chegaria a 80%.

| Efeito | 0 | 0,1 | 0,2 | 0,3 | 0,4 | 0,5 | 0,6 | 0,7 | 0,8 | 0,9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mann-Whitney | 4,3% | 5,1% | 6,0% | 9,0% | 12,9% | 21,1% | 31,1% | 51,2% | 75,7% | 97,0% |
| t de Welch | 1,7% | 1,9% | 2,1% | 2,4% | 3,3% | 5,2% | 7,3% | 12,4% | 21,7% | 36,6% |

- **80% de poder:** o Mann-Whitney passa de 80% entre os efeitos 0,8 e 0,9 (por interpolação, cerca de 0,82, ou seja, a mediana com bot em 18% da mediana sem bot). O Welch **não chega a 80%** em nenhum efeito da grade.
- O Mann-Whitney tem mais poder em todos os efeitos. A vantagem **não muda de lado** em nenhuma das situações simuladas.

## Q3: situações que violam os pressupostos (S2-A4)

`src/cenarios_q3.py`: os três geradores têm a mesma assinatura do gerador base.

| Situação | O que muda | Pressuposto violado | Erro tipo I Welch | Erro tipo I MW | Poder em 0,9 Welch | Poder em 0,9 MW |
|---|---|---|---|---|---|---|
| base | nada | (referência) | 1,69% | 4,74% | 36,6% | 97,0% |
| assimetria_extrema | sigma × 2 (4,46) | normalidade aproximada da média amostral (TCL não basta com n = 30) | **0,42%** | 4,42% | 1,8% | 47,4% |
| com_outliers | 5% dos valores × 10, nos dois grupos | ausência de valores extremos (inflam a variância e dominam a média) | 1,60% | 4,92% | 30,2% | 96,1% |
| amostra_pequena | n = 10 por grupo | n grande para a aproximação t | **0,84%** | 4,59% | 9,0% | 54,4% |

- **Por que afeta mais o Welch:** o Welch usa média e variância, que são dominadas pela cauda. O Mann-Whitney usa só a ordem dos valores. Um outlier × 10 continua sendo apenas "o maior", e dobrar o sigma não muda os postos sob H0.
- Em todas as situações, o Mann-Whitney fica perto de 5% (de 4,4% a 4,9%), e o Welch fica conservador, de forma extrema com assimetria extrema (0,42%).
- Os outliers quase não mudam o resultado. Eles caem nos dois grupos com a mesma chance, e numa lognormal com sigma = 2,23 já existem valores 10 vezes maiores que a mediana. A violação que mais pesa é a assimetria.

### Quando a vantagem mudaria de lado (checagem exploratória)

Mesma grade com n = 30, seed 42 e 10.000 repetições, variando sigma, ou seja, o quão assimétrico é o tempo de merge:

| sigma | Efeito | Poder Welch | Poder MW |
|---|---|---|---|
| 0,1 | 0,05 | 48,8% | 46,5% |
| 0,3 | 0,15 | 52,0% | 51,5% |
| 0,6 | 0,15 | 15,2% | 16,3% |
| 1,0 | 0,30 | 17,8% | 24,4% |

O Welch só empata ou passa um pouco à frente com dados **quase simétricos** (sigma ≤ 0,3). A partir de
sigma ≈ 0,6, o Mann-Whitney já é melhor. Os dados reais têm sigma ≈ 2,2.

Para refazer esta checagem: `rodar_grade({"base": gerar_dados}, TESTES, [0, efeito], 30, np.random.default_rng(42), params={"mediana": 55.7, "sigma": s})`.

## α = 0,01 (pergunta 12, F-A3)

`results/q1_q2_q3_alpha001.csv`

- **Erro tipo I (G3):** a linha de referência desce para 1%. Mann-Whitney 0,90% e Welch 0,04% na base. O Welch continua muito conservador (0,00% a 0,03% nas situações da Q3).
- **Poder (G4):** todas as curvas caem. Mann-Whitney em 0,9: 97,0% → 88,2%; em 0,8: 75,7% → 52,2%. Welch em 0,9: 36,6% → 8,7%. Um α menor troca erro tipo I por erro tipo II. Para manter o poder, seria preciso mais dados.

## Tamanho da amostra (F-A3)

`results/tamanho_amostra.csv`, efeito observado nos dados reais de **0,257** (mediana ajustada de 41,4 h com bot contra 55,7 h sem bot).

| n por grupo | 30 | 50 | 100 | 200 | 400 | 800 | 1.200 | 1.600 |
|---|---|---|---|---|---|---|---|---|
| Mann-Whitney | 7,3% | 10,0% | 15,0% | 25,4% | 44,3% | 73,5% | 88,5% | 95,8% |
| t de Welch | 2,3% | 3,1% | 4,6% | 6,3% | 9,9% | 15,1% | 19,8% | 24,1% |

- Com o n coletado, o poder é de 7% (Mann-Whitney) e 2% (Welch). O "não rejeita H0" dos dados reais era o esperado, mesmo que o efeito seja real.
- Para 80% de poder, seriam necessários cerca de **974 PRs por grupo** no Mann-Whitney. O Welch não chega a 80% nem com 1.600.
