import collections
import csv
import enum

from . import DataColumns
from misc import Path

@enum.unique
class Characters(enum.Enum):
    alisa = '[ALISA]'
    asuka = '[Asuka]'
    bob = '[BOB_SATSUMA]'
    bryan = '[Bryan]'
    claudio = '[CLAUDIO]'
    devil_jin = '[DEVIL_JIN]'
    dragunov = '[Dragunov]'
    eddy = '[EDDY]'
    feng = '[FENG]'
    gigas = '[Gigas]'
    heihachi = '[HEIHACHI]'
    hwoarang = '[HWOARANG]'
    jack7 = '[Jack]'
    jin = '[JIN]'
    josie = '[JOSIE]'
    katarina = '[KATARINA]'
    kazumi = '[KAZUMI]'
    kazuya = '[KAZUYA]'
    king = '[KING]'
    kuma = '[Kuma]'
    lars = '[Lars]'
    law = '[LAW]'
    lee = '[LEE]'
    leo = '[Eleonor]'
    lili = '[EMILIE]'
    lucky_chloe = '[Chloe]'
    master_raven = '[FRV]'
    miguel = '[Miguel]'
    nina = '[NINA]'
    panda = '[PANDA]'
    paul = '[Paul]'
    shaheen = '[SHAHEEN]'
    steve = '[Steve_Fox]'
    xiaoyu = '[Lin_Xiaoyu]'
    yoshimitsu = '[YOSHIMITSU]'
    akuma = '[Mr.X]'
    eliza = '[Vampire]'
    geese = '[Geese_Howard]'
    noctis = '[Noctis]'
    lei = '[Lei_Wulong]'
    marduk = '[MARDUK]'
    armor_king = '[ARMOR_KING]'
    julia = '[JULIA]'
    negan = '[Negan]'
    zafina = '[ZAFINA]'
    ganryu = '[GANRYU]'
    leroy = '[NSB]'
    fahkumram = '[NSC]'
    kunimitsu = '[Kunimitsu]'

db_field_to_col = {
    'move_id': DataColumns.DataColumns.move_id,
    'Command': DataColumns.DataColumns.cmd,
    'Hit level': DataColumns.DataColumns.hit_type,
    # 'Damage':
    'Start up frame': DataColumns.DataColumns.startup,
    'Block frame': DataColumns.DataColumns.block,
    'Hit frame': DataColumns.DataColumns.normal,
    'Counter hit frame': DataColumns.DataColumns.counter,
    # 'Notes':
}

class History:
    might_be_missing = [DataColumns.DataColumns.cmd, DataColumns.DataColumns.block, DataColumns.DataColumns.normal, DataColumns.DataColumns.counter]
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, entry):
        for field in self.might_be_missing:
            self.record_field(field, entry)

    def record_field(self, field, entry):
        if field in entry:
            v = entry[field]
        else:
            v = None
        most_common = v
        if v is None:
            max_count = 0
        else:
            self.counts[field][v] += 1
            max_count = self.counts[field][v]
        for existing, count in self.counts[field].items():
            if count > max_count:
                most_common = existing
                max_count = count
        if most_common != v:
            if v is None:
                new_v = most_common
            else:
                new_v = "(%s)" % (v)
            entry[field] = new_v

def key(entry):
    return (entry[DataColumns.DataColumns.char_name], str(entry[DataColumns.DataColumns.move_id]))

def populate_database():
    for character in Characters:
        populate_character(character.name)

def populate_character(character_name):
    existing = [i for i in database.keys() if i[0] == character_name]
    for i in existing:
        del database[i]
    path = Path.path('./frame_data/%s.csv' % character_name)
    with open(path, encoding='UTF-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        data = [i for i in reader if i]
        raw_moves[Characters[character_name]] = data
    header = data[0]
    for move in data[1:]:
        populate_move(character_name, header, move)

def populate_move(char_name, header, move):
    entry = {}
    entry[DataColumns.DataColumns.char_name] = char_name
    for i, db_field in enumerate(header):
        if i >= len(move): break
        if db_field in db_field_to_col:
            col = db_field_to_col[db_field]
            val = move[i]
            entry[col] = val
    move_ids_raw = entry[DataColumns.DataColumns.move_id]
    if not move_ids_raw:
        return
    move_ids = move_ids_raw.split(',')
    for move_id in move_ids:
        entry_to_save = dict(entry)
        entry_to_save[DataColumns.DataColumns.move_id] = move_id
        k = key(entry_to_save)
        if k in database:
            print('%s already in database, skipping' % (k,))
        else:
            database[k] = entry_to_save

def load(entry):
    k = key(entry)
    if k in database:
        found = database[k]
        for field, value in found.items():
            entry[field] = value
        return True
    else:
        return False

def record(entry):
    k = key(entry)
    history = histories[k]
    history.record(entry)

histories = collections.defaultdict(History)
database = {}
raw_moves = {}
