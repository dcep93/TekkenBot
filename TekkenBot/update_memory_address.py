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
    return "0x8EE02C8 0x10 0x68 0x8 0x30"

to_update = [
    ("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset,
]

if __name__ == "__main__":
    main()
