// frontend/src/components/LobbyView.jsx
import React, { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';

export default function LobbyView() {
  const [lobbies, setLobbies] = useState([]);
  const [newLobbyName, setNewLobbyName] = useState('');
  const [currentLobby, setCurrentLobby] = useState(null);
  const { messages, sendMessage } = useWebSocket();
  
  useEffect(() => {
    // Check if player exists and create one if not
    const playerId = localStorage.getItem('playerId');
    if (!playerId) {
      createPlayer();
    }
  }, []);
  
  // Fetch lobbies on component mount
  useEffect(() => {
    fetchLobbies();
  }, []);

  const fetchLobbies = async () => {
    try {
      console.log('Fetching lobbies...');
      const response = await fetch('http://127.0.0.1:8000/api/lobbies/');
      const data = await response.json();
      console.log('Received lobbies:', data.lobbies);
      setLobbies(data.lobbies);
    } catch (error) {
      console.error('Error fetching lobbies:', error);
    }
  };

  const createLobby = async () => {
    try {
      const playerId = localStorage.getItem('playerId');
      console.log('Creating lobby with playerId:', playerId);
      
      const response = await fetch('http://127.0.0.1:8000/api/lobbies/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newLobbyName,
          player_id: playerId
        })
      });
      const data = await response.json();
      console.log('Lobby created response:', data);
      
      if (data.error) {
        console.error('Error from server:', data.error);
        return;
      }
      
      setCurrentLobby(data);
      console.log('Current lobby state:', data);
      fetchLobbies();
    } catch (error) {
      console.error('Error creating lobby:', error);
    }
  };

  const joinLobby = async (lobbyId) => {
    try {
      const playerId = localStorage.getItem('playerId');
      console.log(`Attempting to join lobby ${lobbyId} with player ${playerId}`);
      
      const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${lobbyId}/join/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId
        })
      });
      
      const data = await response.json();
      console.log('Join lobby response:', data);
      
      if (data.error) {
        console.error('Error from server:', data.error);
        return;
      }
      
      setCurrentLobby(data);
    } catch (error) {
      console.error('Error joining lobby:', error);
    }
  };

  const leaveLobby = async () => {
    if (!currentLobby) return;
    
    try {
      const playerId = localStorage.getItem('playerId');
      const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${currentLobby.id}/leave/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId
        })
      });
      const data = await response.json();
      if (data.success) {
        setCurrentLobby(null);
        fetchLobbies();
      } else {
        console.error('Error leaving lobby:', data.error);
      }
    } catch (error) {
      console.error('Error leaving lobby:', error);
    }
  };

  const createPlayer = async () => {
    try {
      // Get the old player ID if it exists
      const oldPlayerId = localStorage.getItem('playerId');
      
      const response = await fetch('http://127.0.0.1:8000/api/player/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_player_id: oldPlayerId
        })
      });
      const data = await response.json();
      localStorage.setItem('playerId', data.id);
    } catch (error) {
      console.error('Error creating player:', error);
    }
  };

  return (
    <div className="lobby-container">
      {!currentLobby ? (
        <>
          <div className="create-lobby">
            <h2>Create New Lobby</h2>
            <input
              type="text"
              value={newLobbyName}
              onChange={(e) => setNewLobbyName(e.target.value)}
              placeholder="Enter lobby name"
            />
            <button onClick={createLobby}>Create Lobby</button>
          </div>

          <div className="lobby-list">
            <h2>Available Lobbies</h2>
            {lobbies.map(lobby => (
              <div key={lobby.id} className="lobby-item">
                <span>{lobby.name} ({lobby.players.length} players)</span>
                <button onClick={() => joinLobby(lobby.id)}>Join</button>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="current-lobby">
          <h2>Lobby: {currentLobby.name}</h2>
          <div className="player-list">
            <h3>Players:</h3>
            {currentLobby.players.map(player => (
              <div key={player.id} className="player-item">
                Player {player.id}
              </div>
            ))}
          </div>
          <button onClick={leaveLobby}>Leave Lobby</button>
        </div>
      )}
    </div>
  );
}