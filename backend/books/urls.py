from django.urls import path
from .views import (
    BookListView,
    BookDetailView,
    BooksByLanguageView,
    AvailableLanguagesView,
    BookTextView,
    BookSearchView,
    AdvancedBookSearchView,
    InvertedIndexSearchView,
    RankedBookSearchView,
    ClosenessBookSearchView,
    BookTextHighlightView,
)

urlpatterns = [
    path('books/', BookListView.as_view(), name='all-books'),
    path('book/<int:id>/', BookDetailView.as_view(), name='book-detail'),
    path('books/by-language/<str:language>/', BooksByLanguageView.as_view(), name='books-by-language'),
    path('books/available-languages/', AvailableLanguagesView.as_view(), name='available-languages'),
    path('book/<int:book_id>/text/', BookTextView.as_view(), name='fetch_book_text'),
    path('search/', BookSearchView.as_view(), name='search'),
    path('search/advanced/', AdvancedBookSearchView.as_view(), name='advanced-search'),
    path('search/inverted/<str:word>/', InvertedIndexSearchView.as_view(), name='inverted-search'),
    path('search/ranked/', RankedBookSearchView.as_view(), name='ranked-search'),
    path('search/closeness/', ClosenessBookSearchView.as_view(), name='closeness-search'),
    path('book/<int:book_id>/text/highlight/', BookTextHighlightView.as_view(), name='highlight-book-text'),
]
