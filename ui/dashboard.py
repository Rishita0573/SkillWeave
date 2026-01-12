import streamlit as st
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.main import SkillWeave

st.set_page_config(
    page_title="SkillWeave",
    page_icon="🧠",
    layout="wide"
)

engine = SkillWeave()

st.markdown("""
# 🧠 SkillWeave  
### AI-powered Semantic NCO Career Intelligence Platform
---
""")

# ---------- Input ----------
col1, col2 = st.columns([2, 1])

with col1:
    text = st.text_area(
        "Job Title / Resume Description",
        height=150,
        placeholder="e.g. Software engineer working on backend systems"
    )

with col2:
    skills_raw = st.text_area(
        "Your Skills (comma-separated)",
        height=150,
        placeholder="Python, Git, SQL"
    )

analyze = st.button("🚀 Analyze Career Profile", use_container_width=True)

# ---------- Output ----------
if analyze:
    if not text.strip():
        st.error("Please enter job title or resume description.")
    else:
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        
        try:
            result = engine.analyze(text, skills)
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.stop()


        st.markdown("## 🎯 Best Matching NCO Role")
        st.success(
            f"{result['best_match']['title']} "
            f"(NCO {result['best_match']['nco_code']})"
        )
        st.write(
            f"Confidence Score: **{round(result['best_match']['confidence'], 2)}**"
        )

        st.markdown("## 🔗 Related Roles")
        for r in result["related_roles"]:
            st.write(f"- {r['title']} (NCO {r['nco_code']})")

        st.markdown("## 🧩 Skill Gap Analysis")
        if result["skill_gap"]:
            for s in result["skill_gap"]:
                st.warning(s)
        else:
            st.success("No critical skill gaps identified.")

        st.markdown("## 📈 Career Transition Opportunities")
        if result["career_paths"]:
            for c in result["career_paths"]:
                st.write(f"- Possible transition to NCO {c}")
        else:
            st.info("No predefined transitions available.")

        st.markdown("## 🧠 Explainability")
        st.info(result["explanation"]["match"])
        st.info(result["explanation"]["skills"])

        st.caption("SkillWeave MVP • Government Pilot Ready")
