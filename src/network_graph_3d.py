import numpy as np
import plotly.graph_objects as go


def move_middle_points(p1, p2, shift):
    """
    :param p1: Coordinates of the starting point of an edge
    :param p2: Coordinates of the ending point of an edge
    :param shift: Indicates by how much to shift both points along the edge towards the middle
    :return: Start end end coordinates of the shortened edge along with the unit direction vector
    """
    p1_np = np.array(p1)
    p2_np = np.array(p2)
    unit_direction = (p2_np - p1_np) / np.linalg.norm(p2_np - p1_np)
    p1_new = p1_np + unit_direction * shift
    p2_new = p2_np - unit_direction * shift
    return p1_new, p2_new, unit_direction


def draw_nodes(plot_dict, figure, config):
    """
    :param plot_dict: Dictionary containing coordinates of each node, and target nodes with weights
    :param figure: Plotly figure
    :param config: Global configurations
    :return: Draws the nodes with its corresponding id
    """
    x = [item["x"] for key, item in plot_dict.items()]
    y = [item["y"] for key, item in plot_dict.items()]
    z = [item["z"] for key, item in plot_dict.items()]
    text = [item["name"] for key, item in plot_dict.items()]
    color = [item["color"] for key, item in plot_dict.items()]

    for i in range(len(x)):
        figure.add_trace(go.Scatter3d(
            x=[x[i]],
            y=[y[i]],
            z=[z[i]],
            text=text[i][0],
            mode='markers+text',
            marker=dict(size=config["node_size_3d"],
                        color=color[i]),
            textfont=dict(size=15),
            hovertemplate=text[i],
            hoverlabel=dict(namelength=0),
            hoverinfo="skip",
            textposition="middle center"
        ))

    return figure


def draw_edges(plot_dict, figure, config, weight_range):
    """
    :param plot_dict: Dictionary containing coordinates of each node, and target nodes with weights
    :param figure: Plotly figure
    :param config: Global configurations
    :param weight_range: Minimum and maximum weights given in the network
    :return: Draws the edges with the weights
    """
    skip = []  # skip edges that were already added from the other direction
    for key, item in plot_dict.items():
        for i, target in enumerate(item["targets"]):
            if (key, target) in skip:
                continue
            p1_init = (item["x"], item["y"], item["z"])
            p2_init = (plot_dict[target]["x"], plot_dict[target]["y"], plot_dict[target]["z"])
            p1_line, p2_line, unit_direction = move_middle_points(p1_init, p2_init, config["midpoint_shift_3d"])

            weight = item["target_weights"][i]
            source_name = item["name"]
            target_name = plot_dict[target]["name"]
            text = '<b>{} -> {}: {}</b>'.format(source_name, target_name, str(weight))
            width = config["line_width_3d"]

            bidirectional = key in plot_dict[target]["targets"]
            if bidirectional:  # for directed edges in both directions, only add edge once
                other_weight = plot_dict[target]["target_weights"][plot_dict[target]["targets"].index(key)]
                text = '<b>{} -> {}: {} <br> {} -> {}: {}</b>'.format(source_name, target_name, str(weight),
                                                                     target_name, source_name, str(other_weight))
                skip.append((target, key))

            # add line
            figure.add_trace(go.Scatter3d(
                x=[p1_line[0], p2_line[0]],
                y=[p1_line[1], p2_line[1]],
                z=[p1_line[2], p2_line[2]],
                mode='lines',
                line=dict(cmin=weight_range[0]-1,
                          cmax=weight_range[1]+1,
                          color=[weight],
                          width=width,
                          colorscale="bluered",
                          showscale=True,
                          colorbar=dict(title="Weight")),
                text=text,
                hoverinfo='text',
                opacity=0.5
                ))

            # add cone
            cone_size = config["cone_size"]
            figure.add_trace(go.Cone(
                x=[p2_line[0]],
                y=[p2_line[1]],
                z=[p2_line[2]],
                u=[(unit_direction*cone_size)[0]],
                v=[(unit_direction*cone_size)[1]],
                w=[(unit_direction*cone_size)[2]],
                hoverinfo="skip",
                sizemode="scaled",
                showlegend=False,
                opacity=0.8,
                showscale=False
            ))

            if bidirectional:
                p1_line, p2_line, unit_direction = move_middle_points(p2_init, p1_init, config["midpoint_shift_3d"])
                figure.add_trace(go.Cone(
                    x=[p2_line[0]],
                    y=[p2_line[1]],
                    z=[p2_line[2]],
                    u=[(unit_direction * cone_size)[0]],
                    v=[(unit_direction * cone_size)[1]],
                    w=[(unit_direction * cone_size)[2]],
                    hoverinfo="skip",
                    sizemode="scaled",
                    showlegend=False,
                    opacity=0.5,
                    showscale=False
                ))

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
                    "z": layout[add_id][2],
                    "color": df_nodes[df_nodes["node_id"] == add_id]["node_color"].values[0],
                    "name": df_nodes[df_nodes["node_id"] == add_id]["node_label"].values[0],
                    "targets": [],
                    "target_weights": []
                }
                plot_dict[add_id] = new_element

        plot_dict[source_id]["targets"].append(target_id)
        plot_dict[source_id]["target_weights"].append(weight)
    weight_range = (min(df_edges["weights"]), max(df_edges["weights"]))

    return plot_dict, weight_range


def create_figure(df_edges, df_nodes, layout, config):
    """
    :param df: Dataframe with source nodes, target nodes, and weights
    :param layout: Coordinates for each node
    :param config: Global configurations
    :return: Create a 3D directed weighted network graph from the given dataframe
    """
    fig = go.Figure()
    plot_dict, weight_range = create_plot_dict(df_edges, df_nodes, layout)
    fig = draw_nodes(plot_dict, fig, config)
    fig = draw_edges(plot_dict, fig, config, weight_range)
    fig.update_layout(
        title=dict(text="Network Graph",
                   font=dict(size=50),
                   x=0.5),
        template="none",
        autosize=False,
        hovermode="closest",
        width=800,
        height=800,
        showlegend=False,
        coloraxis_showscale=False,
        scene=dict(
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            zaxis=dict(showticklabels=False),
        )
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)
    return fig