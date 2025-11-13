# -*- coding: utf-8 -*-
"""
Daily Quiz Generator
自動產生每日電影問答題目

使用方法:
  python generate_daily_quiz.py
  
可選參數:
  --date YYYY-MM-DD  指定日期（預設為今天）
  --count N          每日題目數量（預設為3）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from app.models.quiz import DailyQuiz
from datetime import date, datetime
import argparse

# 預設的問題庫（可以擴充）
QUIZ_TEMPLATES = [
    # === 科幻類 ===
    {
        "question": "《星際效應》中，主角庫珀進入黑洞後看到的五維空間是用來做什麼？",
        "options": ["觀察過去的地球", "與外星人溝通", "傳遞訊息給過去的女兒", "尋找新的星球"],
        "correct_answer": 2,
        "explanation": "在五維空間中，庫珀能夠跨越時間，透過書架向過去的女兒墨菲傳遞重要訊息。",
        "difficulty": "medium",
        "category": "科幻",
        "movie_reference": {
            "title": "星際效應",
            "year": 2014,
            "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
        }
    },
    {
        "question": "《全面啟動》中，主角 Cobb 的陀螺在夢境中會如何？",
        "options": ["會停止轉動", "會永遠轉動", "會倒下", "會消失"],
        "correct_answer": 1,
        "explanation": "在夢境中，陀螺會永遠轉動而不會停止，這是 Cobb 用來確認現實的方式。",
        "difficulty": "medium",
        "category": "科幻",
        "movie_reference": {
            "title": "全面啟動",
            "year": 2010,
            "poster_url": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg"
        }
    },
    {
        "question": "《駭客任務》中，尼歐選擇了哪一顆藥丸來了解真相？",
        "options": ["藍色藥丸", "紅色藥丸", "綠色藥丸", "黃色藥丸"],
        "correct_answer": 1,
        "explanation": "尼歐選擇了紅色藥丸，從而離開虛擬世界，看見真實的世界。",
        "difficulty": "easy",
        "category": "科幻",
        "movie_reference": {
            "title": "駭客任務",
            "year": 1999,
            "poster_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg"
        }
    },
    {
        "question": "《回到未來》中，時光機需要達到多少速度才能穿越時空？",
        "options": ["時速 88 英里", "時速 100 英里", "時速 120 英里", "音速"],
        "correct_answer": 0,
        "explanation": "在電影中，DeLorean 時光機需要達到時速 88 英里才能啟動時空穿越功能。",
        "difficulty": "easy",
        "category": "科幻",
        "movie_reference": {
            "title": "回到未來",
            "year": 1985,
            "poster_url": "https://image.tmdb.org/t/p/w500/fNOH9f1aA7XRTzl1sAOx9iF553Q.jpg"
        }
    },
    {
        "question": "《異形》系列中，異形的血液有什麼特性？",
        "options": ["劇毒", "強酸性", "能治癒傷口", "會爆炸"],
        "correct_answer": 1,
        "explanation": "異形的血液是強酸性的，能夠腐蝕金屬和其他物質，是電影中的重要設定。",
        "difficulty": "medium",
        "category": "科幻",
        "movie_reference": {
            "title": "異形",
            "year": 1979,
            "poster_url": "https://image.tmdb.org/t/p/w500/vfrQk5IPloGg1v9Rzbh2Eg3VGyM.jpg"
        }
    },
    {
        "question": "《E.T. 外星人》中，E.T. 最想做什麼？",
        "options": ["征服地球", "打電話回家", "尋找食物", "研究人類"],
        "correct_answer": 1,
        "explanation": "E.T. 的經典台詞「E.T. phone home」表達了他想要打電話回家的願望。",
        "difficulty": "easy",
        "category": "科幻",
        "movie_reference": {
            "title": "E.T. 外星人",
            "year": 1982,
            "poster_url": "https://image.tmdb.org/t/p/w500/an0nD6uq6byfxXCfk6lQBzdL2J1.jpg"
        }
    },
    {
        "question": "《銀翼殺手》中，複製人的壽命被設定為幾年？",
        "options": ["2 年", "4 年", "6 年", "8 年"],
        "correct_answer": 1,
        "explanation": "Nexus-6 型複製人被設計成只有 4 年壽命，這是電影核心衝突之一。",
        "difficulty": "hard",
        "category": "科幻",
        "movie_reference": {
            "title": "銀翼殺手",
            "year": 1982,
            "poster_url": "https://image.tmdb.org/t/p/w500/63N9uy8nd9j7Eog2axPQ8lbr3Wj.jpg"
        }
    },
    
    # === 劇情類 ===
    {
        "question": "《刺激1995》中，安迪杜佛蘭用什麼工具挖掘逃生隧道？",
        "options": ["湯匙", "小鐵鎚", "螺絲起子", "鑿子"],
        "correct_answer": 1,
        "explanation": "安迪花了近20年時間，用一把小鐵鎚在牢房牆壁上挖出逃生隧道，藏在海報後面。",
        "difficulty": "easy",
        "category": "劇情",
        "movie_reference": {
            "title": "刺激1995",
            "year": 1994,
            "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg"
        }
    },
    {
        "question": "《阿甘正傳》中，阿甘最喜歡的水果是什麼？",
        "options": ["蘋果", "香蕉", "巧克力", "草莓"],
        "correct_answer": 2,
        "explanation": "阿甘的經典台詞：「人生就像一盒巧克力，你永遠不知道會拿到什麼口味。」",
        "difficulty": "easy",
        "category": "劇情",
        "movie_reference": {
            "title": "阿甘正傳",
            "year": 1994,
            "poster_url": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg"
        }
    },
    {
        "question": "《當幸福來敲門》中，主角從事什麼職業？",
        "options": ["教師", "醫生", "股票經紀人", "律師"],
        "correct_answer": 2,
        "explanation": "克里斯最終成為成功的股票經紀人，這是根據真人真事改編的勵志故事。",
        "difficulty": "easy",
        "category": "劇情",
        "movie_reference": {
            "title": "當幸福來敲門",
            "year": 2006,
            "poster_url": "https://image.tmdb.org/t/p/w500/uOzb2UIBT5YizcK93MzSomSSofH.jpg"
        }
    },
    {
        "question": "《美麗人生》的故事背景發生在哪個時期？",
        "options": ["一戰", "二戰", "越戰", "韓戰"],
        "correct_answer": 1,
        "explanation": "電影講述二戰期間，一位父親在集中營中用想像力保護兒子的感人故事。",
        "difficulty": "easy",
        "category": "劇情",
        "movie_reference": {
            "title": "美麗人生",
            "year": 1997,
            "poster_url": "https://image.tmdb.org/t/p/w500/74hLDKjD5aGYOotO6esUVaeISa2.jpg"
        }
    },
    {
        "question": "《辛德勒的名單》中，辛德勒拯救了多少猶太人？",
        "options": ["約 600 人", "約 900 人", "約 1100 人", "約 1500 人"],
        "correct_answer": 2,
        "explanation": "奧斯卡·辛德勒在二戰期間拯救了約 1100 名猶太人的生命。",
        "difficulty": "medium",
        "category": "劇情",
        "movie_reference": {
            "title": "辛德勒的名單",
            "year": 1993,
            "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg"
        }
    },
    {
        "question": "《綠色奇蹟》中，約翰·考夫利有什麼特殊能力？",
        "options": ["預知未來", "治癒疾病", "隱形", "讀心術"],
        "correct_answer": 1,
        "explanation": "約翰·考夫利擁有神奇的治癒能力，能夠吸收和治療疾病。",
        "difficulty": "medium",
        "category": "劇情",
        "movie_reference": {
            "title": "綠色奇蹟",
            "year": 1999,
            "poster_url": "https://image.tmdb.org/t/p/w500/velWPhVMQeQKcxggNEU8YmIo52R.jpg"
        }
    },
    
    # === 愛情類 ===
    {
        "question": "《鐵達尼號》中，蘿絲最後將什麼物品扔入大海？",
        "options": ["項鍊「海洋之心」", "傑克的畫像", "船票", "訂婚戒指"],
        "correct_answer": 0,
        "explanation": "年老的蘿絲將價值連城的藍寶石項鍊「海洋之心」扔回大海，象徵著對傑克的永恆思念。",
        "difficulty": "easy",
        "category": "愛情",
        "movie_reference": {
            "title": "鐵達尼號",
            "year": 1997,
            "poster_url": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg"
        }
    },
    {
        "question": "《手札情緣》中，諾亞為艾莉做了什麼？",
        "options": ["蓋了一棟房子", "寫了一本書", "種了一座花園", "買了一艘船"],
        "correct_answer": 0,
        "explanation": "諾亞按照艾莉夢想中的樣子，親手為她蓋了一棟白色的房子。",
        "difficulty": "easy",
        "category": "愛情",
        "movie_reference": {
            "title": "手札情緣",
            "year": 2004,
            "poster_url": "https://image.tmdb.org/t/p/w500/qom1SZSENdmHFNZBXbtJAU0WTlC.jpg"
        }
    },
    {
        "question": "《真愛每一天》中，男主角擁有什麼能力？",
        "options": ["時空旅行", "讀心術", "預知未來", "隱形"],
        "correct_answer": 0,
        "explanation": "提姆能夠回到過去重新經歷人生中的任何時刻，但他最終領悟到珍惜當下的重要性。",
        "difficulty": "medium",
        "category": "愛情",
        "movie_reference": {
            "title": "真愛每一天",
            "year": 2013,
            "poster_url": "https://image.tmdb.org/t/p/w500/qQMKdNz0vT5XhvA2VJeavJJAwq0.jpg"
        }
    },
    {
        "question": "《樂來越愛你》中，男女主角分別的夢想是什麼？",
        "options": ["開咖啡廳和當演員", "當音樂家和開餐廳", "開爵士酒吧和當演員", "環遊世界和寫小說"],
        "correct_answer": 2,
        "explanation": "賽巴斯汀夢想開一家爵士酒吧，米亞則想成為演員，兩人為夢想做出了選擇。",
        "difficulty": "medium",
        "category": "愛情",
        "movie_reference": {
            "title": "樂來越愛你",
            "year": 2016,
            "poster_url": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg"
        }
    },
    
    # === 動作類 ===
    {
        "question": "《黑暗騎士》中，小丑的經典台詞是什麼？",
        "options": ["Why so serious?", "I am Batman", "Let it go", "May the Force be with you"],
        "correct_answer": 0,
        "explanation": "小丑的經典台詞「Why so serious?」成為了電影史上最經典的反派台詞之一。",
        "difficulty": "easy",
        "category": "動作",
        "movie_reference": {
            "title": "黑暗騎士",
            "year": 2008,
            "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
        }
    },
    {
        "question": "《捍衛戰士》中，主角的代號是什麼？",
        "options": ["Maverick", "Iceman", "Goose", "Viper"],
        "correct_answer": 0,
        "explanation": "湯姆·克魯斯飾演的彼得·米契爾，代號為「Maverick（獨行俠）」。",
        "difficulty": "easy",
        "category": "動作",
        "movie_reference": {
            "title": "捍衛戰士",
            "year": 1986,
            "poster_url": "https://image.tmdb.org/t/p/w500/xUuHj3CgmZQ9P2cMaqQs4J0d4Zc.jpg"
        }
    },
    {
        "question": "《玩命關頭》系列中，主角最常說的台詞是什麼？",
        "options": ["速度與激情", "家人最重要", "永不放棄", "正義必勝"],
        "correct_answer": 1,
        "explanation": "「Family（家人）」是整個系列的核心主題，唐老大經常強調家人的重要性。",
        "difficulty": "easy",
        "category": "動作",
        "movie_reference": {
            "title": "玩命關頭",
            "year": 2001,
            "poster_url": "https://image.tmdb.org/t/p/w500/ljsZTbVsrQSqZgWeep2B1QiDKuh.jpg"
        }
    },
    {
        "question": "《不可能的任務》中，伊森·韓特的特工組織代號是什麼？",
        "options": ["CIA", "FBI", "IMF", "MI6"],
        "correct_answer": 2,
        "explanation": "IMF（Impossible Missions Force，不可能任務情報局）是電影中的虛構特工組織。",
        "difficulty": "medium",
        "category": "動作",
        "movie_reference": {
            "title": "不可能的任務",
            "year": 1996,
            "poster_url": "https://image.tmdb.org/t/p/w500/s6AeR1KFeXFJ7iPPQNduUSoKk72.jpg"
        }
    },
    {
        "question": "《終極警探》的故事發生在哪裡？",
        "options": ["銀行大樓", "中央車站", "中原大樓", "白宮"],
        "correct_answer": 2,
        "explanation": "第一集的故事發生在洛杉磯的中原大樓（Nakatomi Plaza）聖誕派對上。",
        "difficulty": "medium",
        "category": "動作",
        "movie_reference": {
            "title": "終極警探",
            "year": 1988,
            "poster_url": "https://image.tmdb.org/t/p/w500/yFihWxQcmqcaBR31QM6Y8gT6aYV.jpg"
        }
    },
    
    # === 喜劇類 ===
    {
        "question": "《三個傻瓜》中，藍丘最後從事什麼職業？",
        "options": ["工程師", "教師", "科學家", "企業家"],
        "correct_answer": 1,
        "explanation": "藍丘最後成為一名教師，在山區開設學校，教導孩子們真正的知識。",
        "difficulty": "medium",
        "category": "喜劇",
        "movie_reference": {
            "title": "三個傻瓜",
            "year": 2009,
            "poster_url": "https://image.tmdb.org/t/p/w500/66A9MqXOyVFCssoloscw79z8U0Y.jpg"
        }
    },
    {
        "question": "《摩登大聖》中，孫悟空最後變成了什麼？",
        "options": ["一根棍子", "一個月餅", "一塊石頭", "一朵雲"],
        "correct_answer": 0,
        "explanation": "在周星馳的經典演繹中，至尊寶最後化身為孫悟空，而他的金箍棒成為永恆的象徵。",
        "difficulty": "easy",
        "category": "喜劇",
        "movie_reference": {
            "title": "西遊記大結局之仙履奇緣",
            "year": 1995,
            "poster_url": "https://image.tmdb.org/t/p/w500/6dHtohSEqVSJty35hGMfWGRiNIv.jpg"
        }
    },
    {
        "question": "《楚門的世界》中，楚門住在哪個虛構的城市？",
        "options": ["西海岸", "海景鎮", "桃源市", "自由城"],
        "correct_answer": 1,
        "explanation": "楚門從出生就生活在一個名為「海景鎮（Seahaven）」的巨大攝影棚中。",
        "difficulty": "medium",
        "category": "喜劇",
        "movie_reference": {
            "title": "楚門的世界",
            "year": 1998,
            "poster_url": "https://image.tmdb.org/t/p/w500/vuza0WqY239yBXOadKlGwJsZJFE.jpg"
        }
    },
    
    # === 驚悚/懸疑類 ===
    {
        "question": "《沉默的羔羊》中，漢尼拔是什麼職業？",
        "options": ["律師", "精神病學家", "外科醫生", "教授"],
        "correct_answer": 1,
        "explanation": "漢尼拔·萊克特醫生是一位才華橫溢的精神病學家，也是一個食人魔。",
        "difficulty": "easy",
        "category": "驚悚",
        "movie_reference": {
            "title": "沉默的羔羊",
            "year": 1991,
            "poster_url": "https://image.tmdb.org/t/p/w500/rplLJ2hPcOQmkFhTqUte0MkEaO2.jpg"
        }
    },
    {
        "question": "《鬥陣俱樂部》中，主角們成立的組織叫什麼？",
        "options": ["地下拳擊會", "鬥陣俱樂部", "革命軍", "無政府聯盟"],
        "correct_answer": 1,
        "explanation": "「Fight Club（鬥陣俱樂部）」是一個地下組織，第一條規則就是「不要談論鬥陣俱樂部」。",
        "difficulty": "easy",
        "category": "驚悚",
        "movie_reference": {
            "title": "鬥陣俱樂部",
            "year": 1999,
            "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg"
        }
    },
    {
        "question": "《記憶拼圖》的故事是以什麼方式呈現的？",
        "options": ["正序", "倒序", "雙線敘事", "循環敘事"],
        "correct_answer": 1,
        "explanation": "諾蘭以倒敘的方式講述故事，呼應主角短期記憶喪失的困境。",
        "difficulty": "hard",
        "category": "驚悚",
        "movie_reference": {
            "title": "記憶拼圖",
            "year": 2000,
            "poster_url": "https://image.tmdb.org/t/p/w500/yuNs09hvpHVU1cBTCAk9zxsL2oW.jpg"
        }
    },
    {
        "question": "《教父》中，馬龍·白蘭度飾演的維托·柯里昂最著名的台詞是什麼？",
        "options": ["我會給他一個無法拒絕的提議", "家族就是一切", "永遠不要違背家族", "尊重才是力量"],
        "correct_answer": 0,
        "explanation": "「I'm gonna make him an offer he can't refuse」是電影史上最經典的台詞之一。",
        "difficulty": "easy",
        "category": "劇情",
        "movie_reference": {
            "title": "教父",
            "year": 1972,
            "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg"
        }
    },
    {
        "question": "《侏羅紀公園》中，科學家如何復活恐龍？",
        "options": ["克隆化石", "從琥珀中蚊子提取DNA", "時光機器", "基因改造蜥蜴"],
        "correct_answer": 1,
        "explanation": "科學家從保存在琥珀中的史前蚊子體內提取恐龍血液，獲得恐龍DNA並進行復活。",
        "difficulty": "medium",
        "category": "科幻",
        "movie_reference": {
            "title": "侏羅紀公園",
            "year": 1993,
            "poster_url": "https://image.tmdb.org/t/p/w500/oU7Oq2kFAAlGqbU4VoAE36g4hoI.jpg"
        }
    }
]

def get_recently_used_questions(db, lookback_days=10):
    """取得最近使用過的題目"""
    from datetime import timedelta
    cutoff_date = date.today() - timedelta(days=lookback_days)
    
    recent_quizzes = db.query(DailyQuiz).filter(
        DailyQuiz.date >= cutoff_date
    ).all()
    
    # 提取使用過的題目（透過問題文字比對）
    used_questions = {quiz.question for quiz in recent_quizzes}
    return used_questions

def generate_daily_quiz(target_date=None, count=3, avoid_recent=True):
    """生成每日問答題目
    
    Args:
        target_date: 目標日期
        count: 題目數量
        avoid_recent: 是否避免使用最近 10 天出過的題目
    """
    if target_date is None:
        target_date = date.today()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    
    db = next(get_db())
    
    # 檢查該日期是否已有題目
    existing = db.query(DailyQuiz).filter(DailyQuiz.date == target_date).count()
    if existing > 0:
        print(f"警告: {target_date} 已有 {existing} 題，是否要覆蓋? (y/n)")
        response = input().strip().lower()
        if response != "y":
            print("取消操作")
            return
        # 刪除舊題目
        db.query(DailyQuiz).filter(DailyQuiz.date == target_date).delete()
        db.commit()
    
    # 智能選題：避免最近使用過的題目
    import random
    
    available_templates = QUIZ_TEMPLATES
    
    if avoid_recent:
        used_questions = get_recently_used_questions(db, lookback_days=10)
        available_templates = [
            template for template in QUIZ_TEMPLATES 
            if template["question"] not in used_questions
        ]
        
        if len(available_templates) < count:
            print(f"⚠️ 警告: 最近 10 天內已用過太多題目，可用題目僅 {len(available_templates)} 題")
            print(f"將從全部 {len(QUIZ_TEMPLATES)} 題中隨機選擇")
            available_templates = QUIZ_TEMPLATES
        else:
            print(f"✓ 智能選題: 從 {len(available_templates)} 個未使用的題目中選擇（排除最近 10 天）")
    
    selected_templates = random.sample(available_templates, min(count, len(available_templates)))
    
    added_count = 0
    for i, template in enumerate(selected_templates, 1):
        quiz_data = {
            "date": target_date,
            "sequence_number": i,
            **template
        }
        try:
            quiz = DailyQuiz(**quiz_data)
            db.add(quiz)
            added_count += 1
        except Exception as e:
            print(f"新增第 {i} 題時發生錯誤: {e}")
    
    db.commit()
    print(f"✓ 成功為 {target_date} 新增 {added_count} 題")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="產生每日電影問答題目")
    parser.add_argument("--date", type=str, help="目標日期 (YYYY-MM-DD)，預設為今天")
    parser.add_argument("--count", type=int, default=3, help="題目數量，預設為3")
    parser.add_argument("--no-smart", action="store_true", help="關閉智能選題（允許重複最近的題目）")
    
    args = parser.parse_args()
    
    generate_daily_quiz(
        target_date=args.date, 
        count=args.count,
        avoid_recent=not args.no_smart
    )
