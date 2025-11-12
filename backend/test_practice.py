import requests

login = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'quiz_test@example.com', 'password': 'quiz123456'})
token = login.json()['access_token']
quiz = requests.get('http://127.0.0.1:8000/api/v1/quiz/today', headers={'Authorization': f'Bearer {token}'})
quiz_id = quiz.json()['quiz']['id']
print('練習模式測試...')
r1 = requests.post('http://127.0.0.1:8000/api/v1/quiz/submit', json={'quiz_id': quiz_id, 'answer': 1, 'time_spent': 10, 'practice_mode': True}, headers={'Authorization': f'Bearer {token}'})
print('積分:', r1.json()['points_earned'])
r2 = requests.post('http://127.0.0.1:8000/api/v1/quiz/submit', json={'quiz_id': quiz_id, 'answer': 0, 'time_spent': 10, 'practice_mode': True}, headers={'Authorization': f'Bearer {token}'})
print('第二次:', r2.status_code)
