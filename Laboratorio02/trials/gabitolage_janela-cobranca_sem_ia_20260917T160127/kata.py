"""Agregacao de cobrancas para o trial; a implementacao sera feita pelo participante."""


def agrupar_cobrancas(eventos: list[dict], inicio: int, tamanho: int) -> dict[int, int]:
    janelas: dict[int, int] = {}
    for evento in eventos:
        indice = (evento["instante"] - inicio) // tamanho
        janelas[indice] = janelas.get(indice, 0) + evento["valor"]
    return janelas
