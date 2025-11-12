import sys
sys.path.insert(0, '.')
from app.services.mapping_tables import MOOD_LABEL_TO_DB_TAGS, ZH_TO_EN_MOOD
from sqlalchemy import text
from db.database import SessionLocal

all_m = set(ZH_TO_EN_MOOD.values())
for d in MOOD_LABEL_TO_DB_TAGS.values():
    all_m.update(d.get('db_mood_tags', []))

db = SessionLocal()
r = db.execute(text('SELECT DISTINCT jsonb_array_elements_text(mood_tags) FROM movies WHERE jsonb_array_length(mood_tags) > 0'))
db_m = set(x[0] for x in r)
t = db.execute(text('SELECT COUNT(*) FROM movies')).scalar()
w = db.execute(text('SELECT COUNT(*) FROM movies WHERE jsonb_array_length(mood_tags) > 0')).scalar()
db.close()

print('='*60)
print('Mapping Tables  Database 斷層分析')
print('='*60)
print(f'Total Movies: {t}')
print(f'With mood_tags: {w} ({w/t*100:.1f}%)')
print(f'DB unique tags: {len(db_m)}')
print(f'Mapping tags: {len(all_m)}')
c = all_m & db_m
g = db_m - all_m
print(f'Coverage: {len(c)}/{len(db_m)} ({len(c)/len(db_m)*100:.1f}%)')
if g:
    print(f'Gap: {sorted(g)}')
else:
    print('Gap: None - Perfect Coverage!')
print(f'Total Mood Labels: {len(MOOD_LABEL_TO_DB_TAGS)}')
print('='*60)
