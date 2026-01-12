import pandas as pd
import numpy as np

from core.embeddings import EmbeddingModel
from core.vector_index import VectorStore
from intelligence.career_graph import CareerGraph
from intelligence.skill_gap import SkillGapAnalyzer
from core.explainability import ExplainabilityEngine

class SkillWeaveEngine:
    def __init__(self):
        self.nco_df = pd.read_csv("data/nco_occupations.csv")
        self.embedder = EmbeddingModel()
        self.skill_gap = SkillGapAnalyzer("data/skills_mapping.csv")
        self.graph = CareerGraph("data/transitions.csv")

        self.embeddings = self.embedder.encode(
            (self.nco_df["title"] + " " + self.nco_df["description"]).tolist()
        )
        self.store = VectorStore(self.embeddings)

    def analyze(self, text, user_skills):
        query_vec = self.embedder.encode([text])
        scores, idxs = self.store.search(query_vec)

        best = self.nco_df.iloc[idxs[0]]
        best_score = scores[0]

        related = self.nco_df.iloc[idxs[1:4]][["nco_code", "title"]].to_dict("records")

        next_roles = self.graph.next_roles(best.nco_code)
        gaps = self.skill_gap.gap(user_skills, best.nco_code)

        return {
            "best_match": {
                "nco_code": int(best.nco_code),
                "title": best.title,
                "confidence": float(best_score)
            },
            "related_roles": related,
            "skill_gap": gaps,
            "career_paths": next_roles,
            "explanation": {
                "match": ExplainabilityEngine.explain_match(best.title, best_score),
                "skills": ExplainabilityEngine.explain_gap(gaps)
            }
        }
