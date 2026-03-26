import requests
import json

# Supabase API Settings
SUPABASE_URL = "https://lgfvgkuruycynalkvfrg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxnZnZna3VydXljeW5hbGt2ZnJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxNjMyODIsImV4cCI6MjA4OTczOTI4Mn0.KrOt_YenJqI1W-1VGhQQ_kIaWYUEJn1kNhuXSBMN16g"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def test_inspect_schema():
    print("--- Inspecting Settings Schema ---")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/settings?limit=1", headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data:
            print("Sample Row Keys:")
            print(list(data[0].keys()))
        else:
            print("Settings table is empty.")
    else:
        print(f"GET Error: {r.status_code} - {r.text}")

if __name__ == "__main__":
    test_inspect_schema()
