import React, { useEffect, useState } from "react";
import './App.css'
import Header from './components/Header'
import Footer from './components/Footer'
import Main from './components/Main'

function App() {
  const [apiMsg, setApiMsg] = useState("");
  const [wsMsg, setWsMsg] = useState("");
  const [socket, setSocket] = useState(null);

  // Connect to WebSocket
  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/hello/");
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      console.log("Received from Django:", data);
      if (data.message) setWsMsg(data.message);
      if (data.broadcast) setWsMsg(data.broadcast);
      if (data.echo) setWsMsg(data.echo);
    };
    ws.onopen = () => console.log("WebSocket connected");
    setSocket(ws);
    return () => ws.close();
  }, []);

  // Trigger WebSocket broadcast via REST
  const triggerBroadcast = async () => {
    await fetch("http://127.0.0.1:8000/api/broadcast/");
  };

  // Send direct message through socket
  const sendWsMessage = () => {
    socket.send(JSON.stringify({ message: "Hi Django WebSocket!" }));
  };

  // Test API fetch
  const getApiMessage = async () => {
    const res = await fetch("http://127.0.0.1:8000/api/hello/");
    const data = await res.json();
    setApiMsg(data.message);
  };

  return (
    <>
      <div>
        <h1>Full-Stack Live Hello World</h1>

        <button onClick={getApiMessage}>Call Django API</button>
        <p>API → {apiMsg}</p>

        <button onClick={sendWsMessage}>Send WebSocket Message</button>
        <button onClick={triggerBroadcast}>Broadcast from Django</button>
        <p>WebSocket → {wsMsg}</p>
      </div>
      
        
    </>
  )
}

export default App
