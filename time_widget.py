import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter import messagebox
from datetime import datetime
from skyfield.api import load

def submit_date_time(date_entry, hour_spinbox, minute_spinbox):
    try:
        # Datum und Uhrzeit aus den Eingabefeldern holen
        selected_date = date_entry.get_date()
        selected_hour = int(hour_spinbox.get())
        selected_minute = int(minute_spinbox.get())

        # Datum und Uhrzeit kombinieren
        selected_datetime = datetime(
            selected_date.year, 
            selected_date.month, 
            selected_date.day, 
            selected_hour, 
            selected_minute
        )
        
        # Anzeige der ausgewählten Zeit als Bestätigung
        time_str = selected_datetime.strftime("%Y-%m-%d %H:%M:%S")
        messagebox.showinfo("Ausgewählte Zeit", f"Die ausgewählte Zeit ist: {time_str}")

        # Konvertiere in Skyfield-Format
        ts = load.timescale()
        skyfield_time = ts.utc(selected_datetime.year, selected_datetime.month, selected_datetime.day,
                               selected_datetime.hour, selected_datetime.minute, selected_datetime.second)

        return skyfield_time

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Eingabe: {e}")

def open_date_time_window():
    # Neues Fenster zur Datums- und Zeiteingabe
    window = tk.Tk()
    window.title("Position ausrechnen")
    window.geometry("300x250")

    # DateEntry für das Datum
    date_label = tk.Label(window, text="Datum auswählen:")
    date_label.pack(pady=5)

    date_entry = DateEntry(window, date_pattern='yyyy-mm-dd', width=12)
    date_entry.pack(pady=5)

    # Uhrzeit-Spinnboxen
    time_label = tk.Label(window, text="Zeit auswählen:")
    time_label.pack(pady=5)

    hour_spinbox = ttk.Spinbox(window, from_=0, to=23, width=5, format="%02.0f")
    hour_spinbox.set("00")  # Standardwert auf "00"
    hour_spinbox.pack(side="left", padx=5)

    minute_spinbox = ttk.Spinbox(window, from_=0, to=59, width=5, format="%02.0f")
    minute_spinbox.set("00")  # Standardwert auf "00"
    minute_spinbox.pack(side="left", padx=5)

    # Button zum Bestätigen der Eingabe
    submit_button = tk.Button(window, text="Bestätigen", command=lambda: submit_date_time(date_entry, hour_spinbox, minute_spinbox))
    submit_button.pack(pady=10)

    # Fenster anzeigen
    window.mainloop()

# Das Fenster öffnen
if __name__ == "__main__":
    open_date_time_window()
