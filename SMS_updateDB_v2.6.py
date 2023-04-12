import pyodbc
import pandas as pd
import numpy as np
import regex as re
import ast
import os
import datetime
import time
import json
import warnings
warnings.filterwarnings('ignore', 'This pattern is interpreted as a regular expression, and has match groups.')

def parse_direct_pattern():
    """
    Parse direct pattern and return as regex pattern
    """
    data = read_json()
    direct_regex_pattern = []
    for i in data:
        if "pattern" in i and "replaced" in i:
            pattern_direct = "(.|\n)*" + i["pattern"] + "[^-].*?" + "(\d{4,8})" + "(.|\n)*"
            replaced = i["replaced"].replace("%code%", "\\2")
            direct_regex_pattern.append(
                {"pattern": pattern_direct, "replaced": replaced, "handle": False, "direct_pattern_count": 0}
            )
    #print(direct_regex_pattern)
    return direct_regex_pattern


def parse_pattern():
    """
    Parse pattern and return as regex pattern
    """
    data = read_json()
    regex_pattern = []

    for i in data:
        if "pattern_to_be_replaced" in i and "replaced_pattern" in i:
            regex_to_be_replaced = re.escape(i["pattern_to_be_replaced"])
            regex_to_be_replaced = (
                regex_to_be_replaced
                .replace("%code%", "([0-9]{4,8})")
                .replace("\\ ", "\s")
            )
            
            regex_placed = (
                i["replaced_pattern"]
                .replace("%code%", "\\1")
            )
            
            regex_pattern.append(
                {
                    "regex_to_be_replaced": regex_to_be_replaced,
                    "regex_placed": regex_placed,
                }
            )
    # print(regex_pattern)        
    return regex_pattern


def search_and_replace_loop(mdb):
    # Set up DB info
    # default_MDB = "./SMS.mdb"
    # mdb = input("Please enter SMS.mdb path: ") or default_MDB
    drv = "{Microsoft Access Driver (*.mdb, *.accdb)}"
    pwd = "gd2013"

    # Connect to DB
    con = pyodbc.connect("DRIVER={};DBQ={};PWD={}".format(drv, mdb, pwd))
    cur = con.cursor()

    # Create dict of pattern
    regex_pattern_list = parse_pattern()

    # Create dict of direct pattern
    pattern_replace_list = parse_direct_pattern()
    

    print(str(datetime.datetime.now()))
    # Query DB
    SQL = "SELECT * FROM L_SMS ORDER BY id"
    cur.execute(SQL)
    all_tuple = cur.fetchall()
    desc = cur.description

    # Read into dataframe
    # print(f"Read database: {mdb} infomation")
    df_column = pd.DataFrame(desc)
    all_list = [list(i) for i in all_tuple]
    df = pd.DataFrame(all_list, columns=df_column[0])
    
    # Create dict of pattern
    for idx, x in enumerate(regex_pattern_list):
        x["id"] = idx            
        x["pattern_count"] = (
            df["content"]
            .str.contains(r"^{}".format(x["regex_to_be_replaced"]))
            .sum()
        )
    
    # Start to find and replace pattern
    # print(f"current pattern dict: {regex_pattern_list}")
    # print("start to find pattern")
    for x in regex_pattern_list:
        # print(x['regex_to_be_replaced'])            
        if x["pattern_count"] > 0:
            print(
                f"Found pattern: '{x['regex_to_be_replaced']}', Start replacing with '{x['regex_placed']}', count: {x['pattern_count']}..."
            )
            matched_pattern = r"{}".format(x["regex_to_be_replaced"])
            placed_pattern = r"{}".format(x["regex_placed"])
            print(f"matched_pattern: {matched_pattern}")
            print(f"placed_pattern: {placed_pattern}")
            df["content"] = df["content"].str.replace(
                matched_pattern, placed_pattern, regex=True
            )

            # Write into database
            print(f"Write updated text into database: {mdb}")
            df_dict = df.to_dict()
            id_list = []
            content_list = []

            for k, v in df_dict["id"].items():
                id_list.append(v)

            for k, v in df_dict["content"].items():
                content_list.append(v)

            for id, content in zip(id_list, content_list):
                cur.execute(
                    "UPDATE L_SMS SET content = ? WHERE id = ?", content, id
                )

            con.commit()  # commit to database
            print("Normal pattern find and replace done!")
            # cur.close()
            # con.close()
        


    # print(direct_pattern["direct_pattern_count"])
    # print(f"pattern_replace_list: {pattern_replace_list}")
    for idx, direct_pattern in enumerate(pattern_replace_list):
        pattern = r"{}".format(direct_pattern['pattern'])
        direct_pattern["direct_pattern_count"] = (
        df["content"].str.contains(pattern).sum()
        )
        # print(direct_pattern)
        # print(df["content"][3781])
        # print(df["content"].str.contains(r"^{}".format(direct_pattern["pattern"])).sum())
    
    # Start to find and replace direct pattern
    # print(f"current direct dict: {pattern_replace_list}")
    # print("start to find direct pattern")

    for direct_pattern in pattern_replace_list:            
        # print(direct_pattern)            
        if direct_pattern["direct_pattern_count"] > 0 and direct_pattern['handle'] == False:
            print(
                f"Found pattern: '{direct_pattern['pattern']}', Start replacing with '{direct_pattern['replaced']}', count: {direct_pattern['direct_pattern_count']}..."
            )
            matched_pattern = r"{}".format(direct_pattern["pattern"])
            placed_pattern = r"{}".format(direct_pattern["replaced"])
            print(f"matched_pattern: {matched_pattern}")
            print(f"placed_pattern: {placed_pattern}")
            df["content"] = df["content"].str.replace(
                matched_pattern, placed_pattern, regex=True
            )

            # Write into database
            print(f"Write updated text into database: {mdb}")
            df_dict = df.to_dict()
            id_list = []
            content_list = []

            for k, v in df_dict["id"].items():
                id_list.append(v)

            for k, v in df_dict["content"].items():
                content_list.append(v)

            for id, content in zip(id_list, content_list):
                cur.execute(
                    "UPDATE L_SMS SET content = ? WHERE id = ?", content, id
                )

            con.commit()  # commit to database
            print("Direct pattern find and replace done!")
            direct_pattern['handle'] = True
    cur.close()
    con.close()


def read_json():
    with open("pattern.json", "r", encoding="utf8") as json_file:
        return json.load(json_file)


def write_json(data):
    with open("pattern.json", "w", encoding="utf-8") as json_file:
        json_file.write(json.dumps(data, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    default_MDB = "./SMS.mdb"
    mdb = input("Please enter SMS.mdb path: ") or default_MDB
    while True:
        search_and_replace_loop(mdb)
        time.sleep(10)
