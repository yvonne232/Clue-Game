from django.urls import path
from . import views

urlpatterns = [
    # Game endpoints
    path('games/', views.GameListCreateView.as_view(), name='game-list'),
    path('games/<int:pk>/', views.GameRetrieveUpdateDeleteView.as_view(), name='game-detail'),

    # Player endpoints
    path('players/', views.PlayerListCreateView.as_view(), name='player-list'),
    path('players/<int:pk>/', views.PlayerRetrieveUpdateDeleteView.as_view(), name='player-detail'),
]