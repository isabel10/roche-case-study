import numpy as np
import plotly.graph_objects as go


def parallel_coord(p1, p2, shift):
    """
    :param p1: Coordinates of the starting point of an edge
    :param p2: Coordinates of the ending point of an edge
    :param shift: Indicates by how much to do parallel shifting
    :return: Start and end coordinates of parallel edge
    """
    p1_np = np.array(p1)
    p2_np = np.array(p2)
    unit_direction = (p2_np - p1_np) / np.linalg.norm(p2_np - p1_np)
    orthogonal_direction = np.array([-unit_direction[1], unit_direction[0]])
    p1_new = p1_np + shift * orthogonal_direction
    p2_new = p2_np + shift * orthogonal_direction
    return p1_new, p2_new


def midpoint_shift(p1, p2, shift):
    """
    :param p1: Coordinates of the starting point of an edge
    :param p2: Coordinates of the ending point of an edge
    :param shift: Indicates by how much to shift both points along the edge towards the middle
    :return: Start end end coordinates of the shortened edge
    """
    x = shift * p1[0] + (1-shift) * p2[0]
    y = shift * p1[1] + (1-shift) * p2[1]
    return x, y


def draw_nodes(plot_dict, figure, config):
    """
    :param plot_dict: Dictionary containing coordinates of each node, and target nodes with weights
    :param figure: Plotly figure
    :param config: Global configurations
    :return: Draws the nodes with its corresponding id
    """
    x = [item["x"] for key, item in plot_dict.items()]
    y = [item["y"] for key, item in plot_dict.items()]
    text = [item["name"] for key, item in plot_dict.items()]
    color = [item["color"] for key, item in plot_dict.items()]

    for i in range(len(x)):
        figure.add_trace(go.Scatter(
            x=[x[i]],
            y=[y[i]],
            mode='markers+text',
            marker=dict(size=config["node_radius"] * 2,
                        color=color[i]),
            legendgroup=text[i],
            text=text[i][0],
            hovertemplate=text[i],
            hoverlabel=dict(namelength=0),
            hoverinfo="skip",
            textfont=dict(size=15),
            #hoverinfo='none',
        ))

    return figure


def draw_edges(plot_dict, figure, config):
    """
    :param plot_dict: Dictionary containing coordinates of each node, and target nodes with weights
    :param figure: Plotly figure
    :param config: Global configuration
    :return: Draws the edges with the weights
    """
    for key, item in plot_dict.items():
        for i, target in enumerate(item["targets"]):
            p1 = (item["x"], item["y"])
            p2 = (plot_dict[target]["x"], plot_dict[target]["y"])
            weight = item["target_weights"][i]
            bidirectional = key in plot_dict[target]["targets"]
            if bidirectional:
                p1, p2 = parallel_coord(p1, p2, config["parallel_shift"])

            figure.add_annotation(
                x=p2[0],
                y=p2[1],
                ax=p1[0],
                ay=p1[1],
                xref='x',
                yref='y',
                axref='x',
                ayref='y',
                text='',
                opacity=0.2,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1.5,
                arrowcolor='black',
                standoff=config["node_radius"],
                startstandoff=config["node_radius"]
            )

            mid_x, mid_y = midpoint_shift(p1, p2, config["midpoint_shift"])
            figure.add_annotation(
                x=mid_x,
                y=mid_y,
                text=str(weight),
                font=dict(size=12),
                showarrow=False,
            )

    return figure


def create_plot_dict(df_edges, df_nodes, layout):
    """
    :param df: Dataframe with source nodes, target nodes, and weights
    :param layout: Coordinates for each node
    :return: Dictionary containing coordinates of each node, and target nodes with weights
    """
    plot_dict = dict()

    for id, row in df_edges.iterrows():
        source_id = row["source_id"]
        target_id = row["target_id"]
        weight = row["weights"]

        for add_id in [source_id, target_id]:
            if add_id not in plot_dict:
                new_element = {
                    "x": layout[add_id][0],
                    "y": layout[add_id][1],
                    "color": df_nodes[df_nodes["node_id"] == add_id]["node_color"].values[0],
                    "name": df_nodes[df_nodes["node_id"] == add_id]["node_label"].values[0],
                    "targets": [],
                    "target_weights": []
                }
                plot_dict[add_id] = new_element

        plot_dict[source_id]["targets"].append(target_id)
        plot_dict[source_id]["target_weights"].append(weight)

    return plot_dict


def create_figure(df_edges, df_nodes, layout, config):
    """
    :param df: Dataframe with source nodes, target nodes, and weights
    :param layout: Coordinates for each node
    :param config: Global configurations
    :return: Create a 2D directed weighted network graph from the given dataframe
    """
    fig = go.Figure()
    plot_dict = create_plot_dict(df_edges, df_nodes, layout)
    fig = draw_nodes(plot_dict, fig, config)
    fig = draw_edges(plot_dict, fig, config)
    fig.update_layout(
        title=dict(text="Network Graph",
                   font=dict(size=50),
                   x=0.5),
        template="none",
        autosize=False,
        width=800,
        height=800,
        showlegend=False,
        hovermode="closest"
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig