"""Ordenacao de pedidos para o trial; a implementacao sera feita pelo participante."""


def ordenar_pedidos(pedidos: list[dict]) -> list[dict]:
    return sorted(pedidos, key=lambda pedido: (-pedido["prioridade"], pedido["prazo"], pedido["chegada"]))
