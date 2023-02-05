# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
from dash.dependencies import Input, Output

# Carrega os dados do arquivo CSV
df = pd.read_csv("https://raw.githubusercontent.com/Hudsonkzv/ptransp/main/aux_pnad_tratada.csv")

# Formata a coluna de referência para o formato MMM-AA
df['mes_ref'] = pd.to_datetime(df['mes_ref'], format='%Y%m').dt.strftime('%b/%y')

# Adiciona colunas com os valores dos benefícios em bilhões:
df["valor_bolsa_familia_bi"] = df["valor_bolsa_familia"] / 1000000000
df["valor_cadunico_bi"] = df["valor_cadunico"] / 1000000000
df["valor_extracad_bi"] = df["valor_extracad"] / 1000000000

# Adiciona uma coluna "valor_total_beneficio" para a soma dos valores das três categorias de benefício
df["valor_total_beneficio"] = df["valor_bolsa_familia_bi"] + df["valor_cadunico_bi"] + df["valor_extracad_bi"]

# Cria a aplicação Dash
app = dash.Dash()

# Define o layout da aplicação
app.layout = html.Div([
    html.H1("Força de Trabalho Desocupada x Valor Total do Auxílio Emergencial"),
    html.Div([
        html.P("Selecione a categoria de benefício:"),
        dcc.Dropdown(
            id="categoria_beneficio",
            options=[
                {"label": "Bolsa Família", "value": "valor_bolsa_familia_bi"},
                {"label": "CadÚnico", "value": "valor_cadunico_bi"},
                {"label": "Extra-Cadastro", "value": "valor_extracad_bi"},
                {"label": "Total", "value": "valor_total_beneficio"},
            ],
            value="valor_total_beneficio",
        ),
    ]),
    html.Div([
        html.P("Selecione o estado:"),
        dcc.Dropdown(
            id="estado",
            options=[{"label": estado, "value": estado} for estado in df["uf"].unique()] + [{"label": "Brasil", "value": "Brasil"}],
            value="Brasil",
        ),
    ]),
    dcc.Graph(id="grafico"),
])

# Define a função de atualização do gráfico
@app.callback(
    Output("grafico", "figure"),
    [Input("categoria_beneficio", "value"), Input("estado", "value")],
)
def atualiza_grafico(categoria_beneficio, estado):
    if estado == "Brasil":
        df_filtrado = df.copy()
    else:
        df_filtrado = df[df["uf"] == estado]
    
    fig = px.bar(
        df_filtrado,
        x="mes_ref",
        y=categoria_beneficio,
        color="forca_trabalho_descoupada",
        barmode="group",
        labels={'mes_ref':'Mês de Referência', 'forca_trabalho_descoupada':'População Descoupada em milhares', 'valor_total_beneficio': 'Valor Total Auxílio Emergencial em R$ bilhões',
                'valor_bolsa_familia_bi': 'Valor Auxílio Emergencial - Bolsa Família em R$ bilhões', 'valor_cadunico_bi': 'Valor Auxílio Emergencial - CadÚnico em R$ bilhões',
                'valor_extracad_bi': 'Valor Auxílio Emergencial - ExtraCadastro em R$ bilhões'}
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)