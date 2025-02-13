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
from django.core.cache import cache

# ✅ Liste des livres
class BookPagination(PageNumberPagination):
    page_size = 5  # Nombre de livres par page par défaut
    page_size_query_param = 'page_size'  # Paramètre pour modifier la taille de la page
    max_page_size = 100  # Taille maximale de la page

    # Personnalisation de la réponse de pagination
    def get_paginated_response(self, data):
        return Response({
            'total_books': self.page.paginator.count,  # Nombre total de livres
            'books': data  # Données des livres
        })

class BookListView(generics.ListAPIView):
    queryset = Book.objects.select_related('author').order_by('id')
    serializer_class = BookSerializer
    pagination_class = BookPagination  # Utiliser la classe de pagination personnalisée


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
            # Vérifier si le texte du livre est en cache
            cache_key = f'book_text_{book_id}'
            cached_text = cache.get(cache_key)
            
            if cached_text is None:
                book = Book.objects.get(id=book_id)
                if not book.text:
                    return Response({'error': 'Texte non disponible.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Stocker en cache pour les futures requêtes
                cached_text = book.text.replace('\n', '<br/>').strip()
                cache.set(cache_key, cached_text, timeout=3600)  # Cache pour 1 heure
            
            # Récupération des paramètres de pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 500))  # Nombre de mots par page
            words = cached_text.split()
            
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_text = ' '.join(words[start_index:end_index])
            total_pages = (len(words) // page_size) + (1 if len(words) % page_size > 0 else 0)
            
            return Response({
                'text': paginated_text,
                'total_books': total_pages
            })
        except Book.DoesNotExist:
            return Response({'error': 'Livre introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Paramètres invalides.'}, status=status.HTTP_400_BAD_REQUEST)

class BookTextHighlightView(APIView):
    def get(self, request, book_id):
        word = request.GET.get('word', '').lower()
        requested_page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 300))

        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            book = Book.objects.get(id=book_id)
            if not book.text:
                return Response({'error': 'Texte non disponible.'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Découper le texte en mots une seule fois
            words = book.text.split()
            total_words = len(words)
            total_pages = (total_words + page_size - 1) // page_size

            # Vérifier si la page demandée existe
            if requested_page < 1 or requested_page > total_pages:
                return Response(
                    {'error': f'La page demandée n\'existe pas. Le livre contient {total_pages} pages.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Trouver les positions des mots en termes d'index de mots
            word_positions = self.find_word_positions(words, word)

            # Calculer les pages contenant le mot
            pages_with_word = []
            if word_positions:
                pages_with_word = sorted(set(pos // page_size + 1 for pos in word_positions))

            # Extraire le texte de la page demandée
            start_word_index = (requested_page - 1) * page_size
            end_word_index = min(start_word_index + page_size, total_words)
            page_words = words[start_word_index:end_word_index]
            
            # Construire le texte avec les balises de surbrillance si nécessaire
            page_text = self.highlight_words(page_words, word_positions, start_word_index)

            response_data = {
                'book_id': book.id,
                'page': requested_page,
                'total_books': total_pages,
                'text': page_text,
                'total_occurrences': len(word_positions),
                'pages_with_word': pages_with_word,
                'word': word
            }
            
            return Response(response_data)

        except Book.DoesNotExist:
            return Response({'error': 'Livre introuvable.'}, 
                          status=status.HTTP_404_NOT_FOUND)

    def find_word_positions(self, words, search_word):
        """Trouve les positions (index) du mot recherché dans la liste des mots."""
        positions = []
        for i, word in enumerate(words):
            # Nettoyer le mot de la ponctuation pour la comparaison
            cleaned_word = ''.join(c for c in word.lower() if c.isalnum())
            if cleaned_word == search_word:
                positions.append(i)
        return positions

    def highlight_words(self, page_words, word_positions, start_word_index):
        """Construit le texte de la page avec les mots en surbrillance."""
        result = []
        for i, word in enumerate(page_words):
            absolute_pos = i + start_word_index
            if absolute_pos in word_positions:
                result.append(f"<mark>{word}</mark>")
            else:
                result.append(word)
        return ' '.join(result)