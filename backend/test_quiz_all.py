import requests
import json

print('Testing /quiz/today/all endpoint...')
login = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'jefflu1000@gmail.com', 'password': 'password123'})
print(f'Login status: {login.status_code}')
if login.status_code == 200:
    token = login.json()['access_token']
    quiz_all = requests.get('http://127.0.0.1:8000/api/v1/quiz/today/all', headers={'Authorization': f'Bearer {token}'})
    print(f'Quiz API status: {quiz_all.status_code}')
    print('Response:')
    print(json.dumps(quiz_all.json(), indent=2, ensure_ascii=False))
