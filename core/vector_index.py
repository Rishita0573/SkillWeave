import faiss
import numpy as np

class SemanticIndex:
    def __init__(self, embeddings: np.ndarray):
        self.dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embeddings)

    def search(self, query_vec, top_k: int):
        scores, idxs = self.index.search(query_vec, top_k)
        return scores[0], idxs[0]
