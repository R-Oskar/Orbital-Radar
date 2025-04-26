import tkinter as tk
from threading import Thread
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import requests
import os
import time
from skyfield.api import Topos, load
import get_list as g
import tkinter.ttk as ttk  # Ergänzen für Combobox
from datetime import datetime

# Globale Variablen für mehrere Satelliten
tracking = False
satellites = {}  # Dictionary für verschiedene Satelliten
prev_satellites = {}

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
def track_satellite(satellite_id):
    global satellites
    ts = load.timescale()

    # TLE-Daten lokal abrufen
    satellite_tle = fetch_tle_data()

    if not satellite_tle:
        print(f"Fehler: TLE-Daten für {satellite_id} konnten nicht abgerufen werden.")
        return

    try:
        # Statt der API die lokale TLE-Datei verwenden
        satellites_api = load.tle_file('satellite_data.txt')  # Lade TLE-Daten aus der richtigen lokalen Datei
        #print(f"Geladene Satelliten: {[sat.name for sat in satellites_api]}")

        # Suche nach dem Satelliten mit dem entsprechenden Namen
        satellite = next((sat for sat in satellites_api if satellite_id in sat.name), None)

        if not satellite:
            raise ValueError(f"Satellit mit dem Namen {satellite_id} nicht gefunden!")

        longitudes = []
        latitudes = []

        while satellites[satellite_id]["tracking"]:
            try:
                t = ts.now()
                satellite_position = satellite.at(t)
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
        Thread(target=track_satellite, args=(satellite_id,), daemon=True).start()

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

        satellites[satellite_id]["text"] = ax.text(longitude, latitude, satellite_id + " :" + now.strftime("%Y-%m-%d %H:%M:%S"), transform=ccrs.PlateCarree(), fontsize=6, color='black')
        
        # Update prev_satellites to store the satellite's data in a dictionary
        prev_satellites[satellite_id] = {
            "id": satellite_id,
            "text": satellites[satellite_id]["text"],
            "point": satellites[satellite_id]["point"],
            "path": satellites[satellite_id]["path"],
        }
        fig.canvas.draw()

def reset_tracking_single():
    global prev_satellites
    satellite_id = satellite_var.get()

    # Remove the satellite from the satellites dictionary
    if satellite_id in satellites:
        satellites[satellite_id]["point"].remove()
        satellites[satellite_id]["path"].remove()
        satellites[satellite_id]["text"].remove()
        del satellites[satellite_id]

    # Reset the satellite in prev_satellites
    for satellite_id in prev_satellites:
        satellite_data = prev_satellites[satellite_id]
        satellite_data["point"].remove()
        satellite_data["path"].remove()
        satellite_data["text"].remove()
        del prev_satellites[satellite_id]

    fig.canvas.draw()


# Reset-Button für alle Satelliten
def reset_tracking_all():
    global satellites
    for satellite_id, elements in satellites.items():
        # Grafik-Elemente entfernen
        elements["point"].remove()
        elements["path"].remove()
        elements["text"].remove()
    satellites = {}
    fig.canvas.draw()

# Fenster für die Buttons und das Dropdown-Menü erstellen
root = tk.Tk()
root.title("Satellite Tracker Control")
root.attributes('-topmost', True)
root.geometry("300x400")
root.configure(bg='lightgray')

# Dropdown-Menü für Satelliten
satellite_var = tk.StringVar(root)
satellite_var.set(satellite_list[0])

satellite_menu = ttk.Combobox(root, textvariable=satellite_var, values=satellite_list, state = "readonly")
satellite_menu.pack(fill='both', expand=True)
satellite_menu.current(0)  # Erstes Element vorauswählen

# Start-Button
start_button = tk.Button(root, text="Start Tracking", command=start_tracking)
start_button.pack(fill='both', expand=True)

# Stop-Button
stop_button = tk.Button(root, text="Stop Tracking", command=stop_tracking)
stop_button.pack(fill='both', expand=True)

# Reset-Button für alle Satelliten
reset_button_single = tk.Button(root, text="Reset This", command=reset_tracking_single)
reset_button_single.pack(fill='both', expand=True)


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