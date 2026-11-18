#!/usr/bin/env bash
# Cria as labels e uma issue por card do Kanban do LAB05 (seção "Kanban" do
# docs/planejamento.md). Depois, adicione as issues ao GitHub Project.
#
# Uso:
#   GH_A=<login-integrante-A> GH_B=<login-integrante-B> bash scripts/kanban_seed.sh
# Opcional:
#   REPO=dono/repo   (padrão: repositório do diretório atual)
#   PROJECT=<n>      (número do GitHub Project; se definido, cada issue é adicionada a ele)
#   OWNER=<dono>     (dono do Project; padrão: dono do repositório)
#   DRY_RUN=1        (só imprime os comandos)
set -euo pipefail

REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
OWNER="${OWNER:-${REPO%%/*}}"
GH_A="${GH_A:?defina GH_A com o login do Integrante A}"
GH_B="${GH_B:?defina GH_B com o login do Integrante B}"

run() {
  if [[ "${DRY_RUN:-0}" == "1" ]]; then printf '[dry-run] %q ' "$@"; echo; else "$@"; fi
}

# ---------------------------------------------------------------- labels
label() {  # nome cor descrição
  run gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force
}
label integrante-A  1f77b4 "Tarefa do Integrante A (planejamento, método, impacto)"
label integrante-B  ff7f0e "Tarefa do Integrante B (instrumentação, operação, comunicação)"
label sprint-1      c5def5 "LAB05 Sprint 1"
label sprint-2      bfd4f2 "LAB05 Sprint 2"
label sprint-3      a2c4f5 "LAB05 Sprint 3"
label sprint-final  7f9fd9 "LAB05 Sprint final"
label doc           0e8a16 "Documentação"
label codigo        5319e7 "Código"
label dados         fbca04 "Coleta e dados"

# ---------------------------------------------------------------- issues
# card <integrante A|B> <sprint-label> <labels extras, separadas por vírgula ou vazio> <título> <critério de pronto>
card() {
  local who="$1" sprint="$2" extra="$3" title="$4" done_crit="$5"
  local login labels
  if [[ "$who" == "A" ]]; then login="$GH_A"; else login="$GH_B"; fi
  labels="integrante-$who,$sprint"
  [[ -n "$extra" ]] && labels="$labels,$extra"
  local body
  body="Tarefa do LAB05. Passos detalhados em \`Laboratorio05/docs/planejamento.md\`.

**Critério de pronto:** $done_crit"
  local url
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    run gh issue create --repo "$REPO" --title "[LAB05] $title" --body "$body" --label "$labels" --assignee "$login"
    return
  fi
  url=$(gh issue create --repo "$REPO" --title "[LAB05] $title" --body "$body" --label "$labels" --assignee "$login")
  echo "$url"
  if [[ -n "${PROJECT:-}" ]]; then
    gh project item-add "$PROJECT" --owner "$OWNER" --url "$url" >/dev/null
  fi
}

# Integrante A
card A sprint-1 codigo     "A-1.1 Estrutura do repo, convenções, config.yaml, lockfile e Kanban" "pytest roda; Project com todos os cards"
card A sprint-1 doc        "A-1.2 DuckDB e SQLite: evidências dos 3 critérios" "Tabela por software com fonte e data; OK do professor"
card A sprint-1 doc        "A-1.3 GQM, hipóteses H1–H5, variáveis e design" "Template Basili; escala de cada métrica; justificativa do duckdb_t1"
card A sprint-1 doc        "A-1.4 7 categorias v1 + plano de coleta/análise" "Protocolo, critério de validade, timeout, plano estatístico, critérios do piloto"
card A sprint-2 codigo     "A-2.1 Estatística descritiva" "4 testes passando"
card A sprint-2 codigo     "A-2.2 Testes, Holm, Cliff's δ, speedup, análise entre consultas" "9 testes passando, incluindo censura e variância zero"
card A sprint-2 codigo     "A-2.3 Gráficos + gerador de relatório" "make analyze PHASE=pilot gera o 07 e as figuras"
card A sprint-2 doc        "A-2.4 Ameaças à validade (4 tipos)" "≥ 2 por tipo, com mitigação"
card A sprint-3 codigo,doc "A-3.1 Fontes e cálculo de impacto" "fontes.yaml com link e data; 3 cenários; 'o que não podemos afirmar'"
card A sprint-3 doc        "A-3.2 7 categorias revisadas" "v2 justificada + força da evidência"
card A sprint-3 doc        "A-3.3 Reaproveitamento dos labs" "Tabela Lab01–04"
card A sprint-final doc    "A-F.1 Documento final" "Checklist da seção 8 completo; números conferidos"
card A sprint-final doc    "A-F.2 Guia de defesa" "≥ 20 perguntas, cobrindo as partes de B"

# Integrante B
card B sprint-1 codigo,dados     "B-1.1 Dockerfile + geração/carga TPC-H nos 2 bancos" "5 testes passando; make data gera sf 0,1 e 1"
card B sprint-1 codigo           "B-1.2 22 consultas nos 2 dialetos + hash + OLTP" "22/22 hashes iguais; testes OLTP passando"
card B sprint-1 codigo           "B-1.3 Agenda sorteada, runner, orquestrador, resume, timeout, preflight" "9 testes passando; --dry-run ok"
card B sprint-1 codigo,dados,doc "B-1.4 Validação, manifest, poder + coleta piloto" "Piloto válido; tag pilot-v1; decisões de n e censura no 05"
card B sprint-2 dados            "B-2.1 Coleta completa" "validate sem problemas; tag data-v1; manifest"
card B sprint-2 doc              "B-2.2 Rodar análise + interpretação" "07 final respondendo Q1–Q5"
card B sprint-3 doc              "B-3.1 Conclusões e limitações" "Responde às 2 perguntas + recomendação prática"
card B sprint-3 codigo           "B-3.2 Dashboard Streamlit" "Filtros + calculadora de impacto funcionando"
card B sprint-3 doc              "B-3.3 Rascunho do relatório e roteiro" "Relatório montado; roteiro de 10 min"
card B sprint-final doc          "B-F.1 Apresentação final" "Slides + demo + vídeo de backup"
card B sprint-final ""           "B-F.2 Ensaio e entrega" "≤ 10 min; tag v1.0-entrega; entregue no Canvas"

echo "Pronto: labels e 24 issues criadas em $REPO."
