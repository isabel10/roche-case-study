import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import os
import sys
import numpy as np
import plotly.graph_objects as go
import networkx as nx
from dash.dependencies import Input, Output, State
import src.network_graph_3d as network_graph_3d
import src.network_graph_2d as network_graph_2d

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Load data
filename = sys.argv[1]
df = pd.read_excel(
    os.path.join("data/", filename),
    engine="openpyxl",
)

global_config = {
    "node_radius": 15,
    "parallel_shift": 0.01,
    "midpoint_shift": 0.35,
    "arrow_angle": np.pi/4,
    "arrow_radius": 1,
    "node_size_3d": 15,
    "line_width_3d": 5,
    "midpoint_shift_3d": 0.04,
    "cone_size": 0.12
}


dims = ["2D", "3D"]
layouts = {"2D": ["Spring Layout", "Random Layout", "Bipartite Layout", "Circular Layout"],
           "3D": ["Spring Layout", "Random Layout"]}


app.layout = html.Div([
    html.Div([
        dcc.Loading(
            dcc.Graph(id="plot"),
        ),
    ]),

    html.Div([
        dcc.Dropdown(
            id="dimension",
            options=[{"label": i, "value": i} for i in dims],
            value=dims[0]
        ),
    ], style={"margin-bottom": "10px"}),

    html.Div([
        dcc.Dropdown(
            id="layouts",
            value=layouts[dims[0]][0]
        ),
        ], style={"margin-bottom": "10px"}),

    html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
    html.Hr(),
    html.Div(id="display-selected-values")
    ], style={'margin': 'auto', 'width': "50%"})


@app.callback(
    Output("layouts", "options"),
    Input("dimension", "value")
)
def update_layout_dropdown(chosen_dim):
    return [{"label": i, "value": i} for i in layouts[chosen_dim]]


@app.callback(
    Output('plot', 'figure'),
    Input('submit-button-state', 'n_clicks'),
    State("layouts", 'value'),
    State("dimension", "value"))
def update_graph(n_clicks, fig_name, dim):
    G = nx.from_pandas_edgelist(df, "source_id", "target_id", create_using=nx.DiGraph(), edge_attr="weights")
    valid = 0
    if dim == "2D":
        valid = 1
        network = network_graph_2d
        if fig_name == "Spring Layout":
            layout = nx.spring_layout(G, weight="weights", k=4*1/np.sqrt(len(G.nodes())), iterations=30, dim=2, seed=10)
        if fig_name == "Random Layout":
            layout = nx.random_layout(G, seed=10)
        if fig_name == "Bipartite Layout":
            top = nx.bipartite.sets(G)[0]
            layout = nx.bipartite_layout(G, top)
        if fig_name == "Circular Layout":
            layout = nx.circular_layout(G)
    if dim == "3D":
        network = network_graph_3d
        if fig_name == "Spring Layout":
            layout = nx.spring_layout(G, weight="weights", k=4*1/np.sqrt(len(G.nodes())), iterations=30, dim=3, seed=10)
            valid = 1
        if fig_name == "Random Layout":
            layout = nx.random_layout(G, seed=10, dim=3)
            valid = 1
    if valid == 1:
        return network.create_figure(df, layout, global_config)
    else:
        fig = go.Figure()
        return fig


if __name__ == '__main__':
    app.run_server(debug=True)
