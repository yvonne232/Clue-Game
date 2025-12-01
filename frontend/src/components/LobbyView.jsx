// frontend/src/components/LobbyView.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import CharacterSelect from './CharacterSelect';
import GameView from './GameView';
import '../styles/game.css';

const POLLING_INTERVAL = 1000; // Poll every 1 second

export default function LobbyView() {
  const [lobbies, setLobbies] = useState([]);
  const [newLobbyName, setNewLobbyName] = useState('');
  const [currentLobby, setCurrentLobby] = useState(null);
  const [error, setError] = useState(null);
  const [isGameStarted, setIsGameStarted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [socket, setSocket] = useState(null);
  const socketRef = useRef(null);
  const [playerLobbyInfo, setPlayerLobbyInfo] = useState(null); // Store info about player's lobby
  
  useEffect(() => {
    // Check if player exists and create one if not
    const playerId = localStorage.getItem('playerId');
    if (!playerId) {
      createPlayer();
    } else {
      // Check if player is already in a lobby
      checkPlayerLobby(playerId);
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
  // Set up WebSocket connection
  useEffect(() => {
    if (!currentLobby || !isGameStarted) {
      // Close existing socket if we leave the lobby or game stops
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
        setSocket(null);
      }
      return;
    }

    // Don't create a new socket if one already exists
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    let isMounted = true;
    const lobbyId = currentLobby.id;
    const wsUrl = `ws://127.0.0.1:8000/ws/game/${lobbyId}`;
    
    console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected successfully to:', wsUrl);
      setSocket(ws);
      setError(null); // Clear any previous errors
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        if (data.error) {
          setError(data.error);
        } else if (data.type === "game_state") {
          console.log("Received game state:", data.game_state);
          setMessages(prevMessages => [...prevMessages, data]);
        } else if (data.type === "game.started") {
          console.log("Game started message received");
          if (data.game_state) {
            setMessages(prevMessages => [...prevMessages, { 
              type: 'game_state', 
              game_state: data.game_state 
            }]);
          }
        } else if (data.type === "return_to_character_select") {
          console.log("Return to character select message received");
          setIsGameStarted(false);
          setMessages([]);
        } else if (data.message) {
          if (typeof data.message === 'string') {
            setMessages(prevMessages => [...prevMessages, { type: 'info', text: data.message }]);
          } else {
            setMessages(prevMessages => [...prevMessages, data.message]);
          }
        }
      } catch (parseError) {
        console.error('Error parsing WebSocket message:', parseError, 'Raw data:', event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      console.error('WebSocket URL:', wsUrl);
      console.error('WebSocket readyState:', ws.readyState);
      
      if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
        setError('WebSocket connection failed. Make sure the Django server is running with ASGI (e.g., daphne or uvicorn).');
      } else {
        setError('WebSocket connection error - check if backend server is running with WebSocket support');
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason || 'No reason provided');
      console.log('Was clean close:', event.wasClean);
      
      if (!isMounted) return;
      
      if (event.wasClean) {
        console.log('WebSocket closed cleanly');
        return;
      }
      
      // Connection lost - clear the ref
      socketRef.current = null;
      setSocket(null);
    };
    
    return () => {
      isMounted = false;
      if (ws && ws.readyState !== WebSocket.CLOSED && ws.readyState !== WebSocket.CLOSING) {
        ws.close();
      }
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
    };
  }, [isGameStarted, currentLobby]); // Connect when game starts

  // Listen for game start via polling
  useEffect(() => {
    if (!currentLobby || isGameStarted) return;

    const checkGameStatus = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${currentLobby.id}/`);
        const data = await response.json();
        
        // If game_in_progress changed to true, start the game
        if (data.game_in_progress && !isGameStarted) {
          console.log('Game has started, transitioning to game view');
          setIsGameStarted(true);
        }
      } catch (error) {
        console.error('Error checking game status:', error);
      }
    };

    const interval = setInterval(checkGameStatus, 1000);
    return () => clearInterval(interval);
  }, [currentLobby, isGameStarted]);

  // Handle polling for non-game state
  useEffect(() => {
    if (isGameStarted) return; // Don't poll when game is running

    // Initial fetch
    if (!currentLobby) {
      fetchLobbies();
    }

    // Set up polling intervals for non-game state
    const lobbyListInterval = setInterval(pollLobbies, POLLING_INTERVAL);
    const currentLobbyInterval = setInterval(pollCurrentLobby, POLLING_INTERVAL);

    // Cleanup intervals on unmount
    return () => {
      clearInterval(lobbyListInterval);
      clearInterval(currentLobbyInterval);
    };
  }, [pollLobbies, pollCurrentLobby, currentLobby, isGameStarted]);

  const fetchLobbies = useCallback(async () => {
    try {
      console.log('Fetching lobbies...');
      const response = await fetch('http://127.0.0.1:8000/api/lobbies/');
      const data = await response.json();
      console.log('Received lobbies:', data.lobbies);
      setLobbies(data.lobbies);
    } catch (error) {
      console.error('Error fetching lobbies:', error);
    }
  }, []);

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
        setError(data.error);
        return;
      }
      
      setCurrentLobby(data);
      console.log('Current lobby state:', data);
      
      // Check if the lobby has a game in progress (shouldn't happen for new lobbies, but handle it)
      if (data.game_in_progress) {
        console.log('Lobby has game in progress');
        setIsGameStarted(true);
      }
      
      // Join lobby's WebSocket group
      if (socket) {
        socket.send(JSON.stringify({
          type: 'join_lobby',
          lobby_id: data.id
        }));
      }
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
        setError(data.error);
        return;
      }
      
      if (data.new_player_id) {
        // Server created a new player for us
        console.log('Received new player ID:', data.new_player_id);
        localStorage.setItem('playerId', data.new_player_id);
        localStorage.removeItem('playerCharacter');
        localStorage.removeItem('currentGamePlayerId');
        // Retry joining with new player ID
        return joinLobby(lobbyId);
      }
      
      setCurrentLobby(data);
      
      // Check if the lobby has a game in progress (player is rejoining)
      if (data.game_in_progress) {
        console.log('Rejoining lobby with game in progress');
        setIsGameStarted(true);
      }
    } catch (error) {
      console.error('Error joining lobby:', error);
      setError('Error joining lobby. Please try again.');
    }
  };

  const leaveLobby = useCallback(async () => {
    if (!currentLobby) return false;
    
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
        // Leave lobby's WebSocket group before clearing state
        if (socket && currentLobby) {
          socket.send(JSON.stringify({
            type: 'leave_lobby',
            lobby_id: currentLobby.id
          }));
        }
        setCurrentLobby(null);
        setPlayerLobbyInfo(null); // Clear player lobby info
        fetchLobbies();
        return true;
      }
      console.error('Error leaving lobby:', data.error);
      return false;
    } catch (error) {
      console.error('Error leaving lobby:', error);
      return false;
    }
  }, [currentLobby, fetchLobbies, socket]);

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
      localStorage.removeItem('playerCharacter');
      localStorage.removeItem('currentGamePlayerId');
    } catch (error) {
      console.error('Error creating player:', error);
    }
  };

  const checkPlayerLobby = async (playerId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/player/${playerId}/lobby/`);
      const data = await response.json();
      
      if (data.lobby) {
        console.log('Player is already in a lobby:', data.lobby);
        setPlayerLobbyInfo(data.lobby); // Store lobby info for display
        setCurrentLobby(data.lobby);
        
        // If the lobby has a game in progress, rejoin the game
        if (data.lobby.game_in_progress) {
          console.log('Rejoining game in progress');
          setIsGameStarted(true);
        }
      } else {
        setPlayerLobbyInfo(null);
      }
    } catch (error) {
      console.error('Error checking player lobby:', error);
    }
  };

  const startGame = useCallback(async () => {
    if (!currentLobby) return false;
    try {
      console.log('Starting game for lobby:', currentLobby.id);
      
      const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${currentLobby.id}/start/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const data = await response.json();
      if (data.error) {
        setError(data.error);
        return false;
      }

      console.log('Game start response:', data);
      return true;
    } catch (error) {
      console.error('Error starting game:', error);
      setError('Failed to start game');
      return false;
    }
  }, [currentLobby]);

  return (
    <div className="lobby-container">
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {isGameStarted ? (
        <GameView 
          gameId={currentLobby.id} 
          messages={messages}
          initialGameState={messages.find(m => m.type === 'game_state')?.game_state}
          onReturnToLobby={async () => {
            await leaveLobby();
            setIsGameStarted(false);
            setMessages([]);
          }}
          onReturnToCharacterSelect={async () => {
            // Call the API to return all players to character select
            try {
              const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${currentLobby.id}/return-to-character-select/`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                }
              });
              const data = await response.json();
              if (data.success) {
                setIsGameStarted(false);
                setMessages([]);
              } else {
                setError(data.error || 'Failed to return to character select');
              }
            } catch (error) {
              console.error('Error returning to character select:', error);
              setError('Failed to return to character select');
            }
          }}
          onRestartGame={startGame}
        />
      ) : !currentLobby ? (
        <>
          {playerLobbyInfo && (
            <div className="info-banner" style={{
              backgroundColor: '#e3f2fd',
              padding: '15px',
              marginBottom: '20px',
              borderRadius: '5px',
              border: '1px solid #2196f3'
            }}>
              <strong>Note:</strong> You are currently a member of lobby "{playerLobbyInfo.name}". 
              {playerLobbyInfo.game_in_progress ? (
                <span> A game is in progress. Click "Join" below to rejoin the game.</span>
              ) : (
                <span> Click "Join" below to return to your lobby.</span>
              )}
            </div>
          )}
          
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
                <span>
                  {lobby.name} ({lobby.players.length} players)
                  {playerLobbyInfo && lobby.id === playerLobbyInfo.id && (
                    <span style={{ color: '#2196f3', fontWeight: 'bold' }}> ← Your Lobby</span>
                  )}
                  {lobby.game_in_progress && <span className="game-status in-progress"> </span>}
                  {!lobby.game_in_progress && <span className="game-status available"> </span>}
                </span>
                <button 
                  onClick={() => joinLobby(lobby.id)}
                  disabled={lobby.game_in_progress && (!playerLobbyInfo || lobby.id !== playerLobbyInfo.id)}
                >
                  {playerLobbyInfo && lobby.id === playerLobbyInfo.id 
                    ? (lobby.game_in_progress ? 'Rejoin Game' : 'Return to Lobby')
                    : (lobby.game_in_progress ? 'In Progress' : 'Join')}
                </button>
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
          <div className="lobby-controls">
            <button onClick={leaveLobby} className="leave-button">Leave Lobby</button>
            {currentLobby.players.length >= 2 && (
              <button 
                onClick={startGame} 
                className="start-button"
                disabled={currentLobby.players.some(p => !p.character_name)}
              >
                Start Game
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}