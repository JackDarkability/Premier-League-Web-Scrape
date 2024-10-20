""" ELO calculator

This script calculates Elo ratings for each match in the CSV file 
and saves the updated Elo ratings to the given files. Only works with 1 vs 1 matches.

"""

import pandas as pd


def calculate_elo_and_save_to_file(
    input_excel_file,
    person_1_column_name,
    person_2_column_name,
    output_file_name_with_elos_next_to_matches="all_matches_with_elo.csv",
    output_file_name_peak_elo="teams_peak_elo.csv",
    output_file_name_current_elo="teams_current_elo.csv",
    initial_elo=1000,
    k_factor=120,
):
    """
    Calculate Elo ratings for each match in the CSV file and save the updated Elo ratings to:
    - a new CSV file with Elo ratings next to each match
    - a new CSV file with the peak Elo ratings for each team
    - a new CSV file with the current Elo ratings for each team
    """
    # Load the CSV
    matches_not_sorted = pd.read_csv(input_excel_file, index_col=0)
    matches = matches_not_sorted.reset_index()

    # Save the updated Elo ratings to a new CSV file
    matches, elo_ratings, elo_peak_ratings = calculate_all_elos(
        matches, person_1_column_name, person_2_column_name, initial_elo, k_factor
    )

    save_elos_to_file(
        matches,
        elo_peak_ratings,
        elo_ratings,
        output_file_name_with_elos_next_to_matches,
        output_file_name_peak_elo,
        output_file_name_current_elo,
    )


def expected_score(elo_a, elo_b):
    """Calculate expected score for a match between two players with respect to ELO"""
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def calculate_new_elo(winner_elo, loser_elo, k_factor):
    """Calculate the new Elo ratings for the winner and loser based on who won"""
    expected_win = expected_score(winner_elo, loser_elo)
    new_winner_elo = winner_elo + k_factor * (1 - expected_win)
    new_loser_elo = loser_elo + k_factor * (0 - (1 - expected_win))
    return round(new_winner_elo, 2), round(new_loser_elo, 2)


# Function to calculate Elo ratings for all matches
def calculate_all_elos(
    data_frame, person_1_column_name, person_2_column_name, initial_elo, k_factor
):
    """Go through data frame and calculate Elo ratings for each match"""
    # Sort with the most recent at the bottom
    matches = matches.sort_index(ascending=False)

    # Initialize Elo ratings
    elo_ratings_data_frame = {}
    elo_peak_ratings_data_frame = {}

    # Add columns for Elo ratings
    data_frame[person_1_column_name + "_elo_start"] = 0
    data_frame[person_2_column_name + "_elo_start"] = 0
    data_frame[person_1_column_name + "_elo_end"] = 0
    data_frame[person_2_column_name + "_elo_end"] = 0

    # Calculate Elo ratings for each match
    for index, row in data_frame.iterrows():
        person_1 = row[person_1_column_name]
        person_2 = row[person_2_column_name]

        # Initialize Elo ratings if fighters are encountered for the first time
        if person_1 not in elo_ratings_data_frame:
            elo_ratings_data_frame[person_1], elo_peak_ratings_data_frame[person_1] = (
                initial_elo,
                initial_elo,
            )

        if person_2 not in elo_ratings_data_frame:
            elo_ratings_data_frame[person_2], elo_peak_ratings_data_frame[person_2] = (
                initial_elo,
                initial_elo,
            )

        # Get starting Elo ratings
        person_1_elo_start = elo_ratings_data_frame[person_1]
        person_2_elo_start = elo_ratings_data_frame[person_2]

        # Record starting Elo ratings
        data_frame.at[index, person_1_column_name + "_elo_start"] = person_1_elo_start
        data_frame.at[index, person_2_column_name + "_elo_start"] = person_2_elo_start

        # Update Elo based on the result
        if row["winner"] == person_1:  # Team 1 wins
            new_person_1_elo, new_person_2_elo = calculate_new_elo(
                person_1_elo_start, person_2_elo_start, k_factor
            )
        elif row["winner"] == person_2:  # Team 2 wins
            new_person_2_elo, new_person_1_elo = calculate_new_elo(
                person_2_elo_start, person_1_elo_start, k_factor
            )

        elif row["winner"] == "draw":  # Draw
            new_person_1_elo, new_person_2_elo = calculate_new_elo(
                person_1_elo_start, person_2_elo_start, k_factor / 2
            )
        else:  # Something went wrong, ignore
            print("Error on index: ", index)
            new_person_1_elo, new_person_2_elo = person_1_elo_start, person_2_elo_start

        # Record updated Elo ratings
        data_frame.at[index, person_1_column_name + "_elo_end"] = new_person_1_elo
        data_frame.at[index, person_2_column_name + "_elo_end"] = new_person_2_elo

        # Update Elo ratings in the dictionary
        elo_ratings_data_frame[person_1] = new_person_1_elo
        elo_ratings_data_frame[person_2] = new_person_2_elo

        if elo_ratings_data_frame[person_1] > elo_peak_ratings_data_frame[person_1]:
            elo_peak_ratings_data_frame[person_1] = elo_ratings_data_frame[person_1]

        if elo_ratings_data_frame[person_2] > elo_peak_ratings_data_frame[person_2]:
            elo_peak_ratings_data_frame[person_2] = elo_ratings_data_frame[person_2]

    return data_frame, elo_ratings_data_frame, elo_peak_ratings_data_frame


def save_elos_to_file(
    data_frame,
    peak_elos,
    elos,
    output_file_name_with_elos_next_to_matches,
    output_file_name_peak_elo,
    output_file_name_current_elo,
):
    """Save the updated Elo ratings to a CSV file along with the peaks and currents"""

    data_frame.to_csv(output_file_name_with_elos_next_to_matches, index=False)
    teams_peak_elo = sorted(peak_elos.items(), key=lambda x: x[1], reverse=True)

    teams_peak_elos_df = pd.DataFrame(teams_peak_elo, columns=["Person", "Elo Rating"])
    teams_peak_elos_df.to_csv(output_file_name_peak_elo, index=False)

    teams_current_elo = sorted(elos.items(), key=lambda x: x[1], reverse=True)
    teams_current_elos_df = pd.DataFrame(
        teams_current_elo, columns=["Person", "Elo Rating"]
    )
    teams_current_elos_df.to_csv(output_file_name_current_elo, index=False)
