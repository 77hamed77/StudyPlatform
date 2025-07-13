from django.urls import path
from .views import (
    AllBadgesListView,
    UserAchievementsView,
    LeaderboardView,
    StudyChallengeListView,
    StudyChallengeDetailView,
)

app_name = 'achievements' # Define app_name for namespacing URLs

urlpatterns = [
    # User Achievements and Badges
    path('my-achievements/', UserAchievementsView.as_view(), name='my_achievements'),
    path('all-badges/', AllBadgesListView.as_view(), name='all_badges'),
    
    # Leaderboard
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),

    # Study Challenges
    path('challenges/', StudyChallengeListView.as_view(), name='challenge_list'),
    path('challenges/<int:pk>/', StudyChallengeDetailView.as_view(), name='challenge_detail'),

    # You can add more paths here later for specific actions if needed
]
