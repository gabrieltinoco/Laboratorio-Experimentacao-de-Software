from kata import ordenar_pedidos


def test_lista_vazia():
    assert ordenar_pedidos([]) == []


def test_prioridade_maior_primeiro():
    pedidos = [{"id": "a", "prioridade": 1, "prazo": 2, "chegada": 0}, {"id": "b", "prioridade": 3, "prazo": 9, "chegada": 1}]
    assert [p["id"] for p in ordenar_pedidos(pedidos)] == ["b", "a"]


def test_prazo_desempata_prioridade():
    pedidos = [{"id": "a", "prioridade": 2, "prazo": 8, "chegada": 0}, {"id": "b", "prioridade": 2, "prazo": 3, "chegada": 1}]
    assert [p["id"] for p in ordenar_pedidos(pedidos)] == ["b", "a"]


def test_chegada_desempata_prazo():
    pedidos = [{"id": "a", "prioridade": 2, "prazo": 3, "chegada": 4}, {"id": "b", "prioridade": 2, "prazo": 3, "chegada": 1}]
    assert [p["id"] for p in ordenar_pedidos(pedidos)] == ["b", "a"]


def test_nao_muda_lista_original():
    pedidos = [{"id": "a", "prioridade": 1, "prazo": 1, "chegada": 0}]
    ordenar_pedidos(pedidos)
    assert pedidos == [{"id": "a", "prioridade": 1, "prazo": 1, "chegada": 0}]


def test_preserva_dados_do_pedido():
    pedido = {"id": "a", "prioridade": 1, "prazo": 1, "chegada": 0, "cliente": "x"}
    assert ordenar_pedidos([pedido])[0] == pedido


def test_prioridade_zero_e_valida():
    assert ordenar_pedidos([{"id": "a", "prioridade": 0, "prazo": 1, "chegada": 0}])[0]["id"] == "a"


def test_ordena_tres_criterios():
    pedidos = [{"id": "a", "prioridade": 1, "prazo": 5, "chegada": 2}, {"id": "b", "prioridade": 3, "prazo": 9, "chegada": 2}, {"id": "c", "prioridade": 3, "prazo": 2, "chegada": 0}]
    assert [p["id"] for p in ordenar_pedidos(pedidos)] == ["c", "b", "a"]
