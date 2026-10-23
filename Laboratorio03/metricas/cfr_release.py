"""CFR baseado em releases corretivas e janela de observação."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from metricas.corretiva import classificar_comparacoes, notas_por_tag


@dataclass(frozen=True)
class ResumoCFRRelease:
    cfr: float | None
    releases_avaliadas: int
    releases_falhas: int
    releases_censuradas: int


def _data(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def calcular_cfr_releases(
    releases: list[dict],
    comparacoes: list[dict],
    inicio: str | date,
    fim: str | date,
    janela_dias: int = 7,
) -> ResumoCFRRelease:
    """Calcula CFR (b); as últimas `janela_dias` datas são censuradas."""
    inicio_data = date.fromisoformat(inicio) if isinstance(inicio, str) else inicio
    fim_data = date.fromisoformat(fim) if isinstance(fim, str) else fim
    if fim_data < inicio_data:
        raise ValueError("O fim da janela deve ser igual ou posterior ao início.")
    if janela_dias <= 0:
        raise ValueError("A janela de recuperação deve ser positiva.")

    releases_principais = sorted(
        (
            release for release in releases
            if not release.get("draft", False)
            and not release.get("prerelease", False)
            and release.get("published_at")
            and inicio_data <= _data(release["published_at"]).date() <= fim_data
        ),
        key=lambda release: _data(release["published_at"]),
    )
    limite_censura = fim_data - timedelta(days=janela_dias - 1)
    avaliadas = [
        release for release in releases_principais
        if inicio_data <= _data(release["published_at"]).date() < limite_censura
    ]
    censuradas = sum(
        inicio_data <= _data(release["published_at"]).date() <= fim_data
        and _data(release["published_at"]).date() >= limite_censura
        for release in releases_principais
    )
    corretivas = classificar_comparacoes(comparacoes, notas_por_tag(releases))
    falhas = 0

    for release in avaliadas:
        instante = _data(release["published_at"])
        for seguinte in releases_principais:
            if seguinte is release:
                continue
            instante_seguinte = _data(seguinte["published_at"])
            intervalo = instante_seguinte - instante
            if intervalo < timedelta(0):
                continue
            if intervalo > timedelta(days=janela_dias):
                break
            if corretivas.get(seguinte.get("tag_name"), False):
                falhas += 1
                break

    return ResumoCFRRelease(
        cfr=falhas / len(avaliadas) if avaliadas else None,
        releases_avaliadas=len(avaliadas),
        releases_falhas=falhas,
        releases_censuradas=censuradas,
    )
