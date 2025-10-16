from django.urls import path
from . import views

urlpatterns = [
    path('player/', views.player, name='player'),
    path('<int:player_id>/', views.get_player_by_id, name='get_player'),
    path('get_all_players/', views.get_all_players, name='get_all_players'),
]
