from . import Database

def update(char_name, move_nodes):
    try:
        update_helper(char_name, move_nodes)
    except Exception as e:
        print(e)

def update_helper(char_name, move_nodes):
    print('updating moves for', char_name)
    start = Database.raw_moves[Database.Characters(char_name)]
    names_to_row = {i[-1]:i for i in start if i}
    updated = False
    for node in move_nodes:
        row = names_to_row.get(node.name)
        if row is None:
            continue
        move_id = row[0]
        node_move_id = str(node.move_id)
        if node_move_id != move_id:
            print('mismatch', char_name, node_move_id, node.name)
            print(' '.join(row))
            row[0] = node_move_id
            updated = True
    if updated:
        csv_content = '\n'.join(['\t'.join(i) for i in start])
    print('done')

def update_move(move_id, move_name):
    pass
