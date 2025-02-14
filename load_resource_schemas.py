"""Loads resource schemas for use in command line options."""

import json
import os
import spyctl.api.primitives as api_primitives

API_KEY = os.getenv("P_API_KEY")
API_URL = "https://api.spyderbat.com"
ORG_UID = "spyderdemo"

url = f"{API_URL}/api/v1/org/{ORG_UID}/search/schema/"
response = api_primitives.get(url, API_KEY)
schemas = response.json()

with open(
    "spyctl/commands/get/resource_schemas.json", "w", encoding="utf-8"
) as f:
    json.dump(schemas, f)
