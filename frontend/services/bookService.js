import axios from "axios";

const API_BASE_URL = "http://172.16.8.58:8000/api";

const BookService = {
  getAllBooks: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/books`);
      return response.data; // Retourne les livres récupérés
    } catch (error) {
      console.error("Erreur lors de la récupération des livres :", error);
      throw error;
    }
  },

  getBookById: async (bookId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/book/${bookId}`);
      return response.data;
    } catch (error) {
      console.error("Erreur lors de la récupération du livre :", error);
      throw error;
    }
  },
};

export default BookService;
