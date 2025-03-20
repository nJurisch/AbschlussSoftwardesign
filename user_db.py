from tinydb import TinyDB, Query
import hashlib
import os

# Pfad zur JSON-Datenbank für Benutzer
db_path = os.path.join(os.path.dirname(__file__), 'data', 'users.json')

# Ordner erstellen, wenn er nicht existiert
if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

# Datei erstellen, wenn sie nicht existiert
if not os.path.exists(db_path):
    with open(db_path, 'w') as f:
        f.write("{}")

# TinyDB initialisieren
db = TinyDB(db_path)
UserTable = db.table('users')

# Passwort-Hashing mit SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register(username, password):
    """Registriert einen neuen Benutzer mit gehashtem Passwort"""
    username = username.strip()  # Leere Zeichen entfernen
    
    if not username or not password:
        return False
    
    hashed_password = hash_password(password)
    
    # Überprüfen, ob Benutzername bereits existiert
    User = Query()
    if UserTable.search(User.username == username):
        return False
    
    UserTable.insert({'username': str(username), 'password': hashed_password})
    print(f"Benutzer '{username}' wurde erfolgreich registriert.")
    return True

def login(username, password):
    """Überprüft den Login eines Benutzers"""
    username = username.strip()
    if not username or not password:
        return False
    
    hashed_password = hash_password(password)
    
    User = Query()
    user = UserTable.search(User.username == username)
    
    if user:
        # Debugging-Ausgabe zur Überprüfung
        print(f"Passwort in DB: {user[0]['password']}")
        print(f"Gehashtes Passwort: {hashed_password}")
        
        if user[0]['password'] == hashed_password:
            print("Login erfolgreich")
            return True
        else:
            print("Falsches Passwort")
    
    return False