import axios from "axios";

const API_BASE_URL = "http://192.168.1.100:8000/api";

export async function BookService(id,nbBook){
    try {
      const response = await axios.get(`${API_BASE_URL}/books/?page=${id}&page_size=${nbBook}`);
      //console.log(response.data)
      return response.data; // Retourne les livres récupérés
    } catch (error) {
      console.error("Erreur lors de la récupération des livres :", error);
      throw error;
    }
}
export async function BookChoice(id,pgId){
  console.log('recup en cour',`${API_BASE_URL}/book/${id}/text/?page=${pgId}&page_size=300`)
  try {
    const response = await axios.get(`${API_BASE_URL}/book/${id}/text/?page=${pgId}&page_size=300`);
    return response.data; // Retourne les livres récupérés
  } catch (error) {
    console.error("Erreur lors de la récupération du text :", error);
    throw error;
  }
}
export async function BookChoiceHighlight(id,pgId,word){
  console.log('recup en cour',`${API_BASE_URL}/book/${id}/text/highlight/?word=${word}&page=${pgId}&page_size=300`)
  try {
    const response = await axios.get(`${API_BASE_URL}/book/${id}/text/highlight/?word=${word.replace(" ","")}&page=${pgId}&page_size=300`);
    return response.data; // Retourne les livres récupérés
  } catch (error) {
    console.error("Erreur lors de la récupération du text :", error);
    throw error;
  }
}
export async function CombinedSearch(word,where,setProgress,id) {
  try {
    // Premier appel : BookSearch
    const bookSearchResult = await axios.get(
      `${API_BASE_URL}/search/${word}${where}/?page=${id}&page_size=5`,
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
      total_books: bookSearchResult.data.total_books || 0,
      suggestions: suggestResult.data.suggestions || [],
      total_occurrences: bookSearchResult.data.total_occurrences || 0
    };

  } catch (error) {
    console.error("Erreur lors de la recherche combinée:", error);
    setProgress?.(100);
    return {
      books: [],
      total_books: 0,
      suggestions: [],
      total_occurrences: 0
    };
  }
}