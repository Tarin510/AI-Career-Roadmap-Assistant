import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def analyze_skills(user_skills, job_description):
    prompt = f"""
You are an AI Career Roadmap and Job Recommendation Assistant.

User Skills:
{user_skills}

Job Description:
{job_description}

IMPORTANT:
Return ONLY valid JSON.

You MUST return ALL fields below:

{{
    "matched_skills": [],
    "missing_skills": [],
    "match_score": "",
    "career_roadmap": [],
    "recommended_jobs": []
}}

Rules:
- Extract important technical skills from the user's skills and job description.
- Identify matched skills.
- Identify missing skills.
- Calculate a realistic match percentage.
- Give 3-5 roadmap steps.
- Suggest EXACTLY 3 short job titles for LinkedIn searching.
- recommended_jobs should contain only short job role names, not explanations.
- Return JSON only.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text
    print("\n========== GEMINI RESPONSE ==========")
    print(text)
    print("=====================================\n")

    text = text.replace("```json", "").replace("```", "").strip()

    data = json.loads(text)

    if "recommended_jobs" not in data:
        data["recommended_jobs"] = [
            "Data Analyst",
            "Junior Data Scientist",
            "Machine Learning Engineer"
        ]

    return data