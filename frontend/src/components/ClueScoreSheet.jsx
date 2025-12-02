import React, { useState, useEffect } from "react";
import "../styles/clue-score-sheet.css";

const SUSPECTS = [
  "Colonel Mustard",
  "Miss Scarlet",
  "Mr. Green",
  "Mrs. Peacock",
  "Mrs. White",
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
  "Ballroom",
  "Billiard Room",
  "Conservatory",
  "Dining Room",
  "Hall",
  "Kitchen",
  "Library",
  "Lounge",
  "Study",
];

// Mark states: null (unmarked), "checked" (green checkmark), "maybe" (yellow hyphen)
const MARK_STATES = {
  UNMARKED: null,
  CHECKED: "checked",
  MAYBE: "maybe"
};

function ClueScoreSheet({ myPlayer, gameId }) {
  // Load marked items from localStorage
  const loadMarkedItems = () => {
    if (!gameId) return { suspects: {}, weapons: {}, rooms: {} };
    
    const saved = localStorage.getItem(`clueScoreSheet_${gameId}`);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return { suspects: {}, weapons: {}, rooms: {} };
      }
    }
    return { suspects: {}, weapons: {}, rooms: {} };
  };

  const [markedItems, setMarkedItems] = useState(loadMarkedItems);

  // Clear marks when gameId changes (new game started)
  useEffect(() => {
    if (gameId) {
      setMarkedItems(loadMarkedItems());
    }
  }, [gameId]);

  // Auto-populate based on player's hand and cards revealed by disprovers
  useEffect(() => {
    if (!myPlayer) return;
    
    const knownCards = myPlayer.known_cards || [];
    
    setMarkedItems((prev) => {
      const updated = { ...prev };
      
      // Auto-check all cards the player knows about (hand + revealed cards)
      [...SUSPECTS, ...WEAPONS, ...ROOMS].forEach((item) => {
        const category = 
          SUSPECTS.includes(item) ? "suspects" :
          WEAPONS.includes(item) ? "weapons" : "rooms";
        
        if (knownCards.includes(item)) {
          // Only auto-mark if not already manually marked
          if (!updated[category]) updated[category] = {};
          if (updated[category][item] === undefined || updated[category][item] === MARK_STATES.UNMARKED) {
            updated[category][item] = MARK_STATES.CHECKED;
          }
        }
      });
      
      return updated;
    });
  }, [myPlayer?.known_cards]);

  // Save to localStorage whenever markedItems changes
  useEffect(() => {
    if (gameId) {
      localStorage.setItem(`clueScoreSheet_${gameId}`, JSON.stringify(markedItems));
    }
  }, [markedItems, gameId]);

  // Left click: toggle between checked and unmarked
  const toggleCheck = (category, item) => {
    setMarkedItems((prev) => {
      const currentState = prev[category]?.[item];
      const nextState = currentState === MARK_STATES.CHECKED ? MARK_STATES.UNMARKED : MARK_STATES.CHECKED;
      
      return {
        ...prev,
        [category]: {
          ...prev[category],
          [item]: nextState,
        },
      };
    });
  };

  // Right click: toggle between maybe and unmarked
  const toggleMaybe = (e, category, item) => {
    e.preventDefault(); // Prevent context menu
    setMarkedItems((prev) => {
      const currentState = prev[category]?.[item];
      const nextState = currentState === MARK_STATES.MAYBE ? MARK_STATES.UNMARKED : MARK_STATES.MAYBE;
      
      return {
        ...prev,
        [category]: {
          ...prev[category],
          [item]: nextState,
        },
      };
    });
  };

  const clearAll = () => {
    if (window.confirm("Clear all marks from the score sheet?")) {
      setMarkedItems({ suspects: {}, weapons: {}, rooms: {} });
    }
  };

  // Helper function to get player initials (first letter of first name + first letter of last name)
  const getPlayerInitials = (name) => {
    if (!name) return "";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) {
      // Single name, use first two letters
      return name.substring(0, 2).toUpperCase();
    }
    // Multiple parts, use first letter of first and last name
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const renderSection = (title, items, category) => {
    return (
      <div className="score-sheet-section">
        <div className="score-sheet-header">{title}</div>
        <div className="score-sheet-table">
          {items.map((item) => {
            const markState = markedItems[category]?.[item];
            const revealedBy = myPlayer?.revealed_by?.[item]; // Get who revealed this card to me
            const revealedTo = myPlayer?.revealed_to?.[item]; // Get list of players I revealed this card to
            
            return (
              <div key={item} className="score-sheet-row">
                <div className="score-sheet-cell item-cell">{item}</div>
                <div 
                  className={`score-sheet-cell mark-cell ${markState || ''}`}
                  onClick={() => toggleCheck(category, item)}
                  onContextMenu={(e) => toggleMaybe(e, category, item)}
                  title="Left click: toggle check | Right click: toggle maybe"
                >
                  <div className="mark-content">
                    {markState === MARK_STATES.CHECKED && (
                      <span className="mark-symbol check">✓</span>
                    )}
                    {markState === MARK_STATES.MAYBE && (
                      <span className="mark-symbol maybe">−</span>
                    )}
                    {revealedBy && (
                      <span className="revealed-by-indicator" title={`Revealed by ${revealedBy}`}>
                        {getPlayerInitials(revealedBy)}
                      </span>
                    )}
                    {revealedTo && revealedTo.length > 0 && (
                      <span className="revealed-to-indicator" title={`Revealed to ${revealedTo.join(', ')}`}>
                        {revealedTo.map(name => getPlayerInitials(name)).join(',')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="clue-score-sheet">
      <div className="score-sheet-title-bar">
        <div className="score-sheet-title">
          <span className="clue-logo">CLUE LESS</span>
          <span className="score-sheets-text">SCORE SHEET</span>
        </div>
        <button className="clear-button" onClick={clearAll} title="Clear all marks">
          Clear
        </button>
      </div>

      <div className="score-sheet-help">
        <div className="help-section">
          <strong>Controls:</strong> Left-click = ✓ Check | Right-click = − Maybe
        </div>
        <div className="help-section">
          <strong>Badges:</strong> 
          <span className="revealed-by-indicator help-badge">BL</span> = Revealed by player | 
          <span className="revealed-to-indicator help-badge">OR</span> = Revealed to player
        </div>
      </div>

      <div className="score-sheet-content">
        {renderSection("SUSPECTS", SUSPECTS, "suspects")}
        {renderSection("WEAPONS", WEAPONS, "weapons")}
        {renderSection("ROOMS", ROOMS, "rooms")}
      </div>
    </div>
  );
}

export default ClueScoreSheet;