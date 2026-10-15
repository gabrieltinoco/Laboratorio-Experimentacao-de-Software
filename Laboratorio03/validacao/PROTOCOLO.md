# Protocolo da validação manual (amostra-ouro)

Este protocolo define como a amostra-ouro é sorteada, rotulada e consolidada. Ele serve de referência para a heurística de release corretiva (RQ 03 b) e para o fator *tipo do projeto* (RQ 06).

## 1. Sorteio

Comando: `python -m validacao.gerar_planilha --config config.yaml`

- **Repositórios:** 60 da amostra final (`dados/repositorios.csv`), ordenada por nome e sorteada com `DataFrame.sample(n=60, random_state=42)`.
- **Releases:** para cada repositório sorteado, 5 releases principais (`draft = false`, `prerelease = false`) publicadas na janela, sorteadas com a mesma semente. Todo repositório da amostra tem pelo menos 5 releases desse tipo (critério de inclusão), então são sempre 300 releases.
- O sorteio fica registrado em `amostra_ouro.csv`. Os parâmetros (semente, tamanhos, identificadores dos avaliadores) estão na seção `validacao` do `config.yaml`.

Cada avaliador recebe a própria planilha, `rotulos_<avaliador>.xlsx`, com links para o repositório, para a página de cada release (*release notes*) e para a lista de commits desde a release anterior (`compare`). A planilha **não** mostra a saída da heurística nem o número de versão anterior interpretado. O script não sobrescreve planilhas existentes, a menos que receba `--sobrescrever`.

## 2. Avaliadores e independência

O grupo tem **dois** integrantes, que fazem a rotulação. O enunciado prevê três avaliadores. Com dois, as adaptações são:

| Enunciado (3 avaliadores) | Este grupo (2 avaliadores) |
|---|---|
| kappa de Fleiss | kappa de **Cohen** como medida principal; o de Fleiss também é reportado |
| desempate por maioria simples | **todo** caso divergente vai para a reunião de consenso |

Regras de independência:

1. Cada avaliador preenche a própria planilha **sem consultar o outro** e sem ver a saída da heurística nem o código de `metricas/corretiva.py`.
2. Dúvidas sobre o critério vão na coluna `observacoes`, não para o outro avaliador. Se o critério precisar ser esclarecido no meio da rotulação, o esclarecimento é registrado na seção 6 e vale para os dois.
3. As planilhas são commitadas antes da reunião de consenso e não são editadas depois dela.

## 3. Critérios de rotulação

### 3.1 `tipo_projeto` (por repositório)

Decidido pelo **uso principal** descrito no README e na documentação.

| Valor | Quando usar | Exemplos |
|---|---|---|
| `biblioteca/framework` | consumido como dependência por outro código: pacote em registro (PyPI, npm, crates.io, Maven…), SDK, framework, plugin | `pallets/flask`, `serde-rs/serde` |
| `aplicação/serviço` | executado por usuário final ou implantado como serviço: app desktop, mobile ou web, servidor, banco de dados, sistema *self-hosted* | `bottlesdevs/Bottles`, `immich-app/immich` |
| `ferramenta CLI` | usado principalmente pela linha de comando, por desenvolvedores ou operadores; inclui ferramentas de build, linters e formatadores | `BurntSushi/ripgrep`, `astral-sh/ruff` |
| `outro` | o que não se encaixa acima: documentação, listas, coleções de modelos ou dados, configurações, temas | — |

Se o projeto tiver mais de uma face (ex.: biblioteca com CLI), vale a que o README apresenta primeiro.

### 3.2 `entregas_reais` (por repositório)

As releases do repositório representam **entregas reais ao usuário**?

- `sim`: as releases distribuem versões instaláveis ou utilizáveis (binários, pacotes publicados, imagens), em geral com notas de mudança voltadas a quem usa.
- `não`: as releases são automáticas ou não entregam software novo, como *nightlies*, *snapshots* por commit, releases só de dados ou documentação, ou tags criadas pelo CI sem conteúdo.
- `incerto`: as evidências não bastam para decidir.

### 3.3 `corretiva` (por release)

O **objetivo principal** da release é corrigir defeito(s) recente(s)?

- `sim`: as *release notes* ou os commits são dominados por correções (`fix`, `hotfix`, `bugfix`, regressão, `revert`, correção de segurança), sem funcionalidade nova relevante.
- `não`: a release traz funcionalidades novas, mudanças de comportamento ou manutenção de rotina (atualização de dependências, documentação), mesmo que inclua algumas correções.

Regras:

1. Julgue pelo **conteúdo** (notas e commits), não pelo número da versão. Uma versão *patch* que só adiciona funcionalidade é `não`, e uma versão *minor* lançada para corrigir uma regressão é `sim`.
2. Se as notas estiverem vazias, decida pela lista de commits do link `link_commits`.
3. Em releases mistas, conte as entradas: `sim` só se as correções forem a maioria clara e não houver funcionalidade nova destacada.

## 4. Concordância

Comando: `python -m validacao.concordancia --config config.yaml`

- O script recusa planilhas com células vazias ou com valores fora da lista permitida.
- Para cada dimensão (`tipo_projeto`, `entregas_reais`, `corretiva`), calcula a concordância observada, o kappa de Cohen (`sklearn.metrics.cohen_kappa_score`) e o kappa de Fleiss (`statsmodels`: `aggregate_raters` + `fleiss_kappa`), e salva em `concordancia.csv`.
- A interpretação segue Landis & Koch (1977): < 0 pobre; 0–0,20 leve; 0,21–0,40 razoável; 0,41–0,60 moderada; 0,61–0,80 substancial; 0,81–1 quase perfeita. Quando os dois avaliadores usam um único rótulo, o kappa é indefinido (0/0) e aparece como `indefinido`.
- Os itens divergentes vão para `divergencias.csv`.

## 5. Consenso

Com dois avaliadores não há maioria, então **todo** item divergente é decidido em reunião:

1. Os dois reabrem juntos os links do item e cada um explica o rótulo que deu, com base nos critérios da seção 3.
2. O rótulo acordado vai na coluna `rotulo_consenso` de `divergencias.csv` e a justificativa, em uma frase, na coluna `motivo`. A justificativa cita a evidência (ex.: "notas listam só correções da 2.3.0").
3. Se, depois da discussão, ainda não houver acordo, aplica-se a regra conservadora: `outro` para `tipo_projeto`, `incerto` para `entregas_reais` e `não` para `corretiva` (só é corretiva quando a evidência é clara). O motivo registra que a regra foi aplicada.
4. Rodar `python -m validacao.concordancia` de novo preserva as decisões já preenchidas.

Comando final: `python -m validacao.consenso --config config.yaml`. Ele recusa a consolidação se faltar `rotulo_consenso` válido ou `motivo` em algum item, e gera:

- `consenso_repositorios.csv`: `tipo_projeto` e `entregas_reais` por repositório;
- `consenso_releases.csv`: `corretiva` por release, referência para precisão, recall e F1 da heurística.

O kappa reportado no artigo é o da rotulação independente, de antes do consenso.

## 6. Registro de esclarecimentos

Esclarecimentos de critério feitos durante a rotulação, com data:

| Data | Esclarecimento |
|---|---|
| — | — |
