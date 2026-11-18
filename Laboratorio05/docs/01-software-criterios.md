# 01 — Software e comprovação dos 3 critérios

O objeto do estudo são dois bancos de dados embarcados **em funcionamento**, executados no ambiente do grupo:

- **SQLite**: banco relacional embarcado orientado a linhas. Vem dentro de sistemas operacionais, navegadores e celulares.
- **DuckDB**: banco analítico embarcado, colunar e com execução vetorizada. Muitas vezes é descrito como "o SQLite da análise de dados".

Os dois resolvem o mesmo problema (um banco SQL dentro do processo da aplicação, sem servidor), mas com arquiteturas opostas. Por isso a comparação é justa e útil para quem precisa escolher entre eles.

Todas as fontes estão em [`impacto/fontes.yaml`](impacto/fontes.yaml). Os prints ficam em `evidencias/AAAA-MM-DD-<id>.png`.

## 1. SQLite

| Critério | Evidência | Fonte | Data de acesso |
|---|---|---|---|
| **Real** | Projeto com site e documentação oficiais, mantido por Hipp, Wyrick & Company, Inc. | [sqlite.org](https://www.sqlite.org/) | 2026-11-18 |
| **Real** | O SQLite Consortium é uma associação de membros "dedicada a garantir a vitalidade contínua e a independência do SQLite". Cada membro tem 23 dias por ano de dedicação dos desenvolvedores. | [sqlite.org/consortium.html](https://www.sqlite.org/consortium.html) | 2026-11-18 |
| **Em operação** | Versão estável atual: **3.54.1** (2026-10-16), patch da 3.54.0 (2026-10-09). | [releaselog 3.54.1](https://www.sqlite.org/releaselog/3_54_1.html) | 2026-11-18 |
| **Em operação** | Política de suporte: "a intenção dos desenvolvedores é dar suporte ao SQLite até o ano de **2050**". | [sqlite.org/lts.html](https://www.sqlite.org/lts.html) | 2026-11-18 |
| **Em operação** | Usado em produção por Adobe (Lightroom, Acrobat), Airbus (software de voo do A350 XWB), Apple (macOS, iOS), Bosch (multimídia automotiva), Dropbox, Facebook (osquery), Google (Android, Chrome), Intuit (QuickBooks, TurboTax), Microsoft (componente do Windows 10), Mozilla (Firefox, Thunderbird), PHP, Python e RPM. | [sqlite.org/famous.html](https://www.sqlite.org/famous.html) | 2026-11-18 |
| **Alto impacto** | Presente em todo Android, todo iPhone/iOS, todo Mac, toda instalação de Windows 10/11 e em todo Firefox, Chrome e Safari. Há **mais de 4,0 bilhões** de smartphones em uso, e a estimativa é de **mais de 1 trilhão** de bancos SQLite ativos. "Provavelmente usado mais que todos os outros motores de banco somados." | [sqlite.org/mostdeployed.html](https://www.sqlite.org/mostdeployed.html) (atualizada em 2026-04-21) | 2026-11-18 |
| **Alto impacto** | Stack Overflow Developer Survey 2025: **37,5%** dos respondentes usam SQLite (36,9% entre profissionais). | [survey.stackoverflow.co/2025](https://survey.stackoverflow.co/2025/technology/) | 2026-11-18 |
| **Alto impacto** | DB-Engines Ranking (nov/2026): score **94,68**, **#11** no geral e **#8** entre os SGBDs relacionais. | [db-engines.com](https://db-engines.com/en/system/DuckDB%3BSQLite) | 2026-11-18 |

## 2. DuckDB

| Critério | Evidência | Fonte | Data de acesso |
|---|---|---|---|
| **Real** | Projeto com site e documentação oficiais. | [duckdb.org](https://duckdb.org/) | 2026-11-18 |
| **Real** | A Stichting DuckDB Foundation (Holanda), sem fins lucrativos, detém a propriedade intelectual e as marcas. A licença é **MIT, irrevogável**. Apoiadores: AWS, MotherDuck e Posit (gold), Cloudflare, Hugging Face, PostHog, Hex e outros. | [duckdb.foundation](https://duckdb.foundation/) | 2026-11-18 |
| **Real** | DuckDB Labs, empresa dos criadores (H. Mühleisen e M. Raasveldt), que desenvolve o núcleo e vende suporte. | [duckdblabs.com](https://duckdblabs.com/) | 2026-11-18 |
| **Em operação** | Versão estável atual: **2.0.0 LTS "Cinnamon Teal"** (2026-10-21), com suporte até pelo menos outubro de 2027. | [Anúncio 2.0.0](https://duckdb.org/2026/10/21/announcing-duckdb-200) | 2026-11-18 |
| **Em operação** | Política de suporte: a cada duas versões uma é LTS, com 1 ano de suporte comunitário. Fim de vida da 2.0.0: 2027-10-22. Próximo release (2.0.1) previsto para 2026-11-19. | [release_calendar](https://duckdb.org/release_calendar) | 2026-11-18 |
| **Em operação** | Empresas que financiam e usam o projeto em produtos (AWS, MotherDuck, Posit, Hugging Face, PostHog, Hex, Mode, Rill). | [duckdb.foundation](https://duckdb.foundation/) | 2026-11-18 |
| **Alto impacto** | PyPI: **79.963.100** downloads do pacote `duckdb` nos últimos 30 dias (3,47 milhões no último dia). | [pypistats](https://pypistats.org/api/packages/duckdb/recent) | 2026-11-18 |
| **Alto impacto** | Stack Overflow Developer Survey 2025: **3,3%** dos respondentes usam DuckDB (3,2% entre profissionais). | [survey.stackoverflow.co/2025](https://survey.stackoverflow.co/2025/technology/) | 2026-11-18 |
| **Alto impacto** | DB-Engines Ranking (nov/2026): score **12,18**, **#40** no geral e **#24** entre os SGBDs relacionais. O DuckDB foi lançado em 2018, e o SQLite, em 2000. | [db-engines.com](https://db-engines.com/en/system/DuckDB%3BSQLite) | 2026-11-18 |

> Downloads no PyPI incluem tráfego de CI e reinstalações, então não equivalem a usuários. Usamos esse número só como **ordem de grandeza** da adoção.

## 3. Versões usadas no experimento

| Componente | Versão | Por quê |
|---|---|---|
| Python | 3.12+ (imagem `python:3.12-slim`) | versão estável suportada pelas duas bibliotecas; a mesma no container e no host |
| `duckdb` | **2.0.0** | versão estável atual e LTS (suporte até 2027-10). Inclui as extensões `tpch` (gera dados e consultas TPC-H) e `sqlite` (copia as tabelas para o SQLite) |
| `apsw` | **3.54.1.0** → SQLite **3.54.1** | o `apsw` traz o SQLite embutido numa versão fixa. Assim o resultado não depende do SQLite do sistema operacional nem do módulo `sqlite3` da biblioteca padrão. 3.54.1 é a versão estável atual |
| demais | ver `requirements.lock` | fixadas com `pip freeze` em 2026-11-18 |

Cada run registra `duckdb.__version__` e `apsw.sqlitelibversion()` em `data/raw/env.json`.

> **Atenção à 2.0.0:** é um *major* recém-lançado, e a 2.0.1 (correções) sai em 2026-11-19. Se a 2.0.1 sair antes do piloto, atualizar o `requirements.lock` e esta tabela antes de rodar a coleta. Depois do piloto, a versão fica congelada até o fim.

## 4. Confirmação com o professor

O professor precisa confirmar que nenhum outro grupo escolheu DuckDB/SQLite. Plano reserva, caso já tenham escolhido: *Nginx gzip × brotli × zstd* (ver `planejamento.md`).

| Data | Resposta do professor |
|---|---|
| _(pendente)_ | _(registrar aqui)_ |
