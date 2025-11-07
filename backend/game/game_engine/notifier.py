class Notifier:
    """
    Broadcast messages (mocked for testing).
    """

    @staticmethod
    def broadcast(message):
        print(f"[Broadcast] {message}")
        return message
