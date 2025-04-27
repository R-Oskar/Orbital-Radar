import requests
import os

def get_list():
    local_file = f"satellite_data.txt"

    # Wenn die TLE-Daten bereits lokal gespeichert sind, lade sie
    if os.path.exists(local_file):
        with open(local_file, "r") as file:
            lines = file.readlines()
    else:
        # URL for the TLE data (from the API)
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

        # Make a request to get the TLE data
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Split the content into lines
            lines = response.text.splitlines()

    satellite_names = []

    # Loop through the lines and extract the satellite names (which are every 1st line in each TLE group)
    for i in range(0, len(lines), 3):
        satellite_name = lines[i].strip()  # The name is on the 1st line of each 3-line TLE group
        satellite_names.append(satellite_name)

    # Print the list of satellite names
    satellite_names.sort()
    return satellite_names