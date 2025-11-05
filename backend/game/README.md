
### Domain structure rationale
The “entity classes” from the SDD (Card/Deck, Player, Board, etc) are implemented as plain Python modules inside the `game` app for this minimal increment. These are in-memory domain objects that encode game rules (movement legality, hallway occupancy, dealing, suggestions). This keeps core logic framework-agnostic, fast to test, and consistent with the SDD focus on server subsystem behavior.

### Minimal Increment Rubric:

Purpose of the Minimal system:
- Minimize risk.
- Prove out the architecture.
- All remaining requirements are fleshed out.
- Update the Project Plan.
- Revise the Software Requirements Specification.
- Continue the Design.
- This can serve as a fall-back position in case you can’t get the target increment working properly
- Capabilities delivered in minimal increment:
    - All essential functionality of main use cases.
    - The demonstration video should show an actual working application.

Rubric Criteria:
- Rudimentary User Interface Present (text or graphical)
- Essential functionality present
- Demonstration of working application
- Amount of apparent effort
- Presentation quality and value to stakeholders

