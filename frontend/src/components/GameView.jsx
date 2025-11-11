import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useParams } from "react-router-dom";

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

export default function GameView({ gameId: propGameId, initialGameState }) {
  const { lobbyId } = useParams();
  const gameId = propGameId ?? lobbyId;
  const roomName = useMemo(() => {
    if (!gameId) {
      return null;
    }
    return String(gameId);
  }, [gameId]);

  const [gameState, setGameState] = useState(initialGameState ?? null);
  const [players, setPlayers] = useState(initialGameState?.players ?? []);
  const [currentPlayer, setCurrentPlayer] = useState(
    normalizeCurrentPlayer(initialGameState?.current_player),
  );
  const [myPlayer, setMyPlayer] = useState(null);
  const [moveOptions, setMoveOptions] = useState([]);
  const [isRequestingMoves, setIsRequestingMoves] = useState(false);

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
    () => Boolean(gameState?.is_active && !gameState?.is_completed),
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
  const hasMovedThisTurn = Boolean(gameState?.turn_state?.has_moved);

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
  }, [messages, myPlayer]);

  useEffect(() => {
    if (!isMyTurn || hasMovedThisTurn || myPlayer?.eliminated) {
      setIsRequestingMoves(false);
      setMoveOptions([]);
    }
  }, [isMyTurn, hasMovedThisTurn, myPlayer]);

  const handleMakeMove = useCallback(() => {
    if (!isMyTurn || myPlayer?.eliminated) {
      return;
    }
    setIsRequestingMoves(true);
    setMoveOptions([]);
    sendMessage({
      type: "make_move",
      player_id: myPlayer.id,
    });
  }, [isMyTurn, myPlayer, sendMessage]);

  const handleMoveOptionSelect = useCallback(
    (destination) => {
      if (!isMyTurn || myPlayer?.eliminated || !destination) {
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
    [isMyTurn, myPlayer, sendMessage],
  );

  const handleSuggestion = useCallback(() => {
    if (!isMyTurn || !isInRoom || myPlayer?.eliminated) {
      return;
    }
    const suspect = prompt(
      `Choose a suspect to suggest:\n${SUSPECTS.join("\n")}`,
      SUSPECTS[0],
    );
    if (!suspect || !SUSPECTS.includes(suspect)) {
      return;
    }
    const weapon = prompt(
      `Choose a weapon to suggest:\n${WEAPONS.join("\n")}`,
      WEAPONS[0],
    );
    if (!weapon || !WEAPONS.includes(weapon)) {
      return;
    }
    sendMessage({
      type: "make_suggestion",
      player_id: myPlayer.id,
      suspect,
      weapon,
    });
  }, [isMyTurn, isInRoom, myPlayer, sendMessage]);

  const handleAccusation = useCallback(() => {
    if (!isMyTurn || myPlayer?.eliminated) {
      return;
    }
    const suspect = prompt(
      `Accuse a suspect:\n${SUSPECTS.join("\n")}`,
      SUSPECTS[0],
    );
    if (!suspect || !SUSPECTS.includes(suspect)) {
      return;
    }
    const weapon = prompt(
      `Accuse a weapon:\n${WEAPONS.join("\n")}`,
      WEAPONS[0],
    );
    if (!weapon || !WEAPONS.includes(weapon)) {
      return;
    }
    const room = prompt(`Accuse a room:\n${ROOMS.join("\n")}`, ROOMS[0]);
    if (!room || !ROOMS.includes(room)) {
      return;
    }
    const confirmed = window.confirm(
      `Accuse ${suspect} with the ${weapon} in the ${room}?`,
    );
    if (!confirmed) {
      return;
    }
    sendMessage({
      type: "make_accusation",
      player_id: myPlayer.id,
      suspect,
      weapon,
      room,
    });
  }, [isMyTurn, myPlayer, sendMessage]);

  const handleEndTurn = useCallback(() => {
    if (!isMyTurn || myPlayer?.eliminated) {
      return;
    }
    sendMessage({
      type: "end_turn",
      player_id: myPlayer.id,
    });
  }, [isMyTurn, myPlayer, sendMessage]);

  const renderedMessages = useMemo(() => {
    return messages
      .map((msg, index) => {
        if (!msg || msg.type === "game_state" || msg.type === "move_options") {
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
      .filter(Boolean);
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
          {currentPlayer ? (
            <div>
              Current Turn: <strong>{currentPlayer.name}</strong>
              {isMyTurn && <span className="your-turn"> — Your Turn!</span>}
            </div>
          ) : (
            "Waiting for game start..."
          )}
        </div>
        {gameState?.winner && (
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
          {isMyTurn &&
            !myPlayer?.eliminated &&
            !hasMovedThisTurn &&
            moveOptions.map((option) => (
              <button
                key={option}
                className="game-button movement"
                onClick={() => handleMoveOptionSelect(option)}
              >
                {formatMoveOptionLabel(option) || option}
              </button>
            ))}
          {isMyTurn &&
            !myPlayer?.eliminated &&
            !hasMovedThisTurn &&
            isRequestingMoves &&
            moveOptions.length === 0 && (
              <button className="game-button movement" disabled>
                Getting movement options…
              </button>
            )}
          {isMyTurn && !myPlayer?.eliminated && hasMovedThisTurn && (
            <button className="game-button movement" disabled>
              Movement complete
            </button>
          )}
          <button
            onClick={handleMakeMove}
            className="game-button"
            disabled={
              !isMyTurn || myPlayer?.eliminated || hasMovedThisTurn || isRequestingMoves
            }
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : hasMovedThisTurn
                    ? "You have already moved this turn"
                    : "Request available destinations"
            }
          >
            Request Movement
          </button>
          <button
            onClick={handleSuggestion}
            className="game-button"
            disabled={!isMyTurn || !isInRoom || myPlayer?.eliminated}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : !isInRoom
                  ? "You must be in a room to make a suggestion"
                  : myPlayer?.eliminated
                    ? "You have been eliminated"
                    : "Suggest a suspect and weapon"
            }
          >
            Make Suggestion
          </button>
          <button
            onClick={handleAccusation}
            className="game-button warning"
            disabled={!isMyTurn || myPlayer?.eliminated}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : "Accuse the culprit (wrong guess eliminates you)"
            }
          >
            Make Accusation
          </button>
          <button
            onClick={handleEndTurn}
            className="game-button secondary"
            disabled={!isMyTurn || myPlayer?.eliminated}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : "Finish your turn"
            }
          >
            End Turn
          </button>
        </div>
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