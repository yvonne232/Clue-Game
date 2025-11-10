from rest_framework import serializers
from .models.game import Game
from .models.lobby import Lobby
from .models.lobby_player import LobbyPlayer
from .models.card import Card
from .models.player import Player

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = '__all__'

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'name', 'card_type']

class PlayerSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 
            'game', 
            'character_name',
            'current_room',
            'current_hallway',
            'is_active_turn',
            'is_eliminated',
            'joined_at',
            'location'
        ]

    def get_location(self, obj):
        if obj.current_room:
            return {'type': 'room', 'name': obj.current_room.name}
        elif obj.current_hallway:
            return {'type': 'hallway', 'name': obj.current_hallway.name}
        return None

class LobbyPlayerSerializer(serializers.ModelSerializer):
    character_card = CardSerializer(read_only=True)
    character_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LobbyPlayer
        fields = ['id', 'created_at', 'character_card', 'character_name']
    
    def get_character_name(self, obj):
        if obj.character_card:
            return obj.character_card.name
        return None

class LobbySerializer(serializers.ModelSerializer):
    players = LobbyPlayerSerializer(source='lobby_players', many=True, read_only=True)
    player_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lobby
        fields = ['id', 'name', 'created_at', 'is_active', 'players', 'player_count']
    
    def get_player_count(self, obj):
        count = obj.lobby_players.count()
        # Debug print
        print(f"Lobby {obj.id} player count: {count}")
        print(f"Raw players query: {list(obj.lobby_players.all().values())}")
        return count