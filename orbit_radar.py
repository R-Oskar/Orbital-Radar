import tkinter as tk
from threading import Thread
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import requests
import os
import time
from skyfield.api import load
import get_list as g
import tkinter.ttk as ttk  # Ergänzen für Combobox
from datetime import datetime, timedelta
from tkcalendar import DateEntry

# Globale Variablen für mehrere Satelliten
tracking = False
satellites = {}  # Dictionary für verschiedene Satelliten
prev_satellites = {}
satellite_paths = {}

# Liste der verfügbaren Satelliten
satellite_list = g.get_list()

# TLE-Daten abrufen (über Celestrak oder gespeicherte TLE-Daten)
def fetch_tle_data():
    # Datei, in der die TLE-Daten gespeichert werden sollen
    local_file = f"satellite_data.txt"

    # Wenn die TLE-Daten bereits lokal gespeichert sind, lade sie
    if os.path.exists(local_file):
        with open(local_file, "r") as file:
            return file.readlines()

    # Wenn die Datei nicht existiert, hole die Daten aus der API
    else:
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=tle"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.text.splitlines()
            # Speichere die TLE-Daten lokal, um sie später zu verwenden
            with open(local_file, "w") as file:
                file.write("\n".join(data))

            return data
        else:
            print(f"Fehler beim Abrufen der TLE-Daten: {response.status_code}")
            return []

# Berechnung der Position eines Satelliten mit Skyfield
def track_satellite(satellite_id, timescale, update):
    global satellites

    # TLE-Daten lokal abrufen
    satellite_tle = fetch_tle_data()

    if not satellite_tle:
        print(f"Fehler: TLE-Daten für {satellite_id} konnten nicht abgerufen werden.")
        return

    try:
        # Statt der API die lokale TLE-Datei verwenden
        satellites_api = load.tle_file('satellite_data.txt')  # Lade TLE-Daten aus der richtigen lokalen Datei

        # Suche nach dem Satelliten mit dem entsprechenden Namen
        satellite = next((sat for sat in satellites_api if satellite_id in sat.name), None)

        if not satellite:
            raise ValueError(f"Satellit mit dem Namen {satellite_id} nicht gefunden!")

        longitudes = []
        latitudes = []

        while satellites[satellite_id]["tracking"]:
            try:
                if update:
                    ts = load.timescale()
                    timescale = ts.now()
                satellite_position = satellite.at(timescale)
                subpoint = satellite_position.subpoint()
                longitude = subpoint.longitude.degrees
                latitude = subpoint.latitude.degrees

                longitudes.append(longitude)
                latitudes.append(latitude)

                satellites[satellite_id]["point"].set_data([longitude], [latitude])
                satellites[satellite_id]["path"].set_data(longitudes, latitudes)

                # Update satellite name position
                satellites[satellite_id]["text"].set_position((longitude, latitude))
                satellites[satellite_id]["text"].set_text(satellite_id)

                fig.canvas.draw()

            except Exception as e:
                print(f"Fehler beim Abrufen der {satellite_id}-Daten: {e}")

            time.sleep(1)

    except Exception as e:
        print(f"Fehler beim Tracken des Satelliten {satellite_id}: {e}")
  
# Start-Button für einen Satelliten
def start_tracking():
    satellite_id = satellite_var.get()
    
    if satellite_id not in satellites or not satellites[satellite_id]["tracking"]:
        satellites[satellite_id] = {
            "tracking": True,
            "longitudes": [],
            "latitudes": [],
            "point": ax.plot([], [], marker='o', color='red', markersize=8, transform=ccrs.Geodetic())[0],
            "path": ax.plot([], [], color='yellow', linewidth=1, transform=ccrs.Geodetic())[0],
            "text": ax.text(0, 0, satellite_id, transform=ccrs.PlateCarree(), fontsize=10, color='black')  # Add text for satellite name
        }
        ts = load.timescale()
        t = ts.now()
        Thread(target=track_satellite, args=(satellite_id, t, True), daemon=True).start()

# Stop-Button für einen Satelliten
def stop_tracking():
    global prev_satellites
    satellite_id = satellite_var.get()
    
    if satellite_id in satellites:
        satellites[satellite_id]["tracking"] = False
        satellites[satellite_id]["text"].remove()

        satellites_api = load.tle_file('satellite_data.txt')
        satellite = next((sat for sat in satellites_api if satellite_id in sat.name), None)
        ts = load.timescale()
        t = ts.now()
        satellite_position = satellite.at(t)
        subpoint = satellite_position.subpoint()
        longitude = subpoint.longitude.degrees
        latitude = subpoint.latitude.degrees
        
        now = datetime.now()

        # Neuen Text hinzufügen (mit aktuellem Timestamp)
        satellites[satellite_id]["text"] = ax.text(
            longitude, latitude, 
            satellite_id + " :" + now.strftime("%Y-%m-%d %H:%M:%S"),
            transform=ccrs.PlateCarree(), fontsize=6, color='black'
        )

        if satellite_id not in prev_satellites:
            prev_satellites[satellite_id] = []

        prev_satellites[satellite_id].append({
            "text": satellites[satellite_id]["text"],
            "point": satellites[satellite_id]["point"],
            "path": satellites[satellite_id]["path"],
        })

        fig.canvas.draw()

# Reset-Button für aktuell ausgewählten Satelliten
def reset_tracking_single():
    global prev_satellites, satellites, satellite_paths
    satellite_id = satellite_var.get()

    # Aktive Grafikobjekte vom Satelliten entfernen
    if satellite_id in satellites:
        try:
            satellites[satellite_id]["point"].remove()
        except Exception:
            pass
        try:
            satellites[satellite_id]["path"].remove()
        except Exception:
            pass
        try:
            satellites[satellite_id]["text"].remove()
        except Exception:
            pass
        
        del satellites[satellite_id]

    # Alte gespeicherte Grafikobjekte vom Satelliten entfernen
    if satellite_id in prev_satellites:
        for satellite_data in prev_satellites[satellite_id]:
            try:
                if satellite_data["point"]:
                    satellite_data["point"].remove()
            except Exception:
                pass
            try:
                if satellite_data["path"]:
                    satellite_data["path"].remove()
            except Exception:
                pass
            try:
                if satellite_data["text"]:
                    satellite_data["text"].remove()
            except Exception:
                pass

        del prev_satellites[satellite_id]

    # Pfad vom aktuellen Satelliten entfernen (falls vorhanden)
    if satellite_id in satellite_paths:
        try:
            satellite_paths[satellite_id].remove()
        except Exception:
            pass
        del satellite_paths[satellite_id]

    fig.canvas.draw()

# Reset-Button für alle Satelliten
def reset_tracking_all():
    global satellites, prev_satellites, satellite_paths

    # Lösche alle Satelliten aus "satellites"
    for satellite_id, elements in satellites.items():
        try:
            elements["point"].remove()
        except Exception:
            pass
        try:
            elements["path"].remove()
        except Exception:
            pass
        try:
            elements["text"].remove()
        except Exception:
            pass

    satellites = {}

    # Lösche alle Satelliten aus "prev_satellites"
    for satellite_id, satellite_data_list in prev_satellites.items():
        for satellite_data in satellite_data_list:
            try:
                if satellite_data["point"]:
                    satellite_data["point"].remove()
            except Exception:
                pass
            try:
                if satellite_data["path"]:
                    satellite_data["path"].remove()
            except Exception:
                pass
            try:
                if satellite_data["text"]:
                    satellite_data["text"].remove()
            except Exception:
                pass

    prev_satellites = {}

    # Lösche alle zusätzlichen gezeichneten Pfade aus "satellite_paths"
    for satellite_id, path_line in satellite_paths.items():
        try:
            path_line.remove()
        except Exception:
            pass

    satellite_paths = {}

    # Zeichne die Figur neu
    fig.canvas.draw()

# ausrechnen Button zur Anzeigung der Position des Planetens zu einem bestimmten Zeitpunkt
def calculate():
    global prev_satellites, satellites
    # Datum und Uhrzeit auslesen
    date = date_entry.get()
    hour = hour_spinbox.get()
    minute = minute_spinbox.get()
    
    date_str = f"{date} {hour}:{minute}:00"
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    
    ts = load.timescale()
    skyfield_time = ts.utc(date_obj.year, date_obj.month, date_obj.day, date_obj.hour, date_obj.minute, date_obj.second)

    satellite_id = satellite_var.get()

    # Stop live tracking if necessary
    if satellite_id in satellites:
        satellites[satellite_id]["tracking"] = False
        
        # Save current tracking elements to prev_satellites
        prev_satellites.setdefault(satellite_id, []).append({
            "text": satellites[satellite_id]["text"],
            "point": satellites[satellite_id]["point"],
            "path": satellites[satellite_id]["path"],
        })

    # Now calculate the static position regardless
    try:
        # TLE-Daten laden
        satellites_api = load.tle_file('satellite_data.txt')
        satellite = next((sat for sat in satellites_api if satellite_id in sat.name), None)

        if not satellite:
            raise ValueError(f"Satellit mit dem Namen {satellite_id} nicht gefunden!")

        satellite_position = satellite.at(skyfield_time)
        subpoint = satellite_position.subpoint()
        longitude = subpoint.longitude.degrees
        latitude = subpoint.latitude.degrees

        # Plot new static point
        point = ax.plot(longitude, latitude, marker='o', color='red', markersize=8, transform=ccrs.Geodetic())[0]
        text = ax.text(longitude, latitude, f"{satellite_id} \n{skyfield_time.utc_iso()}", fontsize=6, color='black', transform=ccrs.PlateCarree())

        # Add to prev_satellites
        prev_satellites.setdefault(satellite_id, []).append({
            "text": text,
            "point": point,
            "path": None,  # no path for single calculated point
        })

        fig.canvas.draw()

    except Exception as e:
        print(f"Fehler beim Berechnen der Position des Satelliten {satellite_id} zu der gegebenen Zeit: {e}")

# Button um Satellitenpfad zu toggeln
def toggle_path():
    satellite_id = satellite_var.get()

    try:
        # Prüfen, ob der Pfad für diesen Satelliten schon existiert
        if satellite_id in satellite_paths:
            # Pfad existiert -> lösche ihn
            try:
                satellite_paths[satellite_id].remove()
            except Exception:
                pass  # Falls das Entfernen fehlschlägt, einfach ignorieren

            del satellite_paths[satellite_id]
            fig.canvas.draw()
            return  # Nichts weiter tun

        # Wenn kein Pfad existiert -> Bahn zeichnen
        satellites_api = load.tle_file('satellite_data.txt')
        satellite = next((sat for sat in satellites_api if satellite_id in sat.name), None)

        if not satellite:
            raise ValueError(f"Satellit mit dem Namen {satellite_id} nicht gefunden!")

        ts = load.timescale()
        t0 = ts.now()
        t1 = ts.utc(t0.utc_datetime() + timedelta(minutes=90))  # 90 Minuten in die Zukunft
        times = ts.linspace(t0, t1, 500)  # 500 Punkte für glatte Linie

        geocentric_positions = satellite.at(times)
        subpoints = geocentric_positions.subpoint()

        longitudes = subpoints.longitude.degrees
        latitudes = subpoints.latitude.degrees

        # Bahn zeichnen und im Dictionary speichern
        path_line = ax.plot(longitudes, latitudes, color='black', linewidth=1, transform=ccrs.Geodetic())[0]
        satellite_paths[satellite_id] = path_line

        fig.canvas.draw()

    except Exception as e:
        print(f"Fehler beim Anzeigen/Löschen der Satellitenbahn: {e}")

# GUI

# Fenster für die Buttons und das Dropdown-Menü erstellen
root = tk.Tk()
root.title("Satelliten Tracker Kontrollfenster")
root.attributes('-topmost', True)
root.geometry("300x400")
root.configure(bg='lightgray')

# Dropdown-Menü für Satelliten
satellite_var = tk.StringVar(root)
satellite_var.set(satellite_list[0])

satellite_menu = ttk.Combobox(root, textvariable=satellite_var, values=satellite_list, state="readonly")
satellite_menu.pack(fill='both', expand=True)
satellite_menu.current(0)  # Erstes Element vorauswählen

# Start-Button
start_button = tk.Button(root, text="Starte Tracking", command=start_tracking)
start_button.pack(fill='both', expand=True)

# Stop-Button
stop_button = tk.Button(root, text="Stoppe Tracking", command=stop_tracking)
stop_button.pack(fill='both', expand=True)

# Reset-Button für ausgewählten Satellit
reset_button_single = tk.Button(root, text="Reset This", command=reset_tracking_single)
reset_button_single.pack(fill='both', expand=True)

date_label = tk.Label(root, text="Datum auswählen:")
date_label.pack(pady=5)

date_entry = DateEntry(root, date_pattern='yyyy-mm-dd', width=12)
date_entry.pack(pady=5)

# Uhrzeit-Spinnboxen
time_label = tk.Label(root, text="Zeit auswählen:")
time_label.pack(pady=5)

time_frame = tk.Frame(root)  # Ein Frame für die Uhrzeit-Spinboxen
time_frame.pack(pady=5)

hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=5, format="%02.0f")
hour_spinbox.set("00")  # Standardwert auf "00"
hour_spinbox.pack(side="left", padx=5)

minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=5, format="%02.0f")
minute_spinbox.set("00")  # Standardwert auf "00"
minute_spinbox.pack(side="left", padx=5)

calculate_button = tk.Button(root, text="Position zu diesem Zeitpunkt ausrechnen", command=calculate)
calculate_button.pack(fill='both', expand = True)

graph_button = tk.Button(root, text="Satellitenbahn toggeln", command = toggle_path)
graph_button.pack(fill='both', expand = True)

# Reset-Button für alle Satelliten
reset_button_all = tk.Button(root, text="Reset All", command=reset_tracking_all)
reset_button_all.pack(fill='both', expand=True)

# Karte zeichnen
fig = plt.figure(figsize=(12, 6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_global()
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black')
ax.gridlines(draw_labels=True)
plt.title('Live-Tracking: Satelliten')

# Matplotlib plot in einem separaten Fenster starten
def run_gui():
    plt.show()

root.after(1, run_gui)
root.mainloop()