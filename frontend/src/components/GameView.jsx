import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";

import useWebSocket from "../hooks/useWebSocket";
import ClueScoreSheet from "./ClueScoreSheet";
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

// Helper: Extract hallway ID from location string
function getHallwayId(location) {
  if (!location) return null;
  const match = String(location).match(/H\d{2}/);
  return match ? match[0] : null;
}

// Helper: Get room name from location string
function getRoomName(location) {
  if (!location) return null;
  const locationStr = String(location);
  const rooms = [
    'Kitchen', 'Ballroom', 'Conservatory', 'Dining Room', 
    'Billiard Room', 'Library', 'Lounge', 'Hall', 'Study'
  ];
  for (const room of rooms) {
    if (locationStr === room || locationStr.includes(room)) {
      return room;
    }
  }
  return null;
}

// Helper: Extract the actual room name from a player's location string
// Handles formats like "Room - Dining Room" or just "Dining Room"
function extractRoomNameFromLocation(locationStr) {
  if (!locationStr) return null;
  const str = String(locationStr);
  const rooms = [
    'Kitchen', 'Ballroom', 'Conservatory', 'Dining Room', 
    'Billiard Room', 'Library', 'Lounge', 'Hall', 'Study'
  ];
  
  // Try exact match first
  if (rooms.includes(str)) {
    return str;
  }
  
  // Try to extract from " - " format
  const parts = str.split(' - ');
  if (parts.length > 1) {
    const namePart = parts.slice(1).join(' - ');
    for (const room of rooms) {
      if (namePart === room || namePart.includes(room)) {
        return room;
      }
    }
  }
  
  // Try substring match (but be more careful)
  for (const room of rooms) {
    // Use word boundaries to avoid partial matches
    const regex = new RegExp(`\\b${room.replace(/ /g, '\\s+')}\\b`, 'i');
    if (regex.test(str)) {
      return room;
    }
  }
  
  return null;
}

// Helper: Get players at a specific location
function getPlayersAtLocation(location, players) {
  if (!location || !players) return [];
  const locationStr = String(location);
  
  return players.filter((p) => {
    const playerLoc = p.location ? String(p.location) : '';
    if (!playerLoc) return false;
    
    // Determine what type of location we're checking
    const targetRoomName = getRoomName(locationStr);
    const targetHallwayId = getHallwayId(locationStr);
    
    // If checking a room
    if (targetRoomName) {
      // Only match if player is actually in a room
      if (p.location_type !== 'room') return false;
      
      const playerRoomName = extractRoomNameFromLocation(playerLoc);
      // Exact match of room names
      return playerRoomName === targetRoomName;
    }
    
    // If checking a hallway
    if (targetHallwayId) {
      // Only match if player is actually in a hallway
      if (p.location_type !== 'hallway') return false;
      
      const playerHallwayId = getHallwayId(playerLoc);
      return targetHallwayId === playerHallwayId;
    }
    
    // Exact match fallback
    return playerLoc === locationStr;
  });
}

export default function GameView({
  gameId: propGameId,
  initialGameState,
  onReturnToLobby,
  onReturnToCharacterSelect,
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
  const [pendingStatusMessage, setPendingStatusMessage] = useState(null);
  const [scoreSheetResetKey, setScoreSheetResetKey] = useState(0);

  const { messages, sendMessage, clearMessages } = useWebSocket(roomName);

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

  // Timeout for movement options request
  useEffect(() => {
    if (!isRequestingMoves) return;
    
    const timeoutId = setTimeout(() => {
      console.warn('Movement options timeout - no response received after 5 seconds');
      setIsRequestingMoves(false);
      setMoveOptions([]);
    }, 5000); // 5 second timeout
    
    return () => clearTimeout(timeoutId);
  }, [isRequestingMoves]);

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
  const hasSuggestedThisTurn = Boolean(gameState?.turn_state?.made_suggestion);
  const lastSuggestion = gameState?.last_suggestion ?? null;
  const lastSuggestionCard = lastSuggestion?.card ?? null;
  const lastSuggestionResolved = lastSuggestion != null;
  const isDisproofInProgress = Boolean(disproofInfo);
  
  // Players must confirm their movement before making a suggestion
  const canMakeSuggestion = hasMovedThisTurn;

    useEffect(() => {
    if (!messages.length) {
      return;
    }
    
    // Check recent messages for suggestion_not_disproved (might not be the latest)
    const recentMessages = messages.slice(-5); // Check last 5 messages
    const notDisprovedMsg = recentMessages.find(msg => msg?.type === "suggestion_not_disproved");
    if (notDisprovedMsg && disproofInfo) {
      // Clear disproof state when no one can disprove
      console.log("Received suggestion_not_disproved, clearing disproof state");
      setPendingStatusMessage(null);
      setDisproofInfo(null);
    }
    
    const latest = messages[messages.length - 1];

    if (latest?.type === "game_state" && latest.game_state) {
      const incomingPlayers = Array.isArray(latest.game_state.players)
        ? latest.game_state.players
        : [];
      setGameState(latest.game_state);
      setPlayers(incomingPlayers);
      setCurrentPlayer(normalizeCurrentPlayer(latest.game_state.current_player));
      
      // Clear disproof state if the last suggestion result shows a card was revealed
      // This means the disproof is complete
      if (disproofInfo && latest.game_state.last_suggestion) {
        const lastSuggestion = latest.game_state.last_suggestion;
        if (lastSuggestion.card && lastSuggestion.disprover) {
          // Disproof is complete - clear the state
          console.log("Disproof complete based on game state, clearing disproofInfo");
          setDisproofInfo(null);
          setPendingStatusMessage(null);
          setShowDisproveModal(false);
        } else if (!lastSuggestion.card && !lastSuggestion.disprover && lastSuggestion.suggester) {
          // No one could disprove - clear the state
          console.log("No one could disprove, clearing disproofInfo");
          setDisproofInfo(null);
          setPendingStatusMessage(null);
          setShowDisproveModal(false);
        }
      }
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

      console.log('Received move_options:', {
        playerId,
        player_name: latest.player_name,
        options: latest.options,
        myPlayerId: myPlayer?.id,
        myPlayerName: myPlayer?.name,
        storedGameId,
        storedCharacter,
        matchesId,
        matchesName
      });

      if (matchesId || matchesName) {
        const options = latest.options ?? [];
        console.log('Setting move options:', options);
        setMoveOptions(options);
        setIsRequestingMoves(false);
      } else {
        console.warn('Move options received but player ID/name mismatch:', {
          receivedPlayerId: playerId,
          receivedPlayerName: latest.player_name,
          myPlayerId: myPlayer?.id,
          myPlayerName: myPlayer?.name
        });
        // Still reset the requesting state to prevent UI from being stuck
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
      setDisproofInfo(null);
      setShowDisproveModal(false);
      
      // Only show to the suggester
      if (myPlayer && String(myPlayer.id) === String(latest.suggester_id)) {
        // Suggester sees the card privately
        // Could add to messages or show as a banner
        console.log(`Card revealed: ${latest.card} disproved by ${latest.disprover_name}`);
      }
      return;
    }

    // Handle clear_log message from backend when game is restarted
    if (latest?.type === "clear_log") {
      clearMessages();
      // Increment reset key to trigger score sheet reset
      setScoreSheetResetKey(prev => prev + 1);
      console.log("Game log and score sheet cleared by server");
      return;
    }

    // Handle errors that might occur during movement
    if (latest?.type === "error" && isRequestingMoves) {
      const errorText = latest.message || latest.error || "";
      if (errorText.toLowerCase().includes("move") || 
          errorText.toLowerCase().includes("movement") ||
          errorText.toLowerCase().includes("unable to move")) {
        console.error('Movement error received:', errorText);
        setIsRequestingMoves(false);
        setMoveOptions([]);
      }
    }

  }, [messages, myPlayer, disproofInfo, isRequestingMoves, clearMessages, roomName]);

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

  // Show banner when new suggestion is resolved (either disproved or not disproved)
  useEffect(() => {
    if (lastSuggestionResolved) {
      setShowSuggestionBanner(true);
    }
  }, [lastSuggestionResolved]);

  // Listen for return to character select message
  useEffect(() => {
    const returnMsg = messages.find(msg => msg.type === "return_to_character_select");
    if (returnMsg && onReturnToCharacterSelect) {
      console.log("Received return to character select message, calling callback");
      onReturnToCharacterSelect();
    }
  }, [messages, onReturnToCharacterSelect]);

  const handleMakeMove = useCallback(() => {
    if (!isMyTurn || myPlayer?.eliminated || isGameOver) {
      return;
    }
    console.log('Requesting movement options for player:', myPlayer.id, myPlayer.name);
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
    
    // Immediately set disproof in progress to prevent actions during processing
    setDisproofInfo({
      disprover_id: null,
      disprover_name: "pending",
      suggester_name: myPlayer.name,
      matching_cards: [],
    });
    
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

  const handleReturnToCharacterSelect = useCallback(async () => {
    if (!normalizedLobbyId) return;
    
    try {
      const apiBase =
        import.meta.env.VITE_API_BASE_URL ||
        `${window.location.protocol}//${window.location.hostname}:8000`;
      const response = await fetch(
        `${apiBase}/api/lobbies/${normalizedLobbyId}/return-to-character-select/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );
      
      if (!response.ok) {
        console.error("Failed to return to character select");
      }
    } catch (error) {
      console.error("Error returning to character select:", error);
    }
  }, [normalizedLobbyId]);

  const handleReturnToLobby = useCallback(() => {
    const playerId = localStorage.getItem("playerId");
    if (normalizedLobbyId && playerId) {
      // First, return all players to character select
      (async () => {
        try {
          const apiBase =
            import.meta.env.VITE_API_BASE_URL ||
            `${window.location.protocol}//${window.location.hostname}:8000`;
          
          // Call return to character select to notify other players
          await fetch(
            `${apiBase}/api/lobbies/${normalizedLobbyId}/return-to-character-select/`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
            }
          );
        } catch (error) {
          console.error("Failed to return players to character select:", error);
        }
      })();

      // Then handle leave lobby for this player
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
    // Backend will broadcast clear_log to all players via WebSocket
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
            msg.type === "disprove_prompt" || msg.type === "disproof_result" ||
            msg.type === "suggestion_not_disproved") {
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
                <h2>CLUE LESS Game</h2>
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

            {/* Main Game Layout: Board on left, Hand sidebar on right */}
            <div className="game-main-layout">
              {/* Game Board */}
              <div className="game-board-container">
            {(() => {
              // Helper function to render player markers at a location
              // Show all players at their current positions
              const renderPlayerMarkers = (location) => {
                // Get all players at this location
                const playersHere = getPlayersAtLocation(location, players);
                if (playersHere.length === 0) return null;
                
                // Filter out eliminated players
                const activePlayers = playersHere.filter(p => !p.eliminated);
                if (activePlayers.length === 0) return null;
                
                return (
                  <div className="player-markers">
                    {activePlayers.map((p) => {
                      const isMyPlayer = p.id === myPlayer?.id;
                      const isCurrentPlayer = 
                        (currentPlayer?.id != null && String(currentPlayer.id) === String(p.id)) ||
                        (currentPlayer?.name && currentPlayer.name === p.name);
                      
                      // Determine character class for color
                      let characterClass = '';
                      if (p.name.includes('Scarlet')) characterClass = 'character-scarlet';
                      else if (p.name.includes('Mustard')) characterClass = 'character-mustard';
                      else if (p.name.includes('White')) characterClass = 'character-white';
                      else if (p.name.includes('Green')) characterClass = 'character-green';
                      else if (p.name.includes('Peacock')) characterClass = 'character-peacock';
                      else if (p.name.includes('Plum')) characterClass = 'character-plum';
                      
                      return (
                        <span 
                          key={p.id} 
                          className={`player-marker ${characterClass} ${isMyPlayer ? 'my-marker' : ''} ${isCurrentPlayer ? 'current-marker' : ''}`}
                          title={p.name}
                        >
                          {p.name.split(' ').map(word => word[0]).join('')}
                        </span>
                      );
                    })}
                  </div>
                );
              };

              return (
                <div className="game-board">
                  <div className="board-row">
                    <div className="room-cell">
                      <div className="secret-passage bottom-right" title="Secret passage to Kitchen"></div>
                      <div className="room-name">Study</div>
                      {renderPlayerMarkers('Study')}
                    </div>
                    <div className="hallway-cell vertical">
                      {renderPlayerMarkers('H12')}
                    </div>
                    <div className="room-cell">
                      <div className="room-name">Hall</div>
                      {renderPlayerMarkers('Hall')}
                    </div>
                    <div className="hallway-cell vertical">
                      {renderPlayerMarkers('H11')}
                        </div>
                    <div className="room-cell">
                      <div className="secret-passage bottom-left" title="Secret passage to Conservatory"></div>
                      <div className="room-name">Lounge</div>
                      {renderPlayerMarkers('Lounge')}
                </div>
            </div>

                  <div className="board-row hallway-row">
                    <div className="hallway-cell horizontal">
                      {renderPlayerMarkers('H10')}
                    </div>
                    <div className="empty-cell"></div>
                    <div className="hallway-cell horizontal">
                      {renderPlayerMarkers('H09')}
                    </div>
                    <div className="empty-cell"></div>
                    <div className="hallway-cell horizontal">
                      {renderPlayerMarkers('H08')}
                    </div>
                  </div>
                  <div className="board-row">
                    <div className="room-cell">
                      <div className="room-name">Library</div>
                      {renderPlayerMarkers('Library')}
                    </div>
                    <div className="hallway-cell vertical">
                      {renderPlayerMarkers('H07')}
                    </div>
                    <div className="room-cell">
                      <div className="room-name">Billiard Room</div>
                      {renderPlayerMarkers('Billiard Room')}
                    </div>
                    <div className="hallway-cell vertical">
                      {renderPlayerMarkers('H06')}
                    </div>
                    <div className="room-cell">
                      <div className="room-name">Dining Room</div>
                      {renderPlayerMarkers('Dining Room')}
                    </div>
                  </div>
                  <div className="board-row hallway-row">
                    <div className="hallway-cell horizontal">
                      {renderPlayerMarkers('H05')}
                    </div>
                    <div className="empty-cell"></div>
                    <div className="hallway-cell horizontal">
                      {renderPlayerMarkers('H04')}
                    </div>
                    <div className="empty-cell"></div>
                    <div className="hallway-cell horizontal">
                      {renderPlayerMarkers('H03')}
                    </div>
                  </div>
                  <div className="board-row">
                    <div className="room-cell">
                      <div className="secret-passage top-right" title="Secret passage to Lounge"></div>
                      <div className="room-name">Conservatory</div>
                      {renderPlayerMarkers('Conservatory')}
                    </div>
                    <div className="hallway-cell vertical">
                      {renderPlayerMarkers('H02')}
                    </div>
                    <div className="room-cell">
                      <div className="room-name">Ballroom</div>
                      {renderPlayerMarkers('Ballroom')}
                    </div>
                    <div className="hallway-cell vertical">
                      {renderPlayerMarkers('H01')}
                    </div>
                    <div className="room-cell">
                      <div className="secret-passage top-left" title="Secret passage to Study"></div>
                      <div className="room-name">Kitchen</div>
                      {renderPlayerMarkers('Kitchen')}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Players list and controls below the board */}
            <div className="player-list">
                <h3>Players</h3>
                <div className="players">
          {players.map((player) => {
            const isCurrent =
              (currentPlayer?.id != null &&
                String(currentPlayer.id) === String(player.id)) ||
              (currentPlayer?.name && currentPlayer.name === player.name);

            return (
              <div key={player.id} className="player-name-only">
                {player.name}
                {player.id === myPlayer?.id && " (You)"}
                {isCurrent && <span className="current-turn-marker">🎯</span>}
                            {player.eliminated && (
                  <span className="eliminated-text"> (Eliminated)</span>
                            )}
                        </div>
            );
          })}
                </div>
            </div>

            <div className="game-controls">
        <div className="button-row">
                <button 
                    onClick={handleMakeMove} 
                    className="game-button"
            disabled={
              !isMyTurn ||
              myPlayer?.eliminated ||
              hasMovedThisTurn ||
              isRequestingMoves ||
              isGameOver ||
              isDisproofInProgress
            }
            title={
              !isMyTurn
                ? "Wait for your turn"
                : myPlayer?.eliminated
                  ? "You have been eliminated"
                  : hasMovedThisTurn
                    ? "You have already moved this turn"
                  : isDisproofInProgress
                    ? "Waiting for suggestion to be disproved"
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
            disabled={!isMyTurn || !isInRoom || hasSuggestedThisTurn || !canMakeSuggestion || myPlayer?.eliminated || isGameOver || isDisproofInProgress}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : !isInRoom
                  ? "You must be in a room to make a suggestion"
                  : hasSuggestedThisTurn
                    ? "You have already made a suggestion this turn"
                  : !canMakeSuggestion
                    ? "You must confirm your movement before making a suggestion"
                  : isDisproofInProgress
                    ? "Waiting for suggestion to be disproved"
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
            disabled={!isMyTurn || myPlayer?.eliminated || isGameOver || isDisproofInProgress}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : isDisproofInProgress
                  ? "Waiting for suggestion to be disproved"
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
            disabled={!isMyTurn || myPlayer?.eliminated || isGameOver || isDisproofInProgress}
            title={
              !isMyTurn
                ? "Wait for your turn"
                : isDisproofInProgress
                  ? "Waiting for suggestion to be disproved"
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
            <button 
              className="game-button secondary" 
              onClick={handleReturnToCharacterSelect}
            >
              Return to Character Select
            </button>
          </div>
        )}

        {pendingStatusMessage && (
          <div className="suggestion-result-banner pending-status">
            {pendingStatusMessage}
          </div>
        )}

        {showSuggestionBanner && lastSuggestionResolved && myPlayer && (
          <div className="suggestion-result-banner">
            {lastSuggestionCard ? (
              // Someone disproved
              <>
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
                ) : (
                  // Other players see that it was disproved
                  <>
                    <strong>{lastSuggestion?.suggester}</strong>'s suggestion was disproved by{' '}
                    <strong>{lastSuggestion?.disprover}</strong>.
                  </>
                )}
              </>
            ) : (
              // No one could disprove
              <>
                {lastSuggestion?.suggester === myPlayer.name ? (
                  <>
                    No one could disprove your suggestion.
                  </>
                ) : (
                  <>
                    No one could disprove{' '}
                    <strong>{lastSuggestion?.suggester}</strong>'s suggestion.
                  </>
                )}
              </>
            )}
          </div>
        )}
              </div>
            </div>

            {/* Right Side: User Hand only */}
            <div className="game-sidebar">
              <div className="player-hands-container">
                <div className="hand-label">
                  <strong>Your Hand:</strong>
                </div>
                <div className="hand-cards">
                  {(() => {
                    const me = players.find(
                      (p) => p.id === myPlayer?.id,
                    );
                    if (!me || !Array.isArray(me.hand) || me.hand.length === 0) {
                      return <div className="no-cards">No cards in hand</div>;
                    }
                    return me.hand.map((card, index) => {
                      const cardType = SUSPECTS.includes(card)
                        ? "suspect"
                        : WEAPONS.includes(card)
                        ? "weapon"
                        : ROOMS.includes(card)
                        ? "room"
                        : "unknown";
                      const cardIcon =
                        cardType === "suspect"
                          ? "👤"
                          : cardType === "weapon"
                          ? "⚔️"
                          : cardType === "room"
                          ? "🏠"
                          : "❓";
                      return (
                        <div
                          key={index}
                          className={`game-card card-${cardType}`}
                        >
                          <div className="card-corner card-corner-top-left">
                            {cardIcon}
                          </div>
                          <div className="card-corner card-corner-bottom-right">
                            {cardIcon}
                          </div>
                          <div className="card-content">
                            <div className="card-name">{card}</div>
                            <div className="card-type">{cardType}</div>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            </div>
          </div>

            {/* Movement Options Below Board and Players Section */}
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

            <div className="game-messages">
        {renderedMessages.length > 0 ? (
          renderedMessages
        ) : (
          <div className="game-message placeholder">
            Game updates will appear here.
                    </div>
        )}
            </div>

        <ClueScoreSheet 
          myPlayer={myPlayer} 
          gameId={roomName}
          resetKey={scoreSheetResetKey}
        />
        </div>
    );
}