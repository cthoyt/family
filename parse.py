import json
import os
from pathlib import Path
from urllib.request import urlretrieve

import click
import networkx as nx
import pandas as pd
from networkx.readwrite.json_graph import cytoscape_data

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
DATA.mkdir(exist_ok=True, parents=True)

PATH = os.path.join(HERE, "tree.tsv")
HOYT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQn5iJCSSQwCnxtkb65dG3jS0i27oBfkksOXLXGfqV4ERDB7EK0aPPL2NWXToYV5qpZthliNY6csbqv/pub?gid=580418978&single=true&output=tsv"
HOYT_PATH = DATA / "hoyts.tsv"
GRAVE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiQhr3Is9lkCrbc2pneAxlE6BjKuZgarmGZ69ZpVX7BvkrdqIrwoc4ZQ2tck-fc_k2QgGA2yGXnmy/pub?gid=0&single=true&output=tsv"
GRAVE_PATH = DATA / "graves.tsv"
CYTOSCAPE = os.path.join(HERE, "cytoscape.json")


def get_df(url: str, path: Path, label: str, force: bool = False) -> pd.DataFrame:
    if not os.path.exists(path) and not force:
        urlretrieve(url, path)

    df = pd.read_csv(
        path,
        sep="\t",
        dtype=str,
    )
    df = df[df["Name"].notna()]
    for key in "Index", "Father", "Mother", "Spouse":
        df[key] = df[key].map(lambda x: f"{label}:{x}", na_action="ignore")
    return df


def get_hoyt_df(force: bool = False):
    return get_df(HOYT_URL, HOYT_PATH, label="hoyt", force=force)


def get_grave_df(force: bool = False):
    return get_df(GRAVE_URL, GRAVE_PATH, label="grave", force=force)


def df_to_graph(df: pd.DataFrame, prefix: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    # Index	Name	Father	Mother	Birthday	Deathday
    # Wedding	Spouse	Siblings	Birthplace	Immigration	Residences
    # Burial Site	Education	Military Service	Occupation
    # Christening	Notes	Link1	Link2

    for _, row in df.iterrows():
        idx = row.pop("Index")
        siblings = row.pop("Siblings")
        data = {
            k: v
            for k, v in row.items()
            if pd.notna(v) and k not in {"Father", "Mother", "Spouse", "Siblings"}
        }
        if pd.notna(siblings):
            try:
                data["Siblings"] = int(siblings)
            except ValueError:
                pass
        graph.add_node(idx, **data)

    for key in "Father", "Mother", "Spouse":
        for idx, object_idx in df[["Index", key]].itertuples(index=False):
            if pd.notna(object_idx) and object_idx in graph:
                graph.add_edge(idx, object_idx, type=key, id=f"{idx}_{object_idx}")

    # add levels from chuck (# 1)
    # levels = nx.single_source_shortest_path_length(graph, "1")
    # max_level = 1 + max(levels.values())
    # #graph.nodes[1]['level'] = max_level
    # for node in graph:
    #     level = levels[node]
    #     graph.nodes[node]['level'] = max_level - level

    return graph


def get_nuclear_graph():
    g = nx.DiGraph()
    g.add_node("n:0", name="Dorothy Hoyt")
    g.add_node("n:1", name="William Hoyt")
    g.add_node("n:2", name="Charlie Hoyt")
    g.add_node("n:3", name="Amelia Hoyt")
    g.add_node("n:4", name="Olivia Hoyt")
    g.add_node("n:5", name="Hillary Hoyt")


def merge(a: nx.DiGraph, b: nx.DiGraph) -> nx.DiGraph:
    """"""
    rv = nx.DiGraph()
    rv.add_nodes_from(a.nodes(data=True))
    rv.add_nodes_from(b.nodes(data=True))
    rv.add_edges_from(a.edges(data=True))
    rv.add_edges_from(b.edges(data=True))
    return rv


@click.command()
@click.option("--force", is_flag=True)
def main(force: bool):
    hoyt_df = get_hoyt_df(force=force)
    print(f"There are {len(hoyt_df.index)} Hoyts listed")
    hoyt_graph = df_to_graph(hoyt_df, "hoyt")

    # grave_df = get_grave_df(force=force)
    # print(f'There are {len(grave_df.index)} Graves listed')
    # grave_graph = df_to_graph(grave_df, "grave")
    #
    # graph = merge(hoyt_graph, grave_graph)
    graph = hoyt_graph

    with open(CYTOSCAPE, "w") as file:
        json.dump(cytoscape_data(graph, attrs={"name": "Name"}), file, indent=2)


if __name__ == "__main__":
    main()
