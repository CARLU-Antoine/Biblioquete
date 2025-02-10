import re
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from .models import Book, Author, InvertedIndex
from .serializers import BookSerializer
from collections import defaultdict


# ✅ Liste des livres
class BookListView(generics.ListAPIView):
    queryset = Book.objects.select_related('author')
    serializer_class = BookSerializer

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
            
            pages_data = self.split_text_into_pages(highlighted_text, book.text, real_positions, 1000)
            
            # Préparer les statistiques uniquement pour les pages avec des résultats
            pages_stats = [
                {
                    'page_number': i + 1,
                    'occurrences': len(page['positions'])
                }
                for i, page in enumerate(pages_data)
                if page['positions']
            ]
            
            response_data = {
                'book_id': book.id,
                'pages': [page['text'] for page in pages_data],
                'matching_pages_stats': pages_stats,
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

    def split_text_into_pages(self, highlighted_text, original_text, original_positions, chars_per_page):
        """
        Découpe le texte en pages et calcule les positions relatives pour chaque page.
        
        Args:
            highlighted_text: Texte avec les balises de surlignage
            original_text: Texte original sans surlignage
            original_positions: Positions dans le texte original
            chars_per_page: Nombre de caractères par page
        """
        pages = []
        current_pos = 0
        text_length = len(original_text)
        page_start_pos = 0  # Position de début dans le texte original
        
        while current_pos < text_length:
            # Calculer la fin de la page dans le texte original
            end_pos = min(current_pos + chars_per_page, text_length)
            
            if end_pos < text_length:
                # Chercher la fin du mot
                while end_pos < text_length and original_text[end_pos] != ' ':
                    end_pos += 1
            
            # Extraire le texte surligné correspondant
            highlighted_chunk = self.get_highlighted_chunk(
                highlighted_text, 
                current_pos, 
                end_pos
            )
            
            # Calculer les positions relatives pour cette page
            page_positions = [
                pos - page_start_pos 
                for pos in original_positions 
                if page_start_pos <= pos < end_pos
            ]
            
            pages.append({
                'text': f'--- PAGE {len(pages) + 1} ---\n{highlighted_chunk.strip()}',
                'positions': page_positions
            })
            
            # Mettre à jour les positions pour la prochaine page
            page_start_pos = end_pos
            current_pos = end_pos
        
        return pages

    def get_highlighted_chunk(self, highlighted_text, start_pos, end_pos):
        """
        Extrait une portion du texte surligné en s'assurant de ne pas couper les balises.
        """
        # Chercher le début du chunk
        chunk_start = start_pos
        while chunk_start > 0:
            if highlighted_text[chunk_start-1:chunk_start+5] == '<mark>':
                chunk_start -= 6
            else:
                break
        
        # Chercher la fin du chunk
        chunk_end = end_pos
        while chunk_end < len(highlighted_text):
            if highlighted_text[chunk_end:chunk_end+7] == '</mark>':
                chunk_end += 7
            else:
                break
        
        return highlighted_text[chunk_start:chunk_end]