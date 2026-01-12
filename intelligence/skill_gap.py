import pandas as pd
from utils.paths import resolve

class SkillGapEngine:
    def __init__(self):
        self.df = pd.read_csv(resolve("data/skills.csv"))

    def gap(self, user_skills, nco_code):
        required = set(
            self.df[self.df.nco_code == nco_code]["skill"]
        )
        return sorted(required - set(user_skills))
