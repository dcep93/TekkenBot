import sys

sys.path.append('src')

def main():
    found = {}
    for path, f in to_update:
        count = 0
        while True:
            count += 1
            print(count, path)
            address = f()
            if address is None:
                continue
            found[path] = address
            break
    print(found)
        

def player_data_pointer_offset():
    return True

to_update = [
    ("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset,
]

if __name__ == "__main__":
    main()
