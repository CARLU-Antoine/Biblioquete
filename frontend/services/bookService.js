import axios from "axios";

const API_BASE_URL = "http://172.16.8.32:8000/api";

export async function BookService(id){
    try {
      const response = await axios.get(`${API_BASE_URL}/books/?page=${id}&page_size=5`);
      //console.log(response.data)
      return response.data; // Retourne les livres récupérés
    } catch (error) {
      console.error("Erreur lors de la récupération des livres :", error);
      throw error;
    }
}
export async function CombinedSearch(word, where, setProgress) {
  try {
    // Premier appel : BookSearch
    const bookSearchResult = await axios.get(
      `${API_BASE_URL}/search/${word}${where}`,
      {
        onDownloadProgress: (progressEvent) => {
          const total = progressEvent.total;
          const loaded = progressEvent.loaded;
          if (total) {
            // On calcule la progression jusqu'à 90% pour la recherche principale
            const searchProgress = Math.floor((loaded / total) * 90);
            setProgress?.(searchProgress);
          }
        }
      }
    );

    let suggestResult = { data: { suggestions: [] } };
    
    try {
      // Deuxième appel : WordSuggest (les 10% restants)
      suggestResult = await axios.get(
        `${API_BASE_URL}/search/suggestions/${word}`,
        {
          onDownloadProgress: (progressEvent) => {
            const total = progressEvent.total;
            const loaded = progressEvent.loaded;
            if (total) {
              // On ajoute la progression des suggestions aux 90% déjà acquis
              const suggestProgress = Math.floor((loaded / total) * 10);
              setProgress?.(90 + suggestProgress);
            }
          }
        }
      );
      // On s'assure d'atteindre 100% après la complétion des suggestions
      setProgress?.(100);
    } catch (suggestError) {
      console.warn("Pas de suggestions trouvées:", suggestError);
      // En cas d'erreur sur les suggestions, on passe directement à 100%
      setProgress?.(100);
    }

    return {
      books: bookSearchResult.data.books || [],
      total_pages: bookSearchResult.data.total_pages || 0,
      suggestions: suggestResult.data.suggestions || []
    };

  } catch (error) {
    console.error("Erreur lors de la recherche combinée:", error);
    setProgress?.(100);
    return {
      books: [],
      total_pages: 0,
      suggestions: []
    };
  }
}