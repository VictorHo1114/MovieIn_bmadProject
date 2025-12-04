# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from app.services.simple_recommend import recommend_movies_embedding_first
from db.database import SessionLocal

async def test_diversity():
    print('=' * 70)
    print('多樣性測試：重複查詢應返回不同結果')
    print('=' * 70)
    print()
    
    query = 'heartwarming family movie'
    runs = 3
    
    db = SessionLocal()
    all_results = []
    
    for i in range(runs):
        print(f'\n Run {i+1}/{runs}: {query}')
        print('-' * 70)
        
        results = await recommend_movies_embedding_first(
            natural_query=query,
            mood_labels=[],
            genres=[],
            count=10,
            db_session=db,
            use_cache=False
        )
        
        movie_ids = [r['id'] for r in results]
        movie_titles = [r['title'][:40] for r in results[:5]]
        
        all_results.append(set(movie_ids))
        
        print(f'Top 5: {movie_titles}')
        print(f'IDs: {movie_ids}')
    
    db.close()
    
    # 分析多樣性
    print('\n' + '=' * 70)
    print('多樣性分析')
    print('=' * 70)
    
    # Top 3 應該相同（guaranteed）
    top3_run1 = list(all_results[0])[:3]
    top3_run2 = list(all_results[1])[:3]
    top3_run3 = list(all_results[2])[:3]
    
    print(f'\nTop 3 穩定性（應該相同）:')
    print(f'  Run 1 Top 3: {top3_run1}')
    print(f'  Run 2 Top 3: {top3_run2}')
    print(f'  Run 3 Top 3: {top3_run3}')
    
    # 計算不同電影數
    unique_movies = all_results[0] | all_results[1] | all_results[2]
    common_movies = all_results[0] & all_results[1] & all_results[2]
    
    print(f'\n總覽:')
    print(f'  每次返回: 10 部電影')
    print(f'  3次總共出現: {len(unique_movies)} 部不同電影')
    print(f'  3次都出現: {len(common_movies)} 部（應 <= 3）')
    print(f'  多樣性評分: {(len(unique_movies) - 10) / 20 * 100:.1f}% (期望 >60%)')
    
    if len(unique_movies) >= 16:
        print('\n 多樣性測試通過！每次至少有 6 部新電影')
    else:
        print('\n 多樣性不足，建議檢查隨機選取機制')

if __name__ == '__main__':
    asyncio.run(test_diversity())
