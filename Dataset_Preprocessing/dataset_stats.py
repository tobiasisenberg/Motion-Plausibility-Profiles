import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import csv
import powerlaw

# Select what metrics you want to compute
compute_most_active_users = True
compute_count_valid_sequences = True
compute_plot_speed_distribution = True

#########################################################
# Return the list of the most active users in the dataset
#########################################################
def most_active_users():
    familyFiles = [ "droseraceae", "nepenthaceae", "sarraceniaceae", "roridulaceae", "byblidaceae", "lentibulariaceae", "cephalotaceae", "drosophyllaceae" ]
    usersList = []
    usersContributions = {}

    for file in familyFiles:
        path = "Observations/" + file + ".csv"
        df = pd.read_csv(path)
        for login, uid in zip(df["user_login"], df["user_id"]):
            user_key = f"{uid}-{login}"
            if user_key not in usersList:
                usersList.append(user_key)
                usersContributions[user_key] = 1
            else:
                usersContributions[user_key] += 1

    dsc = [(k, v) for k, v in sorted(usersContributions.items(), key=lambda item: item[1], reverse=True)]
    return dsc


#######################################################################
# Computes the number of valid sequences of observations in the dataset
#######################################################################
def count_valid_sequences():
    # A valid sequence is a sequence of unobscured observations that were posted by the same user, the same day.
    
    valid_sequences_count = 0
    sequence_length_distribution = {}

    current_day = None
    unobscured_obs_in_day = 0

    if os.path.exists("frequent-poster.log"):
        with open("frequent-poster.log", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("==="):
                    continue
                if "active from" in line:
                    if unobscured_obs_in_day > 2:
                        valid_sequences_count += 1
                        sequence_length_distribution[unobscured_obs_in_day] = sequence_length_distribution.get(unobscured_obs_in_day, 0) + 1
                    current_day = None
                    unobscured_obs_in_day = 0
                    continue
                
                parts = line.split(",")
                if len(parts) >= 4:
                    obs_id = parts[0].strip()
                    date = parts[3].strip()
                    
                    is_obscured = obs_id.startswith("iN-o")
                    
                    if date != current_day:
                        if unobscured_obs_in_day > 2:
                            valid_sequences_count += 1
                            sequence_length_distribution[unobscured_obs_in_day] = sequence_length_distribution.get(unobscured_obs_in_day, 0) + 1
                        current_day = date
                        unobscured_obs_in_day = 0
                    
                    if not is_obscured:
                        unobscured_obs_in_day += 1
        f.close()

        # Check the last day processed
        if unobscured_obs_in_day > 2:
            valid_sequences_count += 1
            sequence_length_distribution[unobscured_obs_in_day] = sequence_length_distribution.get(unobscured_obs_in_day, 0) + 1

        print(f"Number of valid sequences (days with > 2 unobscured observations): {valid_sequences_count}")
        print("Distribution of valid observations per valid sequence:")
        length_list = []
        for length in sorted(sequence_length_distribution.keys()):
            print(f"  {length} observations: {sequence_length_distribution[length]} sequences")
            length_list.append(sequence_length_distribution[length])

        sizes_arr = np.array(sorted(sequence_length_distribution.keys()))
        length_arr = np.array(length_list)
        total_valid_observations = np.sum(sizes_arr * length_arr)
        average_length = total_valid_observations / valid_sequences_count
        print(f"Average length of a valid sequence: {average_length:.2f} observations")

        # Create a plot to visualize valid observations sequences length
        plt.plot(sizes_arr, length_arr)
        plt.yscale('log')
        plt.xlabel('Number of valid observations')
        plt.ylabel('Number of sequences (log scale)')
        plt.title('Distribution of Valid Observation Sequences')
        plt.grid(True, which="both", ls="-", alpha=0.5)
        plt.savefig('vis/0_sequences_length.png')
    else:
        print("frequent-poster.log not found.")


#######################################################################################
# Shows how the speeds and distances between points in a valid sequence are distributed
#######################################################################################
def plot_speed_distribution():
    speeds = []
    distances = []
    with open("frequent-poster.log", "r") as f:
        for line in f:
            parts = line.strip().split(", ")
            if len(parts) == 8 and parts[7].endswith("km/h"):
                try:
                    speed = float(parts[7].replace("km/h", ""))
                    distance = float(parts[6].replace("m", ""))
                    # Filter strictly positive values (powerlaw needs values > 0)
                    if speed > 0: 
                        speeds.append(speed)
                    if distance > 0:
                        distances.append(distance)
                except ValueError:
                    pass
    f.close()

    print(f"Found {len(speeds)} strictly positive speed measurements.")
    speeds_arr = np.array(speeds)
    clean_speeds = speeds_arr[(speeds_arr>0.3)]

    if len(speeds) > 0:
        fit_speed = powerlaw.Fit(clean_speeds)
        fit_distance = powerlaw.Fit(distances)
        print(f"Power law alpha_speed: {fit_speed.power_law.alpha}")
        print(f"Power law xmin_speed: {fit_speed.power_law.xmin}")
        print(f"Power law alpha_distance: {fit_distance.power_law.alpha}")
        print(f"Power law xmin_distance: {fit_distance.power_law.xmin}")

        # Pit the power law directly against the log-normal distribution
        R_speed, p_speed = fit_speed.distribution_compare('power_law', 'lognormal')
        R_distance, p_distance = fit_distance.distribution_compare('power_law', 'lognormal')

        print(f"Log-likelihood ratio (R_speed): {R_speed}")
        print(f"p-value_speed: {p_speed}")
        print(f"Log-likelihood ratio (R_distance): {R_distance}")
        print(f"p-value_distance: {p_distance}")
        
        print(f"Lognormal mu distance: {fit_distance.lognormal.mu}")
        print(f"Lognormal sigma distance: {fit_distance.lognormal.sigma}")
        
        os.makedirs('vis', exist_ok=True)
        
        # -- SPEED PLOT --
        plt.figure(figsize=(10, 6))
        fit_speed.plot_pdf(color='b', linewidth=2, label='Empirical Data (pdf)')
        fit_speed.power_law.plot_pdf(color='r', linestyle='--', label=f'Power Law Fit (alpha={fit_speed.power_law.alpha:.2f})')
        plt.title('Distribution of Speeds (Log-Log scale)')
        plt.xlabel('Speed (km/h)')
        plt.ylabel('P(Speed)')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig('vis/0_speed_powerlaw_distribution.png', bbox_inches='tight')
        plt.close()
        print("Saved plot to vis/0_speed_powerlaw_distribution.png")

        # -- DISTANCE PLOT --
        plt.figure(figsize=(10, 6))
        fit_distance.plot_pdf(color='b', linewidth=2, label='Empirical Data (pdf)')
        fit_distance.power_law.plot_pdf(color='r', linestyle='--', label=f'Power Law Fit (alpha={fit_distance.power_law.alpha:.2f})')
        fit_distance.lognormal.plot_pdf(color='g', linestyle='-.', label=f'Log-Normal Fit (mu={fit_distance.lognormal.mu:.2f}, sigma={fit_distance.lognormal.sigma:.2f})')
        plt.title('Distribution of Distances (Log-Log scale)')
        plt.xlabel('Distance (m)')
        plt.ylabel('P(Distance)')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig('vis/0_distance_powerlaw_distribution.png', bbox_inches='tight')
        plt.close()
        print("Saved plot to vis/0_distance_powerlaw_distribution.png")

        # Your parameters
        alpha_speed = fit_speed.power_law.alpha
        x_min_speed = fit_speed.power_law.xmin
        alpha_distance = fit_distance.power_law.alpha
        x_min_distance = fit_distance.power_law.xmin

        # Generate data points
        # We use np.linspace for linear scale, or np.logspace for a smoother log plot
        x_speed = np.linspace(x_min_speed, x_min_speed * 10, 1000)
        x_distance = np.linspace(x_min_distance, x_min_distance * 10, 1000)

        # The Power Law PDF Formula
        # y = ((alpha - 1) / x_min) * (x / x_min)**(-alpha)
        y = ((alpha_speed - 1) / x_min_speed) * (x_speed / x_min_speed)**(-alpha_speed)
        y_distance = ((alpha_distance - 1) / x_min_distance) * (x_distance / x_min_distance)**(-alpha_distance)

        # Create the figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Plot 1: Linear Scale (The "Long Tail")
        ax1.plot(x_speed, y, color='tab:blue', lw=2)

        ax1.set_title(f"Linear Scale ($alpha$={alpha_speed})")
        ax1.set_xlabel("x")
        ax1.set_ylabel("P(x)")
        ax1.grid(True, alpha=0.3)

        # Plot 2: Log-Log Scale (The "Straight Line")
        ax2.loglog(x_speed, y, color='tab:red', lw=2)
        ax2.set_title(f"Log-Log Scale (Slope = -{alpha_speed})")
        ax2.set_xlabel("x (log)")
        ax2.set_ylabel("P(x) (log)")
        ax2.grid(True, which="both", ls="-", alpha=0.2)

        plt.tight_layout()
        plt.savefig('vis/0_speed_powerlaw_nolog.png')

    else:
        print("No valid speed data found.")


if compute_most_active_users:
    most_active_users()
if compute_count_valid_sequences:
    count_valid_sequences()
if compute_plot_speed_distribution:
    plot_speed_distribution()