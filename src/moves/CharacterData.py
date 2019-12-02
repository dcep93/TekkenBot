import json
import os
from NotationParser import ParseMoveList

from enum import Enum

class ResponseTypes(Enum):
    st_punishes = 1
    ws_punishes = 2



class Gameplan:
    def __init__(self, json_data:dict):
        self.move_index = {}
        self.json_data = json_data

        #print(json_data["punishes"])
        self.AddDictIfExists(ResponseTypes.st_punishes)
        self.AddDictIfExists(ResponseTypes.ws_punishes)

    def AddDictIfExists(self, tag_name:ResponseTypes):
        if tag_name.name in self.json_data:
            moves = {}
            for key in self.json_data[tag_name.name]:
                moves[int(key)] = ParseMoveList(self.json_data[tag_name.name][key])
            self.move_index[tag_name.name] = moves

    def GetMoveByFrame(self, tag_name:ResponseTypes, frames:int):
        if tag_name.name in self.move_index:
            moves = self.move_index[tag_name.name]
            for i in range(frames):
                punishKey = frames - i
                if punishKey in moves :
                    return moves[punishKey]
        return None


def GetGameplan(char_id):
    directory = "src/moves/CharacterData/"
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            #print(os.path.join(directory, filename))
            with open(os.path.join(directory, filename)) as data_file:
                data = json.load(data_file)
                if int(data['char_id']) == int(char_id):
                    print('Gameplan located: ' + str(data['name']))
                    return Gameplan(data)
    print("Gameplan not found for char_id: " + str(char_id) + " Using default gameplan.")
    return GetGameplan(-9999)
