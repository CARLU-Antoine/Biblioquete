import axios from "axios";

const API_BASE_URL = "http://192.168.34.24:8000/api";

export async function BookService(id){
    try {
      const response = await axios.get(`${API_BASE_URL}/books/?page=${id}`);
      //console.log(response.data)
      return response.data; // Retourne les livres récupérés
    } catch (error) {
      console.error("Erreur lors de la récupération des livres :", error);
      throw error;
    }
}

export async function BookSearch(word,where){
  // console.log(`${API_BASE_URL}/search/suggestions/${word}${where==undefined ? '' : '/'+where}`);
  try {
    const response = await axios.get(`${API_BASE_URL}/search/${word}${where}`);
    return response.data; // Retourne les livres récupérés
  } catch (error) {
    console.error("Erreur lors de la récupération des livres :", error);
    throw error;
  }
}

export async function WordSuggest(word){
  // console.log(`${API_BASE_URL}/search/suggestions/${word}${where==undefined ? '' : '/'+where}`);
  try {
    const response = await axios.get(`${API_BASE_URL}/search/suggestions/${word}`);
    return response.data; // Retourne les livres récupérés
  } catch (error) {
    console.error("Erreur lors de la récupération des livres :", error);
    throw error;
  }
}