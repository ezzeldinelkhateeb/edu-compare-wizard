import requests; print("Testing API..."); response = requests.get("http://localhost:8001/health"); print(f"Status: {response.status_code}"); print(response.json())
