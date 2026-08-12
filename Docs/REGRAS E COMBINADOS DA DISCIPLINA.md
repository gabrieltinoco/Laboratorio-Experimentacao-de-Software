## Regras e Combinados da Disciplina
Documento de referência única com as regras gerais da disciplina e os combinados de
processo (Kanban/GitHub) que valem para todos os laboratórios.
---
### 1. Estrutura dos Laboratórios (sprints e pontuação)
| Laboratório | Estrutura | Pontuação | Total |
|---|---|---|---|
| Laboratório 01 | 3 sprints + Relatório Final | 4 + 4 + 4 + 3 | 15 pontos |
| Laboratório 02 | 3 sprints + Relatório Final | 5 + 5 + 5 + 5 | 20 pontos |
| Laboratório 03 | 3 sprints + Relatório Final | 5 + 5 + 5 + 5 | 20 pontos |
| Laboratório 04 | 3 sprints + Relatório Final | 5 + 5 + 5 + 5 | 20 pontos |
| Laboratório 05 | 3 sprints + Relatório Final | 5 + 5 + 5 + 5 | 20 pontos |
O Relatório Final é uma entrega própria, com pontuação separada das 3 sprints
técnicas — não está mais embutido na última sprint.
### 2. Grupos
- Os laboratórios deverão ser realizados **em trios**.
- Todo e cada aluno deve entregar no GitHub a tarefa, **individualmente** — ou
seja, mesmo trabalhando em grupo, a contribuição de cada aluno deve ser
identificável e rastreável no repositório (ver seção 6).
### 3. Apresentações
- Após a última Sprint de cada laboratório, haverá uma aula de apresentação do
relatório finalizado pelo grupo.
### 4. Desenvolvimento
- Os enunciados dos laboratórios são pontos de partida, e representam 60% do que
deve ser produzido pela equipe. Os demais 40% devem ser propostos pelo time no
processo de experimentação, com novas Questões-Pesquisa, Variáveis, Métricas e
conclusões.
- Os laboratórios devem ser realizados em repositório GitHub criado e
disponibilizado pelos próprios alunos.
- Todos os participantes do grupo devem realizar contribuições e commits.
- Os commits/pull requests devem estar devidamente descritos.
- Os códigos devem estar devidamente comentados.
- Atenção à organização de funções, arquivos, nomeações e pastas.
- Atenção à organização das branches.
### 5. Aula-Sprint
- Cada e todo aluno deverá ligar uma máquina do laboratório.
- Cada e todo aluno deverá logar em uma máquina do laboratório.
- Em determinado momento da aula, ocorrerá um momento de **Daily Scrum**. Todos
ficarão de pé, e cada aluno irá compartilhar tecnicamente:
- aprendizados;
- o que ele realizou na última sprint;
- em que está trabalhando agora;
- impedimentos.
- Em todas as aulas, cada grupo deverá apresentar ao professor o feedback do Kanban
(andamento do board), independentemente de ser dia de Daily Scrum completo.
- Deve haver **evolução semanal visível no board** — Kanban parado ou sem
movimentação perceptível de uma aula para a outra é tratado como falha de processo
(ver desconto de qualidade do board, seção 6).
---
### 6. Kanban e GitHub Projects (orientações gerais consolidadas dos laboratórios)
Estas regras complementam as da seção 2 e 4 acima e valem para todos os 5
laboratórios do semestre.
- **Ferramenta obrigatória: GitHub Projects (v2)**, vinculado ao repositório do
grupo — nativo do GitHub, gratuito e ilimitado, e reaproveita a mesma API
(GraphQL/REST) usada nos laboratórios de mineração de dados.
- **Cartões = Issues** do repositório, adicionadas ao Project (não usar "draft
issues" soltas).
- **Toda Issue deve ter um Assignee definido** (o integrante responsável) — é o
mecanismo nativo de "quem fez qual card", consultável via API, sem necessidade de
planilha ou tabela manual paralela.
- Colunas mínimas (campo Status): `Backlog → To Do → Doing → Review → Done`.
- **Limite de WIP obrigatório** na coluna Doing (sugestão: 2 cartões por pessoa
ativa no board).
- Cada sprint de cada laboratório vira um conjunto de Issues rastreáveis no board
(granularidade de tarefa, não só de sprint).
- **Snapshot semanal obrigatório:** o GitHub Projects v2 não mantém histórico de
mudanças de status consultável via API, então o grupo exporta, via script GraphQL,
o estado atual do board **a cada semana/aula** (não só ao final de cada sprint)
para um CSV. A série desses snapshots ao longo do semestre é a base de dados usada
nos laboratórios de dashboard e no meta-laboratório final, e é também a evidência
objetiva da evolução semanal exigida na seção 5.
- **Referencie o número da Issue em cada commit** (ex.: `#12 implementa consulta
GraphQL`), para que o GitHub vincule automaticamente commit ↔ Issue no histórico.
- **A correção do professor é feita sempre a partir do Kanban (GitHub Projects),
não apenas do relatório entregue.** Commits que não estiverem referenciados a
nenhuma Issue do board não serão considerados na correção, mesmo que estejam no
repositório.
- **Qualidade do board como parte da nota:** cada sprint tem até 10% de desconto
sobre sua pontuação condicionado à qualidade do uso do board (WIP respeitado,
Issues com Assignee definido e atualizadas, sem cartões "fantasmas" parados sem
movimentação, e evolução semanal visível).
- **Distribuição de trabalho desigual:** a distribuição de Issues por Assignee é
analisada automaticamente no laboratório final; desequilíbrio relevante entre
integrantes ao longo do semestre pode resultar em nota individual diferenciada
dentro do grupo, a critério do professor.
- O relatório de cada laboratório deve incluir o link do repositório/GitHub
Projects do grupo.
---
