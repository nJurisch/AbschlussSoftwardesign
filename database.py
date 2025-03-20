from tinydb import TinyDB, Query
import os

# Pfad zur JSON-Datenbank
db_path = os.path.join(os.path.dirname(__file__), 'data', 'mechanisms.json')

# Ordner und Datei automatisch erstellen, falls nicht vorhanden
if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

if not os.path.exists(db_path):
    with open(db_path, 'w') as f:
        f.write("{}")

# TinyDB initialisieren
db = TinyDB(db_path)
MechanismTable = db.table('mechanisms')

def save_mechanism(user, name, data):
    """Speichert einen Mechanismus in der Datenbank (Benutzer + Name)"""
    MechanismTable.upsert({'user': user, 'name': name, 'data': data}, 
                          (Query().user == user) & (Query().name == name))

def load_mechanism(user, name):
    """Lädt einen gespeicherten Mechanismus eines Benutzers"""
    result = MechanismTable.search((Query().user == user) & (Query().name == name))
    if result:
        return result[0]['data']
    return None

def delete_mechanism(user, name):
    """Löscht einen gespeicherten Mechanismus eines Benutzers"""
    MechanismTable.remove((Query().user == user) & (Query().name == name))

def list_mechanisms(user):
    """Gibt eine Liste der gespeicherten Mechanismen für einen Benutzer zurück"""
    return [entry['name'] for entry in MechanismTable.search(Query().user == user)]

JointPositionTable = db.table('joint_positions')

def save_joint_position(frame, joint_index, x, y, mechanism_name):
    """Speichert die Gelenkpositionen pro Frame in der Datenbank"""
    JointPositionTable.insert({
        'frame': frame,
        'joint_index': joint_index,
        'x_position': x,
        'y_position': y,
        'mechanism_name': mechanism_name
    })

def get_joint_positions_by_mechanism(mechanism_name):
    """Lädt alle gespeicherten Gelenkpositionen für einen bestimmten Mechanismus"""
    return JointPositionTable.search(Query().mechanism_name == mechanism_name)

def delete_joint_positions(mechanism_name):
    """Löscht alle gespeicherten Gelenkpositionen für einen Mechanismus"""
    JointPositionTable.remove(Query().mechanism_name == mechanism_name)