import pandas as pd
from core.embeddings import EmbeddingEngine
from core.vector_index import SemanticIndex
from utils.paths import resolve
from config.settings import EMBEDDING_MODEL, TOP_K

class NCOMatcher:
    def __init__(self):
        self.df = pd.read_csv(resolve("data/nco.csv"))
        self.embedder = EmbeddingEngine(EMBEDDING_MODEL)

        corpus = (
            self.df["title"] + ". " +
            self.df["description"] + ". Sector: " +
            self.df["sector"]
        ).tolist()

        self.embeddings = self.embedder.encode(corpus)
        self.index = SemanticIndex(self.embeddings)

    def match(self, text: str):
        query = self.embedder.encode([text])
        scores, idxs = self.index.search(query, TOP_K)

        results = []
        for score, idx in zip(scores, idxs):
            row = self.df.iloc[idx]
            results.append({
                "nco_code": int(row.nco_code),
                "title": row.title,
                "confidence": float(score)
            })

        return results
