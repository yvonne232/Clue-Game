import React, { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import '../styles/game.css';

export default function GameView({ gameId }) {
    const [gameState, setGameState] = useState(null);
    const [players, setPlayers] = useState([]);
    const [currentPlayer, setCurrentPlayer] = useState(null);
    const [myPlayer, setMyPlayer] = useState(null);
    const [isMyTurn, setIsMyTurn] = useState(false);
    const { messages, sendMessage } = useWebSocket(`game/${gameId}`);

    useEffect(() => {
        // Find my player info when players list updates
        const playerId = localStorage.getItem('playerId');
        const player = players.find(p => p.id === playerId);
        setMyPlayer(player);
    }, [players]);

    // Handle incoming WebSocket messages
    useEffect(() => {
        if (messages.length > 0) {
            const latestMessage = messages[messages.length - 1];
            if (latestMessage.type === 'game_state') {
                setGameState(latestMessage.game_state);
                if (latestMessage.game_state.players) {
                    setPlayers(latestMessage.game_state.players);
                }
                if (latestMessage.game_state.current_player) {
                    setCurrentPlayer(latestMessage.game_state.current_player);
                    // Check if it's my turn
                    const playerId = localStorage.getItem('playerId');
                    const isMyTurn = latestMessage.game_state.current_player === playerId;
                    setIsMyTurn(isMyTurn);
                }
            }
        }
    }, [messages]);

    // Game action handlers
    const handleMakeMove = () => {
        if (!isMyTurn) return;
        sendMessage({
            type: 'make_move'
        });
    };

    const handleSuggestion = () => {
        if (!isMyTurn) return;
        sendMessage({
            type: 'make_suggestion'
        });
    };

    const handleAccusation = () => {
        if (!isMyTurn) return;
        sendMessage({
            type: 'make_accusation'
        });
    };

    return (
        <div className="game-view">
            <div className="game-header">
                <h2>Clue-Less Game</h2>
                <div className="turn-indicator">
                    {currentPlayer ? (
                        <div>
                            Current Turn: <strong>{currentPlayer}</strong>
                            {isMyTurn && <span className="your-turn"> - Your Turn!</span>}
                        </div>
                    ) : 'Game starting...'}
                </div>
            </div>

            <div className="player-list">
                <h3>Players</h3>
                <div className="players">
                    {players.map((player) => (
                        <div 
                            key={player.id} 
                            className={`player-card 
                                ${player.id === myPlayer?.id ? 'my-player' : ''} 
                                ${player.name === currentPlayer ? 'current-player' : ''}
                                ${player.eliminated ? 'eliminated' : ''}`}
                        >
                            <div className="player-name">
                                {player.name} {player.id === myPlayer?.id ? '(You)' : ''}
                                {player.name === currentPlayer && <span className="current-turn-marker">🎯</span>}
                            </div>
                            <div className="player-location">
                                Location: {player.location || 'Unknown'}
                            </div>
                            {player.eliminated && (
                                <div className="player-eliminated">
                                    Eliminated
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {isMyTurn && (
                <div className="game-controls">
                    <button onClick={handleMakeMove} className="game-button">
                        Make Move
                    </button>
                    {myPlayer?.location?.includes('Room') && (
                        <button onClick={handleSuggestion} className="game-button">
                            Make Suggestion
                        </button>
                    )}
                    <button onClick={handleAccusation} className="game-button warning">
                        Make Accusation
                    </button>
                </div>
            )}

            <div className="game-messages">
                {messages.map((msg, index) => (
                    <div key={index} className="game-message">
                        {msg.message}
                    </div>
                ))}
            </div>
        </div>
    );
}