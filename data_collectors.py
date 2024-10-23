""" Module that holds all of the functions that scrape data from the website

get_all_season_data: Get all the seasons for a given competition (where competition is an ID number)
get_matches_data: Get all the matches from a premier league webpage of a season

"""

import time
import logging

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from helper_functions import setup_driver, load_entire_page


def get_all_season_data(base_url, competition):
    """Getting all the ids and years for the seasons"""

    logging.info(f"Getting all seasons for competition {competition}")
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
        season_data.append(
            {"number": id_of_season, "year": year_of_season, "competition": competition}
        )

    driver.quit()

    return season_data


def get_matches_data(full_link, year):
    """Get all the matches from a premier league link"""

    # logging.info(
    print(
        f"Getting all matches for competition {year['competition']} and season {year['year']}"
    )
    driver = setup_driver()
    driver.get(full_link)
    # Scroll until all matches are loaded
    soup = load_entire_page(driver)

    # Get all the divs that contain all matches for a given day
    all_match_days = soup.find_all("div", class_="fixtures__date-container")

    results_of_matches = []

    for match_day in all_match_days:
        date = match_day.find("time", class_="fixtures__date fixtures__date--long").text
        matches = match_day.find_all(
            "li", class_="match-fixture"
        )  # List of matches for a given day

        for match in matches:
            # Get the data for the individual match
            # ID Can be used later for link to specific match
            match_id = match.get(
                "data-comp-match-item"
            )  
            home_team = match.get("data-home")
            away_team = match.get("data-away")
            venue = match.get("data-venue")
            score_span = match.find("span", class_="match-fixture__score")
            score = score_span.text.strip()
            home_team_goals, away_team_goals = score.split("-")

            # Decide winner and loser
            if home_team_goals > away_team_goals:
                winner = home_team
                loser = away_team
            elif home_team_goals < away_team_goals:
                winner = away_team
                loser = home_team
            else:
                winner = "draw"
                loser = "draw"

            # Save as dictionary to list of matches
            results_of_matches.append(
                {
                    "match_id": match_id,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_team_goals": home_team_goals,
                    "away_team_goals": away_team_goals,
                    "winner": winner,
                    "loser": loser,
                    "venue": venue,
                    "league": year["competition"],
                    "year": year["year"],
                    "date": date,
                }
            )

    driver.quit()
    # logging.info(
    print(
        f"Finished getting all matches for competition {year['competition']} and season {year['year']}"
    )

    return results_of_matches


def get_detailed_match_data(driver, match_id, cookies_accepted=False):
    """
    Get data only available from the actual match page
    It is VERY slow to get all the data for all matches, so only use this for excel files with a few matches
    """

    print(f"Getting detailed match data for match {match_id}")
    driver.get(f"https://www.premierleague.com/match/{match_id}")

    # Wait for the tablist to be visible
    tablist = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tablist"))
    )
    time.sleep(1)
    if not cookies_accepted:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )
            cookies_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")

            # Click the accept cookies button
            cookies_button.click()

        except:
            print("cookies fine")
    
    # Locate the "Stats" tab by its data-tab-index or class "active"
    stats_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//ul[@class='tablist']//li[@data-tab-index='2']"))
    )   
    stats_tab.click()

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "higher"))
        )
    except:
        print("Timed out waiting for page to load.")
        driver.quit()
        return None
    

    
    soup = BeautifulSoup(driver.page_source, "html.parser")

    match_summary_information = soup.find_all("div", class_="mc-summary__info")
    # For some there isn't an attendance, like match 93551
    match_attendance = "N/A"
    match_referee = "N/A"

    try:
        match_attendance = match_summary_information[2].text.strip()
        match_referee = match_summary_information[3].text.strip()

        match_attendance = match_attendance.split(": ")[1].strip()
        match_referee = match_referee.split(": ")[1].strip()

    except:
        pass

    # Get stats of match like possession etc.
    big_div = soup.find("div", {"data-ui-tab": "Match Stats", "class": ["mcStatsTab", "statsSection", "season-so-far", "wrapper", "col-12"]})
    stats = big_div.find("tbody", class_="matchCentreStatsContainer")

    separated_stats = stats.find_all("tr")
    match_stats = {'attendance': match_attendance, 'referee': match_referee}

    for stat in separated_stats:
        stat_elements = stat.find_all("p")

        category = stat_elements[1].text.strip() # Category
        category = category.replace(" ", "_").lower()
    
        home_stat = stat_elements[0].text.strip() # Home team stat
        away_stat = stat_elements[2].text.strip() # Away team stat

        match_stats[category+"_home"] = home_stat
        match_stats[category+"_away"] = away_stat
    
    return match_stats


    




