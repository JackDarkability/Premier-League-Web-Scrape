""" Script that scrapes football match data from the Premier League website. 

Uses multiprocessing to scrape data for all seasons in parallel.
Saves data to the CSV file "football_matches.csv" with the following columns:

home_team
away_team
home_team_goals
away_team_goals
winner
loser
venue
league
year
date

"""
import logging
from multiprocessing import Pool
import pandas as pd

from helper_functions import get_full_link
from data_collectors import get_all_season_data, get_matches_data

def main():

    # Set up logging
    logging_level = logging.INFO
    logging_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=logging_level, format=logging_format)

    """
    Example URL: https://www.premierleague.com/results?co=1&se=363&cl=-1
    co = competition, 1 = Premier League
    se = season, 363 = 2021-2022
    cl = club, -1 = all clubs
    """

    BASE_URL = "https://www.premierleague.com/results?co="
    COMPETITIONS = ["1"]  # Just premier league for now
    CLUBS = ["-1"]  # All clubs for now
    seasons = get_all_season_data(
        BASE_URL, "1"
    )  # Only gets season data for premier league for now

    for season in seasons:
        logging.info(season["year"] + " " + season["number"])

    results_of_matches = []

    # Parallel processing
    with Pool(processes=2) as pool:
        tasks = []
        for competition in COMPETITIONS:
            for season in seasons:
                for club in CLUBS:
                    full_link = get_full_link(BASE_URL, competition, season, club)
                    tasks.append((full_link, competition, season))

        print(tasks)

        for data in pool.starmap(get_matches_data, tasks):
            results_of_matches.extend(data)

    # Convert all matches to a DataFrame
    all_matches_df = pd.DataFrame(results_of_matches)

    # Save to CSV, different encoding due to accented characters
    all_matches_df.to_csv("football_matches.csv", encoding="iso-8859-1", index=False)


if __name__ == "__main__":
    main()
