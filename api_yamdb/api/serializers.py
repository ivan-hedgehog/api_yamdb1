import datetime as dt

from django.core.validators import MaxValueValidator, MinValueValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )

    def username_validator(self, username):
        if username == 'me':
            raise serializers.ValidationError(
                'Использовать имя me запрещено.'
            )
        return username

    def nonadmin_update(self, instance, validated_data):
        validated_data.pop('role', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SignUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'email', )

    def validate_exist(self, attrs):
        username = attrs.get('username')
        if_user = User.objects.filter(username=username)
        if if_user.exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует'
            )
        email = attrs.get('email')
        if_email = User.objects.filter(email=email)
        if if_email.exists():
            raise serializers.ValidationError('Почта уже использовалась')

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" не разрешено.'
            )
        return value


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True
    )
    confirmation_code = serializers.CharField(
        max_length=150,
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Category
        lookup_field = 'slug'


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleGetSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(
        many=True
    )
    category = CategorySerializer(
        many=False
    )
    rating = serializers.IntegerField(
        required=False
    )

    class Meta:
        model = Title
        fields = '__all__'


class TitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        slug_field='slug'
    )
    category = serializers.SlugRelatedField(
        many=False,
        queryset=Category.objects.all(),
        slug_field='slug'
    )

    def year_validator(self, value):
        year = dt.time.today().year
        if value > year:
            raise serializers.ValidationError(
                'Год произведения не может быть больше текущего.'
            )

    class Meta:
        model = Title
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    score = serializers.IntegerField(
        required=True,
        validators=[
            MaxValueValidator(10),
            MinValueValidator(1)

        ]
    )

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context['view'].kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if request.method == 'POST':
            if Review.objects.filter(title=title, author=author).exists():
                raise ValidationError('Вы не можете добавить более'
                                      'одного отзыва на произведение')
        return data

    class Meta:
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        model = Review


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
