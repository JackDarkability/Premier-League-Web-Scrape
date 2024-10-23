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
import time
import pandas as pd

from helper_functions import get_full_link, initialise_dictionary, setup_driver
from data_collectors import get_all_season_data, get_detailed_match_data, get_matches_data
from elo_calculator import calculate_elo_and_save_to_file


def scrape_football_data(
    competitions=["1"], clubs=["-1"], output_file="football_matches.csv"
):
    """
    Scrape football match data from the Premier League website of the entered competition and season and save it to a CSV file.
    For clubs -1 means all clubs, otherwise use the club id from the website.
    """

    """
    Example URL: https://www.premierleague.com/results?co=1&se=363&cl=-1
    co = competition, 1 = Premier League
    se = season, 363 = 2021-2022
    cl = club, -1 = all clubs
    """

    BASE_URL = "https://www.premierleague.com/results?co="
    seasons = []
    for competition in competitions:
        # Set up only for 1 competition at the moment with premier league.
        seasons.extend(get_all_season_data(BASE_URL, competition))

    for season in seasons:
        logging.info(season["year"] + " " + season["number"])

    results_of_matches = []

    # Parallel processing
    with Pool(processes=1) as pool:
        tasks = []
        for season in seasons:
            for club in clubs:
                full_link = get_full_link(BASE_URL, season, club)
                tasks.append((full_link, season))

        for data in pool.starmap(get_matches_data, tasks):
            results_of_matches.extend(data)


    # Convert all matches to a DataFrame and change date to correct format
    all_matches_df = pd.DataFrame(results_of_matches)

    all_matches_df['date'] = pd.to_datetime(
        all_matches_df['date'], format="%A %d %B %Y"
    )

    # Save to CSV
    all_matches_df.to_csv(output_file, index=False)


def update_with_detailed_stats(results_of_matches):
    '''
    Get much more detailed match stats such as possession and attendance.
    Warning: Goes through every page individually, so will be VERY slow on large data files (such as every match ever in the premier league)
    '''
    driver = setup_driver()
    cookies_accepted = False
    for match in results_of_matches:
        # Dictionary

        detailed_stats = get_detailed_match_data(driver,match["match_id"], cookies_accepted)
        match_full_dictionary = initialise_dictionary(match)
        for key, value in detailed_stats.items():
            match_full_dictionary[key] = value

        match.update(match_full_dictionary)
        cookies_accepted = True
    
    all_matches_df = pd.DataFrame(results_of_matches)
    all_matches_df.to_csv("football_matches_with_ID_detailed.csv", index=False)

    return results_of_matches



if __name__ == "__main__":
    # Set up logging
    logging_level = logging.INFO
    logging_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=logging_level, format=logging_format)

    # Scrape data and calculate Elo ratings
    #scrape_football_data(clubs=["2"], output_file="aston_villa_matches_with_ID.csv")
    #calculate_elo_and_save_to_file("football_matches_with_ID.csv", "home_team", "away_team")
    
    df = pd.read_csv("aston_villa_matches_with_ID.csv")

    results_of_matches = df.to_dict("records")
    results_of_matches = update_with_detailed_stats(results_of_matches)
    results_of_matches.to_csv("aston_villa_matches_with_ID_detailed.csv", index=False)
    




'''
Possible improvements for the future:

- Go into each match collected and get who scored each goal, the kick off time, attendance, and the referee.  
Although would likely add a lot of time as would need to go into each match page so load 12000+ pages.
Could maybe be done in parallel but the internet connection would likely be what stops it as even with just seasons too many threads causes problems.

- Figure out what's causing the occasional error when scraping the data with too many threads, 
It makes the site not load and therefore seasons to be missed, but no exception is thrown so hard to debug.
Must be fixed if wanting to scrape individual match data as that would be even more pages to load and need more threads.

- If the team specified is not in the league for a given season, the code will still run but the data will just hold all the matches for that season. Should fix this

'''