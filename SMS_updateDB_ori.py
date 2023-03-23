import pyodbc
import pandas as pd
import numpy as np
import regex as re
import ast
import os
import datetime
import time
import json


def parse_pattern():
    """
    Parse pattern and return as regex pattern
    """
    data = read_json()
    regex_pattern = []
    for i in data:
        regex_to_be_replaced = (
            i["pattern_to_be_replaced"]
            .replace(" ", "\s")
            .replace("(", "\(")
            .replace(")", "\)")
            .replace("（", "\（")
            .replace("）", "\）")
            .replace(".", "\.")
            .replace("%code%", "([0-9]{4,8})")
        )
        regex_placed = (
            i["replaced_pattern"]
            .replace(" ", "\s")
            .replace("(", "\(")
            .replace(")", "\)")
            .replace("（", "\（")
            .replace("）", "\）")
            .replace(".", "\.")
            .replace("%code%", "\\1")
        )
        regex_pattern.append(
            {"regex_to_be_replaced": regex_to_be_replaced, "regex_placed": regex_placed}
        )
    return regex_pattern


def search_and_replace_loop():

    # Set up DB info
    default_MDB = "./SMS.mdb"
    mdb = input("Please enter SMS.mdb path: ") or default_MDB
    drv = "{Microsoft Access Driver (*.mdb, *.accdb)}"
    pwd = "gd2013"

    # Connect to DB
    con = pyodbc.connect("DRIVER={};DBQ={};PWD={}".format(drv, mdb, pwd))
    cur = con.cursor()

    while True:
        print(str(datetime.datetime.now()))
        # Query DB
        SQL = "SELECT * FROM L_SMS ORDER BY id"
        cur.execute(SQL)
        all_tuple = cur.fetchall()
        desc = cur.description

        # Read into dataframe
        print(f"Read database: {mdb} infomation")
        df_column = pd.DataFrame(desc)
        all_list = [list(i) for i in all_tuple]
        df = pd.DataFrame(all_list, columns=df_column[0])

        # Create dict of pattern
        regex_pattern_list = parse_pattern()
        print(regex_pattern_list)
        for idx, x in enumerate(regex_pattern_list):
            x["id"] = idx
            regex_pattern_count = x["regex_to_be_replaced"].replace(
                "\([0-9]{4,8}\)", "[0-9]{4,8}"
            )
            x["pattern_count"] = (
                df["content"].str.contains(r"^{}".format(regex_pattern_count)).sum()
            )

        for x in regex_pattern_list:
            if x["pattern_count"] > 0:
                print(
                    f"Found pattern: '{x['regex_to_be_replaced']}', Start replacing with '{x['regex_placed']}'..."
                )
                re_express = r"{}".format(x["regex_to_be_replaced"])
                re_express_1 = r"{}".format(x["regex_placed"])
                print(re_express)
                print(re_express_1)
                df["content"] = df["content"].str.replace(
                    re_express,
                    re_express_1,
                    regex=True
                )

            # Write into database
            # print(f"Write updated text into database: {mdb}")
            # df_dict = df.to_dict()
            # id_list = []
            # content_list = []

            # for k, v in df_dict["id"].items():
            #     id_list.append(v)

            # for k, v in df_dict["content"].items():
            #     content_list.append(v)

            # for id, content in zip(id_list, content_list):

            #     cur.execute("UPDATE L_SMS SET content = ? WHERE id = ?", content, id)

            # con.commit()  # commit to database
            # print("Done!")
            # cur.close()
            # con.close()
        time.sleep(1000)


def read_json():
    with open("pattern.json", "r", encoding="utf8") as json_file:
        return json.load(json_file)


def write_json(data):
    with open("pattern.json", "w", encoding="utf-8") as json_file:
        json_file.write(json.dumps(data, indent=4, ensure_ascii=False))


def add_pattern():
    found_flag = False
    pattern_to_be_replaced = str(input("Pattern to be replaced: "))
    replaced_pattern = str(input("Pattern after replacing: "))
    data = read_json()

    pattern_to_be_replaced.replace("", "\s")

    for d in data:
        # -- found pre-specified pattern
        if d["pattern_to_be_replaced"] == pattern_to_be_replaced:
            d["replaced_pattern"] = replaced_pattern
            found_flag = True
            break

    # -- add new record if not existed
    if not found_flag:
        data.append(
            {
                "pattern_to_be_replaced": pattern_to_be_replaced,
                "replaced_pattern": replaced_pattern,
            }
        )

    write_json(data)
    show_pattern()


def show_pattern():
    with open("pattern.json", "r", encoding="utf8") as json_file:
        json_object = json.load(json_file)
        print(json.dumps(json_object, indent=4, ensure_ascii=False))
    return


while True:
    msg = "------------------Monitor & Replace------------------"
    msg += "Choose operation: [1-4]\n"
    msg += "1: Start to monitor and replace\n"
    msg += "2: Add/Change Replace pattern\n"
    msg += "3: Check all replace pattern\n"
    msg += "4: exit program\n"
    msg += "Your choice: \n"
    parse_pattern()
    resp = int(input(msg))
    if resp == 1:
        search_and_replace_loop()
    elif resp == 2:
        add_pattern()
    elif resp == 3:
        show_pattern()
    else:
        break
