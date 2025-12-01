/**
 * WebSocket 即時訊息管理器
 * 單例模式，自動重連、心跳檢測、訊息佇列
 */

import { API_BASE } from "./config";

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

interface WebSocketMessage {
  type: string;
  data?: any;
  [key: string]: any;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5000; // 5 秒重連
  private heartbeatInterval: number | null = null;
  private reconnectTimer: number | null = null;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private disconnectionHandlers: Set<ConnectionHandler> = new Set();
  private userId: string | null = null;
  private token: string | null = null;
  private isIntentionalClose = false;
  private isConnected = false;
  private messageQueue: any[] = []; // 離線時的訊息佇列

  /**
   * 連接到 WebSocket 伺服器
   * @param token JWT token
   */
  connect(token: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log("[WebSocket] Already connected");
      return;
    }

    this.token = token;
    this.isIntentionalClose = false;

    try {
      // 將 http://localhost:8000 轉換為 ws://localhost:8000
      const wsUrl = API_BASE.replace(/^http/, "ws") + `/api/v1/ws/chat?token=${encodeURIComponent(token)}`;
      
      console.log("[WebSocket] Connecting to:", wsUrl);
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("[WebSocket] Connected successfully");
        this.isConnected = true;
        this.startHeartbeat();
        this.notifyConnectionHandlers();
        
        // 發送佇列中的訊息
        this.flushMessageQueue();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log("[WebSocket] Received:", message);
          
          // 處理連線確認訊息
          if (message.type === "connected") {
            this.userId = message.user_id;
            console.log("[WebSocket] User ID:", this.userId);
          }
          
          // 處理 pong (心跳回應)
          if (message.type === "pong") {
            console.debug("[WebSocket] Heartbeat OK");
            return;
          }
          
          // 觸發訂閱的 handler
          this.notifyHandlers(message.type, message);
          
          // 發送自定義事件給其他組件
          if (message.type === "new_message") {
            window.dispatchEvent(new CustomEvent("newMessage", { detail: message }));
          }
          
          if (message.type === "user_online" || message.type === "user_offline") {
            window.dispatchEvent(new CustomEvent("userStatusChanged", { detail: message }));
          }
        } catch (e) {
          console.error("[WebSocket] Failed to parse message:", e);
        }
      };

      this.ws.onclose = (event) => {
        console.log("[WebSocket] Disconnected", event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        this.notifyDisconnectionHandlers();

        // 非主動關閉時，自動重連
        if (!this.isIntentionalClose) {
          console.log(`[WebSocket] Reconnecting in ${this.reconnectInterval / 1000}s...`);
          this.reconnectTimer = window.setTimeout(() => {
            if (this.token) {
              this.connect(this.token);
            }
          }, this.reconnectInterval);
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };
    } catch (e) {
      console.error("[WebSocket] Connection failed:", e);
    }
  }

  /**
   * 斷開連線
   */
  disconnect() {
    this.isIntentionalClose = true;
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.userId = null;
    this.token = null;
    console.log("[WebSocket] Disconnected intentionally");
  }

  /**
   * 發送訊息
   */
  send(message: any) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("[WebSocket] Not connected, queueing message");
      this.messageQueue.push(message);
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (e) {
      console.error("[WebSocket] Failed to send message:", e);
      this.messageQueue.push(message);
      return false;
    }
  }

  /**
   * 發送私訊
   */
  sendMessage(recipientId: string, body: string) {
    return this.send({
      type: "send_message",
      recipient_id: recipientId,
      body: body,
    });
  }

  /**
   * 發送佇列中的訊息
   */
  private flushMessageQueue() {
    if (this.messageQueue.length === 0) return;
    
    console.log(`[WebSocket] Flushing ${this.messageQueue.length} queued messages`);
    const queue = [...this.messageQueue];
    this.messageQueue = [];
    
    queue.forEach((msg) => {
      this.send(msg);
    });
  }

  /**
   * 訂閱特定類型的訊息
   */
  on(messageType: string, handler: MessageHandler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    this.messageHandlers.get(messageType)!.add(handler);
  }

  /**
   * 取消訂閱
   */
  off(messageType: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 訂閱連線事件
   */
  onConnect(handler: ConnectionHandler) {
    this.connectionHandlers.add(handler);
  }

  /**
   * 訂閱斷線事件
   */
  onDisconnect(handler: ConnectionHandler) {
    this.disconnectionHandlers.add(handler);
  }

  /**
   * 取消訂閱連線/斷線事件
   */
  offConnect(handler: ConnectionHandler) {
    this.connectionHandlers.delete(handler);
  }

  offDisconnect(handler: ConnectionHandler) {
    this.disconnectionHandlers.delete(handler);
  }

  /**
   * 觸發訊息處理器
   */
  private notifyHandlers(messageType: string, data: any) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (e) {
          console.error(`[WebSocket] Handler error for ${messageType}:`, e);
        }
      });
    }
  }

  /**
   * 觸發連線處理器
   */
  private notifyConnectionHandlers() {
    this.connectionHandlers.forEach((handler) => {
      try {
        handler();
      } catch (e) {
        console.error("[WebSocket] Connection handler error:", e);
      }
    });
  }

  /**
   * 觸發斷線處理器
   */
  private notifyDisconnectionHandlers() {
    this.disconnectionHandlers.forEach((handler) => {
      try {
        handler();
      } catch (e) {
        console.error("[WebSocket] Disconnection handler error:", e);
      }
    });
  }

  /**
   * 開始心跳檢測
   */
  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = window.setInterval(() => {
      this.send({ type: "ping" });
    }, 30000); // 每 30 秒一次心跳
  }

  /**
   * 停止心跳檢測
   */
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      window.clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 檢查是否已連線
   */
  getConnectionState(): boolean {
    return this.isConnected && this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 取得當前用戶 ID
   */
  getUserId(): string | null {
    return this.userId;
  }
}

// 全域單例
export const wsManager = new WebSocketManager();

// 在視窗關閉時清理
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    wsManager.disconnect();
  });
}
