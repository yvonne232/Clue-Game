from django.contrib import admin
# Register your models here.
from .models import Card, Solution, Room, Hallway, Game, Player, StartingPosition 

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
    list_display = ("name", "has_secret_passage", "connected_rooms_list")
    search_fields = ("name",)
    filter_horizontal = ("connected_rooms",)

    @admin.display(description="Connected Rooms")
    def connected_rooms_list(self, obj):
        return ", ".join(room.name for room in obj.connected_rooms.all())


@admin.register(Hallway)
class HallwayAdmin(admin.ModelAdmin):
    list_display = ("name", "room1", "room2", "is_occupied")
    list_filter = ("is_occupied",)
    search_fields = ("name", "room1__name", "room2__name")

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "is_completed",
        "created_at",
        "solution",
        "current_player",
    )
    list_filter = ("is_active", "is_completed")
    search_fields = ("name",)
    autocomplete_fields = ("solution", "current_player")

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "character_name",
        "game",
        "starting_position",
        "current_room",
        "current_hallway",
        "is_active_turn",
        "is_eliminated",
    )
    list_filter = ("game", "is_active_turn", "is_eliminated")
    search_fields = ("character_name", "game__name")
    autocomplete_fields = (
        "game",
        "starting_position",
        "current_room",
        "current_hallway",
    )
@admin.register(StartingPosition)
class StartingPositionAdmin(admin.ModelAdmin):
    list_display = ("character", "hallway")
    search_fields = ("character__name", "hallway__name")