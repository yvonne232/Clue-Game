import { useEffect, useState, useRef } from "react";

export default function useWebSocket(roomName = "default") {
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProtocol}://${window.location.host}/ws/game/${roomName}/`;
    const socket = new WebSocket(`ws://localhost:8000/ws/game/default/`);
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
