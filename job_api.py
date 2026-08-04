import os
from dotenv import load_dotenv
from apify_client import ApifyClient


load_dotenv()

apify_token = os.getenv("APIFY_API_TOKEN")
client = ApifyClient(apify_token)


def fetch_linkedin_jobs(search_query, location="Bangladesh", rows=10):
    """
    Fetch LinkedIn jobs using Apify free-trial actor.
    """

    run_input = {
        "searchKeywords": search_query,
        "location": location
    }

    run = client.actor("jungle_thunder/linkedin-jobs-scraper-free-trial").call(
        run_input=run_input
    )

    jobs = []

    for item in client.dataset(run.default_dataset_id).iterate_items():
        jobs.append({
            "title": item.get("jobTitle", item.get("title", "No title")),
            "company": item.get("company", item.get("companyName", "Unknown company")),
            "location": item.get("location", "Unknown location"),
            "link": item.get("jobUrl", item.get("link", ""))
        })

    return jobs