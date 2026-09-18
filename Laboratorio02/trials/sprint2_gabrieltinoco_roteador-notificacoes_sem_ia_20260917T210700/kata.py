"""Escolha de canal para o trial; a implementacao sera feita pelo participante."""


def escolher_canal(preferencias: list[str], disponiveis: set[str], fallback: str | None) -> str | None:
    for canal in dict.fromkeys(preferencias):
        if canal in disponiveis:
            return canal
    return fallback
