import re
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from .models import Book, InvertedIndex
from .serializers import BookSerializer
from Levenshtein import distance as levenshtein_distance
from collections import defaultdict


# ✅ Recherche basique d'un mot dans les livres
class BookSearchView(APIView):
    def get(self, request):
        word = request.GET.get('word')
        if not word:
            return Response({'error': 'Veuillez fournir un mot clé.'}, status=status.HTTP_400_BAD_REQUEST)

        books_found = Book.objects.filter(
            Q(text__icontains=word) | Q(summary__icontains=word)
        ).values('id', 'title', 'languages', 'summary', 'author__name')

        if not books_found:
            return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'books': list(books_found)})

# ✅ Recherche avancée avec RegEx (optimisée avec indexation inversée)
class AdvancedBookSearchView(APIView):
    def get(self, request):
        regex_pattern = request.GET.get('pattern')
        if not regex_pattern:
            return Response({'error': 'Veuillez fournir une expression régulière.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            re.compile(regex_pattern)  # Vérifier si la regex est valide
        except re.error:
            return Response({'error': 'Expression régulière invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        words = re.findall(r'\w+', regex_pattern)

        if len(words) == 1:
            try:
                index_entry = InvertedIndex.objects.get(word=words[0].lower())
                books = index_entry.books.values('id', 'title', 'languages', 'summary', 'author__name')
            except InvertedIndex.DoesNotExist:
                return Response({'message': f'Aucun livre trouvé pour "{regex_pattern}".'}, status=status.HTTP_404_NOT_FOUND)
        else:
            books = Book.objects.filter(
                Q(text__regex=regex_pattern) | Q(summary__regex=regex_pattern)
            ).values('id', 'title', 'languages', 'summary', 'author__name')

        return Response({'books': list(books)})



# ✅ Recherche optimisée avec l'index inversé
class InvertedIndexSearchView(APIView):
    def get(self, request, word):
        word = word.lower().strip()

        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Recherche de l'index pour le mot exact (ignorant la casse)
            index_entry = InvertedIndex.objects.filter(word__iexact=word).first()

            if not index_entry:
                return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

            # Filtrer les livres en fonction des positions (en extrayant l'ID du livre du JSON)
            books = []
            for position in index_entry.positions:
                book_id = position.get("book")  # Extrait l'ID du livre depuis la structure JSON
                occurrences = position.get("occurrences", 0)  # Nombre d'occurrences dans ce livre



                if book_id:
                    # Chercher le livre dans la table Book en utilisant l'ID
                    book = Book.objects.select_related('author').filter(id=book_id).first()

                    if book:
                        # Sérialiser les informations du livre et inclure l'occurrence du mot
                        book_data = BookSerializer(book).data
                        book_data['occurrences'] = occurrences  # Ajouter le nombre d'occurrences pour ce mot dans ce livre
                        books.append(book_data)


            return Response({'word': word, 'books': books}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ Erreur lors de la recherche pour '{word}': {str(e)}")
            return Response({'error': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# ✅ Recherche optimisée avec l'index inversé avec l'algo Levenshtein et l'arbre jaccard pour afficher des suggestions
def jaccard_similarity(set1, set2):
    """ Calcule la similarité de Jaccard entre deux ensembles de mots. """
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union != 0 else 0

class InvertedIndexSuggectionsView(APIView):
    def get(self, request, word):
        word = word.lower().strip()

        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        # Définir un seuil de similarité ajustable pour éviter les mots trop éloignés
        similarity_threshold = 0.87  # Modifier cette valeur pour ajuster la similarité acceptée

        try:
            # Étape 1 : Récupérer tous les mots de l'index inversé
            all_index_words = InvertedIndex.objects.values_list('word', flat=True)

            # Étape 2 : Trouver les mots similaires avec Levenshtein
            similar_words = []
            for index_word in all_index_words:
                lev_sim = 1 - (levenshtein_distance(word, index_word) / max(len(word), len(index_word)))
                if lev_sim >= similarity_threshold:  # Seulement les mots ayant une bonne similarité
                    similar_words.append((index_word, lev_sim))

            # Trier les suggestions par similarité décroissante
            similar_words = sorted(similar_words, key=lambda x: x[1], reverse=True)

            # Limiter le nombre de suggestions à 3
            similar_words = similar_words[:4]

            suggestions = [word for word, _ in similar_words]

            # Filtrer le mot exact pour éviter de l'afficher dans les suggestions
            suggestions = [sug for sug in suggestions if sug != word]

            # Étape 3 : Filtrer les entrées qui correspondent aux mots similaires
            index_entries = InvertedIndex.objects.filter(word__in=suggestions)

            if not index_entries.exists():
                return Response({
                    'message': f'Aucun mot trouvé pour "{word}".',
                    'suggestions': [{'word': suggestion, 'occurrences': 0} for suggestion in suggestions]  # ✅ Format JSON sans livres
                }, status=status.HTTP_404_NOT_FOUND)

            words_occurrences = defaultdict(int)

            for entry in index_entries:
                for position_entry in entry.positions:
                    occurrences = position_entry.get("occurrences", 0)
                    words_occurrences[entry.word] += occurrences

            # Créer la réponse avec les mots et le nombre total d'occurrences
            suggestions_with_occurrences = [{
                'word': suggestion,
                'occurrences': words_occurrences.get(suggestion, 0)
            } for suggestion in suggestions]

            return Response({
                'word': word,
                'suggestions': suggestions_with_occurrences
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ Erreur lors de la recherche pour '{word}': {str(e)}")
            return Response({'error': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RankedBookSearchView(APIView):
    def get(self, request):
        word = request.GET.get('word', '').lower()
        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            index_entry = InvertedIndex.objects.get(word=word)
            books = []
            for position_entry in index_entry.positions:
                book_id = position_entry.get("book")
                occurrences = position_entry.get("occurrences", 0)
                
                if book_id:
                    book = Book.objects.select_related('author').filter(id=book_id).first()
                    if book:
                        book_data = BookSerializer(book).data
                        book_data['occurrences'] = occurrences
                        books.append(book_data)
            
            books = sorted(books, key=lambda x: x['occurrences'], reverse=True)
            return Response({'books': books})
        except InvertedIndex.DoesNotExist:
            return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)


class ClosenessBookSearchView(APIView):
    def get(self, request):
        word = request.GET.get('word', '').lower()

        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            index_entry = InvertedIndex.objects.get(word=word)
            books_with_distances = []

            for position_entry in index_entry.positions:
                book_id = position_entry.get("book")
                positions = position_entry.get("positions", [])
                
                if book_id and len(positions) > 1:
                    book = Book.objects.select_related('author').filter(id=book_id).first()
                    if book:
                        avg_distance = self.calculate_avg_distance(positions)
                        closeness_score = 1 / avg_distance if avg_distance > 0 else 0
                        books_with_distances.append({
                            'id': book.id,
                            'title': book.title,
                            'languages': book.languages,
                            'summary': book.summary,
                            'author': book.author.name,
                            'closeness_score': closeness_score
                        })

            books_with_distances.sort(key=lambda x: x['closeness_score'], reverse=True)

            if not books_with_distances:
                return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

            return Response({'books': books_with_distances, 'total_books': len(books_with_distances)})

        except InvertedIndex.DoesNotExist:
            return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

    def calculate_avg_distance(self, positions):
        if len(positions) == 1:
            return 1
        distances = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
        return sum(distances) / len(distances)