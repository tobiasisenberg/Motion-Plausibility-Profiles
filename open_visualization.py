import os
import http.server
import socketserver
import webbrowser
import Dataset_Preprocessing.trajectory_computation

import csv
import json

# Stores in a .json, the path of iNaturalist files from Observations/
def generate_observations_list():
    folder = "Observations"
    if os.path.exists(folder):
        files = [f for f in os.listdir(folder) if f.endswith('.csv')]
        with open("observations_list.txt", "w") as f:
            for file in files:
                f.write(f"{folder}/{file}\n")
        print(f"Generated observations_list.txt with {len(files)} files.")

# Counts the number of posts by users so that the website show them in the right order
def generate_usernames():
    folder = "Observations"
    usernames = {}
    if os.path.exists(folder):
        print("Generating user stats from Observations CSV files...")
        for file in os.listdir(folder):
            if file.endswith('.csv'):
                try:
                    with open(os.path.join(folder, file), 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        if not header: continue
                        try:
                            uid_idx = header.index('user_id')
                            ulogin_idx = header.index('user_login')
                        except ValueError:
                            continue
                        for row in reader:
                            if len(row) > max(uid_idx, ulogin_idx):
                                uid = row[uid_idx]
                                uname = row[ulogin_idx]
                                if uid not in usernames.keys():
                                    usernames[uid] = uname
                except Exception as e:
                    print(f"Error parsing {file}: {e}")
        with open('Interactive_Visualisation/ressources/usernames.json', 'w') as f:
            json.dump(usernames, f)
        print("Generated usernames.json.")

generate_observations_list()
generate_usernames()

# Compute the transitions and trajectories for the interactive visualisation
if not(os.path.exists("Preprocessed_Dataset/observations.json") and os.path.exists("Preprocessed_Dataset/transitions_list.json") and "Preprocessed_Dataset/users_list.json"):
    location_point_preprocessing_and_export()
    trips_and_trajectory_preprocessing_and_export()

# Port of the interactive visualization (can be modified)
PORT = 8001
Handler = http.server.SimpleHTTPRequestHandler

# Opens the server and the interactive visualization
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    # then make a url variable
    url = "http://localhost:" + str(PORT) + "/Interactive_Visualisation/main.html"

    # then call the default open method described above
    webbrowser.open(url)

    httpd.serve_forever()