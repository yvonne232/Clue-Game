import React, { useState, useEffect } from 'react';
import '../styles/character-select.css';

export default function CharacterSelect({ lobbyId, onCharacterSelected }) {
    const [characters, setCharacters] = useState([]);
    const [selectedChar, setSelectedChar] = useState(null);
    const [error, setError] = useState(null);

    // Fetch available characters when component mounts
    useEffect(() => {
        fetchCharacters();
    }, [lobbyId]);

    const fetchCharacters = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${lobbyId}/available-characters/`);
            const data = await response.json();
            setCharacters(data.characters);
        } catch (error) {
            console.error('Error fetching characters:', error);
            setError('Failed to load characters');
        }
    };

    const selectCharacter = async (characterId) => {
        try {
            const playerId = localStorage.getItem('playerId');
            const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${lobbyId}/select-character/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: playerId,
                    character_id: characterId
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message);
            }

            const data = await response.json();
            setSelectedChar(characterId);
            onCharacterSelected(data);
        } catch (error) {
            console.error('Error selecting character:', error);
            setError(error.message);
        }
    };

    return (
        <div className="character-select">
            <h3>Select Your Character</h3>
            {error && <div className="error-message">{error}</div>}
            <div className="character-grid">
                {characters.map(char => (
                    <div 
                        key={char.id} 
                        className={`character-card ${char.taken ? 'taken' : ''} ${selectedChar === char.id ? 'selected' : ''}`}
                        onClick={() => !char.taken && selectCharacter(char.id)}
                    >
                        <div className="character-name">{char.name}</div>
                        {char.taken && <div className="taken-overlay">Taken</div>}
                    </div>
                ))}
            </div>
        </div>
    );
}