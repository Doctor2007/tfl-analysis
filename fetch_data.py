import requests
import pandas as pd

# TfL API Endpoint
url = "https://api.tfl.gov.uk/Line/Mode/tube/Status"

# Fetch data
response = requests.get(url)
data = response.json()

# Extract relevant information
lines = []
for line in data:
    lines.append({
        "name": line["name"],
        "status": line["lineStatuses"][0]["statusSeverityDescription"]
    })

# Convert to DataFrame
df = pd.DataFrame(lines)

# Save to CSV
df.to_csv("tfl_tube_status.csv", index=False)

print(df)
