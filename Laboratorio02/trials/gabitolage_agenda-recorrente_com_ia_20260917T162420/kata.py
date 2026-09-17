"""Expansao de agenda para o trial; a implementacao sera feita pelo participante."""

from datetime import date, timedelta


def gerar_ocorrencias(data_inicial: date, intervalo_dias: int, data_final: date) -> list[date]:
    ocorrencias = []
    atual = data_inicial
    while atual <= data_final:
        ocorrencias.append(atual)
        atual += timedelta(days=intervalo_dias)
    return ocorrencias
