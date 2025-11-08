import { useEffect, useState, useRef } from "react";

export default function useWebSocket(roomName = "default") {
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = import.meta.env.VITE_WS_HOST || window.location.hostname;
    const port = import.meta.env.VITE_WS_PORT || "8000";
    const socket = new WebSocket(`${protocol}://${host}:${port}/ws/game/${roomName}/`);
    socketRef.current = socket;

    socket.onopen = () => console.log("✅ Connected to WebSocket");
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.message) setMessages((prev) => [...prev, data.message]);
    };
    socket.onclose = () => console.log("❌ WebSocket closed");

    return () => socket.close();
  }, [roomName]);

  const sendMessage = (msg) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ message: msg }));
    }
  };

  return { messages, sendMessage };
}
