import json
import os
from urllib.request import urlretrieve

import networkx as nx
import pandas as pd
from networkx.readwrite.json_graph import cytoscape_data

HERE = os.path.abspath(os.path.dirname(__file__))
PATH = os.path.join(HERE, 'tree.tsv')
URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQn5iJCSSQwCnxtkb65dG3jS0i27oBfkksOXLXGfqV4ERDB7EK0aPPL2NWXToYV5qpZthliNY6csbqv/pub?gid=580418978&single=true&output=tsv'
CYTOSCAPE = os.path.join(HERE, 'cytoscape.json')


def get_df(force: bool = False) -> pd.DataFrame:
    if not os.path.exists(PATH) and not force:
        urlretrieve(URL, PATH)

    df = pd.read_csv(
        PATH,
        sep='\t',
        index_col=0,
    )
    df = df[df['Name'].notna()]
    return df


def df_to_graph(df: pd.DataFrame) -> nx.DiGraph:
    graph = nx.DiGraph()
    # Index	Name	Father	Mother	Birthday	Deathday
    # Wedding	Spouse	Siblings	Birthplace	Immigration	Residences
    # Burial Site	Education	Military Service	Occupation
    # Christening	Notes	Link1	Link2

    columns = [
        'Name',
        'Birthday',
        'Deathday',
        'Wedding',
        'Siblings',
    ]
    for idx, row in df[columns].iterrows():
        idx = str(idx)
        label = row.pop('Name')
        d = {
            k: v
            for k, v in row.items()
            if pd.notna(v)
        }
        # add data later
        graph.add_node(idx, label=label, id=idx)

    for idx, father, mother, spouse in df[['Father', 'Mother', 'Spouse']].itertuples(index=True):
        idx = str(int(idx))
        if pd.notna(father):
            father = str(int(father))
            graph.add_edge(idx, father, type='father', id=f'{idx}_{father}')
        if pd.notna(mother):
            mother = str(int(mother))
            graph.add_edge(idx, mother, type='mother', id=f'{idx}_{mother}')
        if pd.notna(spouse):
            spouse = str(int(spouse))
            graph.add_edge(idx, spouse, type='spouse', id=f'{idx}_{spouse}')

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
    print('There are', len(df.index), 'Hoyts listed')
    g = df_to_graph(df)

    with open(CYTOSCAPE, 'w') as file:
        json.dump(cytoscape_data(g), file, indent=2)


if __name__ == '__main__':
    main()
