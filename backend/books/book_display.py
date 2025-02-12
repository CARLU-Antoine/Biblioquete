import re
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from .models import Book, Author, InvertedIndex
from .serializers import BookSerializer
from collections import defaultdict


# ✅ Liste des livres
class BookPagination(PageNumberPagination):
    page_size = 5  # Nombre de livres par page
    page_size_query_param = 'page_size'  # Option pour permettre de modifier la taille de la page
    max_page_size = 100  # Taille maximale de la page

class BookListView(generics.ListAPIView):
    queryset = Book.objects.select_related('author').order_by('id')
    serializer_class = BookSerializer
    pagination_class = BookPagination  # Utiliser la classe de pagination définie

# ✅ Détail d'un livre
class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.select_related('author')
    serializer_class = BookSerializer
    lookup_field = 'id'

# ✅ Liste des livres en fonction des langues
class BooksByLanguageView(APIView):
    def get(self, request, language):
        books = Book.objects.filter(languages__icontains=language)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

# ✅ Liste des langues disponibles
class AvailableLanguagesView(APIView):
    def get(self, request):
        # Récupérer les langues de tous les livres
        languages = Book.objects.values_list('languages', flat=True)

        # Créer un set pour stocker les langues uniques
        unique_languages = set()

        # Parcourir chaque langue et les diviser par des virgules
        for lang_list in languages:
            for lang in lang_list.split(','):
                unique_languages.add(lang.strip().lower())  # Enlever les espaces et convertir en minuscules

        return Response({"languages": list(unique_languages)})


# ✅ Récupérer le texte d'un livre
class BookTextView(APIView):
    def get(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
            if book.text:
                return Response({'text': book.text.strip()})
            return Response({'error': 'Texte non disponible.'}, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            return Response({'error': 'Livre introuvable.'}, status=status.HTTP_404_NOT_FOUND)

# ✅ Recherche de livres
class BookTextHighlightView(APIView):
    def get(self, request, book_id):
        word = request.GET.get('word', '').lower()
        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            book = Book.objects.get(id=book_id)
            if not book.text:
                return Response({'error': 'Texte non disponible.'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            index_entry = InvertedIndex.objects.filter(word=word).first()
            if not index_entry:
                return Response({
                    'message': f'Aucune occurrence trouvée pour "{word}" dans ce livre.'
                }, status=status.HTTP_404_NOT_FOUND)

            positions_data = next(
                (entry['positions'] for entry in index_entry.positions 
                 if entry['book'] == book.id), 
                []
            )
            
            if not positions_data:
                return Response({
                    'message': f'Aucune occurrence trouvée pour "{word}" dans ce livre.'
                }, status=status.HTTP_404_NOT_FOUND)

            real_positions = self.calculate_real_positions(book.text, word)
            highlighted_text = self.highlight_text_by_positions(
                book.text, 
                real_positions,
                len(word)
            )
            
            response_data = {
                'book_id': book.id,
                'highlighted_text': highlighted_text,
                'total_occurrences': len(real_positions)
            }
            
            return Response(response_data)

        except Book.DoesNotExist:
            return Response({'error': 'Livre introuvable.'}, 
                          status=status.HTTP_404_NOT_FOUND)

    def calculate_real_positions(self, text, word):
        word = word.lower()
        text_lower = text.lower()
        positions = []
        start = 0
        
        while True:
            pos = text_lower.find(word, start)
            if pos == -1:
                break
                
            before = text_lower[pos-1] if pos > 0 else ' '
            after = text_lower[pos + len(word)] if pos + len(word) < len(text_lower) else ' '
            
            if not before.isalnum() and not after.isalnum():
                positions.append(pos)
            
            start = pos + 1
            
        return positions

    def highlight_text_by_positions(self, text, positions, word_length):
        positions = sorted(positions, reverse=True)
        text_chars = list(text)
        
        for pos in positions:
            text_chars.insert(pos + word_length, '</mark>')
            text_chars.insert(pos, '<mark>')
            
        return ''.join(text_chars)
