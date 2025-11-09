import React, { useState, useEffect, useCallback } from 'react';
import '../styles/character-select.css';

const CHARACTERS = [
    { id: 1, name: "Miss Scarlet" },
    { id: 2, name: "Colonel Mustard" },
    { id: 3, name: "Mrs. White" },
    { id: 4, name: "Mr. Green" },
    { id: 5, name: "Mrs. Peacock" },
    { id: 6, name: "Professor Plum" }
];

const POLLING_INTERVAL = 1000; // Poll every 1 second

export default function CharacterSelect({ lobbyId, onCharacterSelected }) {
    const [characters, setCharacters] = useState(CHARACTERS);
    const [selectedChar, setSelectedChar] = useState(null);
    const [error, setError] = useState(null);
    const [takenCharacters, setTakenCharacters] = useState([]);
    const [myCharacter, setMyCharacter] = useState(null);

    // Function to check if a character belongs to the current player
    const isMyCharacter = useCallback((characterName) => {
        return myCharacter === characterName;
    }, [myCharacter]);

    // Poll for taken characters
    const pollTakenCharacters = useCallback(async () => {
        if (!lobbyId) return;

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${lobbyId}/`);
            const data = await response.json();
            
            // Extract taken character names from players
            const taken = data.players
                .filter(p => p.character_name)
                .map(p => p.character_name);
            
            // Find my character if exists
            const playerId = localStorage.getItem('playerId');
            const myPlayerData = data.players.find(p => p.id === playerId);
            const myCurrentCharacter = myPlayerData ? myPlayerData.character_name : null;

            // Only update state if there are changes
            if (JSON.stringify(taken) !== JSON.stringify(takenCharacters)) {
                setTakenCharacters(taken);
            }
            if (myCurrentCharacter !== myCharacter) {
                setMyCharacter(myCurrentCharacter);
                if (myCurrentCharacter) {
                    const selectedCharacter = CHARACTERS.find(c => c.name === myCurrentCharacter);
                    if (selectedCharacter) {
                        setSelectedChar(selectedCharacter.id);
                    }
                }
            }
        } catch (error) {
            console.error('Error polling taken characters:', error);
            setError('Failed to update character status');
        }
    }, [lobbyId, takenCharacters, myCharacter]);

    // Set up polling interval
    useEffect(() => {
        // Initial fetch
        pollTakenCharacters();

        // Set up polling interval
        const interval = setInterval(pollTakenCharacters, POLLING_INTERVAL);

        // Cleanup interval on unmount or when lobbyId changes
        return () => clearInterval(interval);
    }, [lobbyId, pollTakenCharacters]);

    const fetchTakenCharacters = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${lobbyId}/`);
            const data = await response.json();
            // Extract taken character names from players
            const taken = data.players
                .filter(p => p.character_name)
                .map(p => p.character_name);
            setTakenCharacters(taken);
        } catch (error) {
            console.error('Error fetching taken characters:', error);
            setError('Failed to load taken characters');
        }
    };

    const selectCharacter = async (character) => {
        try {
            const playerId = localStorage.getItem('playerId');
            const response = await fetch(`http://127.0.0.1:8000/api/lobbies/${lobbyId}/select-character/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: playerId,
                    character_name: character.name
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message);
            }

            const data = await response.json();
            setSelectedChar(character.id);
            onCharacterSelected({ character_name: character.name });
        } catch (error) {
            console.error('Error selecting character:', error);
            setError(error.message || 'Failed to select character');
        }
    };

    return (
        <div className="character-select">
            <h3>{myCharacter ? 'Your Character' : 'Select Your Character'}</h3>
            {error && <div className="error-message">{error}</div>}
            <div className="character-grid">
                {characters.map(char => {
                    const isTaken = takenCharacters.includes(char.name);
                    const isMyChar = isMyCharacter(char.name);
                    const isSelected = selectedChar === char.id;
                    return (
                        <div 
                            key={char.id} 
                            className={`character-card 
                                ${isTaken ? 'taken' : ''} 
                                ${isSelected ? 'selected' : ''} 
                                ${isMyChar ? 'my-character' : ''}`}
                            onClick={() => !isTaken && !myCharacter && selectCharacter(char)}
                        >
                            <div className="character-name">{char.name}</div>
                            {isTaken && (
                                <div className="taken-overlay">
                                    {isMyChar ? 'Your Character' : 'Taken'}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
            {myCharacter && (
                <div className="character-info">
                    <button 
                        className="change-character-btn"
                        onClick={() => {
                            setSelectedChar(null);
                            setMyCharacter(null);
                            setError(null);
                        }}
                    >
                        Change Character
                    </button>
                </div>
            )}
        </div>
    );
}