import requests
import concurrent.futures
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from books.models import Book, Author
from tqdm import tqdm

GUTENDEX_API = "https://gutendex.com/books/"
MAX_BOOKS = 1664
MAX_WORKERS = 200  # Ajuste en fonction de la capacité de ton système
MIN_WORDS = 10000  # Seuil minimum de mots
MAX_WORDS = 30000  # Seuil maximum de mots

class Command(BaseCommand):
    help = "Import books from Gutendex API and store them in the database."

    def fetch_book_text(self, book):
        text_url = book['formats'].get("text/plain; charset=us-ascii") or book['formats'].get("text/plain")
        if not text_url:
            return None

        try:
            text_response = requests.get(text_url, timeout=3)
            text_response.raise_for_status()
            text = text_response.text
            
            # Nettoyage du texte
            text = text.replace("\ufeff", "")
            text = re.sub(r"\*\*\* START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", "", text, flags=re.S)
            text = re.sub(r"\*\*\* END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", "", text, flags=re.S)
            
            return text.strip()
        except requests.exceptions.RequestException:
            return None

    def handle(self, *args, **kwargs):
        books_imported = 0
        page = 1
        authors_to_create = []
        books_to_create = []

        with tqdm(total=MAX_BOOKS, desc="Importing books", ncols=100) as pbar:
            while books_imported < MAX_BOOKS:
                try:
                    response = requests.get(GUTENDEX_API, params={"languages": "en", "page": page}, timeout=10)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"API Error: {e}"))
                    break

                data = response.json()
                books = data.get("results", [])

                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    # Préparer les textes des livres de manière concurrente
                    book_texts = list(executor.map(self.fetch_book_text, books))

                    # Traiter les livres et auteurs
                    with transaction.atomic():
                        for book, text in zip(books, book_texts):
                            if books_imported >= MAX_BOOKS:
                                break

                            # Vérifier si le livre a plus de MIN_WORDS mots
                            if text is None:
                                continue  # Ignorer ce livre si le texte est indisponible

                            word_count = len(text.split())

                            if word_count < MIN_WORDS or word_count > MAX_WORDS:
                                continue

                            # Traiter l'auteur
                            authors = book.get('authors', [])
                            author_data = authors[0] if authors else {'name': 'Unknown'}

                            # Ajouter l'auteur à la liste (pas encore en base de données)
                            authors_to_create.append({
                                'name': author_data.get('name', 'Unknown'),
                                'birth_year': author_data.get('birth_year'),
                                'death_year': author_data.get('death_year')
                            })

                            # Vérifier si le livre existe déjà dans la base de données
                            if not Book.objects.filter(gutenberg_id=book['id']).exists():
                                if text:
                                    summary = book.get('summaries', [None])[0] if book.get('summaries') else None
                                    
                                    books_to_create.append(Book(
                                        gutenberg_id=book['id'],
                                        title=book['title'],
                                        author=None,  # Le lien avec l'auteur sera mis à jour plus tard
                                        subjects=book.get('subjects', []),
                                        bookshelves=book.get('bookshelves', []),
                                        formats=book.get('formats', {}),
                                        media_type=book.get('media_type'),
                                        copyright=book.get('copyright', False),
                                        download_count=book.get('download_count', 0),
                                        languages=','.join(book.get('languages', [])),
                                        translators=book.get('translators', []),
                                        text=text,
                                        summary=summary
                                    ))

                                    books_imported += 1
                                    pbar.update(1)

                page += 1

        # Après avoir créé les auteurs et livres, faire un bulk_create
        with transaction.atomic():
            # Créer les auteurs en masse
            authors = []
            for author_data in authors_to_create:
                author, created = Author.objects.update_or_create(
                    name=author_data['name'],
                    defaults=author_data
                )
                authors.append(author)  # Stocker les auteurs pour les lier aux livres

            # Mettre à jour les auteurs des livres
            for book in books_to_create:
                # Associer l'auteur correct à chaque livre
                author = next((a for a in authors if a.name == book.title), None)
                if author:
                    book.author = author

            # Créer les livres en masse
            Book.objects.bulk_create(books_to_create)

        self.stdout.write(self.style.SUCCESS(f"Import completed: {books_imported} books imported."))
