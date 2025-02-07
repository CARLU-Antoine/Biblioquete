import sqlite3
from sqlalchemy import create_engine, text
import pandas as pd

def convert_copyright(value):
    """Convertit la valeur copyright de int vers bool"""
    return bool(value)

def clean_data_for_postgres(df, table_name):
    """
    Nettoie et prépare les données pour PostgreSQL selon la table
    """
    if table_name == 'books_book':
        # Conversion du champ copyright en booléen
        if 'copyright' in df.columns:
            df['copyright'] = df['copyright'].apply(convert_copyright)
    
    return df

def truncate_table(engine, table_name):
    """Vide une table PostgreSQL"""
    with engine.connect() as connection:
        connection.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        connection.commit()

def migrate_sqlite_to_postgres(sqlite_file, db_params):
    """
    Migre les données de SQLite vers PostgreSQL avec gestion des erreurs
    """
    postgres_url = f"postgresql://{db_params['USER']}:{db_params['PASSWORD']}@{db_params['HOST']}:{db_params['PORT']}/{db_params['NAME']}"
    
    sqlite_conn = sqlite3.connect(sqlite_file)
    postgres_engine = create_engine(postgres_url)

    # Ordre spécifique des tables pour respecter les dépendances
    tables = [
        'books_author',
        'books_book',
        'books_invertedindex',
        'books_invertedindex_books',
    ]

    for table in tables:
        try:
            print(f"\nMigration de la table {table}...")
            
            # Lecture des données depuis SQLite
            df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
            
            if df.empty:
                print(f"Table {table} vide, passage à la suivante")
                continue

            # Nettoyage et préparation des données
            df = clean_data_for_postgres(df, table)
            
            # Pour les tables avec contrainte d'unicité, on vide d'abord la table
            if table in ['books_author', 'books_book']:
                print(f"Nettoyage de la table {table} existante...")
                truncate_table(postgres_engine, table)
                print("Table nettoyée avec succès")

            # Écriture dans PostgreSQL
            df.to_sql(
                name=table,
                con=postgres_engine,
                if_exists='append',
                index=False,
                method='multi',  # Insertion par lots pour de meilleures performances
                chunksize=1000   # Nombre de lignes par lot
            )
            
            print(f"✓ Migration réussie pour {table} ({len(df)} lignes)")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration de {table}: {str(e)}")
            
            # Affichage des détails pour le débogage
            if hasattr(e, '__cause__'):
                print(f"Cause détaillée: {str(e.__cause__)}")

    # Fermeture des connexions
    sqlite_conn.close()
    postgres_engine.dispose()

# Configuration de la base de données
DB_PARAMS = {
    'NAME': 'moteur_de_recherche',
    'USER': 'postgres',
    'PASSWORD': 'Island789+',
    'HOST': 'localhost',
    'PORT': '5432'
}

if __name__ == "__main__":
    SQLITE_FILE = "db.sqlite3"
    
    try:
        with open(SQLITE_FILE, 'r') as f:
            pass
        print("Fichier SQLite trouvé, début de la migration...")
        migrate_sqlite_to_postgres(SQLITE_FILE, DB_PARAMS)
    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier {SQLITE_FILE} n'a pas été trouvé dans le répertoire courant.")