# test_login_clean.py
import requests

url = "http://127.0.0.1:8000/token"
data = {
    "username": "admin",
    "password": "admin123"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=data, headers=headers)

print("Status Code:", response.status_code)
print("Response:", response.json())
