import React from "react";
import "../styles/solution-tracker.css";

function SolutionTracker({ possibleCards }) {
  if (!possibleCards) {
    return null;
  }

  const { suspects = [], weapons = [], rooms = [] } = possibleCards;

  return (
    <div className="solution-tracker">
      <h3>Solution Tracker</h3>
      <p className="tracker-description">
        Cards that could still be in the solution (based on what you've seen)
      </p>

      <div className="tracker-sections">
        <div className="tracker-section">
          <h4>Suspects ({suspects.length})</h4>
          <div className="tracker-cards">
            {suspects.length > 0 ? (
              suspects.map((suspect) => (
                <div key={suspect} className="tracker-card suspect">
                  {suspect}
                </div>
              ))
            ) : (
              <div className="tracker-empty">All suspects eliminated</div>
            )}
          </div>
        </div>

        <div className="tracker-section">
          <h4>Weapons ({weapons.length})</h4>
          <div className="tracker-cards">
            {weapons.length > 0 ? (
              weapons.map((weapon) => (
                <div key={weapon} className="tracker-card weapon">
                  {weapon}
                </div>
              ))
            ) : (
              <div className="tracker-empty">All weapons eliminated</div>
            )}
          </div>
        </div>

        <div className="tracker-section">
          <h4>Rooms ({rooms.length})</h4>
          <div className="tracker-cards">
            {rooms.length > 0 ? (
              rooms.map((room) => (
                <div key={room} className="tracker-card room">
                  {room}
                </div>
              ))
            ) : (
              <div className="tracker-empty">All rooms eliminated</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SolutionTracker;
