import requests

response = requests.get("http://192.168.4.1/")
data = response.json()
print(data)
for channel in data["channels"]:
    print(f"{channel['channel']}: {channel['voltage']} V")
