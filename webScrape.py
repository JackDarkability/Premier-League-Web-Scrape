import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd


def get_link(driver, base_url, competition, season, club="-1"):
    """Create full URL including relevant details and return beautifulsoup object"""

    # a country's league

    full_url = f"{base_url}{competition}&se={season['number']}&cl={club}"
    driver.get(full_url)
    time.sleep(2)
    logging.info(full_url)
    return BeautifulSoup(driver.page_source, "html.parser")


def get_all_season_data(driver, base_url, competition):
    """getting all the links for the seasons"""
    link = f"{base_url}{competition}"
    driver.get(link)
    logging.info(link)
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

    return season_data


def get_data(soup, driver, league, year, results_of_matches):
    """Get all mathes from season"""
    # Div class loader to know if still loading or no.

    html = driver.find_element(By.TAG_NAME,"html")

    # Scroll down page until all matches are loaded
    while True:
        html.send_keys(Keys.PAGE_DOWN)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        loader = soup.findAll(lambda tag: tag.name == 'div' and 
                'loader' in tag.get('class', []) and 
                'u-hide' not in tag.get('class', []))
        time.sleep(2)
        if not loader:
            break



    # Get all the matches
    all_match_days = soup.find_all("div", class_="fixtures__date-container")

    for match_day in all_match_days:
        date = match_day.find("time", class_="fixtures__date fixtures__date--long").text
        matches = match_day.find_all("li", class_="match-fixture")
        for match in matches:
            home_team = match.get("data-home")
            away_team = match.get("data-away")
            venue = match.get("data-venue")
            score_div = match.find("span", class_="match-fixture__score")
            score = (score_div.get_text()).strip()
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
                    "league": league,
                    "year": year["year"],
                    "date": date,
                }
            )

    return results_of_matches


def main():

    # Set up logging
    logging_level = logging.INFO
    logging_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=logging_level, format=logging_format)

    # Set up the web driver
    options = webdriver.ChromeOptions()
    #options.add_argument("headless")
    driver = webdriver.Chrome(options=options)

    # Example URL: https://www.premierleague.com/results?co=1&se=363&cl=-1
    # co = competition, 1 = Premier League
    # se = season, 363 = 2021-2022
    # cl = club, -1 = all clubs

    BASE_URL = "https://www.premierleague.com/results?co="
    COMPETITIONS = ["1"]  # Just premier league for now
    CLUBS = ["-1"]  # All clubs for now
    seasons = get_all_season_data(driver, BASE_URL, "1")

    for season in seasons:
        logging.info(season["year"] + " " + season["number"])

    results_of_matches = []
    season = seasons[0]
    for competition in COMPETITIONS:
        #for season in seasons:
            for club in CLUBS:
                logging.info('Testing for Club: %s, Competition: %s, Season: %s' % (club,competition,season))
                time.sleep(2)
                soup = get_link(driver, BASE_URL, competition, season, club)
                results_of_matches = get_data(
                    soup, driver, competition, season, results_of_matches
                )

                logging.info('Got data for Club: %s, Competition: %s, Season: %s' % (club,competition,season))
    
    # Convert all matches to a DataFrame
    all_matches_df = pd.DataFrame(results_of_matches)

    # Save to CSV, different encoding due to accented characters
    all_matches_df.to_csv("football_matches.csv", encoding="iso-8859-1", index=False)

    


if __name__ == "__main__":
    main()
