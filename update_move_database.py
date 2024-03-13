import concurrent.futures
import json
import os

import requests
from bs4 import BeautifulSoup

CONCURRENT_THREADS = 8

database = os.path.join('assets', 'frame_data')

move_id_placeholder = "0000"
columns = ["move_id", "command", "hit_level", "damage", "startup", "block", "hit", "counter"]

def main():
    characters = get_characters()
    with concurrent.futures.ThreadPoolExecutor(CONCURRENT_THREADS) as executor:
        contents = list(executor.map(get_content, characters))
    for content in contents:
        update(**content)
    print("done")

def fetch(url):
    page = requests.get(url, headers={"User-Agent": ""})
    if page.status_code != 200:
        print(url)
        raise Exception("fetch")
    return page.content

def get_characters():
    content = fetch("https://tekken8framedata.com/")
    soup = BeautifulSoup(content, 'html.parser')
    links = soup.find_all("a", href=True, target=True)
    return [
        (link.text.strip(), link["href"])
        for link in links
        if link["href"].endswith("-tekken-8-frame-data/")
    ]

def get_content(obj):
    name, link = obj
    raw_content = fetch(link)
    content = raw_content.decode("utf-8")
    start = "window.tablesomeTables = "
    trimmed = content[content.index(start)+len(start):]
    trimmed = trimmed[:trimmed.index(";</script>")]
    data = json.loads(trimmed)
    return {"name": name, "rows": data[0]["items"]["rows"]}

def update(name, rows):
    moves = [get_move(row["content"]) for row in rows]
    existing = load(name)
    same = 0
    updated = 0
    added = 0
    for move in moves:
        key = move[0]
        if key not in existing:
            added += 1
        else:
            val = existing[key]
            del existing[key]
            move[0] = val[0]
            if all(move[i] == val[i] for i in range(len(columns))):
                same += 1
            else:
                updated += 1
    extra = len(existing)
    if extra:
        moves += [[]]
    moves += [existing[key] for key in sorted(existing.keys())]
    print(f'same: {same} updated: {updated} added: {added} extra: {extra} - {name}')
    write(name, moves)

def get_move(row):
    return [
        row[str(i)]["value"].strip()
        if i > 0 else move_id_placeholder
        for i, column in enumerate(columns)
    ]

def load(name):
    path = get_path(name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='UTF-8') as fh:
        return {move[0]: move for move in 
            [line.split("\t") for line in fh.read().split("\n")[1:] if line]
        }

def write(name, moves):
    path = get_path(name)
    csv_content = '\n'.join(['\t'.join(i) for i in [columns]+moves])+'\n'
    with open(path, 'w', encoding='UTF-8') as fh:
        fh.write(csv_content)

def get_path(name):
    return os.path.join(database, f"{name}.csv") 

if __name__ == "__main__":
    main()
