# Moteur de Recherche de Bibliothèque Numérique 📚

Une application mobile/web permettant la recherche avancée dans une vaste bibliothèque numérique, développée avec React Native et Django.

## 🎯 À Propos du Projet

Ce moteur de recherche de bibliothèque numérique offre une expérience utilisateur intuitive pour explorer une collection de plus de 1664 livres. L'application utilise des algorithmes de recherche avancés et des métriques de centralité pour fournir des résultats pertinents et des suggestions contextuelles.

## 🛠 Technologies Utilisées

### Frontend
- React Native

### Backend
- Django
- Django REST Framework

## ✨ Fonctionnalités

- 🔍 Recherche par mot-clé
- 🎯 Recherche avancée avec support des expressions régulières
- 📊 Classement intelligent des résultats utilisant des indices de centralité
  - Closeness
  - Betweenness
  - PageRank
- 💡 Système de suggestions de contenus similaires
- 📱 Interface responsive (mobile et web)

## 🚀 Installation

1. **Prérequis**
```bash
# Backend
python -m venv env
source env/bin/activate  # ou `env\Scripts\activate` sous Windows
pip install -r requirements.txt

# Frontend
npm install
# ou
yarn install
```

2. **Configuration**
```bash
# Backend
cd backend
python manage.py migrate
python manage.py loaddata initial_data

# Frontend
cd frontend
cp .env.example .env
```

3. **Lancement**
```bash
# Backend
python manage.py runserver

# Frontend
npm start
# ou
yarn start
```

## 🧪 Tests

```bash
# Backend
python manage.py test

# Frontend
npm test
# ou
yarn test
```

## 📊 Performances

L'application a été testée avec succès sur :
- Une base de données de 1664+ livres
- Des recherches complexes utilisant des expressions régulières
- Des calculs d'indices de centralité en temps réel

## 👥 Équipe

Projet réalisé par une équipe de 2-3 personnes dans le cadre d'un projet académique.

## 📅 Planning

- Date de rendu : 14 février 2025
- Présentation : 20 minutes ou vidéo pitch de 5 minutes

