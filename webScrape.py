import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from multiprocessing import Pool
import pandas as pd


def setup_driver():
    """Set up the web driver"""

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    return driver


def get_full_link(base_url, competition, season, club="-1"):
    """Create full URL including relevant details and return beautifulsoup object"""

    full_url = f"{base_url}{competition}&se={season['number']}&cl={club}"
    logging.debug(full_url)
    return full_url


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


def get_matches_data(full_link, league, year):
    """Get all the matches for a given season"""

    driver = setup_driver()
    driver.get(full_link)

    results_of_matches = []

    # Scroll until all matches are loaded
    soup = load_entire_page(driver)

    # Get all the divs that contain all matches for a given day
    all_match_days = soup.find_all("div", class_="fixtures__date-container")

    for match_day in all_match_days:
        date = match_day.find("time", class_="fixtures__date fixtures__date--long").text
        matches = match_day.find_all("li", class_="match-fixture")
        for match in matches:
            # Get the data for the individual match
            home_team = match.get("data-home")
            away_team = match.get("data-away")
            venue = match.get("data-venue")
            score_div = match.find("span", class_="match-fixture__score")
            score = (score_div.text).strip()
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
    driver.quit()

    return results_of_matches


def load_entire_page(driver):
    """Scroll down the page to load all matches"""

    html = driver.find_element(By.TAG_NAME, "html")
    html.send_keys(Keys.PAGE_DOWN)
    time.sleep(10)

    # Scroll down page until all matches are loaded
    while True:
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # If loader present then matches have not finished loading
        loader = soup.findAll(
            lambda tag: tag.name == "div"
            and "loader" in tag.get("class", [])
            and "u-hide" not in tag.get("class", [])
        )
        if not loader:
            logging.debug("No loader")
            break

    return soup


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
