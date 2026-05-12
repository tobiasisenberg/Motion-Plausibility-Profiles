import pandas as pd
import pickle
import numpy as np
import os
import json
import math
from sklearn.preprocessing import RobustScaler, MinMaxScaler
import matplotlib.pyplot as plt

# Select what shape of data you want to precompute
preprocess_location_points = True #True
preprocess_trips = True

# List and return .csv files in a directory
def open_dataset(directory):
    list_files = []
    for element in os.scandir(directory):
        if element.name.endswith(".csv"):
            list_files.append(str(directory+"/"+element.name))
    if not list_files:
        print(f"No .csv file found in {directory} directory.") 
    return list_files

# Converts to a pandas dataframe iNaturalist files with required metrics
def open_file(path):
    df = pd.read_csv(path)
    if not {"id", "user_id", "user_login", "observed_on", "time_observed_at", "coordinates_obscured", "latitude", "longitude", "taxon_family_name"}.issubset(df.columns):
        print(f"{path} is not a valid file, it does not include the required columns")
        return None
    return df

# Takes a directory as input and preprocess location points in it
def location_point_preprocessing(directory: str) -> [dict, dict, list, list, list] :
    location_points = {} # Store and cluster observations by taxon_family_name (used for ML algorithms)
    location_points_id = {} # Store observation ids that are located at the same index than the id in location_points (used for ML algorithms) 
    users_dictionary = {} # Temporarily store the number of observations posted by every user_id (then converted to users_list)
    users_list = [] # List of every user_id, associated with its number of observations (converted to .json for interactive visualisation)
    species_list = [] # List of every taxon_family_name, associated with the list of every observation of this species (converted to .json for interactive visualisation)
    observations = [] # List of unobscured observations
    obscured_observations = [] # List of obscured observations

    list_files = open_dataset(directory)
    
    for file in list_files:
        df = open_file(file)
        if not df.empty:
            for uid, id, observed_on, time_observed_at, coordinates_obscured, latitude, longitude, taxon_family_name in zip(df["user_id"], df["id"], df["observed_on"], df["time_observed_at"], df["coordinates_obscured"], df["latitude"], df["longitude"], df["taxon_family_name"]):
                # Handle obscured coordinates
                is_obscured = False
                if pd.notna(coordinates_obscured):
                    if coordinates_obscured is True or str(coordinates_obscured).strip().lower() == "true":
                        is_obscured = True

                if is_obscured:
                    obscured_observations.append({
                        "user_id": uid,
                        "observation_id": id,
                        "date": observed_on,
                        "lat": None if pd.isna(latitude) else latitude,
                        "long": None if pd.isna(longitude) else longitude
                    })
                    continue
                
                observations.append({
                        "user_id": uid,
                        "observation_id": id,
                        "date": observed_on,
                        "lat": None if pd.isna(latitude) else latitude,
                        "long": None if pd.isna(longitude) else longitude
                })

                if uid in users_dictionary.keys():
                    users_dictionary[uid] += 1
                else:
                    users_dictionary[uid] = 1

                if taxon_family_name in location_points.keys():
                    location_points[taxon_family_name].append((id, latitude, longitude))
                    location_points_id[taxon_family_name].append(id) #Maybe would it be better to delete this dictionary later
                else:
                    location_points[taxon_family_name] = [(id, latitude, longitude)]
                    location_points_id[taxon_family_name] = [id]
    
    # Convert the dictionnaries into lists of dictionnaries for the .json conversion
    for user in users_dictionary.keys():
        users_list.append({"username": user, "nb_observations": users_dictionary[user]})
        
    # Sort the users list by number of unobscured observations descending
    users_list.sort(key=lambda x: x["nb_observations"], reverse=True)
    
    for species in location_points.keys():
        species_observations = []
        for observation in location_points[species]:
            species_observations.append({"id": observation[0], "lat": observation[1], "long": observation[2]})
        species_list.append({"taxon_family_name": species, "observations": species_observations})

    return location_points, location_points_id, users_list, species_list, obscured_observations, observations

# Calculate bearing between two points
def compute_bearing(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return math.atan2(x, y)

def normalize_trips_and_trajectories(trips, trajectories):
    # Normalize each parameter of a trip (speed, elapsed time, distance, acceleration, bearing change)
    trips = np.array(trips, dtype=object)
    trips_size = np.shape(trips)[0]

    speed_scaler = MinMaxScaler()
    elapsed_time_scaler = MinMaxScaler()
    distance_scaler = MinMaxScaler()
    acceleration_scaler = MinMaxScaler()
    bearing_change_scaler = MinMaxScaler()

    # Fit each scaler on every value and then normalize those values 
    trips[:,1] = speed_scaler.fit_transform(np.log1p(trips[:,1].astype(float)).reshape(-1,1)).reshape(trips_size,)
    trips[:,2] = elapsed_time_scaler.fit_transform(trips[:,2].reshape(-1,1)).reshape(trips_size,)
    trips[:,3] = distance_scaler.fit_transform(trips[:,3].reshape(-1,1)).reshape(trips_size,)
    trips[:,4] = acceleration_scaler.fit_transform(trips[:,4].reshape(-1,1)).reshape(trips_size,)
    trips[:,5] = bearing_change_scaler.fit_transform(trips[:,5].reshape(-1,1)).reshape(trips_size,)
    
    # Normalize the values stored in each trajectory
    for i in range(len(trajectories)):
        trajectory = np.array(trajectories[i], dtype=object)
        trajectory_size = np.shape(trajectory)[0]
        trajectory[:,1] = speed_scaler.transform(np.log1p(trajectory[:,1].astype(float)).reshape(-1,1)).reshape(trajectory_size,)
        trajectory[:,2] = elapsed_time_scaler.transform(trajectory[:,2].reshape(-1,1)).reshape(trajectory_size,)
        trajectory[:,3] = distance_scaler.transform(trajectory[:,3].reshape(-1,1)).reshape(trajectory_size,)
        trajectory[:,4] = acceleration_scaler.transform(trajectory[:,4].reshape(-1,1)).reshape(trajectory_size,)
        trajectory[:,5] = bearing_change_scaler.transform(trajectory[:,5].reshape(-1,1)).reshape(trajectory_size,)
        trajectories[i] = trajectory
    
    return trips, trajectories

def trips_and_trajectory_preprocessing():
    # Computes valid transitions and trajectories between valid observations
    trip_nb = 0 # Variable to determine the id of a trip
    trips = [] # List of every trips between valid observations in the database
    trips_id = [] # List of trip_id that correspond to the trip located at the same index in trips[], store in addition the ids of its observations
    transitions_list = [] # List of transitions for the interactive visualization

    trajectory_nb = 0 # Variable to determine the id of a trajectory
    trajectory = [] # Store temporarily a new trajectory at each iteration
    trajectories = [] # List of every valid trajectory in the dataset
    trajectories_id = [] # List of trajectory_id that correspond to the trajectory located at the same index in trajectories[], store in addition the id of its inner trips
    trajectories_list = [] # List of trajectories for the interactive visualization

    trajectory_user = {} # Dictionary that takes the trajectory_id and returns its corresponding user

    # We use data from the frequent-poster.log file that was generated by _inaturalist.py script
    if os.path.exists("frequent-poster.log"):
        with open("frequent-poster.log", "r") as f:
            trajectory_id = [trajectory_nb]
            prev_date = ""
            prev_user = ""
            prev_point = None

            for line in f:
                line = line.strip()
                if line.startswith("===="):
                    continue
                
                line_elements = []
                line_elements = line.split(",")

                if len(line_elements) == 2:
                    prev_user = line_elements[0]
                
                # For each first observation in a day
                if len(line_elements) == 6:
                    # Ignore the obscured observations
                    if line_elements[0].startswith("iN-o"):
                        continue
                    else:
                        if line_elements[3] != prev_date:
                            if trajectory != []:
                                # A trajectory should contain at least 2 trips (3 valid observations)
                                if len(trajectory) >= 2:
                                    trajectories.append(trajectory)
                                    trajectories_id.append(trajectory_id)
                                    trajectory_nb +=1
                                trajectory = []
                                trajectory_id = [trajectory_nb]
                            # We store informations so that we can identify a trajectory with the user id and the date    
                            trajectory_user[trajectory_nb] = (prev_user, prev_date)
                            prev_date = line_elements[3]
                        
                        obs_id = line_elements[0]
                        lat = float(line_elements[1])
                        lon = float(line_elements[2])
                        # Store as [ID, lat, lon, speed_ms, prev_bearing]
                        prev_point = [obs_id, lat, lon, 0.0, None]

                # For the other observations in a day        
                elif len(line_elements) == 8:
                    obs_id = line_elements[0]
                    # If the observation is unobscured
                    if prev_date == line_elements[3] and not obs_id.startswith("iN-o"):
                        lat = float(line_elements[1])
                        lon = float(line_elements[2])
                        elapsed_time = float(line_elements[5].replace("s", ""))
                        distance = float(line_elements[6].replace("m", ""))
                        speed_kmh = float(line_elements[7].replace("km/h", ""))
                        
                        # Handle sentinel value -1.0km/h for 0s elapsed time
                        if speed_kmh < 0:
                            speed_kmh = 0.0
                        
                        if prev_point is not None:
                            prev_id, prev_lat, prev_lon, prev_speed_ms, prev_bearing = prev_point
                            
                            speed_ms = speed_kmh / 3.6
                            acceleration = (speed_ms - prev_speed_ms) / elapsed_time if elapsed_time > 0 else 0.0
                            
                            current_bearing = compute_bearing(prev_lat, prev_lon, lat, lon)
                            if prev_bearing is None:
                                bearing_change = 0.0
                            else:
                                bearing_change = current_bearing - prev_bearing
                                # Normalize bearing change to be between -pi and pi
                                bearing_change = (bearing_change + math.pi) % (2 * math.pi) - math.pi
                            
                            # TrajectoryPoint: [trip_id, speed, time, distance, acceleration, bearing_change, date, user_id]
                            trip = [trip_nb, speed_kmh, elapsed_time, distance, acceleration, bearing_change, prev_date, prev_user]
                            trips.append(trip)
                            trips_id.append((trip_nb, prev_id, obs_id))

                            trajectory.append(trip)
                            trajectory_id.append(trip_nb)
                            trip_nb += 1
                            
                            # Update prev point for next iteration (pass current_bearing onwards)
                            prev_point = [obs_id, lat, lon, speed_ms, current_bearing]

            # Add the last sequence if any
            if trajectory != []:
                if len(trajectory) >= 2:
                    trajectories.append(trajectory)
                    trajectories_id.append(trajectory_id)

        f.close()

        # Before normalizing data for ML algorithms, we save the original values for the interactive visualisation
        for i in range(len(trips)):
            transitions_list.append({"transition_id": trips[i][0], "user_id": trips[i][7], "observation_id1": trips_id[i][1], "observation_id2": trips_id[i][2], "date": trips[i][6], "speed": trips[i][1], "elapsed_time": trips[i][2], "distance": trips[i][3], "acceleration": trips[i][4], "bearing_change": trips[i][5]})
        for t in range(len(trajectories)):
            trajectories_list.append({"trajectory_id": trajectories_id[t][0], "user_id": trajectories[t][0][7], "date": trajectories[t][0][6], "transitions": trajectories_id[t][1:]})

        # Normalize every parameter in trips and trajectories
        trips, trajectories = normalize_trips_and_trajectories(trips, trajectories)

        
    return trips, trips_id, transitions_list, trajectories, trajectories_id, trajectories_list

def location_point_preprocessing_and_export():
    location_points, location_id, users_list, species_list, obscured_observations, observations = location_point_preprocessing("Observations/")
    # Export data made for ML algorithms in .pkl format
    with open('Preprocessed_Dataset/location_points.pkl', 'wb') as f:
        pickle.dump(location_points, f)
    with open('Preprocessed_Dataset/location_points_id.pkl', 'wb') as f:
        pickle.dump(location_id, f)

    # Export data made for Interactive Visualization in .json format
    with open("Preprocessed_Dataset/users_list.json", "w") as f:
        f.write(json.dumps(users_list, indent=4))
    with open("Preprocessed_Dataset/species_list.json", "w") as f:
        f.write(json.dumps(species_list, indent=4))
    with open("Preprocessed_Dataset/obscured_observations.json", "w") as f:
        f.write(json.dumps(obscured_observations, indent=4))
    with open("Preprocessed_Dataset/observations.json", "w") as f:
        f.write(json.dumps(observations, indent=4))

def trips_and_trajectory_preprocessing_and_export():
    trips, trips_id, transitions_list, trajectories, trajectories_id, trajectories_list = trips_and_trajectory_preprocessing()
    
    # CREATE A FUNCTION TO AUTOMATE THE PLOTS CALCULATION
    '''plt.hist(trips[:, 1], bins=50, range=(0,1), edgecolor='black')
    plt.title("Distribution of Normalized Speed")
    plt.xlabel("Normalized Speed")
    plt.ylabel("Frequency")
    plt.show()'''
    # END OF THE FUNCTION

    # Convert data made for ML algorithms in .pkl format
    with open('Preprocessed_Dataset/trips.pkl', 'wb') as f:
        pickle.dump(trips, f)
    with open('Preprocessed_Dataset/trips_id.pkl', 'wb') as f:
        pickle.dump(trips_id, f)
    
    with open('Preprocessed_Dataset/trajectories.pkl', 'wb') as f:
        pickle.dump(trajectories, f)
    with open('Preprocessed_Dataset/trajectories_id.pkl', 'wb') as f:
        pickle.dump(trajectories_id, f)

    # Convert data made for Interactive Visualization in .json format
    with open("Preprocessed_Dataset/transitions_list.json", "w") as f:
        f.write(json.dumps(transitions_list, indent=4))
    with open("Preprocessed_Dataset/trajectories_list.json", "w") as f:
        f.write(json.dumps(trajectories_list, indent=4))

if preprocess_location_points:
    location_point_preprocessing_and_export()
if preprocess_trips:
    trips_and_trajectory_preprocessing_and_export()