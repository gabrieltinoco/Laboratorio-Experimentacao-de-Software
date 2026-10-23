# Replicação cruzada

> **Estado (23/10/2026): pendente.** O grupo cujo pipeline vamos replicar
> ainda não foi identificado no repositório. Faltam o endereço do repositório
> dele, o CSV original e a lista de 30 repositórios. Esta seção traz o
> procedimento já preparado. Os resultados só devem ser escritos depois da
> execução real.

## Replicação do pipeline de outro grupo

Procedimento, conforme a seção 9 do enunciado:

1. Clonar o repositório do grupo autor e seguir **somente** o README. Registrar
   o ambiente (sistema operacional, versão do Python), cada comando executado,
   o tempo de execução e cada erro, sem pedir ajuda ao grupo autor.
2. Rodar o pipeline sobre a subamostra de 30 repositórios indicada por eles.
3. Comparar com o CSV original usando o comparador do nosso grupo:

   ```powershell
   Set-Location .\Laboratorio03
   python -m replicacao.comparar --referencia caminho\para\original.csv --replicacao caminho\para\replicado.csv --saida replicacao\resultado
   ```

   O comparador calcula, para cada métrica, a diferença absoluta e a relativa
   `(replicação − referência) / |referência|`. Também calcula o percentual de
   repositórios com a mesma categoria DORA e lista os repositórios que
   aparecem em só um dos datasets.
4. Explicar as diferenças pela data da coleta, pelas mudanças nos
   repositórios, pelos filtros aplicados e pelas definições operacionais de
   cada grupo.
5. Abrir no repositório do grupo autor uma Issue por problema observado, com o
   comando, a mensagem de erro e os valores esperados e obtidos.

Resultados: *a preencher após a execução.*

| Métrica | Diferença relativa média | Mesma categoria DORA (%) |
|---|---:|---:|
| Frequência de deploy | — | — |
| Lead time | — | — |
| CFR | — | — |
| Tempo de recuperação | — | — |

## Preparação do nosso pipeline para ser replicado

- O README documenta a instalação, o token, a execução completa e a execução
  sobre uma subamostra (`--repos replicacao/subamostra_30.txt --saida
  dados_replicacao`). A lista de 30 repositórios foi sorteada com semente 42.
- `dados/DICIONARIO.md` descreve cada coluna com tipo, unidade e fórmula.
- `python -m pipeline.recalcular` refaz `repositorios.csv` a partir dos `.jsonl`
  coletados, sem chamar a API.
- Até 23/10/2026, nenhuma Issue de grupo replicador tinha sido aberta no nosso
  repositório. As que chegarem devem entrar no GitHub Projects, com
  responsável, e ser corrigidas ou respondidas com justificativa.
