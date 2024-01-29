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
    count = 0
    if True:
        (key_in, key_out) = -1, 0
        key_to_val = {i.name: str(i.move_id) for i in move_nodes}
    else:
        (key_in, key_out) = 0, -1
        key_to_val = {str(i.move_id): i.name for i in move_nodes}
    for row in start[1:]:
        val_in = row[key_in].split(',')
        val_out = ','.join([j for j in [key_to_val.get(i) for i in val_in] if j])
        check_out = row[key_out]
        if check_out != val_out:
            count += 1
            row[key_out] = val_out
    print('diff', count)
    if count > 0:
        csv_content = '\n'.join(['\t'.join(i) for i in start])+'\n'
        path = Path.path('./frame_data/%s.csv' % char.name)
        with open(path, 'w', encoding='UTF-8') as fh:
            fh.write(csv_content)
    print('done')
