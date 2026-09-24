# Análise RQ1 (tempo) e RQ2 (defeitos)

> Arquivo gerado por [`src/analise_rq1_rq2.py`](../src/analise_rq1_rq2.py). Não editar à mão: rode o script de novo depois de mudar `data/trials.csv`.

## Dados

- Trials analisados: **48** (24 com IA, 24 sem IA), de **12** integrantes.
- Trials censurados no time-box (tempo registrado como 35 min): **0**.
- Pareamento: mediana de cada integrante em cada tratamento. Cada integrante resolve cada kata uma única vez, então o par é o integrante, não a kata.
- Teste: Wilcoxon signed-rank pareado, bilateral, alpha = 0.05. O p unilateral, na direção da H1, aparece como complemento.

## Estatística descritiva por tratamento

| metrica | tratamento | n | mediana | q1 | q3 | iqr | minimo | maximo |
|---|---|---|---|---|---|---|---|---|
| tempo_ate_verde_min | com_ia | 24 | 4.88 | 2.71 | 6.12 | 3.42 | 2.03 | 12.50 |
| tempo_ate_verde_min | sem_ia | 24 | 5.94 | 4.08 | 7.89 | 3.81 | 2.62 | 31.90 |
| testes_falhando | com_ia | 24 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| testes_falhando | sem_ia | 24 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| taxa_sucesso | com_ia | 24 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 |
| taxa_sucesso | sem_ia | 24 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 |

Trials com todos os testes passando: com_ia = 100.0%, sem_ia = 100.0%.

## Outliers (cercas de Tukey, 1,5 × IQR, por tratamento)

Outliers são apenas sinalizados e **permanecem** na análise. O teste usa postos e a mediana por integrante, que são pouco sensíveis a valores extremos.

| metrica | tratamento | integrante | kata | valor | cerca_inferior | cerca_superior |
|---|---|---|---|---|---|---|
| tempo_ate_verde_min | com_ia | Gabriel L. Tinoco | janela-cobranca | 12.50 | -2.42 | 11.25 |
| tempo_ate_verde_min | sem_ia | Gabriel L. Tinoco | agenda-recorrente | 31.90 | -1.64 | 13.61 |
| tempo_ate_verde_min | sem_ia | Gabriel L. Tinoco | roteador-notificacoes | 22.30 | -1.64 | 13.61 |

## Wilcoxon pareado (com_ia − sem_ia)

| metrica | n_pares | n_pares_nao_nulos | mediana_com_ia | mediana_sem_ia | mediana_diferenca | W | p_bilateral | p_unilateral | rank_biserial | rejeita_h0 |
|---|---|---|---|---|---|---|---|---|---|---|
| tempo_ate_verde_min | 12 | 12 | 4.7025 | 5.4800 | -1.8150 | 12.0000 | 0.0342 | 0.0171 | -0.6923 | True |
| testes_falhando | 12 | 0 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | False |
| taxa_sucesso | 12 | 0 | 1.0000 | 1.0000 | 0.0000 | - | - | - | - | False |

`rank_biserial` vai de −1 a 1. Valor negativo indica valores menores com IA. Como referência, |r| ≥ 0,1 é um efeito pequeno, ≥ 0,3 é médio e ≥ 0,5 é grande.

- **testes_falhando**: todas as diferencas sao zero; teste nao aplicavel (nao ha evidencia de diferenca).
- **taxa_sucesso**: todas as diferencas sao zero; teste nao aplicavel (nao ha evidencia de diferenca).

## Conclusão

- **RQ1:** H0 rejeitada (p = 0.0342). Com IA, o tempo até passar em todos os testes foi menor: a diferença mediana pareada é -1.81 e r = -0.69.
- **RQ2:** não houve diferença entre os tratamentos para o número de testes falhando (todas as diferenças pareadas são zero). H0 não é rejeitada.
