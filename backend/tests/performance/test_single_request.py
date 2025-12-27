import asyncio
import aiohttp
import time

async def test_single():
    url = 'http://127.0.0.1:8000/api/v1/recommend/v2/movies'
    query = {
        'query': '難過的時候適合看什麼電影',
        'selected_moods': ['heartwarming'],
        'selected_genres': [],
        'selected_eras': []
    }
    
    print(' Testing single async request...')
    start = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=query, timeout=aiohttp.ClientTimeout(total=30)) as response:
                elapsed = (time.time() - start) * 1000
                if response.status == 200:
                    data = await response.json()
                    print(f' Success! Time: {elapsed:.0f}ms')
                    print(f' Movies: {len(data.get(\"movies\", []))}')
                    print(f' Strategy: {data.get(\"strategy\", \"unknown\")}')
                else:
                    print(f' Failed: HTTP {response.status}')
                    text = await response.text()
                    print(f'Response: {text[:200]}')
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f' Error after {elapsed:.0f}ms: {e}')

asyncio.run(test_single())
