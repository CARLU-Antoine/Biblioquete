from django.core.management.base import BaseCommand
from books.models import Book, InvertedIndex
import re
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
from django.db import transaction, connection
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from psycopg2.extras import execute_values


class Command(BaseCommand):
    help = "Index existing books in the database."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stopwords_cache = {}
        try:
            nltk.download('stopwords', quiet=True)
            self.initialize_stopwords()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Attention: Impossible de charger les stopwords NLTK: {str(e)}"))
            self.stopwords_cache = defaultdict(set)

    def initialize_stopwords(self):
        lang_map = {
            'en': 'english', 'fr': 'french', 'es': 'spanish', 'de': 'german',
            'it': 'italian', 'pt': 'portuguese', 'nl': 'dutch'
        }
        for lang_code, nltk_name in lang_map.items():
            try:
                self.stopwords_cache[lang_code] = set(stopwords.words(nltk_name))
            except Exception:
                self.stopwords_cache[lang_code] = set()

    def handle(self, *args, **kwargs):
        # Réinitialisation complète des tables
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE books_invertedindex_books, books_invertedindex RESTART IDENTITY CASCADE")

        books = Book.objects.all()
        num_workers = 100  # Ajuster selon la config PostgreSQL
        global_word_index = defaultdict(lambda: defaultdict(list))

        # Étape 1 : Analyser les livres et construire l'index global
        with tqdm(total=books.count(), desc="Analyzing books", ncols=100) as pbar:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {executor.submit(self.analyze_book, book): book for book in books if book.text and book.languages}
                for future in as_completed(futures):
                    book = futures[future]
                    try:
                        word_positions, new_positions = future.result()
                        for word, positions in word_positions.items():
                            global_word_index[word][book.id] = positions
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Erreur livre {book.id}: {str(e)}"))
                    pbar.update(1)

        total_words = len(global_word_index)
        if total_words == 0:
            self.stdout.write(self.style.WARNING("Aucun mot à indexer."))
            return

        # Étape 2 : Insérer les mots dans la table books_invertedindex
        word_to_id = {}
        with tqdm(total=total_words, desc="Updating database", ncols=100) as pbar:
            batch_size = 10000
            current_batch = []

            for word, book_positions in global_word_index.items():
                positions_list = [
                    {'book': book_id, 'positions': positions, 'occurrences': len(positions)}
                    for book_id, positions in book_positions.items()
                ]
                total_occurrences = sum(len(positions) for positions in book_positions.values())
                current_batch.append((word, json.dumps(positions_list), total_occurrences))

                if len(current_batch) >= batch_size:
                    self.insert_batch(current_batch, word_to_id)
                    pbar.update(len(current_batch))
                    current_batch = []

            # Insérer le dernier batch s'il reste des éléments
            if current_batch:
                self.insert_batch(current_batch, word_to_id)
                pbar.update(len(current_batch))

        # Étape 3 : Insérer les relations dans books_invertedindex_books
        book_relations = []
        for word, book_positions in global_word_index.items():
            if word in word_to_id:
                index_id = word_to_id[word]
                book_ids = list(book_positions.keys())
                book_relations.extend((index_id, book_id) for book_id in book_ids)

        if not book_relations:
            self.stdout.write(self.style.WARNING("Aucune relation à insérer dans books_invertedindex_books."))
        else:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    execute_values(
                        cursor,
                        "INSERT INTO books_invertedindex_books (invertedindex_id, book_id) VALUES %s",
                        book_relations,
                        template="(%s, %s)",
                        page_size=1000
                    )
            self.stdout.write(self.style.SUCCESS(f"{len(book_relations)} relations insérées dans books_invertedindex_books."))

        # Étape 4 : Nettoyer et optimiser la base de données
        with connection.cursor() as cursor:
            cursor.execute("VACUUM ANALYZE books_invertedindex")
            cursor.execute("VACUUM ANALYZE books_invertedindex_books")

        self.stdout.write(self.style.SUCCESS(f"Indexation terminée : {total_words} mots indexés."))

    def insert_batch(self, batch, word_to_id):
        """Insère un batch de mots dans la table books_invertedindex."""
        with transaction.atomic():
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO books_invertedindex (word, positions, occurrences)
                    VALUES %s RETURNING id, word
                """
                execute_values(cursor, sql, batch, template="(%s, %s, %s)", page_size=1000)
                results = cursor.fetchall()
                word_to_id.update({word: index_id for index_id, word in results})

    def analyze_book(self, book):
        """Analyse un livre et retourne un dictionnaire de mots avec leurs positions."""
        languages = [lang.strip().lower() for lang in book.languages.split(',')]
        all_stopwords = set()
        for lang_code in languages:
            all_stopwords.update(self.stopwords_cache.get(lang_code, set()))

        word_pattern = re.compile(r'\b\w+\b')
        words = word_pattern.findall(book.text.lower())
        word_positions = defaultdict(list)
        new_positions = []

        # Liste pour stocker les positions dans le texte filtré (sans stopwords)
        adjusted_position = 0

        for index, word in enumerate(words):
            if word and word not in all_stopwords and len(word) > 1:
                word_positions[word].append(adjusted_position)
                adjusted_position += 1  # Ajuster la position pour le texte sans stopwords
                new_positions.append(word)  # Liste des mots restants

        return dict(word_positions), new_positions
