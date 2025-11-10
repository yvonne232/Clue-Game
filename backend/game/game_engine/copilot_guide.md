# Clue-Less Game Implementation Guide

## Game Overview
Clue-Less is a simplified version of the classic board game Clue implemented as an online multiplayer game. Players move around a board, make suggestions about the murder's circumstances, and try to make a correct accusation to win.

## Core Game Components

### Cards and Game Elements
- Characters: Miss Scarlet, Colonel Mustard, Professor Plum, Mrs. Peacock, Mr. Green, Mrs. White
- Weapons: Candlestick, Knife/Dagger, Lead Pipe, Revolver, Rope, Wrench
- Rooms: Kitchen, Ballroom, Conservatory, Dining Room, Billiard Room, Library, Lounge, Hall, Study

### Board Layout
```
[Study]---[Hall]---[Lounge]
   |        |         |
   |        |         |
[Library]--[Billiard]--[Dining]
   |        |         |
   |        |         |
[Conserv]--[Ball]---[Kitchen]
```

### Character Starting Positions
- Miss Scarlet: Between Lounge and Hall
- Colonel Mustard: Between Dining Room and Lounge
- Professor Plum: Between Library and Study
- Mrs. Peacock: Between Conservatory and Library
- Mr. Green: Between Ballroom and Conservatory
- Mrs. White: Between Kitchen and Ballroom

### Movement Rules
1. Players don't roll dice - movement is deterministic
2. When in a room, you may:
   - Move through a door to an unoccupied hallway
   - Take a secret passage to the opposite corner room (if available)
   - Stay in room if moved there by suggestion
3. When in a hallway:
   - Must move to one of the connected rooms
4. Restrictions:
   - Only one character per hallway
   - Cannot move to occupied hallways
   - If all exits blocked and no secret passage, skip movement

## Game Mechanics

### Turn Structure
1. Movement Phase
   - Follow movement rules above
   - Must move if in hallway
   - May stay if suggestion-moved
2. Action Phase (Optional)
   - Make suggestion if in room
   - Make accusation anytime during turn

### Suggestions
1. Must be made from current room
2. Specify suspect and weapon only
3. Named suspect moves to suggestion room
4. Players clockwise try to disprove
5. Show one matching card if possible
6. Card shown is only visible to the player making the suggestion, other players get a message that indicates a card is shown but not which card.

### Accusations
1. Available anytime during turn
2. Must name exact suspect, weapon, room
3. Correct accusation wins game
4. Wrong accusation eliminates player but:
   - Still shows cards for suggestions
   - Cannot make further actions

## Technical Implementation

### Database Models Used
1. Room
   - Name, connections, secret passage
2. Hallway
   - Connected rooms, occupancy
3. Card
   - Type (suspect/weapon/room), name
4. Player
   - Character, location, game status
5. Game
   - Players, state, solution

### WebSocket Events
- Game State Updates
- Player Movement
- Suggestions/Responses
- Accusations/Results
- Turn Management

### Key Game States
1. Game Setup
   - Create solution
   - Deal cards
   - Place players
2. Turn Execution
   - Movement validation
   - Action processing
3. Game Resolution
   - Correct accusation
   - All players eliminated

### Error Handling
- Invalid moves
- Out-of-turn actions
- Duplicate characters
- Disconnections
- Timeout management