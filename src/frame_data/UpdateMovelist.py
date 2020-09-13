from . import Database

from misc import Path

def update(char_name, move_nodes):
    try:
        update_helper(char_name, move_nodes)
    except Exception as e:
        print(e)

def update_helper(char_name, move_nodes):
    print('updating moves for', char_name)
    char = Database.Characters(char_name)
    start = Database.raw_moves[char]
    names_to_row = {i[-1]:i for i in start if i}
    count = 0
    for node in move_nodes:
        row = names_to_row.get(node.name)
        if row is None:
            continue
        move_ids = row[0].split(',')
        node_move_id = str(node.move_id)
        if node_move_id not in move_ids:
            print('mismatch', char_name, node_move_id, node.name)
            print(' '.join(row))
            row[0] = node_move_id
            count += 1
    print('diff', count)
    if count > 0:
        csv_content = '\n'.join(['\t'.join(i) for i in start])+'\n'
        path = Path.path('./database/%s.csv' % char.name)
        with open(path, 'w', encoding='UTF-8') as fh:
            fh.write(csv_content)
    print('done')

def update_move(move_id, move_name):
    pass
