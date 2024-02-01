import subprocess
import sys
import tkinter as tk
from tkinter import filedialog
import os
import pickle

class WordDictionary:
    def __init__(self):
        self.data = {}  # A dictionary that maps a word to a start and end time
        self.counter = {}  # A dictionary that tracks the amount of occurences of each word

    def add(self, entry):
        if entry[2] in self.counter:
            self.data[entry[2] + "_" + str(self.counter[entry[2]])] = entry[0:2]
            self.counter[entry[2]] += 1
        else:
            self.data[entry[2] + "_1"] = entry[0:2]
            self.counter[entry[2]] = 2

    def __str__(self):
        return_string = ""
        for key, value in self.data.items():
            return_string += key + "\n"
            return_string += "Start: " + str(value[0]) + "s\n"
            return_string += "End: " + str(value[1]) + "s\n\n"
        return return_string

    def getKey(self, n):
        for i, key in enumerate(self.data.keys()):
            if n == i:
                return key

    def getValue(self, n):
        key = self.getKey(n)
        return self.data[key]


def get_word_category(word: str):
    '''
    This function returns an integer based on the "category" of the word. There are 4 categories that we
    are concerned with. Affricate first, affricate second, fricative first, fricative second. "First" refers
    to the phoneme being present in the first syllable. We need to treat these categories differently. For example,
    take "hongcha", which is a affricate second word. We need to replace "C2c" with "Tc" and "C2r" with "T".
    '''
    # Here, we exploit the fact that all syllables in pinyin are at least two letters (for the words present
    # in the word-list.
    first_half = word[0:2]
    second_half = word[2:]
    if first_half == "ch":
        return 1
    if "ch" in second_half:
        return 2
    if first_half == "sh":
        return 3
    if "sh" in second_half:
        return 4
    return 0

def preprocess_file(file, modify=False):
    """
    This function preprocesses a TextGrid file for later Praat script processing. While it is possible to process
    the files solely with scripting, it would be more time consuming. Here, this script will mark target phonemes
    with the letter "t". Therefore, the Praat script will need no knowledge of the words, and can focus on
    solely the phonemes. This function would run faster if the word tier was above the phoneme tier. But, considering
    speed is not a problem (for now), we save time by not manually changing all the files.
    """
    word_boundary = False
    word_data = WordDictionary()  # This will be the durations of all the words
    current_word_data = []  # This stores the xmin and xmax of the current word
    index_to_check = 12  # We want to check for even intervals. With single digit intervals, we just check the only
                        # digit present. But, when we hit interval 8, we need to check the digit after on the next
                        # interval.
    with open(file, "r") as my_file:
        word_tier = False
        lines = my_file.readlines()
        for line in lines:
            line = line.strip()
            if line == "name = \"sentence - words\"":
                word_tier = True

            if word_tier:
                if line[0:4] == "item":
                    break
                if word_boundary:
                    if line[0] == "x":  # Adding xmin, xmax
                        current_word_data.append(float(line[7:]))
                    else:
                        current_word_data.append(line[8:-1])
                        word_data.add(current_word_data)
                        current_word_data = []
                        word_boundary = False
                # The first interval is empty. Then, every other interval contains a word. Therefore, each
                # even interval will contain a word, hence the % 2.
                if line[0:10] == "intervals ":
                    interval_number = int(line[11:index_to_check])
                    if interval_number % 2 == 0:
                        word_boundary = True  # Signals the function "entering" the boundary of a word.
                    if interval_number in [9, 99, 999]:
                        index_to_check += 1
    current_word_index = 0
    buffer = 0  # TODO FIX THIS, it's very stupid (but it works).
    if modify:
        with open("modified_file.TextGrid", "w") as new_file:
            current_key = word_data.getKey(current_word_index)
            current_word = current_key.partition("_")[0]
            word_category = get_word_category(current_word)
            modified = False
            for line in lines:
                line = line.strip()
                if word_category == 0:
                    modified = True

                if word_category == 1:
                    if line[8:11].lower() == "c1r" or line[8:10].lower() == "c1":
                        line = "text = \"t\""
                        modified = True
                        buffer = 12

                if word_category == 2:
                    if line[8:11].lower() == "c2c":
                        line = "text = \"tc\""
                    if line[8:11].lower() == "c2r":
                        line = "text = \"t\""
                        modified = True

                if word_category == 3:
                    if line[8:10] == "C1":
                        line = "text = \"t\""
                        modified = True
                        buffer = 12

                if word_category == 4:
                    if line[8:10] == "C2":
                        line = "text = \"t\""
                        modified = True
                if current_word_index == len(word_data.data) - 1:
                    modified = False
                if modified and buffer == 0:
                    current_word_index += 1
                    current_key = word_data.getKey(current_word_index)
                    current_word = current_key.partition("_")[0]
                    word_category = get_word_category(current_word)
                    modified = False
                if buffer > 0:
                    buffer -= 1
                new_file.write(line + "\n")
    with open(file + '.pickle', 'wb') as word_data_file:
        pickle.dump(word_data, word_data_file, protocol = pickle.HIGHEST_PROTOCOL) # TODO: check highest_protocl
def combine_files(python_output, praat_output):
    with open(python_output, 'rb') as pickle_file:
        word_data = pickle.load(pickle_file)
    line_index = 0
    with open(praat_output, "r") as praat_file:
        praat_lines = praat_file.readlines()

    file_name = "combined_data"
    while os.path.exists(file_name + ".txt"):
        try:
            file_count = int(file_name[13:])
        except ValueError:
            file_name += "1"
            continue
        file_count += 1
        file_name = "combined_data" + str(file_count)

    with open(file_name + ".txt", "w") as my_file:
        for key, value in word_data.data.items():
            if get_word_category(key) == 0:
                continue
            my_file.write(key + "\n")
            word_duration = value[1] - value[0]
            my_file.write("Word duration: " + str(word_duration) + "\n")

            closure_check = True # Used to write "Closure: " if there is no closure present, for data processing purposes
            while True:
                if closure_check:
                    if praat_lines[line_index][0:3] != "Clo":
                        my_file.write("Closure: \n")
                    closure_check = False

                if praat_lines[line_index] == "\n":
                    line_index += 1
                    my_file.write("\n")
                    break

                my_file.write(praat_lines[line_index])
                line_index += 1
def txt_to_csv(file):
    new_file_lines = ""
    with open(file, "r") as my_file:
        lines = my_file.readlines()
    for line in lines:
        if line != "\n":
            line = line[0:-1] + ","
        new_file_lines += line
    with open("csv.csv", "w") as new_file:
        new_file.write(new_file_lines)
def subprocess_test():
    subprocess.run(["C:\Praat.exe"])

def main():
    # Get location of Praat
    print("Select where your Praat.exe file is located")
    while True:
        praat_location = filedialog.askopenfilename()
        if praat_location[-9:] == "Praat.exe":
            print("Success!")
            print("Praat found at: " + praat_location)
            print()
            break
        else:
            print("Praat not found, please try again.")
    # Get location of .wav and .TextGrid
    # Note that this does not work with a .txt or .mp3, for example
    print("Select both the sound and TextGrid file to be analyzed")
    sound_file_found = False
    textgrid_file_found = False
    while True:
        files = filedialog.askopenfilenames()
        if len(files) != 2:
            print("Please select exactly two files")
            continue
        else:
            for file in files:
                if file[-3:] == "wav":
                    sound_file = file
                    sound_file_found = True
                elif file[-4:] == "Grid":
                    textgrid_file = file
                    textgrid_file_found = True
        if not sound_file_found or not textgrid_file_found:
            print("Files not found, please try again.")
            for file in files:
                print(file[-3:])
            continue
        print("Success!")
        print("Sound file found at: " + sound_file)
        print("TextGrid file found at: " + textgrid_file)
        print()
        break
    subprocess.run([praat_location, "--open", sound_file])
def main2():
    subprocess.Popen(["C:/Users/rober/Documents/Praat.exe", "--open", ["C:/Users/rober/Downloads/016_3(1).TextGrid","C:/Users/rober/Downloads/019-2_2_part_2.wav"]])
    #subprocess.Popen(["C:/Users/rober/Documents/Praat.exe", "--open", ])
    os.system("C:/Users/rober/Documents/Praat.exe" + " --open " + "C:/Users/rober/Downloads/016_3(1).TextGrid")
    os.system("C:/Users/rober/Documents/Praat.exe" + " --open " + "C:/Users/rober/Downloads/016_3(1).TextGrid")



if __name__ == "__main__":
    #main2()
    file_name = '019-2_2_part_2'
    preprocess_file(file_name + ".TextGrid", True)
    combine_files(file_name + ".TextGrid.pickle", "script_output.txt")
    #txt_to_csv("combined_data.txt")
