from django.urls import path
from . import views

urlpatterns = [
    # Game endpoints
    path('games/', views.GameListCreateView.as_view(), name='game-list'),
    path('games/<int:pk>/', views.GameRetrieveUpdateDeleteView.as_view(), name='game-detail'),
    path('games/reset/', views.GameResetView.as_view(), name='game-reset'),
    path('games/simulate/', views.GameSimulationView.as_view(), name='game-simulate'),
    path('games/state/', views.GameStateView.as_view(), name='game-state'),

    # Player endpoints
    path('players/', views.PlayerListCreateView.as_view(), name='player-list'),
    path('players/<int:pk>/', views.PlayerRetrieveUpdateDeleteView.as_view(), name='player-detail'),

    # Lobby endpoints
    path('lobbies/', views.list_lobbies, name='lobby-list'),
    path('lobbies/create/', views.create_new_lobby, name='lobby-create'),
    path('lobbies/<int:lobby_id>/', views.get_lobby, name='lobby-detail'),
    path('lobbies/<int:lobby_id>/join/', views.join_lobby, name='lobby-join'),
    path('lobbies/<int:lobby_id>/leave/', views.leave_lobby, name='lobby-leave'),
    path('lobbies/<int:lobby_id>/select-character/', views.select_character, name='lobby-select-character'),
    path('lobbies/<int:lobby_id>/start/', views.start_game, name='lobby-start-game'),
    
    # Player endpoints
    path('player/create/', views.create_player, name='player-create'),
]