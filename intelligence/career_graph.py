import pandas as pd
import networkx as nx
from utils.paths import resolve

class CareerGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        df = pd.read_csv(resolve("data/transitions.csv"))

        for _, row in df.iterrows():
            self.graph.add_edge(
                int(row.from_nco),
                int(row.to_nco),
                reason=row.reason
            )

    def next_roles(self, nco_code):
        return list(self.graph.successors(nco_code))
