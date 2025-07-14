# ✅ Confirmed working Python test to bypass curl / PowerShell
# Save this file as `test_login.py` in your backend folder and run:
#     python test_login.py

import requests

url = "http://127.0.0.1:8000/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "username": "admin",
    "password": "admin123"
}

response = requests.post(url, data=data, headers=headers)

print("Status Code:", response.status_code)
print("Response:", response.json())
