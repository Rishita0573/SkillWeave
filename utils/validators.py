def validate_text(text: str):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text must be a non-empty string.")


def validate_skills(skills):
    if skills is None:
        return []
    if not isinstance(skills, list):
        raise ValueError("Skills must be provided as a list.")
    return [s.strip() for s in skills if isinstance(s, str) and s.strip()]
