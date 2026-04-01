import os
import requests

RAILWAY_TOKEN = os.getenv("RAILWAY_API_TOKEN")
SERVICE_ID = os.getenv("STREAMLIT_SERVICE_ID")
ENVIRONMENT_ID = os.getenv("RAILWAY_ENVIRONMENT_ID")

if not RAILWAY_TOKEN or not SERVICE_ID or not ENVIRONMENT_ID:
    print("Missing RAILWAY_API_TOKEN, STREAMLIT_SERVICE_ID, or RAILWAY_ENVIRONMENT_ID env vars")
    exit(1)

query = """
mutation serviceInstanceRedeploy($serviceId: String!, $environmentId: String!) {
  serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId)
}
"""

response = requests.post(
    "https://backboard.railway.app/graphql/v2",
    headers={
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json",
    },
    json={"query": query, "variables": {"serviceId": SERVICE_ID, "environmentId": ENVIRONMENT_ID}},
)

if response.status_code == 200:
    print("Redeploy triggered successfully")
else:
    print(f"Failed to trigger redeploy: {response.text}")
