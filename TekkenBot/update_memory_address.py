import sys

sys.path.append('src')

def main():
    found = {}
    for path, f in to_update:
        count = 0
        while True:
            count += 1
            print(count, path)
            try:
                address = f()
            except:
                continue
            found[path] = address
            break
    print(found)
        

def player_data_pointer_offset():
    pass

to_update = [
    ("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset,
]

if __name__ == "__main__":
    main()
