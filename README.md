# ClueLess_MysteryGang_EN.605.601.81.FA25
GitHub for EN.605.601.81.FA25 - Mystery Gang

## Skeletal Backend Setup

Django project structure configured to support Django Channels and ASGI for Websocket communication


### Current Progress

So far, this increment includes:
- Created a Python virtual environment (`.venv`)
- Installed **Django**, **Channels**, and **Daphne**
- Started a Django project (`backend`) and app (`realtime`)
- Modified:
  - `backend/settings.py` → enabled `channels` and added an in-memory channel layer
  - `backend/asgi.py` → made the backend ASGI- and WebSocket-capable

Frontend:
- React frontend
- Modified:
  - `frontend/src/App.jsx` → enables the communication between backend and frontend via websockets, also defines webpage contents


## Backend Setup Instructions

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply database migrations
Propagates changes made to models into database schema
Source: https://www.geeksforgeeks.org/python/django-manage-py-migrate-command-python/
```bash
python backend/manage.py migrate
```

### 4. Run ASGI server
Run this command within the backend/ folder
```bash
daphne backend.asgi:application
```
Starts the Django + Channels server on port 8000

## Backend Setup Instructions

### 1. Go the the frontend (from the home directory)

```bash
cd frontend/
```

### 2. Install npm (one-time)

```bash
npm install
```
You may also need to update Node.js to its latest version before proceeding

### 3. Start the server

```bash
npm run dev
```