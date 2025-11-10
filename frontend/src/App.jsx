import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import useWebSocket from "./hooks/useWebSocket";
import LobbyView from './components/LobbyView';
import GameView from './components/GameView';
import GameFeed from "./components/GameFeed";

const defaultApiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
const API_BASE = import.meta.env.VITE_API_BASE_URL || defaultApiBase;

export default function App() {
  const { messages, clearMessages } = useWebSocket("default");
  const [isRunning, setIsRunning] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const resetGame = async (gameName = "default") => {
    setIsResetting(true);
    setError("");
    clearMessages();

    try {
      await callWithRetry(async () => {
        const response = await fetch(`${API_BASE}/api/games/reset/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ game_name: gameName }),
        });

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.detail || `Reset failed (${response.status})`);
        }

        await response.json();
      });
      setResult(null);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsResetting(false);
    }
  };

  const triggerSimulation = async (rounds = 20) => {
    setIsRunning(true);
    setResult(null);
    setError("");

    try {
      const data = await callWithRetry(async () => {
        const response = await fetch(`${API_BASE}/api/games/simulate/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rounds }),
        });

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.detail || `Simulation failed (${response.status})`);
        }

        return response.json();
      });

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Router>
      <div className="app-root">
        <Routes>
          <Route path="/" element={<LobbyView />} />
          <Route path="/game/:lobbyId" element={<GameView />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </Router>
  );
}

const RETRYABLE_ERRORS = [
  "Save with update_fields did not affect any rows",
  "database is locked",
];

async function callWithRetry(action, retries = 2, delayMs = 200) {
  let attempt = 0;
  while (attempt <= retries) {
    try {
      return await action();
    } catch (err) {
      const message = err?.message || "";
      const shouldRetry =
        attempt < retries && RETRYABLE_ERRORS.some((signal) => message.includes(signal));
      if (!shouldRetry) {
        throw err;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      attempt += 1;
    }
  }
  // Should never reach here
  throw new Error("Exceeded retry attempts");
}

// function App() {
//   const [apiMsg, setApiMsg] = useState("");
//   const [wsMsg, setWsMsg] = useState("");
//   const [socket, setSocket] = useState(null);
//   // const [playerMsg, setPlayerMsg] = useState("");
//   const [player, setPlayer] = useState("");
//   const [allPlayers, setAllPlayers] = useState([]);

//   // Connect to WebSocket
//   useEffect(() => {
//     const ws = new WebSocket("ws://127.0.0.1:8000/ws/game/");
//     ws.onopen = async () => {
//         console.log("WebSocket connected");
//         try {
//             const res = await fetch("http://127.0.0.1:8000/player/");
//             const data = await res.json();
//             console.log("Fetched player:", data.player);
//             // Store player ID in localStorage
//             localStorage.setItem('player', data.player);
//             setPlayer(data.player);
//             // Send player ID to WebSocket
//             ws.send(JSON.stringify({
//                 player_id: data.player
//             }));
//         } catch (error) {
//             console.error("Error fetching player:", error);
//         }
//     };
    
//     ws.onmessage = (e) => {
//         const data = JSON.parse(e.data);
//         console.log("Received from server:", data);
//         if (data.type) setWsMsg(data.type);
//         if (data.type === 'player_list') {
//           setAllPlayers(data.players);
//       }
//     };
    
//     setSocket(ws);
//     return () => ws.close();
//   }, []);

//   // Trigger WebSocket broadcast via REST
//   const triggerBroadcast = async () => {
//     await fetch("http://127.0.0.1:8000/api/broadcast/");
//   };

//   // Send direct message through socket
//   const sendWsMessage = () => {
//     socket.send(JSON.stringify({ message: "Hi Django WebSocket!" }));
//   };

//   // Test API fetch
//   const getApiMessage = async () => {
//     const res = await fetch("http://127.0.0.1:8000/api/hello/");
//     const data = await res.json();
//     setApiMsg(data.message);
//   };

//   // Test New App Player
//   const getPlayerInfo = async () => {
//     const playerId = localStorage.getItem('player');
//     if (!playerId) {
//         console.error("No player name found");
//         return;
//     }

//     try {
//       const res = await fetch(`http://127.0.0.1:8000/${playerId}/`);
//       if (!res.ok) {
//           throw new Error(`HTTP error! Status: ${res.status}`);
//       }
//       const data = await res.json();
//       console.log("Player info:", data);
//       setPlayer(data.player);
//     } catch (error) {
//       console.error("Error fetching player info:", error);
//     }
//   };

//   const getAllPlayers = async () => {
//     try {
//         const res = await fetch("http://127.0.0.1:8000/get_all_players/", {
//             method: 'POST',  // Changed to POST to trigger broadcast
//             headers: {
//                 'Content-Type': 'application/json',
//                 'Accept': 'application/json',
//                 'Origin': 'http://localhost:5173'
//             },
//             credentials: 'include'  // This is important for CORS
//         });
//         if (!res.ok) {
//             throw new Error(`HTTP error! Status: ${res.status}`);
//         }
//     } catch (error) {
//         console.error("Error triggering player list broadcast:", error);
//     }
//   };

//   return (
//     <>
//       <div>
//         <h1>Full-Stack Live Hello World</h1>

//         <button onClick={getApiMessage}>Call Django API</button>
//         <p>API → {apiMsg}</p>

//         <button onClick={sendWsMessage}>Send WebSocket Message</button>
//         <button onClick={triggerBroadcast}>Broadcast from Django</button>
//         <p>WebSocket → {wsMsg}</p>

//         <p>Player → {player}</p>
//         <button onClick={getPlayerInfo}>Player Info</button>
//         <button onClick={getAllPlayers}>Get All Players</button>
//         <ul>
//           {allPlayers.map((p, index) => (
//             <li key={index}>{p}</li>
//           ))}
//         </ul>

//         <button>Sample test button</button>
//       </div>
      
        
//     </>
//   )
// }

// export default App
