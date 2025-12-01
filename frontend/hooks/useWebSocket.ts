/**
 * React Hook for WebSocket 即時訊息
 * 自動管理連線、訂閱、清理
 */

import { useEffect, useState, useCallback } from "react";
import { wsManager } from "@/lib/websocket";

interface UseWebSocketOptions {
  token?: string | null;
  autoConnect?: boolean;
  onMessage?: (message: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    token,
    autoConnect = true,
    onMessage,
    onConnect,
    onDisconnect,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);

  // 監聽連線狀態
  useEffect(() => {
    const checkConnection = () => {
      setIsConnected(wsManager.getConnectionState());
      setUserId(wsManager.getUserId());
    };

    const handleConnect = () => {
      checkConnection();
      onConnect?.();
    };

    const handleDisconnect = () => {
      checkConnection();
      onDisconnect?.();
    };

    wsManager.onConnect(handleConnect);
    wsManager.onDisconnect(handleDisconnect);

    // 初始檢查
    checkConnection();

    return () => {
      wsManager.offConnect(handleConnect);
      wsManager.offDisconnect(handleDisconnect);
    };
  }, [onConnect, onDisconnect]);

  // 自動連線
  useEffect(() => {
    if (autoConnect && token && !isConnected) {
      wsManager.connect(token);
    }
  }, [token, autoConnect, isConnected]);

  // 訂閱訊息
  useEffect(() => {
    if (!onMessage) return;

    const handleNewMessage = (message: any) => {
      onMessage(message);
    };

    wsManager.on("new_message", handleNewMessage);

    return () => {
      wsManager.off("new_message", handleNewMessage);
    };
  }, [onMessage]);

  // 發送訊息
  const sendMessage = useCallback(
    (recipientId: string, body: string) => {
      return wsManager.sendMessage(recipientId, body);
    },
    []
  );

  // 手動連線
  const connect = useCallback((tokenToUse?: string) => {
    const finalToken = tokenToUse || token;
    if (finalToken) {
      wsManager.connect(finalToken);
    }
  }, [token]);

  // 手動斷線
  const disconnect = useCallback(() => {
    wsManager.disconnect();
  }, []);

  return {
    isConnected,
    userId,
    sendMessage,
    connect,
    disconnect,
    wsManager, // 暴露管理器以便進階使用
  };
}

/**
 * 監聽新訊息的 Hook
 */
export function useWebSocketMessage(
  messageType: string,
  handler: (data: any) => void
) {
  useEffect(() => {
    wsManager.on(messageType, handler);
    return () => {
      wsManager.off(messageType, handler);
    };
  }, [messageType, handler]);
}

/**
 * 監聽用戶上下線狀態
 */
export function useUserOnlineStatus() {
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);

  useEffect(() => {
    const handleUserOnline = (message: any) => {
      setOnlineUsers((prev) => {
        if (!prev.includes(message.user_id)) {
          return [...prev, message.user_id];
        }
        return prev;
      });
    };

    const handleUserOffline = (message: any) => {
      setOnlineUsers((prev) => prev.filter((id) => id !== message.user_id));
    };

    const handleConnected = (message: any) => {
      if (message.online_users) {
        setOnlineUsers(message.online_users);
      }
    };

    wsManager.on("user_online", handleUserOnline);
    wsManager.on("user_offline", handleUserOffline);
    wsManager.on("connected", handleConnected);

    return () => {
      wsManager.off("user_online", handleUserOnline);
      wsManager.off("user_offline", handleUserOffline);
      wsManager.off("connected", handleConnected);
    };
  }, []);

  const isUserOnline = useCallback(
    (userId: string) => {
      return onlineUsers.includes(userId);
    },
    [onlineUsers]
  );

  return {
    onlineUsers,
    isUserOnline,
  };
}
