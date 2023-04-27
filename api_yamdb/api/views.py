from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, mixins, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .email import send_confirmation_code
from .filters import TitleFilter
from .mixins import CreateListDestroyViewSet
from .permissions import (IsSuperuserAdminModeratorAuthorPermission,
                          IsSuperuserOrAdminPermission, ReadOnlyPermission)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer, SignUpSerializer,
                          TitleGetSerializer, TitleSerializer, TokenSerializer,
                          UserSerializer)
from reviews.models import Category, Genre, Review, Title
from users.models import User


class UserCreateViewSet(mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    """Вьюсет для создания обьектов класса User."""

    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)

    def create(self, request):
        """Создает объект класса User и
        отправляет на почту пользователя код подтверждения."""
        if User.objects.filter(
                username=request.data.get('username'),
                email=request.data.get('email')
        ).exists():
            return Response(request.data, status=status.HTTP_200_OK)
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = User.objects.get_or_create(**serializer.validated_data)
        confirmation_code = default_token_generator.make_token(user)
        send_confirmation_code(
            email=user.email,
            confirmation_code=confirmation_code
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserReceiveTokenViewSet(mixins.CreateModelMixin,
                              viewsets.GenericViewSet):
    """Вьюсет для получения пользователем JWT токена."""

    queryset = User.objects.all()
    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        """Предоставляет пользователю JWT токен по коду подтверждения."""
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        confirmation_code = serializer.validated_data.get('confirmation_code')
        user = get_object_or_404(User, username=username)

        if not default_token_generator.check_token(user, confirmation_code):
            message = {'confirmation_code': 'Код подтверждения невалиден'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        message = {'token': str(AccessToken.for_user(user))}
        return Response(message, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (
        IsSuperuserOrAdminPermission,
        IsAuthenticated,
        IsSuperuserAdminModeratorAuthorPermission
    )
    lookup_field = 'username'
    search_fields = ('username',)
    filter_backends = (filters.SearchFilter,)
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']

    @action(
        detail=False,
        methods=['GET', 'PATCH'],
        permission_classes=(IsAuthenticated,),
        url_path='me',
        url_name='me'
    )
    def get_user_info(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(self.request.user)
        else:
            user = self.request.user
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            if serializer.validated_data.get('role'):
                serializer.validated_data.pop('role')
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).order_by('name')
    serializer_class = TitleSerializer
    permission_classes = (ReadOnlyPermission | IsSuperuserOrAdminPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TitleGetSerializer
        else:
            return TitleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response((serializer.data), status=status.HTTP_201_CREATED)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsSuperuserAdminModeratorAuthorPermission
    )

    def get_title(self):
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Title, pk=title_id)

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user, title=self.get_title()
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsSuperuserAdminModeratorAuthorPermission,
    )

    def get_review(self):
        review_id = self.kwargs.get('review_id')
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Review,
                                 pk=review_id,
                                 title_id=title_id)

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=self.get_review()
        )
