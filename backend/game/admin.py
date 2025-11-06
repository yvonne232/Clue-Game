from django.contrib import admin
# Register your models here.
from .models import Card, Solution, Room, Hallway, Game, Player

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'card_type')
    list_filter = ('card_type',)
    search_fields = ('name',)

@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('character', 'weapon', 'room', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('character__name', 'weapon__name', 'room__name')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'has_secret_passage')
    search_fields = ('name',)
    filter_horizontal = ('connected_rooms',)


@admin.register(Hallway)
class HallwayAdmin(admin.ModelAdmin):
    list_display = ('name', 'room1', 'room2', 'is_occupied')
    list_filter = ('is_occupied',)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_completed', 'created_at')
    list_filter = ('is_active', 'is_completed')
    search_fields = ('name',)
    autocomplete_fields = ('solution', 'current_player', 'starting_room')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('character_card', 'game', 'current_room', 'is_active_turn', 'is_eliminated')
    list_filter = ('game', 'is_active_turn', 'is_eliminated')
    search_fields = ('character_card__name', 'game__name')
    autocomplete_fields = ('character_card', 'game', 'current_room')