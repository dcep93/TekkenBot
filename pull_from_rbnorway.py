import concurrent.futures
import csv
import os
import requests
import sys

from bs4 import BeautifulSoup

CONCURRENT_THREADS = 8
COMMAND = 'Command'
TO_SKIP = ['panda']

database = os.path.join('assets', 'database')

def main():
    names = [i for i in get_file_names() if i.replace('.csv', '') not in TO_SKIP]
    with concurrent.futures.ThreadPoolExecutor(CONCURRENT_THREADS) as executor:
        contents = list(executor.map(get_content, names))
    for i in range(len(names)):
        name = names[i]
        content = contents[i]
        update(name, content)

def get_file_names():
    args = sys.argv[1:]
    if args:
        return [f'{i}.csv' for i in args]
    return os.listdir(database)

def get_content(name):
    url_name = name.replace('.csv', '').replace('_', '-')
    url = f'http://rbnorway.org/{url_name}-t7-frames/'
    page = requests.get(url, headers={"User-Agent": ""})
    if page.status_code != 200:
        print(url)
        return []
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find('tbody')
    rows = table.find_all('tr')
    return [[cell.text.strip() for cell in row.find_all('td')] for row in rows]

def update(name, content):
    existing = load(name)
    same = 0
    updated = 0
    missing = 0
    for row in content:
        key = normalize(row[0])
        if key not in existing:
            missing += 1
            move_id = ''
            move_name = ''
        else:
            move_id_pos = len(row) + 1
            val = existing[key]
            del existing[key]
            if are_same(row, val):
                same += 1
            else:
                updated += 1
            move_id = val[0]
            move_name = idx(val, move_id_pos)
        row.insert(0, move_id)
        row.append(move_name)
    header = existing[COMMAND]
    del existing[COMMAND]
    content.insert(0, header)
    extra = len(existing)
    if extra:
        content += [[]]
    content += [existing[key] for key in sorted(existing.keys())]
    print(f'same: {same} updated: {updated} missing: {missing} extra: {extra} - {name}')
    write(name, content)

def load(name):
    path = get_path(name)
    with open(path, encoding='UTF-8') as fh:
        reader = csv.reader(fh, delimiter='\t')
        return {normalize(i[1]): i for i in reader if i}

def normalize(move):
    return ', '.join([i.strip() for i in move.split(',')])

def write(name, content):
    path = get_path(name)
    csv_content = '\n'.join(['\t'.join(i) for i in content])+'\n'
    with open(path, 'w', encoding='UTF-8') as fh:
        fh.write(csv_content)

def are_same(pulled, existing):
    for i, val in enumerate(pulled):
        if idx(existing, i+1) != val:
            return False
    return True

def idx(arr, pos, default=''):
    if pos >= len(arr):
        return default
    return arr[pos]

def get_path(name):
    return os.path.join(database, name) 

if __name__ == "__main__":
    main()
