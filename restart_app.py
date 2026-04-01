import os
import requests

RAILWAY_TOKEN = os.getenv("RAILWAY_API_TOKEN")
SERVICE_ID = os.getenv("STREAMLIT_SERVICE_ID")

if not RAILWAY_TOKEN or not SERVICE_ID:
    print("Missing RAILWAY_API_TOKEN or STREAMLIT_SERVICE_ID env vars")
    exit(1)

query = """
mutation serviceInstanceRedeploy($serviceId: String!) {
  serviceInstanceRedeploy(serviceId: $serviceId)
}
"""

response = requests.post(
    "https://backboard.railway.app/graphql/v2",
    headers={
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json",
    },
    json={"query": query, "variables": {"serviceId": SERVICE_ID}},
)

if response.status_code == 200:
    print("Redeploy triggered successfully")
else:
    print(f"Failed to trigger redeploy: {response.text}")
