import { useEffect, useState, useRef, useCallback } from "react";

export default function useWebSocket(roomName = "default") {
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!roomName) {
      return;
    }
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = import.meta.env.VITE_WS_HOST || window.location.hostname;
    const port = import.meta.env.VITE_WS_PORT || "8000";
    
    // Ensure we're using the correct path based on the roomName
    const wsPath = roomName === 'lobbies' ? '/ws/lobbies' : 
                   roomName === 'player' ? '/ws/player' :
                   `/ws/game/${roomName}`;
                   
    console.log(`Connecting to WebSocket: ${protocol}://${host}:${port}${wsPath}`);
    const socket = new WebSocket(`${protocol}://${host}:${port}${wsPath}`);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log("✅ Connected to WebSocket");
      if (roomName === 'lobbies') {
        // Request initial lobby state
        socket.send(JSON.stringify({ type: 'get_lobbies' }));
      }
    };
    
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      let normalized = data;

      if (typeof data === "string") {
        normalized = { type: "text", message: data };
      } else if (!data?.type && typeof data?.message === "string") {
        normalized = { type: "text", message: data.message };
      }

      setMessages((prev) => [...prev, normalized]);
      console.log("Received WebSocket message:", normalized);
    };
    
    socket.onclose = () => {
      console.log("❌ WebSocket closed");
      // Add error state handling if needed
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [roomName]);

  const sendMessage = useCallback((msg) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      // If msg is already a string, parse it first to ensure it's an object
      const msgObj = typeof msg === 'string' ? JSON.parse(msg) : msg;
      console.log('Sending WebSocket message:', msgObj);
      socketRef.current.send(JSON.stringify(msgObj));
    } else {
      console.warn('WebSocket is not connected, cannot send message');
    }
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, sendMessage, clearMessages };
}