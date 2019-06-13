from bs4 import BeautifulSoup
import urllib.request
import json
import sys
from selenium import webdriver
from bs4 import BeautifulSoup
import time


def get_relay_times_rough_draft():
    """
        Input: a team_id, season, and gender used to uniquely identify a team
        Output: List of tuples containing swimmer names and IDs
    """
    swimmer_id = 389668
    players = {}
    # gets a list of (Name, swimmer_id) tuples and the team name for a given team_id
    url = "https://www.collegeswimming.com/results/119948/event/2/"
    browser = webdriver.Chrome()
    browser.get(url)
    browser.find_element_by_id('time20484192').click()
    time.sleep(1)
    soup = BeautifulSoup(browser.page_source, "html5lib")

    current_soup = soup.find("a", href="/swimmer/{}".format(swimmer_id))
    players[swimmer_id] = current_soup.text
    print(players[swimmer_id])
    table_soup = current_soup.find_parent('ol')
    print(table_soup)
    for swimmer in table_soup.select('a'):
        print(swimmer['href'].split('/')[2])

    table_body = current_soup.find_parent('td').find_next_sibling().find('div')
    print(table_body)
    browser.close()


get_relay_times_rough_draft()

