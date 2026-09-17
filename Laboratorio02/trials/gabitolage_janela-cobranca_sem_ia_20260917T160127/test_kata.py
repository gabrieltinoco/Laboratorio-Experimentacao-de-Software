from kata import agrupar_cobrancas


def test_sem_eventos():
    assert agrupar_cobrancas([], 0, 10) == {}


def test_evento_na_primeira_janela():
    assert agrupar_cobrancas([{"instante": 2, "valor": 7}], 0, 10) == {0: 7}


def test_evento_na_segunda_janela():
    assert agrupar_cobrancas([{"instante": 10, "valor": 7}], 0, 10) == {1: 7}


def test_fronteira_inicial():
    assert agrupar_cobrancas([{"instante": 0, "valor": 4}], 0, 10) == {0: 4}


def test_soma_eventos_da_mesma_janela():
    eventos = [{"instante": 1, "valor": 4}, {"instante": 9, "valor": 6}]
    assert agrupar_cobrancas(eventos, 0, 10) == {0: 10}


def test_preserva_janelas_com_intervalo_vazio():
    eventos = [{"instante": 1, "valor": 4}, {"instante": 21, "valor": 6}]
    assert agrupar_cobrancas(eventos, 0, 10) == {0: 4, 2: 6}


def test_inicio_deslocado():
    assert agrupar_cobrancas([{"instante": 12, "valor": 5}], 10, 10) == {0: 5}


def test_valor_zero_e_contabilizado():
    assert agrupar_cobrancas([{"instante": 2, "valor": 0}], 0, 10) == {0: 0}