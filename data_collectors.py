""" Module that holds all of the functions that scrape data from the website

get_all_season_data: Get all the seasons for a given competition (where competition is an ID number)
get_matches_data: Get all the matches from a premier league webpage of a season

"""

import time
import logging

from bs4 import BeautifulSoup

from helper_functions import setup_driver, load_entire_page

def get_all_season_data(base_url, competition):
    """Getting all the ids and years for the seasons"""
    link = f"{base_url}{competition}"
    # Set up the web driver
    driver = setup_driver()

    driver.get(link)
    logging.debug(link)

    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    seasons_drop_down = soup.find(
        "div", {"data-dropdown-block": "compSeasons", "class": "dropDown active"}
    )
    seasons = seasons_drop_down.find_all("li")
    season_data = []
    for season in seasons:
        id_of_season = season.get(
            "data-option-id"
        )  # A number to identify the season in the URL
        year_of_season = season.text.strip()  # Like "2021/2022"
        season_data.append({"number": id_of_season, "year": year_of_season})

    driver.quit()

    return season_data


def get_matches_data(full_link, competition, year):
    """Get all the matches from a premier league link"""

    driver = setup_driver()
    driver.get(full_link)
    # Scroll until all matches are loaded
    soup = load_entire_page(driver)

    # Get all the divs that contain all matches for a given day
    all_match_days = soup.find_all("div", class_="fixtures__date-container")

    results_of_matches = []

    for match_day in all_match_days:
        date = match_day.find("time", class_="fixtures__date fixtures__date--long").text
        matches = match_day.find_all("li", class_="match-fixture") # List of matches for a given day
        for match in matches:
            # Get the data for the individual match
            home_team = match.get("data-home")
            away_team = match.get("data-away")
            venue = match.get("data-venue")
            score_span = match.find("span", class_="match-fixture__score")
            score = score_span.text.strip()
            home_team_goals, away_team_goals = score.split("-")

            if home_team_goals > away_team_goals:
                winner = home_team
                loser = away_team
            elif home_team_goals < away_team_goals:
                winner = away_team
                loser = home_team
            else:
                winner = "draw"
                loser = "draw"

            results_of_matches.append(
                {
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_team_goals": home_team_goals,
                    "away_team_goals": away_team_goals,
                    "winner": winner,
                    "loser": loser,
                    "venue": venue,
                    "league": competition,
                    "year": year["year"],
                    "date": date,
                }
            )
    driver.quit()

    return results_of_matches