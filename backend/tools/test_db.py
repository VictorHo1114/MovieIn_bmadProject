"""
資料庫連線測試腳本
"""
import sys
from sqlalchemy import create_engine, text, inspect
from db.database import DATABASE_URL

def test_database_connection():
    """測試資料庫連線並列出所有表格"""
    try:
        # 創建引擎
        engine = create_engine(DATABASE_URL)
        
        # 測試連線
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ 資料庫連線成功！\n")
            
            # 列出所有表格
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print(f"📊 找到 {len(tables)} 張資料表：\n")
            print("=" * 60)
            
            for i, table in enumerate(sorted(tables), 1):
                # 獲取表格欄位資訊
                columns = inspector.get_columns(table)
                column_count = len(columns)
                
                # 檢查是否達標（≥6 欄位）
                status = "✅" if column_count >= 6 else "⚠️"
                
                print(f"{i:2}. {status} {table:<25} ({column_count} 欄位)")
                
                # 顯示欄位詳情
                for col in columns:
                    col_name = col['name']
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"     - {col_name:<20} {col_type:<20} {nullable}")
                print()
            
            print("=" * 60)
            
            # 統計達標情況
            达标表格 = [t for t in tables if len(inspector.get_columns(t)) >= 6]
            print(f"\n📈 作業達標分析：")
            print(f"   總表格數：{len(tables)}")
            print(f"   ≥6 欄位：{len(达标表格)}")
            print(f"   達標率：{len(达标表格)/len(tables)*100:.1f}%")
            
            if len(tables) >= 5 and len(达标表格) >= 5:
                print(f"\n🎉 恭喜！完全達成作業要求！")
            
    except Exception as e:
        print(f"❌ 資料庫連線失敗：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_database_connection()
