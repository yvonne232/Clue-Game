from django.db.models.signals import pre_save
from django.dispatch import receiver, Signal
from .models.lobby import Lobby
from .models.lobby_player import LobbyPlayer
import atexit
import signal
import sys

cleanup_signal = Signal()

def cleanup_database():
    """Clean up all active lobbies and their associated players"""
    try:
        # Delete all lobby players first (due to foreign key constraints)
        LobbyPlayer.objects.all().delete()
        # Then delete all lobbies
        Lobby.objects.all().delete()
        print("\nCleaned up all lobbies and players.")
    except Exception as e:
        print(f"\nError during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle termination signals"""
    print("\nReceived shutdown signal. Cleaning up...")
    cleanup_database()
    sys.exit(0)

# Register the cleanup function to run on normal interpreter shutdown
atexit.register(cleanup_database)

# Register signal handlers for various termination signals
signal.signal(signal.SIGINT, signal_handler)  # Handles Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handles termination request