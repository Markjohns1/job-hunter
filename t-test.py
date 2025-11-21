import requests

url = "https://api.telegram.org/bot8508046194:AAHRWAI2kZfpoP-GCF3L1aUdgxkarg0UkNY/sendMessage"
data = {
    'chat_id': '7380705360',
    'text': '🚀 JobHunterPro is LIVE!\n\nYou will receive notifications when:\n✅ New jobs are found\n✅ Applications are sent\n✅ Status updates happen\n\nLet\'s get you hired! 💪'
}

response = requests.post(url, data=data)
print(response.json())