"""
WebSocket 即時訊息系統
提供雙向即時通訊，取代輪詢機制
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from db.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.routers.messages import _existing_columns
from app.core.cache import MessageCacheKeys
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """管理所有活躍的 WebSocket 連線"""
    
    def __init__(self):
        # user_id -> Set[WebSocket] (一個用戶可能有多個裝置/Tab連線)
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> user_id 反向查詢
        self.connection_to_user: Dict[WebSocket, str] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """接受新連線"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_to_user[websocket] = user_id
        
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """移除連線"""
        user_id = self.connection_to_user.get(websocket)
        if not user_id:
            return
        
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.connection_to_user:
            del self.connection_to_user[websocket]
        
        logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """發送訊息給特定用戶的所有連線"""
        if user_id not in self.active_connections:
            logger.debug(f"User {user_id} not connected, message not delivered")
            return False
        
        disconnected = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                disconnected.append(connection)
        
        # 清理失效連線
        for conn in disconnected:
            self.disconnect(conn)
        
        return True
    
    async def broadcast(self, message: dict, exclude_user: str = None):
        """廣播訊息給所有連線（可選排除特定用戶）"""
        for user_id, connections in list(self.active_connections.items()):
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_personal_message(message, user_id)
    
    def is_user_online(self, user_id: str) -> bool:
        """檢查用戶是否在線"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_online_users(self) -> list[str]:
        """取得所有在線用戶列表"""
        return list(self.active_connections.keys())


# 全域連線管理器實例
manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket 聊天端點
    
    客戶端連線: ws://localhost:8000/api/v1/ws/chat?token=<jwt_token>
    
    訊息格式:
    Client -> Server:
    {
        "type": "send_message",
        "recipient_id": "user_uuid",
        "body": "Hello!"
    }
    
    Server -> Client:
    {
        "type": "new_message",
        "data": {
            "id": 123,
            "sender_id": "uuid",
            "recipient_id": "uuid",
            "body": "Hello!",
            "created_at": "2025-12-01T10:00:00Z"
        }
    }
    
    {
        "type": "user_online",
        "user_id": "uuid"
    }
    
    {
        "type": "user_offline",
        "user_id": "uuid"
    }
    
    {
        "type": "ping"
    }
    
    {
        "type": "pong"
    }
    """
    
    # 先 accept WebSocket 連線
    await websocket.accept()
    
    # 從 query string 手動讀取 token
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("No token provided in query string")
        await websocket.close(code=1008, reason="Authentication required: missing token")
        return
    
    # 驗證 token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing 'sub' field")
            await websocket.close(code=1008, reason="Invalid token: missing user ID")
            return
    except JWTError as e:
        logger.error(f"JWT decode failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed: invalid token")
        return
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Token 驗證成功，註冊到連線管理器（不要再次 accept）
    if user_id not in manager.active_connections:
        manager.active_connections[user_id] = set()
    
    manager.active_connections[user_id].add(websocket)
    manager.connection_to_user[websocket] = user_id
    
    logger.info(f"User {user_id} connected via WebSocket")
    
    # 通知其他用戶此用戶上線
    await manager.broadcast({
        "type": "user_online",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }, exclude_user=user_id)
    
    # 發送歡迎訊息
    await websocket.send_json({
        "type": "connected",
        "message": "WebSocket connected successfully",
        "user_id": user_id,
        "online_users": manager.get_online_users()
    })
    
    try:
        while True:
            # 接收客戶端訊息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            # 處理 ping (心跳檢測)
            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                continue
            
            # 處理發送訊息
            if message_type == "send_message":
                recipient_id = message_data.get("recipient_id")
                body = message_data.get("body", "").strip()
                
                if not recipient_id or not body:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing recipient_id or body"
                    })
                    continue
                
                # 儲存訊息到資料庫
                try:
                    # 使用已快取的 schema 檢查函數，避免每次查詢 information_schema
                    cols = _existing_columns(db)
                    
                    # 使用正確的欄位名稱插入
                    if "receiver_id" in cols:
                        insert_query = text("""
                            INSERT INTO messages (sender_id, receiver_id, body, is_read, created_at)
                            VALUES (:sender_id, :receiver_id, :body, false, NOW())
                            RETURNING id, sender_id, receiver_id AS recipient_id, body, is_read, created_at
                        """)
                    else:
                        insert_query = text("""
                            INSERT INTO messages (sender_id, recipient_id, body, is_read, created_at)
                            VALUES (:sender_id, :recipient_id, :body, false, NOW())
                            RETURNING id, sender_id, recipient_id, body, is_read, created_at
                        """)
                    
                    # 執行插入並記錄時間以便監控延遲
                    t0 = time.time()
                    result = db.execute(insert_query, {
                        "sender_id": user_id,
                        "receiver_id": recipient_id if "receiver_id" in cols else None,
                        "recipient_id": recipient_id,
                        "body": body
                    })
                    t1 = time.time()
                    db.commit()
                    t2 = time.time()
                    logger.debug("websocket.post_message timings: execute=%.3fms commit=%.3fms total=%.3fms", (t1-t0)*1000, (t2-t1)*1000, (t2-t0)*1000)
                    
                    row = result.fetchone()
                    if row:
                        message_record = dict(row._mapping)
                        
                        # 將所有需要序列化的欄位轉換為適當格式
                        serialized_message = {
                            'id': str(message_record['id']) if message_record.get('id') else None,  # ID 轉為字串避免 JS 精度問題
                            'sender_id': str(message_record['sender_id']) if message_record.get('sender_id') else None,
                            'recipient_id': str(message_record['recipient_id']) if message_record.get('recipient_id') else None,
                            'body': message_record.get('body', ''),
                            'is_read': message_record.get('is_read', False),
                            'created_at': message_record['created_at'].isoformat() if message_record.get('created_at') else None
                        }
                        
                        logger.debug(f"Serialized message: {serialized_message}")
                        
                        # 發送給接收者
                        logger.info(f"📤 Sending new_message to recipient {recipient_id}")
                        await manager.send_personal_message({
                            "type": "new_message",
                            "data": serialized_message
                        }, recipient_id)
                        
                        # 確認發送給發送者
                        logger.info(f"✅ Sending message_sent confirmation to sender {user_id}")
                        await websocket.send_json({
                            "type": "message_sent",
                            "data": serialized_message
                        })
                        logger.info(f"✅ message_sent sent successfully")
                        
                        # 清除雙方的訊息快取（未讀數、對話列表都會改變）
                        MessageCacheKeys.invalidate_user_messages(user_id)
                        MessageCacheKeys.invalidate_user_messages(recipient_id)
                        logger.debug(f"[Cache INVALIDATE] users {user_id}, {recipient_id} after new message")
                        
                        logger.info(f"Message {message_record['id']} from {user_id} to {recipient_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to save message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to send message: {str(e)}"
                    })
                    db.rollback()
            
            # 處理其他類型的訊息
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # 移除連線
        manager.disconnect(websocket)
        
        # 通知其他用戶此用戶離線
        await manager.broadcast({
            "type": "user_offline",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user_id)


@router.get("/online-users")
async def get_online_users():
    """取得目前在線用戶列表（用於除錯）"""
    return {
        "online_users": manager.get_online_users(),
        "total": len(manager.get_online_users())
    }


@router.get("/user-status/{user_id}")
async def get_user_status(user_id: str):
    """檢查特定用戶是否在線"""
    return {
        "user_id": user_id,
        "is_online": manager.is_user_online(user_id)
    }
