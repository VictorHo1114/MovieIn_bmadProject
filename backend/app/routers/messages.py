from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from db.database import get_db
from sqlalchemy.orm import Session
import logging

# auth + user model
from app.core.security import get_current_user
from app.models import User
import time

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])

logger = logging.getLogger(__name__)


def _existing_columns(db: Session, table: str = "messages"):
    """Return a set of column names present for `table` in the current DB schema."""
    # simple runtime cache to avoid querying information_schema on every request
    if not hasattr(_existing_columns, '_cache'):
        _existing_columns._cache = {}
    cache = _existing_columns._cache
    if table in cache:
        return cache[table]
    try:
        res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table})
        cols = set(r[0] for r in res.fetchall())
        cache[table] = cols
        return cols
    except Exception:
        return set()


@router.get("/conversation")
def get_conversation(user: str, db: Session = Depends(get_db)):
    """Return messages involving the given user (both sender and recipient).
    Public for development: returns any messages where sender or recipient equals the provided user id.
    """
    cols = _existing_columns(db)
    has_receiver = "receiver_id" in cols
    has_content = "content" in cols

    recipient_select = "COALESCE(recipient_id, receiver_id) AS recipient_id" if has_receiver else "recipient_id AS recipient_id"
    body_select = "COALESCE(body, content) AS body" if has_content else "body AS body"
    where_clause = "sender_id = :u OR recipient_id = :u OR receiver_id = :u" if has_receiver else "sender_id = :u OR recipient_id = :u"

    q_text = f"""
SELECT
  id,
  sender_id,
  {recipient_select},
  {body_select},
  COALESCE(is_read, false) AS is_read,
  created_at
FROM messages
WHERE {where_clause}
ORDER BY created_at ASC
LIMIT 1000
"""
    try:
        q = text(q_text)
        res = db.execute(q, {"u": user})
        rows = res.fetchall()
        items = [dict(r._mapping) for r in rows]
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("")
def post_message(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Insert a new message. Requires authenticated user; sender is set to current_user.
    Expects JSON: { recipient_id, body }.
    """
    recipient_id = payload.get("recipient_id")
    body = payload.get("body")
    sender_id = str(current_user.user_id)

    if not recipient_id or not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recipient_id and body are required")

    cols = _existing_columns(db)
    has_receiver = "receiver_id" in cols
    has_content = "content" in cols

    # choose insert statement based on detected schema to avoid failing+fallback which costs time
    if has_receiver and has_content:
        ins_text = (
            "INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) "
            "VALUES (:s, :r, :b, false, now()) RETURNING id, sender_id, receiver_id, content, is_read, created_at"
        )
        params = {"s": sender_id, "r": recipient_id, "b": body}
        normalize_receiver = True
    else:
        # default to recipient/body schema
        ins_text = (
            "INSERT INTO messages (sender_id, recipient_id, body, is_read, created_at) "
            "VALUES (:s, :r, :b, false, now()) RETURNING id, sender_id, recipient_id, body, is_read, created_at"
        )
        params = {"s": sender_id, "r": recipient_id, "b": body}
        normalize_receiver = False

    try:
        logger.debug("post_message: executing insert; normalize_receiver=%s", normalize_receiver)
        t0 = time.time()
        res = db.execute(text(ins_text), params)
        t1 = time.time()
        db.commit()
        t2 = time.time()
        logger.debug("post_message timings: execute=%.3fms commit=%.3fms total=%.3fms", (t1-t0)*1000, (t2-t1)*1000, (t2-t0)*1000)
        row = res.fetchone()
        if not row:
            return {"item": {}}
        data = dict(row._mapping)
        if normalize_receiver:
            normalized = {
                "id": data.get("id"),
                "sender_id": data.get("sender_id"),
                "recipient_id": data.get("receiver_id"),
                "body": data.get("content"),
                "is_read": data.get("is_read"),
                "created_at": data.get("created_at"),
            }
            return {"item": normalized}
        else:
            return {"item": data}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return recent conversations for the authenticated user.
    Each item: { user_id, display_name, last_message, last_time, unread }
    """
    cols = _existing_columns(db)
    has_receiver = "receiver_id" in cols
    has_content = "content" in cols

    user_expr = "COALESCE(recipient_id, receiver_id)" if has_receiver else "recipient_id"
    body_expr = "COALESCE(body, content)" if has_content else "body"
    recipient_cond = "(recipient_id = :me OR receiver_id = :me)" if has_receiver else "recipient_id = :me"
    where_clause = "sender_id = :me OR recipient_id = :me OR receiver_id = :me" if has_receiver else "sender_id = :me OR recipient_id = :me"

    q_text = f"""
SELECT
    sub.user_id AS user_id,
    p.display_name AS display_name,
    sub.last_message AS last_message,
    sub.last_time AS last_time,
    COALESCE(sub.unread, 0) AS unread
FROM (
    SELECT
        CASE WHEN sender_id = :me THEN {user_expr} ELSE sender_id END AS user_id,
        max(created_at) AS last_time,
        (array_agg({body_expr} ORDER BY created_at DESC))[1] AS last_message,
        SUM(CASE WHEN {recipient_cond} AND is_read = false THEN 1 ELSE 0 END) AS unread
    FROM messages
    WHERE {where_clause}
    GROUP BY user_id
) AS sub
LEFT JOIN profiles p ON p.user_id = sub.user_id
WHERE sub.user_id IS NOT NULL AND sub.user_id != :me
ORDER BY sub.last_time DESC
LIMIT 200
"""
    try:
        q = text(q_text)
        res = db.execute(q, {"me": str(current_user.user_id)})
        rows = res.fetchall()
        items = [dict(r._mapping) for r in rows]
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/unread_count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        cols = _existing_columns(db)
        has_receiver = "receiver_id" in cols
        recipient_cond = "(recipient_id = :me OR receiver_id = :me)" if has_receiver else "recipient_id = :me"
        q = text(f"SELECT COUNT(*) AS count FROM messages WHERE {recipient_cond} AND is_read = false")
        res = db.execute(q, {"me": str(current_user.user_id)})
        row = res.fetchone()
        return {"count": int(row[0]) if row and row[0] is not None else 0}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/mark_read")
def mark_conversation_read(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark messages from a specific user to the current_user as read.
    Expects JSON: { user_id }
    """
    other = payload.get("user_id")
    upto_id = payload.get("upto_id")
    if not other:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")
    try:
        cols = _existing_columns(db)
        has_receiver = "receiver_id" in cols
        recipient_cond = "(recipient_id = :me OR receiver_id = :me)" if has_receiver else "recipient_id = :me"
        # optionally restrict to messages up to a specific message id to avoid races
        upto_clause = ""
        params = {"other": other, "me": str(current_user.user_id)}
        if upto_id is not None:
            try:
                # ensure integer-like
                params["upto_id"] = int(upto_id)
                upto_clause = " AND id <= :upto_id"
            except Exception:
                # ignore malformed upto_id and treat as not provided
                upto_clause = ""

        upd = text(f"UPDATE messages SET is_read = true, read_at = now() WHERE sender_id = :other AND {recipient_cond} AND is_read = false{upto_clause} RETURNING id")
        res = db.execute(upd, params)
        rows = res.fetchall()
        db.commit()

        # return the number of rows marked plus the new unread count for the current user
        try:
            q_count = text(f"SELECT COUNT(*) FROM messages WHERE {recipient_cond} AND is_read = false")
            cnt_res = db.execute(q_count, {"me": str(current_user.user_id)})
            cnt_row = cnt_res.fetchone()
            unread_now = int(cnt_row[0]) if cnt_row and cnt_row[0] is not None else 0
        except Exception:
            unread_now = None

        return {"marked": len(rows), "unread_count": unread_now}
    except Exception as e:
        db.rollback()
        logger.exception("Error in mark_conversation_read: %s", e)
        # Return more detailed message for debugging in dev environment
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
