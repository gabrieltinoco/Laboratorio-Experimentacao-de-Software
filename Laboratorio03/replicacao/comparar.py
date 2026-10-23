"""Compara os resultados DORA deste grupo com os de outro grupo.

Uso:
python -m replicacao.comparar --referencia dados/repositorios.csv \
    --replicacao caminho/para/repositorios.csv --saida replicacao/resultado
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

METRICAS = (
    "deploy_freq_semana",
    "deploy_freq_com_prereleases_semana",
    "deploy_freq_tags_semana",
    "lead_time_release_dias",
    "lead_time_commit_dias",
    "cfr_ci",
    "cfr_releases",
    "recuperacao_horas",
)
CATEGORIAS = (
    "categoria_frequencia",
    "categoria_lead_time",
    "categoria_cfr",
    "categoria_recuperacao",
    "categoria_geral",
)
CHAVE = "repositorio"


def _validar(df: pd.DataFrame, nome: str) -> None:
    obrigatorias = {CHAVE, *METRICAS, *CATEGORIAS}
    faltantes = sorted(obrigatorias - set(df.columns))
    if faltantes:
        raise ValueError(f"{nome} não contém as colunas obrigatórias: {', '.join(faltantes)}.")
    if df[CHAVE].isna().any() or df[CHAVE].astype(str).str.strip().eq("").any():
        raise ValueError(f"{nome} contém identificador de repositório vazio.")
    if df[CHAVE].duplicated().any():
        duplicados = df.loc[df[CHAVE].duplicated(keep=False), CHAVE].astype(str).unique()
        raise ValueError(f"{nome} contém repositórios duplicados: {', '.join(duplicados[:10])}.")


def comparar(
    referencia: pd.DataFrame, replicacao: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compara métricas e categorias nos repositórios presentes nos dois CSVs.

    Diferença relativa = (valor do outro grupo - referência) / |referência|.
    Quando a referência é zero, a diferença relativa é indefinida e não entra
    nas médias relativas; a diferença absoluta continua sendo reportada.
    """
    _validar(referencia, "A referência")
    _validar(replicacao, "A replicação")

    colunas = [CHAVE, *METRICAS, *CATEGORIAS]
    base = referencia[colunas].copy()
    outro = replicacao[colunas].copy()
    unido = base.merge(
        outro,
        on=CHAVE,
        how="inner",
        suffixes=("_referencia", "_replicacao"),
        validate="one_to_one",
    )
    repos_ref = set(base[CHAVE].astype(str))
    repos_rep = set(outro[CHAVE].astype(str))
    ausentes = [
        {CHAVE: repositorio, "situacao": "ausente na replicação"}
        for repositorio in sorted(repos_ref - repos_rep)
    ] + [
        {CHAVE: repositorio, "situacao": "ausente na referência"}
        for repositorio in sorted(repos_rep - repos_ref)
    ]
    divergencias_repositorios = pd.DataFrame(
        ausentes, columns=[CHAVE, "situacao"]
    )

    resumo_metricas = []
    divergencias_metricas = []
    for metrica in METRICAS:
        coluna_base = f"{metrica}_referencia"
        coluna_outro = f"{metrica}_replicacao"
        a = pd.to_numeric(unido[coluna_base], errors="raise")
        b = pd.to_numeric(unido[coluna_outro], errors="raise")
        validos = a.notna() & b.notna()
        diferenca = b[validos] - a[validos]
        relativos = diferenca[a[validos].ne(0)] / a[validos].abs().where(a[validos].ne(0))
        resumo_metricas.append({
            "metrica": metrica,
            "n_repositorios_referencia": len(referencia),
            "n_repositorios_replicacao": len(replicacao),
            "repositorios_comuns": len(unido),
            "n_comparaveis": int(validos.sum()),
            "n_sem_valor": int((~validos).sum()),
            "n_referencia_zero": int((validos & a.eq(0)).sum()),
            "diferenca_media_assinada": float(diferenca.mean()) if len(diferenca) else None,
            "diferenca_relativa_media_pct": (
                float(relativos.mean() * 100) if len(relativos) else None
            ),
            "diferenca_relativa_absoluta_media_pct": (
                float(relativos.abs().mean() * 100) if len(relativos) else None
            ),
        })
        for indice in unido.index[validos]:
            valor_base = float(a.loc[indice])
            valor_outro = float(b.loc[indice])
            delta = valor_outro - valor_base
            if delta == 0:
                continue
            divergencias_metricas.append({
                CHAVE: unido.loc[indice, CHAVE],
                "metrica": metrica,
                "valor_referencia": valor_base,
                "valor_replicacao": valor_outro,
                "diferenca_assinada": delta,
                "diferenca_relativa_pct": (
                    delta / abs(valor_base) * 100 if valor_base != 0 else None
                ),
            })

    resumo_categorias = []
    divergencias_categorias = []
    for categoria in CATEGORIAS:
        coluna_base = f"{categoria}_referencia"
        coluna_outro = f"{categoria}_replicacao"
        a, b = unido[coluna_base], unido[coluna_outro]
        validos = a.notna() & b.notna() & a.astype(str).ne("") & b.astype(str).ne("")
        iguais = a[validos].eq(b[validos])
        resumo_categorias.append({
            "categoria": categoria,
            "n_comparaveis": int(validos.sum()),
            "n_iguais": int(iguais.sum()),
            "n_diferentes": int((~iguais).sum()),
            "percentual_igual": float(iguais.mean() * 100) if len(iguais) else None,
        })
        for indice in unido.index[validos & a.ne(b)]:
            divergencias_categorias.append({
                CHAVE: unido.loc[indice, CHAVE],
                "categoria": categoria,
                "valor_referencia": a.loc[indice],
                "valor_replicacao": b.loc[indice],
            })

    return (
        pd.DataFrame(resumo_metricas),
        pd.DataFrame(resumo_categorias),
        pd.DataFrame(divergencias_metricas),
        pd.DataFrame(divergencias_categorias),
        divergencias_repositorios,
    )


def salvar(
    resultados: tuple[
        pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
    ],
    saida: str | Path,
) -> None:
    """Grava resumos, divergências e um relatório Markdown."""
    (
        metricas,
        categorias,
        divergencias_metricas,
        divergencias_categorias,
        divergencias_repositorios,
    ) = resultados
    pasta = Path(saida)
    pasta.mkdir(parents=True, exist_ok=True)
    metricas.to_csv(pasta / "metricas.csv", index=False)
    categorias.to_csv(pasta / "classificacoes.csv", index=False)
    divergencias_metricas.to_csv(pasta / "divergencias_metricas.csv", index=False)
    divergencias_categorias.to_csv(pasta / "divergencias_classificacao.csv", index=False)
    divergencias_repositorios.to_csv(pasta / "divergencias_repositorios.csv", index=False)

    linhas = [
        "# Comparação da replicação",
        "",
        "Diferença relativa calculada como `(replicação - referência) / "
        "|referência|`. Quando a referência é zero, ela é indefinida.",
        "",
        "## Diferença entre métricas",
        "",
        metricas.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Concordância das classificações",
        "",
        categorias.to_markdown(index=False, floatfmt=".2f"),
        "",
        "Os arquivos `divergencias_metricas.csv` e "
        "`divergencias_classificacao.csv` detalham as diferenças nos repositórios "
        "comuns. `divergencias_repositorios.csv` lista os que estão ausentes em "
        "um dos conjuntos.",
        "Revise as diferenças com o grupo antes de abrir Issues no repositório "
        "replicado.",
        "",
    ]
    (pasta / "relatorio.md").write_text("\n".join(linhas), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compara resultados DORA entre grupos.")
    parser.add_argument("--referencia", required=True, help="CSV de resultados deste grupo.")
    parser.add_argument("--replicacao", required=True, help="CSV de resultados do outro grupo.")
    parser.add_argument("--saida", default="replicacao/resultado", help="Pasta dos relatórios.")
    args = parser.parse_args(argv)

    resultados = comparar(
        pd.read_csv(args.referencia),
        pd.read_csv(args.replicacao),
    )
    salvar(resultados, args.saida)
    print(f"Relatório e divergências gravados em {args.saida}")


if __name__ == "__main__":
    main()
