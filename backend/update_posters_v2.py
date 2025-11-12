import sys
sys.path.insert(0, '.')
from db.database import SessionLocal
from app.models.quiz import DailyQuiz
from datetime import date
from sqlalchemy.orm.attributes import flag_modified

db = SessionLocal()

quizzes = db.query(DailyQuiz).filter(DailyQuiz.date == date.today()).all()

poster_urls = [
    'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
    'https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg',
]

print(f'Found {len(quizzes)} quizzes')

for i, q in enumerate(quizzes):
    if q.movie_reference:
        q.movie_reference['poster_url'] = poster_urls[i % len(poster_urls)]
        flag_modified(q, 'movie_reference')
        print(f'Updated quiz {q.id}: {q.movie_reference}')

db.commit()
print('Done!')
db.close()
