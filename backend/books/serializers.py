from rest_framework import serializers
from .models import Author, Book, InvertedIndex

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'birth_year', 'death_year']

class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'languages', 'summary', 'formats'
        ]
