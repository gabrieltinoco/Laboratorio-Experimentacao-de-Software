# Cenário, hipóteses e palpite inicial

Par escolhido: **P1, t de Welch × Mann-Whitney**.

## Pergunta

O uso de um bot de revisão de código muda o tempo até o merge de pull requests?

## Hipóteses

Sejam $F_{sem}$ e $F_{com}$ as distribuições do tempo até o merge (em horas) dos PRs sem bot e com bot de revisão.

| | Em palavras | Em notação |
|---|---|---|
| **H0** | O tempo até o merge tem a mesma distribuição com e sem bot. | $F_{sem} = F_{com}$ |
| **H1** | O tempo até o merge tem distribuições diferentes com e sem bot: em um dos grupos, os PRs tendem a ficar prontos para o merge antes. | $F_{sem} \neq F_{com}$ |

Como cada teste olha para uma característica diferente da distribuição, H0 e H1 ficam assim para cada um:

- **t de Welch:** H0: $\mu_{sem} = \mu_{com}$ × H1: $\mu_{sem} \neq \mu_{com}$ (médias).
- **Mann-Whitney:** H0: $P(X_{sem} > X_{com}) = 0{,}5$ × H1: $P(X_{sem} > X_{com}) \neq 0{,}5$ (um grupo tende a ter valores maiores que o outro).

Na simulação as duas distribuições têm a mesma forma e só muda a mediana. Por isso, sob H0 as duas versões valem ao mesmo tempo, e sob H1 as duas são falsas.

### Por que bicaudal

O bot pode **acelerar** o merge, porque aponta problemas cedo e poupa rodadas de revisão humana. Também pode **atrasar** o merge, porque gera mais comentários para o autor resolver antes da aprovação. Não temos motivo para descartar nenhum dos dois lados antes de olhar os dados, então o teste é **bicaudal**.

## O que cada teste compara

- **t de Welch** compara as **médias** dos dois grupos sem supor que as variâncias sejam iguais. A estatística é $t = (\bar{x}_{sem} - \bar{x}_{com}) / \sqrt{s^2_{sem}/n_{sem} + s^2_{com}/n_{com}}$, com graus de liberdade de Welch-Satterthwaite. Supõe que as médias amostrais sejam aproximadamente normais, o que depende do tamanho da amostra e da cauda dos dados.
- **Mann-Whitney** compara os **postos**. Ordena todas as observações juntas e verifica se os PRs de um grupo tendem a ocupar posições mais altas que os do outro. Usa só a ordem dos valores, então não depende de normalidade e um valor extremo pesa tanto quanto o segundo maior.

## Nível de significância

α = 0,05.

## Erro tipo I e erro tipo II neste cenário

- **Erro tipo I** (rejeitar H0 verdadeira): concluir que o bot muda o tempo até o merge quando ele não muda. Consequência: o time adota o bot, ou mantém a assinatura dele, esperando ganho de velocidade, e paga custo de licença e de ruído nos PRs por um efeito que não existe.
- **Erro tipo II** (não rejeitar H0 falsa): concluir que não há diferença quando o bot de fato muda o tempo até o merge. Consequência: o time descarta um bot que encurtaria o ciclo de revisão, ou não percebe que ele está atrasando os merges.

## Palpite registrado antes de simular

> **Registrado em 04/11/2026, antes de qualquer simulação. Este bloco não será alterado depois.**
>
> Esperamos que o **Mann-Whitney se saia melhor** que o t de Welch neste cenário:
>
> 1. **Poder:** o Mann-Whitney deve ter mais poder para detectar uma redução da mediana. O tempo até o merge é muito assimétrico, com cauda longa à direita (alguns PRs ficam abertos por semanas). No t de Welch, esses poucos valores enormes inflam a variância e dominam a média, e a diferença entre os grupos se perde no ruído. O Mann-Whitney usa postos e não é afetado pelo tamanho da cauda.
> 2. **Erro tipo I:** com H0 verdadeira, os dois testes devem ficar perto de 5%. O Mann-Whitney deve ficar mais perto, e o Welch pode ficar um pouco **conservador** (abaixo de 5%) com n = 30, porque a cauda longa faz a estatística t ter caudas mais leves que a t de Student.
> 3. **Violações (Q3):** com assimetria ainda maior, outliers ou amostras pequenas, a vantagem do Mann-Whitney deve aumentar.

## Dados reais

- **Origem:** PRs do repositório público [microsoft/PowerToys](https://github.com/microsoft/PowerToys) com merge entre 01/08/2026 e 31/10/2026, coletados pela API REST do GitHub em 04/11/2026 (`src/coleta.py`). Detalhes, critério e limitações em [`data/real/FONTE.md`](../data/real/FONTE.md).
- **Grupos:** "com bot" = PR com review do `copilot-pull-request-reviewer[bot]`; "sem bot" = PR sem review desse bot. PRs abertos por bots foram excluídos.
- **Observações:** **30 PRs com bot** e **30 PRs sem bot**, sorteados com semente 42 entre os 483 PRs abertos por pessoas no período.
- **Variável:** `horas_ate_merge = merged_at − created_at`.

## Como os dados da simulação são gerados

O tempo de merge real é muito assimétrico. A mediana é de 52 h sem bot e 37 h com bot, mas as médias são de 332 h e 236 h, e há PRs que esperaram meses. Em escala log, os dados ficam próximos de uma normal: a assimetria de `log(horas)` é −0,06 com bot e −1,12 sem bot, e o teste de Shapiro-Wilk em `log(horas)` dá p = 0,61 com bot e p = 0,02 sem bot, este último puxado por um PR com merge em 1 minuto. Por isso usamos uma **lognormal**.

Os parâmetros saem de `src/parametros.py` e não são digitados à mão: `mu = mean(log(x))`, `sigma = std(log(x), ddof=1)` e `mediana = e^mu`, por grupo.

| Grupo | n | mu | sigma | Mediana ajustada (e^mu) |
|---|---|---|---|---|
| com bot | 30 | 3,723 | 2,099 | 41,4 h |
| sem bot | 30 | 4,020 | 2,365 | 55,7 h |

**Simulação base:** o tempo de merge real é assimétrico, com mediana de 55,7 h no grupo sem bot. Usamos uma lognormal com **mediana 55,7 h** e **sigma 2,23**, a média dos sigmas dos dois grupos, para ambos os grupos.

- **Sob H0** (efeito = 0), os dois grupos vêm exatamente da mesma lognormal.
- **Sob H1**, o grupo com bot tem a mediana reduzida em uma fração `efeito`, ou seja, mediana × (1 − efeito), com o mesmo sigma. Por exemplo, efeito = 0,3 dá mediana de 39 h, perto da diferença observada nos dados reais (41,4 / 55,7 ≈ 0,74, isto é, efeito ≈ 0,26).

Usar o mesmo sigma nos dois grupos faz com que, sob H1, uma distribuição seja a outra multiplicada por uma constante. Assim a média, a mediana e P(X_sem > X_com) mudam todas na mesma direção, e os dois testes procuram o mesmo efeito.

O gerador é `gerar_dados(n, mediana, sigma, efeito, rng, n_rep)` em `src/simulacao.py`. Um conjunto de exemplo (n = 30 por grupo, efeito = 0,3, seed 42) está em `results/exemplo_simulado.csv`.
