from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
from requests.compat import urljoin
from datetime import datetime
import re


def game_data():
    xml_bs = "https://www.boardgamegeek.com/xmlapi2/thing?type=boardgame&stats=1&ratingcomments=1&page=1&pagesize=10&id="
    all_items = []
    for pg in range(1, 51):
        pg_items = []
        ct = 0
        soup_pg = browse_games(pg)
        pg_ids, pg_links = extract_game_ids(soup_pg)
        while len(pg_items) != 100:
            xml_fl = requests.get(f'{xml_bs}{",".join(pg_ids)}')
            soup_xml = BeautifulSoup(xml_fl.content, "xml")
            pg_items = extract_xml(soup_xml, pg_links)
            ct += 1
            if ct > 1:
                print(f"page number {pg} attempt number {ct}")
        all_items += pg_items
    return all_items


def extract_xml(soup, game_links):
    item_list = []
    items = soup.find_all("item")
    for idx, item in enumerate(items):
        item_list.append(extract_item(item, game_links[idx]))
    return item_list


def extract_item(game_item, game_url):
    game_dict = {"name": game_item.find("name")["value"], "game_id": game_item["id"]}
    values_int = [
        "yearpublished",
        "minplayers",
        "maxplayers",
        "playingtime",
        "minplaytime",
        "maxplaytime",
        "minage",
    ]
    for vals in values_int:
        game_dict[vals] = game_item.find(vals)["value"]
    link_categ = [
        "boardgamecategory",
        "boardgamemechanic",
        "boardgamefamily",
        "boardgameexpansion",
        "boardgameartist",
        "boardgamecompilation",
        "boardgameimplementation",
        "boardgamedesigner",
        "boardgamepublisher",
        "boardgameintegration",
    ]
    for categ in link_categ:
        game_dict[categ] = [
            x["value"] for x in game_item.find_all("link", {"type": categ})
        ]
    stats_float = ["average", "bayesaverage", "stddev", "median", "averageweight"]
    for stat in stats_float:
        game_dict[stat] = float(game_item.find(stat)["value"])
    stats_int = [
        "usersrated",
        "owned",
        "trading",
        "wanting",
        "wishing",
        "numcomments",
        "numweights",
    ]
    for stat in stats_int:
        game_dict[stat] = int(game_item.find(stat)["value"])
    for game_cat in game_item.find_all("rank"):
        cat_name = re.sub("\W", "", game_cat["friendlyname"])
        game_dict[cat_name] = int(game_cat["value"])

    return game_dict


def browse_games(page_num):
    bs_url = "https://boardgamegeek.com/browse/boardgame/page/"
    pg_url = f"{bs_url}{page_num}"
    pg = requests.get(pg_url)
    soup = BeautifulSoup(pg.content, "html.parser")
    return soup


def extract_game_ids(soup):
    bs_pg = "https://boardgamegeek.com/"
    all_games = soup.find_all("td", {"class": "collection_objectname"})
    game_ids = [x.find("a")["href"].split("/")[-2] for x in all_games]
    game_pages = [urljoin(bs_pg, x.find("a")["href"]) for x in all_games]
    return game_ids, game_pages


def export_csv(game_list: list):
    df = pd.DataFrame(game_list)
    df.to_csv(
        f"../../data/kaggle/{str(datetime.now().date())}_bgg_top{len(game_list)}.csv",
        index=False,
    )
    update_metadata(game_list)


def update_metadata(game_list: list):
    with open("../../data/kaggle/dataset-metadata.json", "rb") as f:
        meta_dict = json.load(f)
    meta_dict["resources"].append(
        {
            "path": f"{str(datetime.now().date())}_bgg_top{len(game_list)}.csv",
            "description": f"Board Game Geek top 2000 games on {str(datetime.now().date())}",
        }
    )
    with open("../../data/dataset-metadata_backup.json", "w") as fp:
        json.dump(meta_dict, fp)
    with open("../../data/kaggle/dataset-metadata.json", "w") as fp:
        json.dump(meta_dict, fp)


if __name__ == "__main__":
    game_items = game_data()
    export_csv(game_items)
    # print(5)
