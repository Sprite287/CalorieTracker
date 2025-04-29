import requests

RENDER_URL = "https://calorietracker-2cvm.onrender.com"  # Replace with your deployed URL
TOKEN = "profilebackup"  # Must match SYNC_TOKEN on Render

def download_profiles():
    url = f"{RENDER_URL}/download_profiles?token={TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        with open("profiles.json", "wb") as f:
            f.write(response.content)
        print("profiles.json downloaded successfully!")
    else:
        print("Failed to download profiles.json:", response.status_code, response.text)

if __name__ == "__main__":
    download_profiles()