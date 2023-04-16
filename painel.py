# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from urllib.request import urlopen
import json
import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

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

# Monta o data-frame para geração do mapa
df_mapa_aux = df[['mes_ref', 'uf', 'valor_total_beneficio']]
df_mapa_aux = df_mapa_aux.groupby('uf').sum().reset_index()

# Importa o json de estados do Brasil
with urlopen('https://raw.githubusercontent.com/Hudsonkzv/ptransp/main/brasil_estados.json') as response:
    geojson = json.load(response)

# Importa uma folha de estilos externa
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Cria a aplicação Dash
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# Define as opções do dropdown de estados
options = [{'label': uf, 'value': uf} for uf in df['uf'].unique()]
options.append({'label': 'Brasil', 'value': 'BR'})

# Define estilo para adicionar barra de rolagem e mudar a cor de fundo
ESTILO = {
    "overflow-y": "visible",
    "background-color": "#f3f6fd",
    "padding": "0px 250px 0px 250px",
    "margin": "0"
}

# Define o layout da aplicação
app.layout = html.Div(
    style=ESTILO,
    children=[
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
            options=options,
            value="SP",
        ),
        html.P(),
    ]),
    dcc.Graph(id="grafico"),

    html.P(),

    html.H1("Evolução da Ocupação por Tipo"),

    html.Div([
        html.P("Selecione o estado:"),
        dcc.Dropdown(
            id="estado_2",
            options=options,
            value="SP",
        ),
        html.P(),
    ]),
    
    dcc.Graph(id="grafico_2"),

    html.P(),

    html.H1("Valor total pago no Auxílio Emergencial por UF"),

    html.P(),

    html.Div([
        html.P("Selecione a escala de cores a ser exibida: "),
        dcc.Dropdown(
        id='cor-da-escala',
        options=[
            {'label': 'Vermelho', 'value': 'Reds'},
            {'label': 'Verde', 'value': 'Greens'},
            {'label': 'Roxo', 'value': 'Purples'},
        ],
        value='Reds'
         ),
        html.P(),
    ]), 

    html.P(),

    dcc.Graph(id='mapa-de-calor'),
    
])

# Define a função de atualização do gráfico 1
@app.callback(
    Output("grafico", "figure"),
    [Input("categoria_beneficio", "value"), Input("estado", "value")],
)

def atualiza_grafico(categoria_beneficio, estado):
    if estado == "BR":
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

# Define a função de atualização do gráfico 2
@app.callback(
        Output("grafico_2", "figure"), 
        [Input("estado_2", "value")]
)

def atualiza_grafico_2(estado_2):
    if estado_2 == 'BR':
        df_filtrado2 = df.groupby('mes_ref').sum().reset_index()
        df_filtrado2['mes_ref'] = pd.to_datetime(df_filtrado2['mes_ref'], format='%b/%y')
    else:
        df_filtrado2 = df[df['uf'] == estado_2]

    nomes_completos = {'mes_ref':'Mês de Referência', 'value': 'Total de trabalhadores em milhares'}

    fig = px.bar(df_filtrado2, x='mes_ref', y=['forca_trabalho_descoupada', 'forca_conta_propria', 
                 'forca_privado', 'forca_publico', 'forca_empregador', 'forca_domestico', 'forca_auxiliar'], 
                 barmode='stack',
                 labels=nomes_completos)

    # Adiciona a legenda
    fig.update_layout(legend_title_text='Tipo de Trabalhador')
    fig.update_traces(hovertemplate='%{y:.2f}', name='Desocupados em milhares', selector=dict(name='forca_trabalho_descoupada'))
    fig.update_traces(hovertemplate='%{y:.2f}', name='Trabalhadores por conta própria em milhares', selector=dict(name='forca_conta_propria'))
    fig.update_traces(hovertemplate='%{y:.2f}', name='Trabalhadores do setor privado em milhares', selector=dict(name='forca_privado'))
    fig.update_traces(hovertemplate='%{y:.2f}', name='Trabalhadores do setor público em milhares', selector=dict(name='forca_publico'))
    fig.update_traces(hovertemplate='%{y:.2f}', name='Empregadores em milhares', selector=dict(name='forca_empregador'))
    fig.update_traces(hovertemplate='%{y:.2f}', name='Trabalhadores domésticos em milhares', selector=dict(name='forca_domestico'))
    fig.update_traces(hovertemplate='%{y:.2f}', name='Trabalhadores familiares auxiliares em milhares', selector=dict(name='forca_auxiliar'))

    return fig

# Define a função de atualização do mapa de calor
@app.callback(Output('mapa-de-calor', 'figure'),
              Input('cor-da-escala', 'value'))

def update_mapa_de_calor(cor_da_escala):

    fig =  px.choropleth(df_mapa_aux, geojson=geojson, locations='uf', color='valor_total_beneficio',
                           color_continuous_scale=cor_da_escala,
                           scope='south america',
                           labels={'valor_total_beneficio': 'Valor Total Auxílio Emergencial em R$ bilhões'}
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
