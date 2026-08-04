from bson import ObjectId
from database import analyses_collection


# -----------------------------
# Save analysis result
# -----------------------------
def save_analysis(user_id, skills, job_description, result, linkedin_jobs=None):

    analyses_collection.insert_one({
        "user_id": str(user_id),
        "skills": skills,
        "job_description": job_description,
        "match_score": result.get("match_score", "N/A"),
        "matched_skills": result.get("matched_skills", []),
        "missing_skills": result.get("missing_skills", []),
        "career_roadmap": result.get("career_roadmap", []),
        "recommended_jobs": result.get("recommended_jobs", []),
        "linkedin_jobs": linkedin_jobs or []
    })


# -----------------------------
# Get all analyses for sidebar
# -----------------------------
def get_user_history(user_id):

    analyses = analyses_collection.find(
        {"user_id": str(user_id)}
    ).sort("_id", -1)

    history = []

    for item in analyses:
        history.append((
            str(item["_id"]),
            item.get("match_score", "N/A"),
            item.get("recommended_jobs", []),
            item.get("skills", "")
        ))

    return history


# -----------------------------
# Get one analysis by id
# -----------------------------
def get_analysis_by_id(user_id, analysis_id):

    item = analyses_collection.find_one({
        "_id": ObjectId(analysis_id),
        "user_id": str(user_id)
    })

    return item


# -----------------------------
# Delete one analysis
# -----------------------------
def delete_analysis(analysis_id):

    analyses_collection.delete_one({
        "_id": ObjectId(analysis_id)
    })