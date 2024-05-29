from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from .models import *
from .serializers import *
from rest_framework.throttling import UserRateThrottle

class SignupView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email', '').lower()
        password = data.get('password', '')
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email is already in use'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=email[:email.index("@")], email=email, password=password)
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if User.objects.filter(email=request.data.get('email').lower()).exists():
            user = User.objects.get(email=request.data.get('email').lower())
            if user.check_password(request.data.get('password')):
                token, _ = Token.objects.get_or_create(user=user)
                data = {'token': token.key}
                return Response({'message': 'Logged-In successfully', 'data': data}, 
                                        status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid authentication credentials'}, 
                        status=status.HTTP_400_BAD_REQUEST)

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        query = request.query_params.get('query', '')
        queryset = User.objects.filter(Q(email__iexact=query) | Q(username__icontains=query)).distinct()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return Response({'message': 'User List fetched successfully', 'data': response.data}, 
                        status=status.HTTP_200_OK)


class FriendRequestThrottle(UserRateThrottle):
    rate = '3/min'

class SendFriendRequestView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [FriendRequestThrottle]

    def post(self, request):
        to_user_id = request.data.get('to_user_id')
        to_user = User.objects.get(id=to_user_id)
        if to_user == request.user:
            return Response({'error': 'Cannot send friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)
        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
            return Response({'error': 'Friend request already exist'}, status=status.HTTP_400_BAD_REQUEST)
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        return Response({'message': 'Friend request sent'}, status=status.HTTP_201_CREATED)

class RespondFriendRequestView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        action = request.data.get('action')
        friend_request = FriendRequest.objects.get(id=request_id)
        if action == 'accept':
            friend_request.accepted = True
            friend_request.save()
            return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)
        elif action == 'reject':
            friend_request.delete()
            return Response({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

class ListFriendsView(generics.ListAPIView):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = User.objects.filter(sent_requests__to_user=request.user, sent_requests__accepted=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'message': 'User List fetched successfully', 'data': serializer.data}, 
                        status=status.HTTP_200_OK)

class ListPendingRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = FriendRequest.objects.filter(to_user=request.user, accepted=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'message': 'Request fetched successfully', 'data': serializer.data}, 
                        status=status.HTTP_200_OK)
