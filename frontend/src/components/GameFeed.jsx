import React, { useEffect, useRef } from "react";
import "../styles/feed.css";

export default function GameFeed({ messages }) {
  const feedRef = useRef();

  // Auto scroll to bottom on every new message
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="feed-container">
      <h2>🎲 Clue-Less Live Simulation</h2>
      <div ref={feedRef} className="feed-window">
        {messages.map((msg, i) => (
          <pre key={i} className="feed-line">{msg}</pre>
        ))}
      </div>
    </div>
  );
}
