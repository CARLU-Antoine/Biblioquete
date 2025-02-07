import re
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from .models import Book, Author, InvertedIndex
from .serializers import BookSerializer

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

            # Afficher les livres associés dans le log
            print(f"🔍 Index trouvé pour '{word}': {index_entry}")
            print(f"Livres associés pour '{word}': {index_entry.books.all()}")
            
            # Afficher les positions associées au mot
            print(f"Positions associées pour '{word}': {index_entry.positions}")

            # Filtrer les livres en fonction des positions (en extrayant l'ID du livre du JSON)
            books = []
            for position in index_entry.positions:
                book_id = position.get("book")  # Extrait l'ID du livre depuis la structure JSON
                occurrences = position.get("occurrences", 0)  # Nombre d'occurrences dans ce livre

                print(f'book_id: {book_id}, occurrences: {occurrences}')

                if book_id:
                    # Chercher le livre dans la table Book en utilisant l'ID
                    book = Book.objects.select_related('author').filter(id=book_id).first()

                    if book:
                        # Sérialiser les informations du livre et inclure l'occurrence du mot
                        book_data = BookSerializer(book).data
                        book_data['occurrences'] = occurrences  # Ajouter le nombre d'occurrences pour ce mot dans ce livre
                        books.append(book_data)

            # Limiter à 50 livres si nécessaire
            books = books[:50]

            print(f"Livres trouvés pour '{word}': {books}")

            return Response({'word': word, 'books': books}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ Erreur lors de la recherche pour '{word}': {str(e)}")
            return Response({'error': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ✅ Recherche classée par pertinence (nombre d'occurrences)
class RankedBookSearchView(APIView):
    def get(self, request):
        word = request.GET.get('word', '').lower()
        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            index_entry = InvertedIndex.objects.get(word=word)
            # Recherche optimisée par pertinence avec l'annotation de comptage d'occurrences dans les livres
            books = index_entry.books.annotate(
                occurrence_count=Count('text', filter=Q(text__icontains=word))
            ).order_by('-occurrence_count').values(
                'id', 'title', 'languages', 'summary', 'author__name', 'occurrence_count'
            )
        except InvertedIndex.DoesNotExist:
            return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'books': list(books)})


# ✅ Recherche classée par proximité (Closeness) avec les positions stockées
class InvertedIndexSearchView(APIView):
    def get(self, request, word):
        word = word.lower().strip()

        if not word:
            return Response({'error': 'Veuillez fournir un mot-clé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            index_entry = InvertedIndex.objects.filter(word__iexact=word).first()
            if not index_entry:
                return Response({'message': f'Aucun livre trouvé pour "{word}".'}, status=status.HTTP_404_NOT_FOUND)

            books = []
            for position_entry in index_entry.positions:
                book_id = position_entry.get("book")
                occurrences = position_entry.get("occurrences", 0)
                positions = position_entry.get("positions", [])
                
                if book_id and positions:
                    book = Book.objects.select_related('author').filter(id=book_id).first()
                    if book:
                        book_data = BookSerializer(book).data
                        book_data['occurrences'] = occurrences
                        book_data['positions'] = positions  # Inclure les positions exactes
                        books.append(book_data)

            books = sorted(books, key=lambda x: x['occurrences'], reverse=True)

            return Response({'word': word, 'books': books}, status=status.HTTP_200_OK)

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

            # Extraire les positions pour ce livre
            positions_data = next(
                (entry['positions'] for entry in index_entry.positions 
                 if entry['book'] == book.id), 
                []
            )
            
            if not positions_data:
                return Response({
                    'message': f'Aucune occurrence trouvée pour "{word}" dans ce livre.'
                }, status=status.HTTP_404_NOT_FOUND)

            # Calculer les vraies positions dans le texte original
            real_positions = self.calculate_real_positions(book.text, word)
            
            # Appliquer le surlignage
            highlighted_text = self.highlight_text_by_positions(
                book.text, 
                real_positions,
                len(word)
            )
            
            # Diviser en pages sans casser les mots surlignés
            pages = self.split_text_into_pages(highlighted_text, 1000)
            
            return Response({
                'book_id': book.id,
                'pages': pages,
                'total_occurrences': len(real_positions)
            })

        except Book.DoesNotExist:
            return Response({'error': 'Livre introuvable.'}, 
                          status=status.HTTP_404_NOT_FOUND)

    def calculate_real_positions(self, text, word):
        """
        Calcule les positions réelles du mot dans le texte en tenant compte
        de la casse et des caractères spéciaux.
        """
        word = word.lower()
        text_lower = text.lower()
        positions = []
        start = 0
        
        while True:
            pos = text_lower.find(word, start)
            if pos == -1:
                break
                
            # Vérifier que c'est bien un mot complet
            before = text_lower[pos-1] if pos > 0 else ' '
            after = text_lower[pos + len(word)] if pos + len(word) < len(text_lower) else ' '
            
            if not before.isalnum() and not after.isalnum():
                positions.append(pos)
            
            start = pos + 1
            
        return positions

    def highlight_text_by_positions(self, text, positions, word_length):
        """
        Surligne le texte aux positions spécifiées en tenant compte
        de la longueur du mot.
        """
        # Trier les positions en ordre décroissant pour éviter les décalages
        positions = sorted(positions, reverse=True)
        
        # Convertir en liste pour les modifications
        text_chars = list(text)
        
        for pos in positions:
            # Insérer les balises de fermeture puis d'ouverture
            text_chars.insert(pos + word_length, '</mark>')
            text_chars.insert(pos, '<mark>')
            
        return ''.join(text_chars)

    def split_text_into_pages(self, text, chars_per_page):
        """
        Découpe le texte en pages en préservant les mots et les balises HTML.
        """
        pages = []
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            # Calculer la fin provisoire de la page
            end_pos = min(current_pos + chars_per_page, text_length)
            
            # Si on n'est pas à la fin du texte, chercher la fin du dernier mot
            if end_pos < text_length:
                # Chercher le prochain espace après la position courante
                while end_pos < text_length and text[end_pos] != ' ':
                    end_pos += 1
                
                # Vérifier qu'on ne coupe pas une balise HTML
                tag_start = text.rfind('<mark>', current_pos, end_pos)
                tag_end = text.rfind('</mark>', current_pos, end_pos)
                
                if tag_start > tag_end:  # Si on a une balise ouverte non fermée
                    # Chercher la fermeture de la balise
                    next_tag_end = text.find('</mark>', end_pos)
                    if next_tag_end != -1:
                        end_pos = next_tag_end + 7  # Longueur de '</mark>'
            
            # Extraire la page
            page = text[current_pos:end_pos].strip()
            pages.append(page)
            current_pos = end_pos
        
        # Ajouter les numéros de page
        return [f'--- PAGE {i+1} ---\n{page}' 
                for i, page in enumerate(pages)]