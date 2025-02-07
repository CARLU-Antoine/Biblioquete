# models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    gutenberg_id = models.IntegerField(unique=True)
    title = models.TextField(null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name='books')
    languages = models.TextField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    subjects = models.JSONField(default=list, blank=True)
    bookshelves = models.JSONField(default=list, blank=True)
    formats = models.JSONField(default=dict, blank=True)
    media_type = models.CharField(max_length=50, null=True, blank=True)
    copyright = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    translators = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title

class InvertedIndex(models.Model):
    word = models.CharField(max_length=255, unique=True)
    books = models.ManyToManyField(Book, related_name="indexed_words")
    occurrences = models.IntegerField(default=0)
    positions = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.word

    def update_positions(self, book, positions):
        """Mettre à jour les positions d'un mot dans un livre."""
        # Convertir positions en liste si ce n'est pas déjà le cas
        positions = list(positions)

        # Trouver l'entrée existante pour ce livre
        existing_entry = next((entry for entry in self.positions if entry['book'] == book.id), None)

        if existing_entry:
            # Fusionner les positions sans doublons
            existing_entry['positions'] = list(set(existing_entry['positions'] + positions))
            existing_entry['occurrences'] = len(existing_entry['positions'])
        else:
            # Ajouter une nouvelle entrée
            self.positions.append({
                'book': book.id, 
                'positions': positions, 
                'occurrences': len(positions)
            })

        # Mettre à jour le total des occurrences
        self.occurrences = sum(entry['occurrences'] for entry in self.positions)