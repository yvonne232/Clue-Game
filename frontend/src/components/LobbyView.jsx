// frontend/src/components/LobbyView.jsx
import React, { useState, useEffect, useCallback } from 'react';
import CharacterSelect from './CharacterSelect';

const POLLING_INTERVAL = 1000; // Poll every 1 second

export default function LobbyView() {
  const [lobbies, setLobbies] = useState([]);
  const [newLobbyName, setNewLobbyName] = useState('');
  const [currentLobby, setCurrentLobby] = useState(null);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Check if player exists and create one if not
    const playerId = localStorage.getItem('playerId');
    if (!playerId) {
      createPlayer();
    }
  }, []);
  
  // Polling function for current lobby
  const pollCurrentLobby = useCallback(async () => {
    if (!currentLobby) return;
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${currentLobby.id}/`);
      const data = await response.json();
      
      if (data.error) {
        console.error('Error polling lobby:', data.error);
        return;
      }
      
      // Only update if there are actual changes
      if (JSON.stringify(data) !== JSON.stringify(currentLobby)) {
        setCurrentLobby(data);
      }
    } catch (error) {
      console.error('Error polling current lobby:', error);
    }
  }, [currentLobby]);

  // Polling function for lobby list
  const pollLobbies = useCallback(async () => {
    if (currentLobby) return; // Don't poll lobby list if in a lobby
    try {
      const response = await fetch('http://127.0.0.1:8000/api/lobbies/');
      const data = await response.json();
      
      // Only update if there are actual changes
      if (JSON.stringify(data.lobbies) !== JSON.stringify(lobbies)) {
        setLobbies(data.lobbies);
      }
    } catch (error) {
      console.error('Error polling lobbies:', error);
    }
  }, [lobbies, currentLobby]);

  // Set up polling intervals
  useEffect(() => {
    // Initial fetch
    if (!currentLobby) {
      fetchLobbies();
    }

    // Set up polling intervals
    const lobbyListInterval = setInterval(pollLobbies, POLLING_INTERVAL);
    const currentLobbyInterval = setInterval(pollCurrentLobby, POLLING_INTERVAL);

    // Cleanup intervals on unmount
    return () => {
      clearInterval(lobbyListInterval);
      clearInterval(currentLobbyInterval);
    };
  }, [pollLobbies, pollCurrentLobby]);

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
      
      if (!playerId) {
        console.log('No player ID found, creating new player first');
        await createPlayer();
      }
      
      // Get the (potentially new) player ID
      const currentPlayerId = localStorage.getItem('playerId');
      if (!currentPlayerId) {
        console.error('Failed to create player');
        return;
      }
      
      const response = await fetch('http://127.0.0.1:8000/api/lobbies/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newLobbyName,
          player_id: currentPlayerId
        })
      });
      const data = await response.json();
      console.log('Lobby created response:', data);
      
      if (response.status === 404 && data.error === 'Player not found') {
        console.log('Player not found, creating new player and retrying');
        await createPlayer();
        // Retry creating lobby with new player
        return createLobby();
      }
      
      if (data.error) {
        console.error('Error from server:', data.error);
        return;
      }
      
      setCurrentLobby(data);
      console.log('Current lobby state:', data);
      fetchLobbies();
    } catch (error) {
      console.error('Error creating lobby:', error);
      if (error.message.includes('Failed to fetch')) {
        console.error('Network error - check if the server is running');
      }
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
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
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
            <h3>Players: {currentLobby.player_count}</h3>
            <div className="current-player-info">
              Your Player ID: {localStorage.getItem('playerId')}
            </div>
            {currentLobby.players.map(player => (
              <div 
                key={player.id} 
                className={`player-item ${player.id === localStorage.getItem('playerId') ? 'current-player' : ''}`}
              >
                Player {player.id}
                {player.character_name && <span className="player-character"> - {player.character_name}</span>}
                {player.id === localStorage.getItem('playerId') && <span className="current-player-badge"> (You)</span>}
              </div>
            ))}
          </div>
          <CharacterSelect 
            lobbyId={currentLobby.id}
            onCharacterSelected={(characterData) => {
              // Update the current lobby with the new character selection
              setCurrentLobby(prevLobby => ({
                ...prevLobby,
                players: prevLobby.players.map(player => 
                  player.id === localStorage.getItem('playerId')
                    ? { ...player, character_name: characterData.character_name }
                    : player
                )
              }));
            }}
          />
          <button onClick={leaveLobby} className="leave-button">Leave Lobby</button>
        </div>
      )}
    </div>
  );
}