import json
import os
from pathlib import Path
from urllib.request import urlretrieve

import networkx as nx
import pandas as pd
from networkx.readwrite.json_graph import cytoscape_data

HERE = Path(__file__).parent.resolve()
DATA = HERE / "data"
HOYT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQn5iJCSSQwCnxtkb65dG3jS0i27oBfkksOXLXGfqV4ERDB7EK0aPPL2NWXToYV5qpZthliNY6csbqv/pub?gid=580418978&single=true&output=tsv"
HOYT_PATH = DATA / "hoyts.tsv"

CYTOSCAPE = os.path.join(HERE, "cytoscape.json")


def get_df() -> pd.DataFrame:
    urlretrieve(HOYT_URL, HOYT_PATH)
    df = pd.read_csv(
        HOYT_PATH,
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

    for idx, father, mother, spouse in df[["Father", "Mother", "Spouse"]].itertuples(
        index=True
    ):
        idx = str(int(idx))
        if pd.notna(father):
            father = str(int(father))
            if father in graph:
                graph.add_edge(idx, father, type="father", id=f"{idx}_{father}")
        if pd.notna(mother):
            mother = str(int(mother))
            if mother in graph:
                graph.add_edge(idx, mother, type="mother", id=f"{idx}_{mother}")
        if pd.notna(spouse):
            spouse = str(int(spouse))
            if spouse in graph:
                graph.add_edge(idx, spouse, type="spouse", id=f"{idx}_{spouse}")

    # add levels from chuck (# 1)
    # levels = nx.single_source_shortest_path_length(graph, "1")
    # max_level = 1 + max(levels.values())
    # #graph.nodes[1]['level'] = max_level
    # for node in graph:
    #     level = levels[node]
    #     graph.nodes[node]['level'] = max_level - level

    return graph


def main():
    df = get_df()
    print("There are", len(df.index), "Hoyts listed")
    g = df_to_graph(df)

    with open(CYTOSCAPE, "w") as file:
        json.dump(cytoscape_data(g, attrs={"name": "Name"}), file, indent=2)


if __name__ == "__main__":
    main()
