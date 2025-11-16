from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from db.database import get_db
from sqlalchemy.orm import Session

# auth + user model
from app.core.security import get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])


@router.get("/conversation")
def get_conversation(user: str, db: Session = Depends(get_db)):
    """Return messages involving the given user (both sender and recipient).
    Public for development: returns any messages where sender or recipient equals the provided user id.
    """
    try:
        q = text(
            """
            SELECT id, sender_id, recipient_id, body, is_read, created_at
            FROM messages
            WHERE sender_id = :u OR recipient_id = :u
            ORDER BY created_at ASC
            LIMIT 1000
            """
        )
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
        ins = text(
            "INSERT INTO messages (sender_id, recipient_id, body, is_read, created_at) VALUES (:s, :r, :b, false, now()) RETURNING id, sender_id, recipient_id, body, is_read, created_at"
        )
        res = db.execute(ins, {"s": sender_id, "r": recipient_id, "b": body})
        db.commit()
        row = res.fetchone()
        if row:
            return {"item": dict(row._mapping)}
        return {"item": {}}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
