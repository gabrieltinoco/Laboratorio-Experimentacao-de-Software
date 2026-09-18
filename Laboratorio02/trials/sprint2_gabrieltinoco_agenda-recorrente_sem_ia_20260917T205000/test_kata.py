from datetime import date

from kata import gerar_ocorrencias


def test_data_inicial_inclusa():
    assert gerar_ocorrencias(date(2026, 1, 1), 7, date(2026, 1, 1)) == [date(2026, 1, 1)]


def test_gera_datas_semanais():
    assert gerar_ocorrencias(date(2026, 1, 1), 7, date(2026, 1, 15)) == [date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 15)]


def test_nao_ultrapassa_data_final():
    assert gerar_ocorrencias(date(2026, 1, 1), 7, date(2026, 1, 10)) == [date(2026, 1, 1), date(2026, 1, 8)]


def test_intervalo_de_um_dia():
    assert gerar_ocorrencias(date(2026, 2, 1), 1, date(2026, 2, 3)) == [date(2026, 2, 1), date(2026, 2, 2), date(2026, 2, 3)]


def test_data_final_anterior_retorna_vazio():
    assert gerar_ocorrencias(date(2026, 2, 3), 1, date(2026, 2, 1)) == []


def test_mes_com_troca_de_dias():
    assert gerar_ocorrencias(date(2026, 1, 30), 2, date(2026, 2, 3)) == [date(2026, 1, 30), date(2026, 2, 1), date(2026, 2, 3)]


def test_retorna_datas_em_ordem():
    ocorrencias = gerar_ocorrencias(date(2026, 3, 1), 3, date(2026, 3, 20))
    assert ocorrencias == sorted(ocorrencias)


def test_intervalo_grande():
    assert gerar_ocorrencias(date(2026, 1, 1), 40, date(2026, 3, 1)) == [date(2026, 1, 1), date(2026, 2, 10)]
