import React, { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import '../styles/game.css';

export default function GameView({ gameId }) {
    const [gameState, setGameState] = useState(null);
    const [players, setPlayers] = useState([]);
    const [currentPlayer, setCurrentPlayer] = useState(null);
    const [myPlayerId] = useState(localStorage.getItem('playerId'));
    const { messages, sendMessage } = useWebSocket(`game/${gameId}`);

    // Handle incoming WebSocket messages
    useEffect(() => {
        if (messages.length > 0) {
            const latestMessage = messages[messages.length - 1];
            if (latestMessage.type === 'game_state') {
                setGameState(latestMessage.game_state);
                setPlayers(latestMessage.game_state.players || []);
                setCurrentPlayer(latestMessage.game_state.current_player);
            }
        }
    }, [messages]);

    return (
        <div className="game-view">
            <div className="game-header">
                <h2>Clue-Less Game</h2>
                <div className="turn-indicator">
                    {currentPlayer ? `Current Turn: ${currentPlayer}` : 'Game starting...'}
                </div>
            </div>

            <div className="player-list">
                <h3>Players</h3>
                <div className="players">
                    {players.map((player, index) => (
                        <div 
                            key={player.id} 
                            className={`player-card ${player.id === myPlayerId ? 'my-player' : ''} ${player.id === currentPlayer ? 'current-player' : ''}`}
                        >
                            <div className="player-name">
                                {player.name} {player.id === myPlayerId ? '(You)' : ''}
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

            {/* Game board and controls will be added here */}
        </div>
    );
}