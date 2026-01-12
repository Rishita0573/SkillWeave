from intelligence.nco_matcher import NCOMatcher
from intelligence.skill_gap import SkillGapEngine
from intelligence.career_graph import CareerGraph
from core.explainability import Explainability
from utils.validators import validate_text, validate_skills

class SkillWeave:
    def __init__(self):
        self.matcher = NCOMatcher()
        self.skills = SkillGapEngine()
        self.graph = CareerGraph()

    def analyze(self, text, user_skills):
        validate_text(text)
        user_skills = validate_skills(user_skills)

        matches = self.matcher.match(text)

        if not matches:
            raise RuntimeError("No matching NCO roles found.")

        best = matches[0]

        gap = self.skills.gap(user_skills, best["nco_code"])
        transitions = self.graph.next_roles(best["nco_code"])

        return {
        "best_match": best,
        "related_roles": matches[1:],
        "skill_gap": gap,
        "career_paths": transitions,
        "explanation": {
            "match": Explainability.match(
                best["title"], best["confidence"]
            ),
            "skills": Explainability.skills(gap)
        }
    }
