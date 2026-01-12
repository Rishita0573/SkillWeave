class Explainability:
    @staticmethod
    def match(role, confidence):
        return (
            f"The input semantically aligns with '{role}' "
            f"based on contextual similarity (score: {round(confidence, 2)})."
        )

    @staticmethod
    def skills(missing):
        if not missing:
            return "The user already meets the core skill requirements."
        return "Missing skills identified: " + ", ".join(missing)
