from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from db.database import get_db
from sqlalchemy.orm import Session

# auth + user model
from app.core.security import get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])


def _existing_columns(db: Session, table: str = "messages"):
    """Return a set of column names present for `table` in the current DB schema."""
    try:
        res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table})
        return set(r[0] for r in res.fetchall())
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

    try:
        # Try to insert into common schema (recipient_id, body) first.
        ins = text(
            "INSERT INTO messages (sender_id, recipient_id, body, is_read, created_at) VALUES (:s, :r, :b, false, now()) RETURNING id, sender_id, recipient_id, body, is_read, created_at"
        )
        res = db.execute(ins, {"s": sender_id, "r": recipient_id, "b": body})
        db.commit()
        row = res.fetchone()
        if row:
            return {"item": dict(row._mapping)}
        return {"item": {}}
    except Exception as e1:
        # If first insert failed (schema differences), try alternate columns (receiver_id, content).
        try:
            db.rollback()
        except Exception:
            pass
        try:
            ins2 = text(
                "INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) VALUES (:s, :r, :b, false, now()) RETURNING id, sender_id, receiver_id, content, is_read, created_at"
            )
            res2 = db.execute(ins2, {"s": sender_id, "r": recipient_id, "b": body})
            db.commit()
            row2 = res2.fetchone()
            if row2:
                # normalize returned keys to match frontend expectation
                data = dict(row2._mapping)
                normalized = {
                    "id": data.get("id"),
                    "sender_id": data.get("sender_id"),
                    "recipient_id": data.get("receiver_id"),
                    "body": data.get("content"),
                    "is_read": data.get("is_read"),
                    "created_at": data.get("created_at"),
                }
                return {"item": normalized}
            return {"item": {}}
        except Exception as e2:
            db.rollback()
            # return the original error for debugging
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"first: {e1}; second: {e2}")


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
    if not other:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")
    try:
        cols = _existing_columns(db)
        has_receiver = "receiver_id" in cols
        recipient_cond = "(recipient_id = :me OR receiver_id = :me)" if has_receiver else "recipient_id = :me"
        upd = text(f"UPDATE messages SET is_read = true, read_at = now() WHERE sender_id = :other AND {recipient_cond} AND is_read = false RETURNING id")
        res = db.execute(upd, {"other": other, "me": str(current_user.user_id)})
        rows = res.fetchall()
        db.commit()
        return {"marked": len(rows)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
