"""inspect_db.py

工具：列出資料庫現有表、檢查是否有 `messages` 表、可選擇建立表或插入測試資料。

使用方式（在 project 根目錄）：
  # 在 powershell 中（啟動虛擬環境視專案而定）：
  & .\.venv\Scripts\Activate.ps1  # 或 & .\backend\venv\Scripts\Activate.ps1
  python backend\scripts\inspect_db.py --list
  python backend\scripts\inspect_db.py --create
  python backend\scripts\inspect_db.py --test-insert

此腳本會讀取環境變數 `DATABASE_URL`（或後端目錄的 .env）。在進行建立或插入之前請先備份資料庫。若無法連線，會輸出錯誤資訊。
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
import json
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy import inspect
from dotenv import load_dotenv


def get_database_url() -> str:
    # 優先使用已存在的環境變數
    load_dotenv()  # 讀 backend/.env if present
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL is not set in environment. Set it or add to .env in backend/.")
        sys.exit(1)
    return db_url


def make_engine() -> Engine:
    db_url = get_database_url()
    engine = create_engine(db_url)
    return engine


def list_tables(engine: Engine) -> list[str]:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return tables


def create_messages_table(engine: Engine) -> None:
    # 建立 messages 表（若不存在）
    create_sql = """
    CREATE TABLE IF NOT EXISTS messages (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      conversation_id UUID NULL,
      sender_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
      receiver_id UUID NULL REFERENCES users(user_id) ON DELETE CASCADE,
      content TEXT NULL,
      meta JSONB NULL,
      attachments JSONB NULL,
      is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
      delivered_at TIMESTAMP WITH TIME ZONE NULL,
      read_at TIMESTAMP WITH TIME ZONE NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
    CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id);
    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))
    print("messages 表已嘗試建立（若尚不存在）。")


def test_insert_message(engine: Engine) -> None:
    # 插入一筆測試訊息並回傳
    test_sender = str(uuid.uuid4())
    test_receiver = str(uuid.uuid4())
    insert_sql = text(
        "INSERT INTO messages (sender_id, receiver_id, content, meta) VALUES (:s, :r, :c, :m) RETURNING id, created_at;"
    )
    with engine.begin() as conn:
        try:
            res = conn.execute(insert_sql, {
                "s": test_sender,
                "r": test_receiver,
                "c": "test message from inspect_db.py",
                "m": json.dumps({"test": True}),
            })
            row = res.fetchone()
            if row:
                print("成功插入測試訊息：", dict(row))
            else:
                print("插入指令已執行，但未回傳資料。請檢查資料庫。")
        except Exception as e:
            print("插入測試訊息失敗：", e)
            print("注意：若 users table 有 FK 限制，使用 UUID 隨機值會失敗。可先建立 messages 表後再用真實 user_id 測試。")


def describe_table(engine: Engine, table: str) -> None:
    inspector = inspect(engine)
    cols = inspector.get_columns(table)
    print(f"\nSchema for table '{table}':")
    for c in cols:
        print(f" - {c['name']}: {c['type']} nullable={c.get('nullable')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="列出現有資料表")
    parser.add_argument("--create", action="store_true", help="若缺少 messages 表則建立之（會使用 CREATE TABLE IF NOT EXISTS）")
    parser.add_argument("--test-insert", action="store_true", help="嘗試插入一筆測試訊息（注意 FK 限制）")
    parser.add_argument("--describe", metavar="TABLE", help="顯示指定表的欄位資訊")
    args = parser.parse_args(argv)

    engine = make_engine()

    if args.list:
        tables = list_tables(engine)
        print("資料庫中表：")
        for t in tables:
            print(" -", t)
        if "messages" not in tables:
            print("\n提示：資料庫中沒有 'messages' 表。可使用 --create 建立（請先備份資料庫）。")
        return 0

    if args.describe:
        describe_table(engine, args.describe)
        return 0

    if args.create:
        print("警告：在建立前請先備份資料庫！")
        create_messages_table(engine)
        return 0

    if args.test_insert:
        print("警告：測試插入可能會因外鍵限制失敗。若要用真實 user_id 測試，請提供對應 id 或先插入獨立測試資料。")
        test_insert_message(engine)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
