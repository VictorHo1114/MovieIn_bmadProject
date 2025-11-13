import sys
sys.path.insert(0, '.')
import os
import json
from sqlalchemy import text
from db.database import SessionLocal
from dotenv import load_dotenv

load_dotenv()

# 手動設定一些示範 keywords（模擬 TMDB API 返回）
DEMO_KEYWORDS = {
    13: ['vietnam veteran', 'usa president', 'washington monument', 'single mother', 'hippie'],
    278: ['prison', 'corruption', 'police brutality', 'prison cell', 'escape from prison'],
    238: ['italy', 'loss of father', 'organized crime', 'crime boss', 'sicily'],
    424: ['miami', 'corruption', 'homicide', 'hooligan', 'cop'],
}

DEMO_MOOD_TAGS = {
    13: ['hopeful', 'inspiring', 'emotional', 'heartwarming', 'feel-good'],
    278: ['hopeful', 'intense', 'thought-provoking', 'inspiring', 'epic'],
    238: ['intense', 'dark', 'epic', 'dramatic', 'powerful'],
    424: ['intense', 'thrilling', 'action-packed', 'gritty', 'dark'],
}

db = SessionLocal()

# 獲取前 20 部電影
movies = db.execute(text('SELECT tmdb_id, title FROM movies ORDER BY vote_count DESC LIMIT 20')).fetchall()

print(f'Updating {len(movies)} movies with demo data...')
print('=' * 60)

for tmdb_id, title in movies:
    # 使用示範數據或空列表
    keywords = DEMO_KEYWORDS.get(tmdb_id, ['drama', 'story', 'character-study'])
    mood_tags = DEMO_MOOD_TAGS.get(tmdb_id, ['emotional', 'thought-provoking', 'engaging'])
    
    db.execute(
        text('UPDATE movies SET keywords = :k, mood_tags = :m WHERE tmdb_id = :id'),
        {
            'k': json.dumps(keywords),
            'm': json.dumps(mood_tags),
            'id': tmdb_id
        }
    )
    print(f' {title[:40]:<40} - {len(keywords)} keywords, {len(mood_tags)} moods')

db.commit()
print('=' * 60)
print(' Done!')
db.close()