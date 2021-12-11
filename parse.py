import json
from pathlib import Path
from urllib.request import urlretrieve

import networkx as nx
import pandas as pd
from networkx.readwrite.json_graph import cytoscape_data

HERE = Path(__file__).parent.resolve()

HOYTS_DATA = HERE / "hoyts"
HOYT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQn5iJCSSQwCnxtkb65dG3jS0i27oBfkksOXLXGfqV4ERDB7EK0aPPL2NWXToYV5qpZthliNY6csbqv/pub?gid=580418978&single=true&output=tsv"
HOYT_PATH = HOYTS_DATA / "data.tsv"
HOYT_CYTOSCAPE = HOYTS_DATA / "cytoscape.json"

GRAVE_DATA = HERE / "grave"
GRAVE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiQhr3Is9lkCrbc2pneAxlE6BjKuZgarmGZ69ZpVX7BvkrdqIrwoc4ZQ2tck-fc_k2QgGA2yGXnmy/pub?gid=0&single=true&output=tsv"
GRAVE_PATH = GRAVE_DATA / "data.tsv"
GRAVE_CYTOSCAPE = GRAVE_DATA / "cytoscape.json"


def get_df(url: str, path: Path) -> pd.DataFrame:
    urlretrieve(url, path)
    df = pd.read_csv(
        url,
        sep="\t",
        index_col=0,
    )
    df = df[df["Name"].notna()]
    return df


def df_to_graph(df: pd.DataFrame) -> nx.DiGraph:
    graph = nx.DiGraph()
    # Index	Name	Father	Mother	Birthday	Deathday
    # Wedding	Spouse	Siblings	Birthplace	Immigration	Residences
    # Burial Site	Education	Military Service	Occupation
    # Christening	Notes	Link1	Link2

    for idx, row in df.iterrows():
        idx = str(idx)
        siblings = row.pop("Siblings") if "Siblings" in row else None
        d = {
            k: v
            for k, v in row.items()
            if pd.notna(v) and k not in {"Father", "Mother", "Spouse", "Siblings"}
        }
        if pd.notna(siblings):
            try:
                d["Siblings"] = int(siblings)
            except ValueError:
                pass
        graph.add_node(idx, **d)

    for key in "Father", "Mother", "Spouse":
        for idx, relation in df[key].items():
            if pd.isna(relation):
                continue
            idx = str(int(idx))
            relation = str(int(relation))
            if relation in graph:
                graph.add_edge(idx, relation, type=key.lower(), id=f"{idx}_{relation}")

    # add levels from chuck (# 1)
    # levels = nx.single_source_shortest_path_length(graph, "1")
    # max_level = 1 + max(levels.values())
    # #graph.nodes[1]['level'] = max_level
    # for node in graph:
    #     level = levels[node]
    #     graph.nodes[node]['level'] = max_level - level

    return graph


def make_cytoscape(url, path, cytoscape, label):
    df = get_df(url, path)
    print("There are", len(df.index), f"{label.title()}s listed")
    graph = df_to_graph(df)
    with open(cytoscape, "w") as file:
        json.dump(cytoscape_data(graph, attrs={"name": "Name"}), file, indent=2)
    return graph


def main():
    grave_graph = make_cytoscape(GRAVE_URL, GRAVE_PATH, GRAVE_CYTOSCAPE, label="grave")
    hoyt_graph = make_cytoscape(HOYT_URL, HOYT_PATH, HOYT_CYTOSCAPE, label="hoyt")


if __name__ == "__main__":
    main()
