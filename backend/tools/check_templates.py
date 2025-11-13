import sys
sys.path.insert(0, ".")

# 檢查 QUIZ_TEMPLATES 數量
from tools.generate_daily_quiz import QUIZ_TEMPLATES

print("=== 題庫檢查 ===")
print(f"題庫總數: {len(QUIZ_TEMPLATES)} 題")
print()

# 按分類統計
from collections import Counter
categories = Counter(q["category"] for q in QUIZ_TEMPLATES)
print("分類統計:")
for category, count in sorted(categories.items()):
    print(f"  {category}: {count} 題")

print()

# 按難度統計
difficulties = Counter(q["difficulty"] for q in QUIZ_TEMPLATES)
print("難度統計:")
for difficulty, count in sorted(difficulties.items()):
    print(f"  {difficulty}: {count} 題")

print()
print("=== 資料庫檢查 ===")

# 檢查資料庫
from db.database import get_db
from app.models.quiz import DailyQuiz
from datetime import date, timedelta

db = next(get_db())

# 統計資料庫中的題目
total_db = db.query(DailyQuiz).count()
print(f"資料庫總題目數: {total_db} 題")

# 檢查最近的日期
recent_dates = db.query(DailyQuiz.date).distinct().order_by(DailyQuiz.date.desc()).limit(5).all()
print("\n最近的問答日期:")
for d in recent_dates:
    count = db.query(DailyQuiz).filter(DailyQuiz.date == d[0]).count()
    print(f"  {d[0]}: {count} 題")

db.close()
