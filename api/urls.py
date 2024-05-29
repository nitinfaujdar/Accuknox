from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='search'),
    path('friend_request/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friend_request/<int:request_id>/', RespondFriendRequestView.as_view(), name='respond_friend_request'),
    path('friends/', ListFriendsView.as_view(), name='list_friends'),
    path('pending_requests/', ListPendingRequestsView.as_view(), name='list_pending_requests'),
]
