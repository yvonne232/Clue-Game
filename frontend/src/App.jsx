import React, { useEffect, useState } from "react";
import './App.css'
import Header from './components/Header'
import Footer from './components/Footer'
import Main from './components/Main'

function App() {
  const [apiMsg, setApiMsg] = useState("");
  const [wsMsg, setWsMsg] = useState("");
  const [socket, setSocket] = useState(null);
  // const [playerMsg, setPlayerMsg] = useState("");
  const [player, setPlayer] = useState("");

  // Connect to WebSocket
  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/game/");
    ws.onopen = async () => {
        console.log("WebSocket connected");
        try {
            const res = await fetch("http://127.0.0.1:8000/player/");
            const data = await res.json();
            // Store player ID in localStorage
            localStorage.setItem('player_name', data.player);
            setPlayer(data.player);
            // Send player ID to WebSocket
            ws.send(JSON.stringify({
                player_name: data.player
            }));
        } catch (error) {
            console.error("Error fetching player:", error);
        }
    };
    
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        console.log("Received from server:", data);
        if (data.message) setWsMsg(data.message);
    };
    
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

  // Test New App Player
  // const getPlayerInfo = async () => {
  //   const res = await fetch("http://127.0.0.1:8000/player/");
  //   const data = await res.json();
  //   setPlayerMsg(data.player);

  // }

  return (
    <>
      <div>
        <h1>Full-Stack Live Hello World</h1>

        <button onClick={getApiMessage}>Call Django API</button>
        <p>API → {apiMsg}</p>

        <button onClick={sendWsMessage}>Send WebSocket Message</button>
        <button onClick={triggerBroadcast}>Broadcast from Django</button>
        <p>WebSocket → {wsMsg}</p>

        <p>Player → {player}</p>

        <button>Sample test button</button>
      </div>
      
        
    </>
  )
}

export default App
