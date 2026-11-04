"""Cores e layout padrao dos graficos do Lab04.

Todos os graficos importam daqui, para que cada teste tenha sempre a mesma cor
(regra do enunciado: "a mesma cor para cada teste").
"""

import plotly.graph_objects as go
import plotly.io as pio

COR_WELCH = "#1f77b4"  # azul
COR_MW = "#ff7f0e"  # laranja

CORES_TESTE = {
    "welch": COR_WELCH,
    "mann_whitney": COR_MW,
}

NOMES_TESTE = {
    "welch": "t de Welch",
    "mann_whitney": "Mann-Whitney",
}

# Grupos dos dados (usadas no G1). Neutras, para nao confundir com as cores dos testes.
COR_SEM_BOT = "#7f7f7f"  # cinza
COR_COM_BOT = "#2ca02c"  # verde

CORES_GRUPO = {
    "sem_bot": COR_SEM_BOT,
    "com_bot": COR_COM_BOT,
}

NOMES_GRUPO = {
    "sem_bot": "Sem bot",
    "com_bot": "Com bot",
}

TEMPLATE = "lab04"

pio.templates[TEMPLATE] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Arial, sans-serif", size=14, color="#1a1f26"),
        title=dict(font=dict(size=18), x=0.0, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        margin=dict(l=60, r=20, t=80, b=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#e5e5e5", zeroline=False, linecolor="#888"),
        yaxis=dict(showgrid=True, gridcolor="#e5e5e5", zeroline=False, linecolor="#888"),
        colorway=[COR_WELCH, COR_MW, COR_COM_BOT, COR_SEM_BOT],
    )
)


def aplicar_layout(fig: go.Figure, **kwargs) -> go.Figure:
    """Aplica o template padrao do Lab04 a uma figura Plotly."""
    fig.update_layout(template=TEMPLATE, **kwargs)
    return fig
