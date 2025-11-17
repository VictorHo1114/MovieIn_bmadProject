import os, json, time, httpx
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
KEY = os.getenv('TMDB_API_KEY')

def get_movie(tid):
    try:
        r = httpx.get(f'https://api.themoviedb.org/3/movie/{tid}', params={'api_key':KEY,'language':'zh-TW'}, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def valid(m):
    return m and len(m.get('overview','')) >= 20 and m.get('genres') and m.get('poster_path') and m.get('vote_count',0) >= 10

def search(p, pg):
    try:
        p.update({'api_key':KEY,'language':'zh-TW','page':pg})
        r = httpx.get('https://api.themoviedb.org/3/discover/movie', params=p, timeout=10)
        return r.json().get('results',[]) if r.status_code == 200 else []
    except: return []

def save(c, m):
    try:
        g = [x['name'] for x in m.get('genres',[])]
        r = c.execute(text('INSERT INTO movies (tmdb_id,title,original_title,overview,poster_path,backdrop_path,release_date,genres,vote_average,vote_count,popularity,runtime,original_language,adult) VALUES (:i,:t,:o,:ov,:p,:b,:r,CAST(:g AS jsonb),:va,:vc,:pop,:rt,:l,:a) ON CONFLICT (tmdb_id) DO NOTHING RETURNING tmdb_id'), {'i':m['id'],'t':m.get('title',''),'o':m.get('original_title',''),'ov':m.get('overview',''),'p':m.get('poster_path'),'b':m.get('backdrop_path'),'r':m.get('release_date'),'g':json.dumps(g,ensure_ascii=False),'va':float(m.get('vote_average',0)),'vc':int(m.get('vote_count',0)),'pop':float(m.get('popularity',0)),'rt':m.get('runtime'),'l':m.get('original_language',''),'a':bool(m.get('adult',False))})
        return r.fetchone() is not None
    except: return False

print(' 擴充電影資料庫到1000部')
with engine.begin() as c:
    n = c.execute(text('SELECT COUNT(*) FROM movies')).scalar()
    print(f'當前:{n} 目標:1000 需要:{1000-n}\n')
    a,s = 0, 0
    for name,p,pg in [('動作',{'with_genres':'28','sort_by':'vote_average.desc','vote_count.gte':'200'},8),('劇情',{'with_genres':'18','sort_by':'vote_average.desc','vote_count.gte':'300'},8),('科幻',{'with_genres':'878','sort_by':'vote_average.desc','vote_count.gte':'150'},6),('動畫',{'with_genres':'16','sort_by':'vote_average.desc','vote_count.gte':'100'},6),('喜劇',{'with_genres':'35','sort_by':'vote_average.desc','vote_count.gte':'150'},6),('驚悚',{'with_genres':'53','sort_by':'vote_average.desc','vote_count.gte':'150'},6),('2020s',{'primary_release_date.gte':'2020-01-01','primary_release_date.lte':'2024-12-31','sort_by':'vote_average.desc','vote_count.gte':'100'},5),('2010s',{'primary_release_date.gte':'2010-01-01','primary_release_date.lte':'2019-12-31','sort_by':'vote_average.desc','vote_count.gte':'200'},6),('2000s',{'primary_release_date.gte':'2000-01-01','primary_release_date.lte':'2009-12-31','sort_by':'vote_average.desc','vote_count.gte':'300'},6),('日本',{'with_original_language':'ja','sort_by':'vote_average.desc','vote_count.gte':'50'},5),('韓國',{'with_original_language':'ko','sort_by':'vote_average.desc','vote_count.gte':'100'},5)]:
        if a >= 1000-n: break
        print(f' {name}')
        for i in range(1, pg+1):
            if a >= 1000-n: break
            for mv in search(p.copy(), i):
                if a >= 1000-n: break
                d = get_movie(mv['id'])
                if not valid(d): s += 1; continue
                if save(c, d):
                    a += 1
                    print(f"  [{a}/{1000-n}] {d['title'][:25]} ({d.get('release_date','')[:4]}) {d.get('vote_average',0):.1f}")
                    time.sleep(0.3)
                else: s += 1
            time.sleep(0.5)
    print(f'\n 完成！總計:{c.execute(text("SELECT COUNT(*) FROM movies")).scalar()} 新增:{a} 跳過:{s}')
