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

        # Extraire les mots de l'expression régulière
        words = re.findall(r'\w+', regex_pattern)

        # Si un seul mot est recherché, utiliser l'index inversé
        if len(words) == 1:
            word = words[0].lower()
            # Recherche directe dans la colonne 'word' de l'index inversé
            index_entry = InvertedIndex.objects.filter(word__iexact=word).first()

            if index_entry:
                books = []
                # Ajouter les livres associés à ce mot
                for position in index_entry.positions:
                    book_id = position.get("book")
                    if book_id:
                        book = Book.objects.select_related('author').filter(id=book_id).first()
                        if book:
                            # Récupérer les données du livre
                            book_data = BookSerializer(book).data
                            # Ajouter le livre à la liste
                            books.append(book_data)

                if not books:
                    return Response({'message': f'Aucun livre trouvé pour "{regex_pattern}".'}, status=status.HTTP_404_NOT_FOUND)

                return Response({'books': books}, status=status.HTTP_200_OK)

            else:
                return Response({'message': f'Aucun livre trouvé pour "{regex_pattern}".'}, status=status.HTTP_404_NOT_FOUND)

        # Si plusieurs mots sont recherchés, utiliser l'index inversé pour pré-filtrer
        matching_books = set()
        for word in words:
            index_entry = InvertedIndex.objects.filter(word__iexact=word).first()
            if index_entry:
                for position in index_entry.positions:
                    book_id = position.get("book")
                    if book_id:
                        matching_books.add(book_id)

        if not matching_books:
            return Response({'message': f'Aucun livre trouvé pour "{regex_pattern}".'}, status=status.HTTP_404_NOT_FOUND)

        insensitive_regex = f"(?i){regex_pattern}"
        books = Book.objects.filter(
            id__in=matching_books
        ).filter(
            Q(text__regex=insensitive_regex) | Q(summary__regex=insensitive_regex)
        ).values('id', 'title', 'languages', 'summary', 'author__name')

        if not books:
            return Response({'message': f'Aucun livre trouvé pour "{regex_pattern}".'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'books': list(books)}, status=status.HTTP_200_OK)


class InvertedIndexSearchView(APIView):
    def get(self, request, word, search_method):
        word = word.lower().strip()

        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Recherche de l'index pour le mot exact (ignorant la casse)
            index_entry = InvertedIndex.objects.filter(word__iexact=word).first()

            if not index_entry:
                return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

            books = []

            # Fonction pour surligner les mots dans le texte
            def highlight_text(text, word):
                if isinstance(text, str):  # Vérifier si le texte est bien une chaîne
                    # Utilisation de regex pour rechercher le mot entier et non une sous-chaîne partielle
                    highlighted_text = re.sub(rf'\b({re.escape(word)})\b', r'<mark>\1</mark>', text, flags=re.IGNORECASE)
                    return highlighted_text
                return text  # Retourner le texte tel quel si ce n'est pas une chaîne

            # Définir les champs à rechercher en fonction de la méthode de recherche
            search_fields = {
                'title': ['title'],
                'author': ['author'],
                'summary': ['summary'],
                'text': ['text'],
                'all': ['title', 'author', 'summary', 'text']
            }

            # Séparer les méthodes de recherche si elles sont combinées avec +
            search_methods = search_method.split('+')
            
            # Vérifier si toutes les méthodes sont valides
            for method in search_methods:
                if method not in search_fields:
                    return Response(
                        {'error': f'Méthode de recherche invalide: {method}. Utilisez "title", "author", "summary", "text" ou leurs combinaisons avec "+".'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Combiner tous les champs à rechercher
            fields_to_search = []
            for method in search_methods:
                fields_to_search.extend(search_fields[method])
            fields_to_search = list(set(fields_to_search))  # Supprimer les doublons

            for position in index_entry.positions:
                book_id = position.get("book")  # Extrait l'ID du livre depuis la structure JSON
                occurrences = position.get("occurrences", 0)  # Nombre d'occurrences dans ce livre

                if book_id:
                    # Chercher le livre dans la table Book en utilisant l'ID
                    book = Book.objects.select_related('author').filter(id=book_id).first()

                    if book:
                        # Vérifier si le mot est trouvé dans au moins un des champs recherchés
                        found_in_requested_fields = False
                        book_data = BookSerializer(book).data
                        book_data['occurrences'] = occurrences

                        # Vérifier et surligner pour chaque champ demandé
                        for field in fields_to_search:
                            if field in position["positions"]:
                                if field == 'author':
                                    # Traitement spécial pour le champ auteur
                                    author_name = book_data.get('author', {}).get('name', '')
                                    if author_name:
                                        book_data['author']['name'] = highlight_text(author_name, word)
                                        found_in_requested_fields = True
                                elif field in book_data:
                                    book_data[field] = highlight_text(book_data[field], word)
                                    found_in_requested_fields = True

                        # Vérifier si le mot est trouvé dans le texte uniquement si la recherche inclut le texte
                        text_exists = False
                        if 'text' in fields_to_search and hasattr(book, 'text') and isinstance(book.text, str):
                            if word in book.text.lower():
                                text_exists = True
                                found_in_requested_fields = True

                        book_data['word_found_in_text'] = text_exists

                        # Ajouter le livre uniquement si le mot a été trouvé dans au moins un des champs recherchés
                        if found_in_requested_fields:
                            books.append(book_data)

            if not books:
                return Response(
                    {'message': f'Aucun livre trouvé dans les champs "{", ".join(search_methods)}" pour "{word}".'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                'word': word,
                'search_methods': search_methods,
                'books': books
            }, status=status.HTTP_200_OK)

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
            book_ids = [position_entry.get("book") for position_entry in index_entry.positions if position_entry.get("book")]
            
            if not book_ids:
                return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)
            
            # Récupération des livres en une seule requête
            books = Book.objects.select_related('author').filter(id__in=book_ids)
            
            # Création de la liste des livres avec occurrences
            books_data = []
            for book in books:
                occurrences = next((entry.get("occurrences", 0) for entry in index_entry.positions if entry.get("book") == book.id), 0)
                book_data = BookSerializer(book).data
                book_data['occurrences'] = occurrences
                books_data.append(book_data)

            # Tri des livres par nombre d'occurrences
            books_data = sorted(books_data, key=lambda x: x['occurrences'], reverse=True)
            
            return Response({'books': books_data})

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
                positions = position_entry.get("positions", {}).get("text", [])  # S'assurer que les positions existent dans le bon format

                if book_id and len(positions) > 1:  # Vérifier qu'il y a plus d'une position
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
