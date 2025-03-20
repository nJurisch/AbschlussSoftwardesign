import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import csv
import pandas as pd
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import streamlit.components.v1 as components

from berechnungKopie import Mechanism
from database import save_mechanism, load_mechanism, delete_mechanism, list_mechanisms, get_joint_positions_by_mechanism
from user_db import register, login

# Session-State initialisieren
def initialize_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "username" not in st.session_state:
        st.session_state.username = ""

    if "joints" not in st.session_state:
        st.session_state.joints = []

    if "links" not in st.session_state:
        st.session_state.links = []

    if "crank_speed" not in st.session_state:
        st.session_state.crank_speed = 0.05

    if "running" not in st.session_state:
        st.session_state.running = False

    if "mechanism" not in st.session_state:
        st.session_state.mechanism = Mechanism(crank_speed=0.05)


# Mechanismus-Animation mit to_jshtml()
def create_animation():
    mechanism = Mechanism(st.session_state.crank_speed)
    
    joints = [mechanism.add_joint(j["x"], j["y"], j["fixed"]) for j in st.session_state.joints]
    for j1, j2 in st.session_state.links:
        mechanism.add_link(joints[j1], joints[j2])

    ani = mechanism.animate()
    html = ani.to_jshtml()
    return html


# Gelenkgeschwindigkeit berechnen
def calculate_max_speed():
    if st.session_state.joints:
        selected_joint = st.selectbox("Gelenk für maximale Geschwindigkeit", range(len(st.session_state.joints)))
        joint = st.session_state.joints[selected_joint]
        speed = st.session_state.crank_speed * joint["x"]
        st.write(f"Maximale Geschwindigkeit von Gelenk {selected_joint + 1}: {speed:.2f}")


# Export der Gelenkpositionen als CSV
def export_joint_positions():
    mechanism_name = st.session_state.mechanism_name
    if not mechanism_name:
        st.warning("Kein Mechanismus-Name angegeben!")
        return

    # ✅ Daten aus der Datenbank holen
    data = get_joint_positions_by_mechanism(mechanism_name)
    
    if not data:
        st.warning("Keine gespeicherten Kinematik-Daten gefunden.")
        return
    
    df = pd.DataFrame(data)
    df = df[['frame', 'joint_index', 'x_position', 'y_position']]
    df.columns = ['Frame', 'Gelenk-ID', 'X-Position', 'Y-Position']

    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="Kinematik ausgeben",
        data=buffer,
        file_name=f"kinematik_{mechanism_name}.csv",
        mime="text/csv"
    )


# Gelenke verbinden
def connect_joints():
    if len(st.session_state.joints) < 2:
        st.warning("Mindestens zwei Gelenke sind erforderlich, um eine Verbindung herzustellen.")
        return

    st.write("### Gelenke verbinden")
    joint1 = st.selectbox("Erstes Gelenk auswählen", range(len(st.session_state.joints)))
    joint2 = st.selectbox("Zweites Gelenk auswählen", range(len(st.session_state.joints)))

    if st.button("Verbindung hinzufügen"):
        if joint1 != joint2:
            st.session_state.links.append([joint1, joint2])
            st.success(f"Verbindung zwischen Gelenk {joint1 + 1} und Gelenk {joint2 + 1} hinzugefügt!")
        else:
            st.error("Gelenke müssen unterschiedlich sein.")


# Mechanismus-Logik (Speichern, Laden, Bearbeiten)
def run_simulation():
    st.title(f"Mechanismus-Simulation für {st.session_state.username}")

    mechanism_name = st.text_input("Mechanismus-Name eingeben")
    st.session_state.mechanism_name = mechanism_name

    # Abmelde-Button
    if st.button("Abmelden"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.joints = []
        st.session_state.links = []
        st.session_state.tracked_joint = 0
        st.rerun()

    # Mechanismus speichern
    st.write("Mechanismus speichern")
    mechanism_name = st.text_input("Mechanismusname")

    if st.button("Speichern"):
        if mechanism_name.strip():
            data = {
                'joints': st.session_state.joints,
                'links': st.session_state.links,
                'crank_speed': st.session_state.crank_speed
            }
            save_mechanism(st.session_state.username, mechanism_name, data)
            st.success(f"Mechanismus '{mechanism_name}' gespeichert!")

    # Mechanismus laden und löschen
    st.write("Gespeicherte Mechanismen")
    saved_mechanisms = list_mechanisms(st.session_state.username)

    if saved_mechanisms:
        selected_mechanism = st.selectbox("Gespeicherten Mechanismus laden", [""] + saved_mechanisms)

        if selected_mechanism:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Laden"):
                    data = load_mechanism(st.session_state.username, selected_mechanism)
                    if data:
                        st.session_state.joints = data["joints"]
                        st.session_state.links = data["links"]
                        st.session_state.crank_speed = data.get("crank_speed", 0.05)
                        st.success(f"Mechanismus '{selected_mechanism}' erfolgreich geladen!")
                        st.rerun()

            with col2:
                if st.button("Löschen"):
                        delete_mechanism(st.session_state.username, selected_mechanism)
                        st.success(f"Mechanismus '{selected_mechanism}' erfolgreich gelöscht!")
                        st.rerun()

    # Gelenke bearbeiten
    st.write("Gelenke bearbeiten")
    for i, joint in enumerate(st.session_state.joints):
        cols = st.columns(4)
        joint["x"] = cols[0].number_input(f"X-Koordinate Gelenk {i + 1}", value=joint["x"])
        joint["y"] = cols[1].number_input(f"Y-Koordinate Gelenk {i + 1}", value=joint["y"])
        joint["fixed"] = cols[2].checkbox(f"Fixiert {i + 1}", value=joint["fixed"])
        if cols[3].button("Löschen", key=f"delete_joint_{i}"):
            st.session_state.joints.pop(i)
            st.rerun()

    if st.button("Gelenk hinzufügen"):
        st.session_state.joints.append({"x": 0.0, "y": 0.0, "fixed": False})
        st.rerun()

    # Gelenke verbinden
    connect_joints()

    # Export der Gelenkpositionen als CSV
    if st.button("Kinematik ausgeben"):
        export_joint_positions()

    # Animation
    st.write("---") 
    st.write("Mechanismus-Animation")

    joint_for_tracing = st.number_input("Gib eine Zahl ein:", min_value=0, step=1, format="%d")
    st.write("Ausgewählte Gelenk:", joint_for_tracing)

    if st.button("Simulation starten"):

        mechanism_animation = Mechanism(st.session_state.crank_speed)
        mechanism_animation.set_tracked_joint(joint_for_tracing)
        
        if not st.session_state.joints or not st.session_state.links:
                        st.error("Keine Mechanismus-Daten im Session State gefunden!")
                        st.stop()

                    # Erstelle Datenstruktur für from_data()
        data = {
                        "joints": st.session_state.joints,
                        "links": st.session_state.links
                    }
                   # Debugging: Zeige die geladenen Daten
        st.write("Daten für Mechanismus:", data)

                    # Mechanismus mit den gespeicherten Daten füllen
        for joint in data["joints"]:
                        mechanism_animation.add_joint(joint["x"], joint["y"], joint["fixed"])

        for link in data["links"]:
                        # Hole die Joint-Objekte anhand der Indizes der Links und füge sie hinzu
                        joint1 = mechanism_animation.joints[link[0]]
                        joint2 = mechanism_animation.joints[link[1]]
                        mechanism_animation.add_link(joint1, joint2)

        mechanism_animation.solve_positions()
        mech_ani = mechanism_animation.animate()

                    #Animation mit to_jshtml() einbetten
        components.html(mech_ani.to_jshtml(), height=1000)



# Login-Formular
def login_form():
    st.title("Anmeldung")

    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")

    if st.button("Anmelden"):
        if username.strip() and password.strip():
            success = login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Willkommen, {username}!")
                st.rerun()
            else:
                st.error("Falscher Benutzername oder Passwort.")


# Steuerung für Anmeldung und Simulation
def main():
    initialize_session_state()

    if not st.session_state.logged_in:
        login_form()
    else:
        run_simulation()


if __name__ == "__main__":
    main()

