# Análise RQ3 (estrutura do código)

> Arquivo gerado por [`src/analise_rq3.py`](../src/analise_rq3.py). Não editar à mão: rode `python src/analise_rq3.py --coletar` depois de adicionar código em `trials/`.

## Dados

- Trials com métricas estáticas: **8** (4 com IA, 4 sem IA), de **2** integrantes (2 pares completos).
- Trials registrados em `data/trials.csv` sem pasta de código em `trials/`: **40**. Eles entram na RQ1/RQ2, mas não podem ser medidos na RQ3.
- Ferramentas: Radon (complexidade, LOC, MI) e jscpd (duplicação), com os testes de aceitação excluídos da medição (ver [`docs/metricas_estaticas.md`](metricas_estaticas.md)).
- Teste: Wilcoxon signed-rank pareado por integrante, bilateral, alpha = 0.05.

## Métricas usadas

- `cc_media`: complexidade ciclomática média por função.
- `cc_total_por_kloc`: complexidade total por KLOC.
- `dup_percentual`: % de linhas duplicadas.
- `sloc`: SLOC (controle).
- `mi_medio`: Índice de Manutenibilidade (opcional).

## Estatística descritiva por tratamento

| metrica | tratamento | n | mediana | q1 | q3 | iqr | minimo | maximo |
|---|---|---|---|---|---|---|---|---|
| cc_media | com_ia | 4 | 1.50 | 1.00 | 2.00 | 1.00 | 1.00 | 2.00 |
| cc_media | sem_ia | 4 | 2.50 | 2.00 | 3.00 | 1.00 | 2.00 | 3.00 |
| cc_total_por_kloc | com_ia | 4 | 416.66 | 312.50 | 500.00 | 187.50 | 250.00 | 500.00 |
| cc_total_por_kloc | sem_ia | 4 | 466.66 | 312.50 | 600.00 | 287.50 | 250.00 | 600.00 |
| dup_percentual | com_ia | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| dup_percentual | sem_ia | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sloc | com_ia | 4 | 4.00 | 2.00 | 6.50 | 4.50 | 2.00 | 8.00 |
| sloc | sem_ia | 4 | 5.50 | 5.00 | 6.50 | 1.50 | 5.00 | 8.00 |
| mi_medio | com_ia | 4 | 77.76 | 70.64 | 84.62 | 13.98 | 69.84 | 84.62 |
| mi_medio | sem_ia | 4 | 73.89 | 69.89 | 77.88 | 7.99 | 69.84 | 77.88 |

## Outliers (cercas de Tukey, 1,5 × IQR, por tratamento)

Nenhum trial fora das cercas.

## Wilcoxon pareado (com_ia − sem_ia)

| metrica | n_pares | n_pares_nao_nulos | mediana_com_ia | mediana_sem_ia | mediana_diferenca | W | p_bilateral | rank_biserial | rejeita_h0 |
|---|---|---|---|---|---|---|---|---|---|
| cc_media | 2 | 2 | 1.5000 | 2.5000 | -1.0000 | 0.0000 | 0.5000 | -1.0000 | False |
| cc_total_por_kloc | 2 | 2 | 395.8325 | 445.8325 | -50.0000 | 0.0000 | 0.5000 | -1.0000 | False |
| dup_percentual | 2 | 0 | 0.0000 | 0.0000 | 0.0000 | - | - | - | False |
| sloc | 2 | 2 | 4.5000 | 6.0000 | -1.5000 | 0.0000 | 0.5000 | -1.0000 | False |
| mi_medio | 2 | 2 | 77.4950 | 73.8775 | 3.6175 | 0.0000 | 0.5000 | 1.0000 | False |

- **cc_media**: apenas 2 pares nao nulos: o menor p bilateral possivel e 0.500, logo o teste nao consegue rejeitar H0 com alpha = 0.05.
- **cc_total_por_kloc**: apenas 2 pares nao nulos: o menor p bilateral possivel e 0.500, logo o teste nao consegue rejeitar H0 com alpha = 0.05.
- **dup_percentual**: todas as diferencas sao zero; teste nao aplicavel (nao ha evidencia de diferenca).
- **sloc**: apenas 2 pares nao nulos: o menor p bilateral possivel e 0.500, logo o teste nao consegue rejeitar H0 com alpha = 0.05.
- **mi_medio**: apenas 2 pares nao nulos: o menor p bilateral possivel e 0.500, logo o teste nao consegue rejeitar H0 com alpha = 0.05.

## Conclusão

- **RQ3:** H0 não rejeitada para nenhuma métrica. Com os dados disponíveis, não há evidência de que o uso de IA altere complexidade, duplicação ou LOC.
- Com 2 pares, o Wilcoxon não tem como atingir p < 0.05. O resultado da RQ3 deve ser lido como descritivo até que o código dos demais trials seja commitado em `trials/`.
