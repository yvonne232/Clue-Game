import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";

import useWebSocket from "../hooks/useWebSocket";
import "../styles/game.css";

const SUSPECTS = [
  "Miss Scarlet",
  "Colonel Mustard",
  "Mrs. White",
  "Mr. Green",
  "Mrs. Peacock",
  "Professor Plum",
];

const WEAPONS = [
  "Candlestick",
  "Knife",
  "Lead Pipe",
  "Revolver",
  "Rope",
  "Wrench",
];

const ROOMS = [
  "Kitchen",
  "Ballroom",
  "Conservatory",
  "Dining Room",
  "Billiard Room",
  "Library",
  "Lounge",
  "Hall",
  "Study",
];

function normalizeCurrentPlayer(value) {
  if (!value) {
    return null;
  }
  if (typeof value === "string") {
    return { id: null, name: value };
  }
  if (typeof value === "object") {
    return {
      id: value.id ?? null,
      name: value.name ?? null,
    };
  }
  return null;
}

function formatMoveOptionLabel(option) {
  if (!option) {
    return "";
  }
  if (option.startsWith("Stay")) {
    return option;
  }
  const parts = option.split(" - ");
  const namePart = parts.length > 1 ? parts.slice(1).join(" - ") : option;
  if (/between/i.test(namePart)) {
    const hallwayText = namePart.replace(/^Between/i, (match) =>
      match === "Between" ? "between" : match.toLowerCase(),
    );
    return `Move to hallway ${hallwayText}`;
  }
  return `Move to ${namePart}`;
}

function formatLocationLabel(playerEntry) {
  if (!playerEntry?.location) {
    return "Location: Unknown";
  }
  const parts = String(playerEntry.location).split(" - ");
  const namePart =
    parts.length > 1 ? parts.slice(1).join(" - ") : playerEntry.location;
  if (playerEntry.location_type === "hallway") {
    const hallwayText = namePart.replace(/^Between/i, (match) =>
      match === "Between" ? "between" : match.toLowerCase(),
    );
    return `Location: Hallway (${hallwayText})`;
  }
  if (playerEntry.location_type === "room") {
    return `Location: Room (${namePart})`;
  }
  return `Location: ${namePart}`;
}

export default function GameView({
  gameId: propGameId,
  initialGameState,
  onReturnToLobby,
  onRestartGame,
}) {
  const { lobbyId } = useParams();
  const gameId = propGameId ?? lobbyId;
  const roomName = useMemo(() => {
    if (!gameId) {
      return null;
    }
    return String(gameId);
  }, [gameId]);

  const navigate = useNavigate();
  const normalizedLobbyId = useMemo(() => {
    if (!roomName) {
      return null;
    }
    return roomName.startsWith("lobby_")
      ? roomName.slice("lobby_".length)
      : roomName;
  }, [roomName]);
  const [gameState, setGameState] = useState(initialGameState ?? null);
  const [players, setPlayers] = useState(initialGameState?.players ?? []);
  const [currentPlayer, setCurrentPlayer] = useState(
    normalizeCurrentPlayer(initialGameState?.current_player),
  );
    const [myPlayer, setMyPlayer] = useState(null);
  const [moveOptions, setMoveOptions] = useState([]);
  const [isRequestingMoves, setIsRequestingMoves] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [suggestSuspect, setSuggestSuspect] = useState(SUSPECTS[0]);
  const [suggestWeapon, setSuggestWeapon] = useState(WEAPONS[0]);
  const [suggestRoom, setSuggestRoom] = useState(null);
  const [accuseSuspect, setAccuseSuspect] = useState(SUSPECTS[0]);
  const [accuseWeapon, setAccuseWeapon] = useState(WEAPONS[0]);
  const [accuseRoom, setAccuseRoom] = useState(ROOMS[0]);
  const [showSuggestionForm, setShowSuggestionForm] = useState(false);
  const [showAccusationForm, setShowAccusationForm] = useState(false);
  const [showDisproveModal, setShowDisproveModal] = useState(false);
  const [disproofInfo, setDisproofInfo] = useState(null);
  const [selectedDisproofCard, setSelectedDisproofCard] = useState(null);
  const [showSuggestionBanner, setShowSuggestionBanner] = useState(true);
  const [previousPlayerId, setPreviousPlayerId] = useState(null);
  const [myInitialHand, setMyInitialHand] = useState(null);
  const [pendingStatusMessage, setPendingStatusMessage] = useState(null);

  const { messages, sendMessage } = useWebSocket(roomName);

    useEffect(() => {
    const storedGameId = localStorage.getItem("currentGamePlayerId");
    const storedLobbyId = localStorage.getItem("playerId");
    const storedCharacter = localStorage.getItem("playerCharacter");

    const match =
      (storedGameId &&
        players.find((entry) => String(entry.id) === storedGameId)) ||
      (storedCharacter &&
        players.find((entry) => entry.name === storedCharacter)) ||
      (storedLobbyId &&
        players.find(
          (entry) =>
            String(entry.id) === storedLobbyId || entry.name === storedLobbyId,
        )) ||
      null;

    setMyPlayer(match);

    if (match) {
      localStorage.setItem("currentGamePlayerId", String(match.id));
      if (match.name) {
        localStorage.setItem("playerCharacter", match.name);
      }
    } else {
      localStorage.removeItem("currentGamePlayerId");
    }
    }, [players]);

  const isGameActive = useMemo(
    () =>
      Boolean(
        gameState?.is_active &&
          !gameState?.is_completed &&
          !gameState?.is_over &&
          !gameState?.winner,
      ),
    [gameState],
  );
  const isGameOver = useMemo(
    () =>
      Boolean(
        gameState?.winner ||
          gameState?.is_over ||
          (gameState?.is_completed && !gameState?.is_active),
      ),
    [gameState],
  );

  const isMyTurn = useMemo(() => {
    if (!isGameActive || !myPlayer || myPlayer.eliminated) {
      return false;
    }
    if (!currentPlayer) {
      return false;
    }
    const currentId =
      currentPlayer.id != null ? String(currentPlayer.id) : null;
    if (currentId && currentId === String(myPlayer.id)) {
      return true;
    }
    if (currentPlayer.name && myPlayer.name) {
      return currentPlayer.name === myPlayer.name;
    }
    return false;
  }, [currentPlayer, isGameActive, myPlayer]);

  const isInRoom = myPlayer?.location_type === "room";

  useEffect(() => {
    if (isInRoom) {
      const roomName =
        myPlayer?.location_name ??
        (typeof myPlayer?.location === "string"
          ? myPlayer.location.split(" - ").pop()
          : null);
      setSuggestRoom(roomName ?? null);
    } else {
      setSuggestRoom(null);
    }
  }, [isInRoom, myPlayer]);

  useEffect(() => {
    if (isGameOver || !isMyTurn || !isInRoom || myPlayer?.eliminated) {
      setShowSuggestionForm(false);
    }
  }, [isGameOver, isMyTurn, isInRoom, myPlayer]);

  useEffect(() => {
    if (isGameOver || !isMyTurn || myPlayer?.eliminated) {
      setShowAccusationForm(false);
    }
  }, [isGameOver, isMyTurn, myPlayer]);

  useEffect(() => {
    if (isGameOver || !disproofInfo) {
      setShowDisproveModal(false);
      setDisproofInfo(null);
    }
  }, [isGameOver, disproofInfo]);

  const hasMovedThisTurn = Boolean(gameState?.turn_state?.has_moved);
  const lastSuggestion = gameState?.last_suggestion ?? null;
  const lastSuggestionCard = lastSuggestion?.card ?? null;
  const lastSuggestionResolved = lastSuggestion != null;

  // Capture my initial hand once when first available (baseline before future reveals)
  useEffect(() => {
    if (!myPlayer) return;
    if (myInitialHand !== null) return;
    const me = players.find((p) => String(p.id) === String(myPlayer.id));
    const cards = Array.isArray(me?.known_cards) ? me.known_cards : [];
    if (cards.length) {
      setMyInitialHand([...cards]);
    }
  }, [players, myPlayer, myInitialHand]);

    useEffect(() => {
    if (!messages.length) {
      return;
    }
    const latest = messages[messages.length - 1];

    if (latest?.type === "game_state" && latest.game_state) {
      const incomingPlayers = Array.isArray(latest.game_state.players)
        ? latest.game_state.players
        : [];
      setGameState(latest.game_state);
      setPlayers(incomingPlayers);
      setCurrentPlayer(normalizeCurrentPlayer(latest.game_state.current_player));
      return;
    }

    if (latest?.type === "move_options") {
      const playerId = latest.player_id != null ? String(latest.player_id) : null;
      const storedGameId = localStorage.getItem("currentGamePlayerId");
      const storedCharacter = localStorage.getItem("playerCharacter");
      const matchesId =
        playerId &&
        (playerId === storedGameId ||
          playerId === String(myPlayer?.id) ||
          playerId === localStorage.getItem("playerId"));
      const matchesName =
        latest.player_name &&
        (latest.player_name === myPlayer?.name ||
          latest.player_name === storedCharacter);

      if (matchesId || matchesName) {
        setMoveOptions(latest.options ?? []);
        setIsRequestingMoves(false);
      }
      return;
    }

    if (latest?.type === "disprove_prompt") {
      setDisproofInfo({
        disprover_id: latest.disprover_id,
        disprover_name: latest.disprover_name,
        suggester_name: latest.suggester_name,
        matching_cards: latest.matching_cards,
      });
      
      // Show pending status for all players
      setPendingStatusMessage(`Waiting for ${latest.disprover_name} to choose a card to disprove...`);
      
      // Show modal only if this client is the disprover
      if (myPlayer && String(myPlayer.id) === String(latest.disprover_id)) {
        setShowDisproveModal(true);
        setSelectedDisproofCard(null);
      }
      return;
    }

    if (latest?.type === "disproof_result") {
      // Clear pending status when disproof is complete
      setPendingStatusMessage(null);
      
      // Only show to the suggester
      if (myPlayer && String(myPlayer.id) === String(latest.suggester_id)) {
        // Suggester sees the card privately
        // Could add to messages or show as a banner
        console.log(`Card revealed: ${latest.card} disproved by ${latest.disprover_name}`);
      }
      return;
    }

  }, [messages, myPlayer]);

  useEffect(() => {
    if (!isMyTurn || hasMovedThisTurn || myPlayer?.eliminated) {
      setIsRequestingMoves(false);
      setMoveOptions([]);
    }
  }, [isMyTurn, hasMovedThisTurn, myPlayer]);

  // Hide suggestion banner when turn changes
  useEffect(() => {
    const currentPlayerId = gameState?.current_player?.id;
    if (currentPlayerId !== undefined && previousPlayerId !== null && currentPlayerId !== previousPlayerId) {
      setShowSuggestionBanner(false);
      setPendingStatusMessage(null); // Clear pending status on turn change
    }
    if (currentPlayerId !== undefined) {
      setPreviousPlayerId(currentPlayerId);
    }
  }, [gameState?.current_player?.id, previousPlayerId]);

  // Show banner when new suggestion is resolved
  useEffect(() => {
    if (lastSuggestionResolved && lastSuggestionCard) {
      setShowSuggestionBanner(true);
    }
  }, [lastSuggestionResolved, lastSuggestionCard]);

  const handleMakeMove = useCallback(() => {
    if (!isMyTurn || myPlayer?.eliminated || isGameOver) {
      return;
    }
    setIsRequestingMoves(true);
    setMoveOptions([]);
        sendMessage({
      type: "make_move",
            player_id: myPlayer.id,
    });
  }, [isGameOver, isMyTurn, myPlayer, sendMessage]);

  const handleMoveOptionSelect = useCallback(
    (destination) => {
      if (!isMyTurn || myPlayer?.eliminated || !destination || isGameOver) {
        return;
      }
      setIsRequestingMoves(true);
      setMoveOptions([]);
        sendMessage({
        type: "make_move",
            player_id: myPlayer.id,
        destination,
      });
    },
    [isGameOver, isMyTurn, myPlayer, sendMessage],
  );

  const handleSuggestion = useCallback(() => {
    if (isGameOver || !isMyTurn || !isInRoom || myPlayer?.eliminated) {
      return;
    }
    setShowSuggestionForm(true);
  }, [isGameOver, isInRoom, isMyTurn, myPlayer]);

  const handleSuggestionSubmit = useCallback(() => {
    if (isGameOver || !isMyTurn || !isInRoom || myPlayer?.eliminated) {
      return;
    }
    const suspect = suggestSuspect;
    const weapon = suggestWeapon;
    if (!suspect || !weapon || !suggestRoom) {
      return;
    }
    sendMessage({
      type: "make_suggestion",
      player_id: myPlayer.id,
      suspect,
      weapon,
      room: suggestRoom,
    });
    setShowSuggestionForm(false);
  }, [
    isGameOver,
    isMyTurn,
    isInRoom,
    myPlayer,
    sendMessage,
    suggestSuspect,
    suggestWeapon,
    suggestRoom,
  ]);

  const handleSuggestionCancel = useCallback(() => {
    setShowSuggestionForm(false);
  }, []);

  const handleSelectDisproofCard = useCallback(
    (card) => {
      if (!myPlayer) return;
      setSelectedDisproofCard(card);
      sendMessage({
        type: "choose_disproving_card",
        player_id: myPlayer.id,
        card_name: card,
      });
      setShowDisproveModal(false);
      setDisproofInfo(null);
    },
    [myPlayer, sendMessage],
  );

  const handleAccusation = useCallback(() => {
    if (isGameOver || !isMyTurn || myPlayer?.eliminated) {
      return;
    }
    setShowAccusationForm(true);
  }, [isGameOver, isMyTurn, myPlayer]);

  const handleAccusationSubmit = useCallback(() => {
    if (isGameOver || !isMyTurn || myPlayer?.eliminated) {
      return;
    }

    sendMessage({
      type: "make_accusation",
      player_id: myPlayer.id,
      suspect: accuseSuspect,
      weapon: accuseWeapon,
      room: accuseRoom,
    });
    setShowAccusationForm(false);
  }, [
    isGameOver,
    isMyTurn,
    myPlayer,
    sendMessage,
    accuseSuspect,
    accuseWeapon,
    accuseRoom,
  ]);

  const handleAccusationCancel = useCallback(() => {
    setShowAccusationForm(false);
  }, []);

  const handleEndTurn = useCallback(() => {
    if (!isMyTurn || myPlayer?.eliminated || isGameOver) {
      return;
    }
            sendMessage({
      type: "end_turn",
                player_id: myPlayer.id,
    });
  }, [isGameOver, isMyTurn, myPlayer, sendMessage]);

  const handleReturnToLobby = useCallback(() => {
    const playerId = localStorage.getItem("playerId");
    if (normalizedLobbyId && playerId) {
      if (typeof onReturnToLobby === "function") {
        try {
          onReturnToLobby({
            lobbyId: normalizedLobbyId,
            playerId,
          });
        } catch (error) {
          console.error("Parent onReturnToLobby handler failed:", error);
        }
      } else {
        (async () => {
          try {
            const apiBase =
              import.meta.env.VITE_API_BASE_URL ||
              `${window.location.protocol}//${window.location.hostname}:8000`;
            const response = await fetch(`${apiBase}/api/lobbies/${normalizedLobbyId}/leave/`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ player_id: playerId }),
            });
            if (!response.ok) {
              const payload = await response.json().catch(() => ({}));
              const message =
                payload?.error ||
                payload?.detail ||
                `Leave lobby failed (${response.status})`;
              if (
                response.status !== 400 ||
                (message &&
                  !/player is not in this lobby/i.test(message) &&
                  !/already.*not.*lobby/i.test(message))
              ) {
                console.warn("Leave lobby request did not succeed:", message);
              }
            }
          } catch (error) {
            console.error("Failed to leave lobby:", error);
          }
        })();
      }
    }
    localStorage.removeItem("currentGamePlayerId");
    localStorage.removeItem("playerCharacter");
    navigate("/", { replace: true });
  }, [navigate, normalizedLobbyId, onReturnToLobby]);

  const handleRestartGame = useCallback(async () => {
    if (!normalizedLobbyId) {
      return;
    }
    setIsRestarting(true);
    try {
      if (typeof onRestartGame === "function") {
        await onRestartGame({ lobbyId: normalizedLobbyId });
      } else {
        const apiBase =
          import.meta.env.VITE_API_BASE_URL ||
          `${window.location.protocol}//${window.location.hostname}:8000`;
        const response = await fetch(`${apiBase}/api/lobbies/${normalizedLobbyId}/start/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          const message =
            payload?.detail || payload?.error || `Restart failed (${response.status})`;
          throw new Error(message);
        }
      }
    } catch (error) {
      console.error("Failed to restart game:", error);
      window.alert(error.message || "Unable to restart the game.");
    } finally {
      setIsRestarting(false);
    }
  }, [normalizedLobbyId, onRestartGame]);

  const renderedMessages = useMemo(() => {
    return messages
      .map((msg, index) => {
        if (!msg || msg.type === "game_state" || msg.type === "move_options" || 
            msg.type === "disprove_prompt" || msg.type === "disproof_result") {
          return null;
        }
        const text =
          typeof msg.message === "string"
            ? msg.message
            : typeof msg.text === "string"
              ? msg.text
              : typeof msg.error === "string"
                ? msg.error
                : null;
        if (!text) {
          return null;
        }
        const className =
          msg.type === "error" ? "game-message error" : "game-message";
        return (
          <div key={`${msg.type}-${index}`} className={className}>
            {text}
          </div>
        );
      })
      .filter(Boolean)
      .reverse(); // Newest messages first
  }, [messages]);

  if (!gameId) {
    return (
      <div className="game-view">
        <h2>Clue-Less Game</h2>
        <p>Unable to determine which game to join.</p>
      </div>
    );
  }

    return (
        <div className="game-view">
            <div className="game-header">
                <h2>Clue-Less Game</h2>
                <div className="turn-indicator">
          {isGameOver ? (
                        <div>
              <div className="turn-indicator-title">Game Over</div>
              <div className="turn-indicator-subtitle">
                {gameState?.winner
                  ? `${gameState.winner} solved the mystery!`
                  : "No winner this time."}
                </div>
            </div>
          ) : currentPlayer ? (
            <div>
              Current Turn: <strong>{currentPlayer.name}</strong>
              {isMyTurn && <span className="your-turn"> — Your Turn!</span>}
            </div>
          ) : (
            "Waiting for game start..."
          )}
        </div>
        {isGameOver && gameState?.winner && (
          <div className="winner-banner">
            Winner: <strong>{gameState.winner}</strong>
          </div>
        )}
            </div>

            <div className="player-list">
                <h3>Players</h3>
                <div className="players">
          {players.map((player) => {
            const isCurrent =
              (currentPlayer?.id != null &&
                String(currentPlayer.id) === String(player.id)) ||
              (currentPlayer?.name && currentPlayer.name === player.name);
            const cardClass = [
              "player-card",
              player.id === myPlayer?.id ? "my-player" : "",
              isCurrent ? "current-player" : "",
              player.eliminated ? "eliminated" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <div key={player.id} className={cardClass}>
                            <div className="player-name">
                  {player.name} {player.id === myPlayer?.id ? "(You)" : ""}
                  {isCurrent && <span className="current-turn-marker">🎯</span>}
                            </div>
                            <div className="player-location">
                  {formatLocationLabel(player)}
                            </div>
                {player.id === myPlayer?.id && (
                  (() => {
                    const known = Array.isArray(player.known_cards)
                      ? player.known_cards
                      : [];
                    const initial = Array.isArray(myInitialHand)
                      ? myInitialHand
                      : known; // fallback: if baseline not set, treat current as hand
                    const initSet = new Set(initial);
                    const seen = known.filter((c) => !initSet.has(c));
                    return (
                      <div className="player-known-cards">
                        <div>
                          <strong>Your Hand:</strong>{" "}
                          {initial.length > 0 ? initial.join(", ") : "(none)"}
                        </div>
                        {/* Disproved cards hidden for now to match physical board game
                        {seen.length > 0 && (
                          <div>
                            <strong>Disproved Cards:</strong>{" "}
                            {seen.join(", ")}
                          </div>
                        )}
                        */}
                      </div>
                    );
                  })()
                )}
                            {player.eliminated && (
                  <div className="player-eliminated">Eliminated</div>
                            )}
                        </div>
            );
          })}
                </div>
            </div>

            <div className="game-controls">
        <div className="button-row">
          {isMyTurn && !myPlayer?.eliminated && hasMovedThisTurn && (
            <button className="game-button movement" disabled>
              Movement complete
            </button>
          )}
                <button 
                    onClick={handleMakeMove} 
                    className="game-button"
            disabled={
              !isMyTurn ||
              myPlayer?.eliminated ||
              hasMovedThisTurn ||
              isRequestingMoves ||
              isGameOver
            }
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : hasMovedThisTurn
                    ? "You have already moved this turn"
                  : isGameOver
                    ? "The game has ended"
                    : "Request available destinations"
            }
          >
            Request Movement
                </button>
                <button 
                    onClick={handleSuggestion} 
                    className="game-button"
            disabled={!isMyTurn || !isInRoom || myPlayer?.eliminated || isGameOver}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : !isInRoom
                  ? "You must be in a room to make a suggestion"
                  : myPlayer?.eliminated
                    ? "You have been eliminated"
                  : isGameOver
                    ? "The game has ended"
                    : "Suggest a suspect and weapon"
            }
                >
                    Make Suggestion
                </button>
                <button 
                    onClick={handleAccusation} 
                    className="game-button warning"
            disabled={!isMyTurn || myPlayer?.eliminated || isGameOver}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : isGameOver
                    ? "The game has ended"
                  : "Accuse the culprit (wrong guess eliminates you)"
            }
          >
            Make Accusation
          </button>
          <button
            onClick={handleEndTurn}
            className="game-button secondary"
            disabled={!isMyTurn || myPlayer?.eliminated || isGameOver}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : isGameOver
                    ? "The game has ended"
                  : "Finish your turn"
            }
          >
            End Turn
          </button>
        </div>

        {isMyTurn && !myPlayer?.eliminated && !hasMovedThisTurn && !isGameOver && (
          <div className="move-options">
            {isRequestingMoves && moveOptions.length === 0 ? (
              <button className="game-button movement" disabled>
                Getting movement options…
              </button>
            ) : (
              moveOptions.map((option) => (
                <button
                  key={option}
                  className="game-button movement"
                  onClick={() => handleMoveOptionSelect(option)}
                >
                  {formatMoveOptionLabel(option) || option}
                </button>
              ))
            )}
          </div>
        )}

        {showSuggestionForm && (
          <div className="suggestion-form">
            <div className="suggestion-row">
              <label>
                Suspect
                <select
                  value={suggestSuspect}
                  onChange={(event) => setSuggestSuspect(event.target.value)}
                >
                  {SUSPECTS.map((suspect) => (
                    <option key={suspect} value={suspect}>
                      {suspect}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Weapon
                <select
                  value={suggestWeapon}
                  onChange={(event) => setSuggestWeapon(event.target.value)}
                >
                  {WEAPONS.map((weapon) => (
                    <option key={weapon} value={weapon}>
                      {weapon}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Room
                <input type="text" value={suggestRoom ?? ""} readOnly />
              </label>
            </div>
            <div className="suggestion-actions">
              <button className="game-button" onClick={handleSuggestionSubmit}>
                Submit Suggestion
              </button>
              <button
                className="game-button secondary"
                onClick={handleSuggestionCancel}
              >
                Cancel
                </button>
            </div>
          </div>
        )}

        {showDisproveModal && disproofInfo && (
          <div className="disprove-modal suggestion-form">
            <div className="suggestion-row">
              <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>
                Choose a card to disprove
              </h3>
              <p style={{ marginBottom: "1rem" }}>
                You can reveal one of these cards to {disproofInfo.suggester_name}:
              </p>
              <div className="card-options" style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {disproofInfo.matching_cards.map((card) => (
                  <button
                    key={card}
                    className="game-button"
                    onClick={() => handleSelectDisproofCard(card)}
                  >
                    {card}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {showAccusationForm && (
          <div className="suggestion-form accusation-form">
            <div className="suggestion-row">
              <label>
                Suspect
                <select
                  value={accuseSuspect}
                  onChange={(event) => setAccuseSuspect(event.target.value)}
                >
                  {SUSPECTS.map((suspect) => (
                    <option key={suspect} value={suspect}>
                      {suspect}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Weapon
                <select
                  value={accuseWeapon}
                  onChange={(event) => setAccuseWeapon(event.target.value)}
                >
                  {WEAPONS.map((weapon) => (
                    <option key={weapon} value={weapon}>
                      {weapon}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Room
                <select
                  value={accuseRoom}
                  onChange={(event) => setAccuseRoom(event.target.value)}
                >
                  {ROOMS.map((room) => (
                    <option key={room} value={room}>
                      {room}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="suggestion-actions">
              <button className="game-button warning" onClick={handleAccusationSubmit}>
                Submit Accusation
              </button>
              <button
                className="game-button secondary"
                onClick={handleAccusationCancel}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {isGameOver && (
          <div className="game-over-panel">
            <div className="game-over-text">
              {gameState?.winner
                ? `${gameState.winner} has won the game!`
                : "The game has ended."}
            </div>
            <button
              className="game-button"
              onClick={handleRestartGame}
              disabled={isRestarting}
            >
              {isRestarting ? "Restarting…" : "Restart Game"}
            </button>
            <button className="game-button secondary" onClick={handleReturnToLobby}>
              Return to Lobby
            </button>
          </div>
        )}

        {pendingStatusMessage && (
          <div className="suggestion-result-banner pending-status">
            {pendingStatusMessage}
          </div>
        )}

        {showSuggestionBanner && lastSuggestionResolved && lastSuggestionCard && myPlayer && (
          <div className="suggestion-result-banner">
            {lastSuggestion?.suggester === myPlayer.name ? (
              // Suggester sees the card privately
              <>
                Your suggestion was disproved by <strong>{lastSuggestion?.disprover}</strong>{' '}
                with <strong>{lastSuggestionCard}</strong>.
              </>
            ) : lastSuggestion?.disprover === myPlayer.name ? (
              // Disprover sees confirmation
              <>
                You disproved <strong>{lastSuggestion?.suggester}</strong>'s suggestion
                with <strong>{lastSuggestionCard}</strong>.
              </>
            ) : null}
          </div>
        )}
            </div>

            <div className="game-messages">
        {renderedMessages.length > 0 ? (
          renderedMessages
        ) : (
          <div className="game-message placeholder">
            Game updates will appear here.
                    </div>
        )}
            </div>
        </div>
    );
}