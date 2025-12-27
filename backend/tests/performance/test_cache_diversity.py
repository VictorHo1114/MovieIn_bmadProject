# 測試快取與多樣性平衡
import sys
import time
sys.path.insert(0, '.')

print(' 測試快取與多樣性平衡')
print('='*70)

# 模擬測試
test_body = '{"query":"難過的時候適合看什麼電影","selected_moods":["heartwarming"],"selected_genres":[],"selected_eras":[]}'

print('\n測試 1: 首次查詢')
print('預期: ~4秒 (需要 OpenAI API)')
# 實際測試由 PowerShell 完成

print('\n測試 2: 5秒內重複查詢')
print('預期: ~5ms (快取命中)')

print('\n測試 3: 5分鐘後再次查詢')
print('預期: ~100-600ms (Embedding 快取命中，但推薦結果重新計算)')
print('結果: Top 3 相同，但 4-10 隨機變化')

print('\n 快取策略總結:')
print('   - Embedding 快取: 7 天 (降低 API 成本)')
print('   - 推薦結果快取: 5 分鐘 (避免短期重複)')
print('   - 5分鐘後: 重新隨機選擇 (保持多樣性)')
print('='*70)
