import React, { useState, useEffect } from "react";
import "../styles/clue-score-sheet.css";

const SUSPECTS = [
  "Colonel Mustard",
  "Professor Plum",
  "Mr. Green",
  "Mrs. Peacock",
  "Miss Scarlet",
  "Mrs. White",
];

const WEAPONS = [
  "Knife",
  "Candlestick",
  "Revolver",
  "Rope",
  "Lead Pipe",
  "Wrench",
];

const ROOMS = [
  "Hall",
  "Lounge",
  "Dining Room",
  "Kitchen",
  "Ballroom",
  "Conservatory",
  "Billiard Room",
  "Library",
  "Study",
];

function ClueScoreSheet() {
  // Load marked items from localStorage
  const loadMarkedItems = () => {
    const saved = localStorage.getItem("clueScoreSheet");
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

  // Save to localStorage whenever markedItems changes
  useEffect(() => {
    localStorage.setItem("clueScoreSheet", JSON.stringify(markedItems));
  }, [markedItems]);

  const toggleMark = (category, item) => {
    setMarkedItems((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [item]: !prev[category][item],
      },
    }));
  };

  const clearAll = () => {
    if (window.confirm("Clear all marks from the score sheet?")) {
      setMarkedItems({ suspects: {}, weapons: {}, rooms: {} });
    }
  };

  const renderSection = (title, items, category) => {
    return (
      <div className="score-sheet-section">
        <div className="score-sheet-header">{title}</div>
        <div className="score-sheet-table">
          {items.map((item) => (
            <div key={item} className="score-sheet-row">
              <div className="score-sheet-cell item-cell">{item}</div>
              <div className="score-sheet-cell mark-cell">
                <input
                  type="checkbox"
                  checked={markedItems[category][item] || false}
                  onChange={() => toggleMark(category, item)}
                  className="score-checkbox"
                />
              </div>
            </div>
          ))}
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

      <div className="score-sheet-content">
        {renderSection("SUSPECTS", SUSPECTS, "suspects")}
        {renderSection("WEAPONS", WEAPONS, "weapons")}
        {renderSection("ROOMS", ROOMS, "rooms")}
      </div>
    </div>
  );
}

export default ClueScoreSheet;

