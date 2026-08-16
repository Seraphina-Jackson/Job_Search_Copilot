import re
from collections import Counter

def generate_interview_prep(company: str, role: str) -> str:
    """Generates a structured interview cheat sheet without external API calls."""
    return f"""
### 📖 1-Minute Cheat Sheet: {company} - {role}

#### 🎯 Key Focus Areas
- **Technical Skills:** Review core domain algorithms, data structures, and system design related to **{role}**.
- **Company Context:** Research **{company}**'s latest products, key engineering challenges, and public announcements.

#### ❓ Likely Interview Questions
1. *Behavioral:* "Tell me about a challenging project you worked on and how you resolved technical roadblocks."
2. *Role-Specific:* "How would you design or optimize a system/workflow for a core feature at **{company}**?"
3. *Problem Solving:* "Walk me through how you handle debugging performance bottlenecks under pressure."

#### 💡 Pro-Tip Question to Ask
> *"What does success look like for someone in the {role} position during their first 90 days at {company}?"*
"""


def analyze_resume_match(job_description: str, resume_text: str) -> dict:
    """Performs keyword matching between Job Description and Resume using pure Python."""
    if not job_description or not resume_text:
        return {"score": 0, "matched_skills": [], "missing_skills": []}

    # Helper function to extract meaningful words (4+ letters)
    def extract_keywords(text):
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        # Filter out common stop words
        stop_words = {
            "with", "that", "this", "from", "they", "have", "more", "will", "your", 
            "about", "their", "which", "would", "there", "work", "team", "experience",
            "ability", "strong", "using", "knowledge", "working", "building", "responsibilities"
        }
        return set([w for w in words if w not in stop_words])

    jd_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)

    if not jd_keywords:
        return {"score": 0, "matched_skills": [], "missing_skills": []}

    matched = sorted(list(jd_keywords.intersection(resume_keywords)))
    missing = sorted(list(jd_keywords - resume_keywords))

    score = int((len(matched) / len(jd_keywords)) * 100)

    return {
        "score": score,
        "matched_skills": matched[:10],   # Show top 10 matches
        "missing_skills": missing[:10]   # Show top 10 missing keywords
    }