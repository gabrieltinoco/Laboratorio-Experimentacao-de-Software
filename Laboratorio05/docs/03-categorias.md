# 03 — Classificação do estudo nas 7 categorias

> **Versão v1 (Sprint 1, antes da coleta).** A v2 será revisada na Sprint 3 com base no que foi de fato feito (A-3.2).

| Categoria | Classificação (v1) | Justificativa |
|---|---|---|
| **Natureza** | Aplicada | O objetivo é gerar conhecimento para uma decisão prática: qual banco embarcado usar para cada tipo de carga. Não buscamos uma teoria geral sobre motores de banco. O resultado vira recomendação para desenvolvedores e analistas. |
| **Objetivo** | Explicativo | Não basta descrever que um banco é mais rápido. Queremos explicar **por quê**: o tratamento de controle `duckdb_t1` separa o efeito do motor colunar (C2) do efeito do paralelismo (C3). Também testamos uma relação causa → efeito (engine → tempo), com hipóteses definidas antes da coleta. |
| **Abordagem** | Quantitativa | Todas as variáveis dependentes estão em escala de razão (`elapsed_ms`, `ops_sec`, `p99_ms`, `peak_rss_mb`). A análise usa testes de hipótese, tamanho de efeito (Cliff's δ), speedup com IC por bootstrap e correção de Holm. Não há dados qualitativos. |
| **Procedimento** | Experimental: experimento controlado em laboratório, com medidas repetidas | Manipulamos a variável independente (`engine`, com 3 tratamentos) e controlamos as demais (hardware, container com limites, versões, dados, configurações). A ordem é aleatorizada e cada item é medido várias vezes em todos os tratamentos, o que dá medidas repetidas e pareamento por consulta. |
| **Tempo** | Transversal | Cada observação é feita num único momento, com uma versão fixa de cada software. Não acompanhamos a evolução dos bancos entre versões nem ao longo do tempo. A coleta dura horas, não meses. |
| **Controle** | Alto | O ambiente é inteiramente do grupo. Cada bloco roda num container novo com CPU e memória limitados e o mesmo aquecimento. A ordem é sorteada com semente fixa, há checagem de correção por `result_hash` e teste de tendência para deriva. As variáveis de confusão restantes (temperatura, SO do host) são monitoradas, não eliminadas. |
| **Nível de evidência** | Experimento controlado com validade externa limitada | O controle e a aleatorização dão **alta validade interna**: podemos atribuir as diferenças ao engine. Mas há uma única máquina x86, uma carga sintética (TPC-H), dados de até ~1 GB, nenhuma concorrência entre processos e versões específicas. A generalização para outros contextos é limitada (ver ameaças externas em `06`). |
