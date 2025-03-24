import subprocess
from tkinter import filedialog
import os
import pickle
import pandas as pd
import re

class WordDictionary:
    def __init__(self):
        self.data = {}  # A dictionary that maps a word to a start and end time
        self.counter = {}  # A dictionary that tracks the amount of occurrences of each word

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

    def get_key(self, n): # Gets key at index
        for i, key in enumerate(self.data.keys()):
            if n == i:
                return key

    def getValue(self, n): # Gets value at index
        key = self.get_key(n)
        return self.data[key]
class WordCounter:
    def __init__(self):
        self.counter = {}

    def add(self, word):
        if word in self.counter:
            self.counter[word] += 1
        else:
            self.counter[word] = 1

    def reset(self):
        self.counter = {}

def file_namer(file_name, handle, output_path: '') -> str:  # TODO: Implement keyword argument
    ''' Test

    :param file_name:
    :param handle:
    :param output_path:
    :return:
    '''
    file_counter = 0
    if os.path.exists(output_path + file_name + handle):
        return file_name + handle
    while os.path.exists(output_path + file_name + str(file_counter) + handle):
        file_counter += 1
    return output_path + file_name + str(file_counter) + handle

def file_splitter(file_name):
    if "/" in file_name:
        return file_name.split("/")[-1]
    else:
        return file_name.split("\\")[-1]

def get_word_category(word: str):
    '''
    This function returns an integer based on the "category" of the word. There are 4 categories that we
    are concerned with. Affricate first, affricate second, fricative first, fricative second. "First" refers
    to the phoneme being present in the first syllable. We need to treat these categories differently. For example,
    take "hongcha", which is a affricate second word. We need to replace "C2c" with "Tc" and "C2r" with "T".
    '''
    # Here, we exploit the fact that all syllables in pinyin are at least two letters (for the words present
    # in the word-list).
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


def preprocess_file(file_path, modify=False, output_path='', pickle_path=''):
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

    file_pickle_path = file_splitter(file_path)
    with open(file_path, "r") as my_file:
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
    if modify:
        #file_name = file_namer("modified_file", ".TextGrid", output_path)
        dictionary_exhausted = False
        #with open(file_name, "w") as new_file:
        with open(output_path + "mod" + file_pickle_path, "w") as new_file:
            current_key = word_data.get_key(current_word_index)
            current_word = current_key.partition("_")[0]
            word_category = get_word_category(current_word)
            for line in lines:
                line = line.strip()
                if word_category == 0:
                    pass
                if word_category == 1:
                    if line[8:11].lower() == "c1r": #or line[8:10].lower() == "c1":
                        line = "text = \"t\""

                if word_category == 2:
                    if line[8:11].lower() == "c2c":
                        line = "text = \"tc\""
                    if line[8:11].lower() == "c2r":
                        line = "text = \"t\""

                if word_category == 3:
                    if line[8:10].lower() == "c1":
                        line = "text = \"t\""

                if word_category == 4:
                    if line[8:10].lower() == "c2":
                        line = "text = \"t\""

                if current_word_index == len(word_data.data) - 1:
                    dictionary_exhausted = True
                if not dictionary_exhausted:
                    try: # TODO .1 second tolerance
                        boundary_time = float(line[7:])
                        print(abs(boundary_time - word_data.data[current_key][1]))
                        #if line[7:12] == str(word_data.data[current_key][1])[0:5]:  # Account for precision problems
                        #if abs(boundary_time - word_data.data[current_key][1]) < 0.14:
                        if boundary_time > word_data.data[current_key][1]:
                            current_word_index += 1
                            current_key = word_data.get_key(current_word_index)
                            current_word = current_key.partition("_")[0]
                            word_category = get_word_category(current_word)

                    except IndexError:
                        print("Error")
                        pass

                    except ValueError:
                        pass
                new_file.write(line + "\n")
                # DEBUG:
                print(current_key + "///" + str(word_data.data[current_key][1]))
                print(line)
    '''
    with open(pickle_path + file_pickle_path + '.pickle', 'wb') as word_data_file:
        try:
            pickle.dump(word_data, word_data_file, protocol=pickle.HIGHEST_PROTOCOL)  # TODO: check highest_protocol
        except:
            print("Pickle error. Your version of Python may be outdated. ")
            raise ValueError # TODO: Temp
    '''

def combine_files(python_output, praat_output, output_path=''):
    """ Combines python and praat outputs into a readable file

    :param python_output: A pickle file that can be loaded into a dictionary
    :param praat_output: A .txt file returned from extraction.praat
    :return: A readable .txt file
    """
    with open(python_output, 'rb') as pickle_file:
        word_data = pickle.load(pickle_file)
    line_index = 0
    with open(praat_output, "r") as praat_file:
        praat_lines = praat_file.readlines()
    file_name = python_output[0:-16].split("/")[1] # TODO, this is gamey
    #file_name = file_namer("combined_data", ".txt", output_path="4_ReadableOutputs/")
    with open(output_path + file_name + '.txt', "w", encoding='utf8') as my_file:
        for key, value in word_data.data.items():
            word_category = get_word_category(key)
            if word_category == 0:
                continue
            my_file.write(key + "\n")
            # IPA Unicode conversion based on UCL system
            if word_category > 2:
                my_file.write("Phone: ʂ\n")
            else:
                my_file.write("Phone: ʈʂ\n")

            word_duration = value[1] - value[0]
            my_file.write("Word duration: " + str(word_duration) + "\n")

            closure_check = True  # Used to write "Closure: " if there is no closure present,
                                  # for data processing purposes
            # while True:
            #     if line_index == len(praat_lines)-1:
            #         break
            #
            #     if closure_check:
            #         if praat_lines[line_index][0:3] != "Clo":
            #             my_file.write("Closure: \n")
            #         closure_check = False
            #
            #     if praat_lines[line_index] == "\n":
            #         line_index += 1
            #         my_file.write("\n")
            #         break
            #
            #     my_file.write(praat_lines[line_index])
            #     line_index += 1

            while True:
                if len(praat_lines) == 0:
                    break
                if closure_check:
                    if praat_lines[line_index][0:3] != "Clo":
                        my_file.write("Closure: \n")
                    closure_check = False

                if praat_lines[0] == "\n":
                     my_file.write(praat_lines.pop(0))
                     break
                my_file.write(praat_lines.pop(0))
def modify_script_output(file_path, output_path):
    file_name = file_path[9:]
    with open(output_path + file_name, "w") as new_file:
        pass


def txt_to_csv(file_path, output_path):
    """

    :param file_path:
    :param output_path:
    :return:
    """
    split_file = file_splitter(file_path) # Returns filename.handle
    file_without_handle = split_file.split(".")[0] # Returns filename
    file_without_handle = file_without_handle[9:] # Removes scroutmod

    new_file_lines = ""
    with open(file_path, "r", encoding='utf8') as my_file:
        lines = my_file.readlines()
    block = []
    for line in lines: # [0:-1] cuts off the last newline. Without doing so, we would have an
                             # extra file_without_handle at the end"
        if line == "\n":
            if len(block) == 14:
                block.insert(0, "Closure: ")
            if len(block) == 16:
                # Debugging purposes
                print("Popping")
                block.pop(0)
            new_file_lines += file_without_handle + ","
            try:
                word_category = get_word_category(block[6])
            except IndexError:
                print("Error")
                print(block)
                return
            new_file_lines += block[6][0:-1] + ","
            new_file_lines += block[7][0:-1] + ","
            if word_category > 2:
                new_file_lines += "ʂ,"
            else:
                new_file_lines += "ʈʂ,"
            for i, block_line in enumerate(block):
                if i == 6 or i == 7:
                    continue
                try:
                    new_file_lines += block_line.split(":")[1][1:-1] + ","
                except IndexError:
                    pass
            new_file_lines += "\n"
            block = []
            continue

        block.append(line)
        '''
        if line != "\n":
            split_line = line.split(":")
            if len(split_line) > 1:
                line = split_line[1][1:]

            line = line[0:-1] + ","
            new_file_lines += line
        else:
            new_file_lines += "\n"
            new_file_lines += file_without_handle + ","
        '''
    file_name = output_path + file_without_handle + ".csv"
    with open(file_name, "w", encoding='utf8') as new_file:
        print(new_file)
        new_file.write(new_file_lines)

def csv_to_xlsx(file_path='', output_path='', mode='a', append_target=None, directory_path=None):
    """ Converts from a .csv to a .xlsx file

    :param file_path: The file to be written to xlsx
    :param output_path: NOT IMPLEMENTED
    :param mode: The mode of the function. 'w' for write, 'a' for append
    :param append_target: If append mode is selected, file_path will be appended to append_target
    :return:
    """

    if mode == 'a':
        try:
            pd.read_excel(append_target)
        except ValueError:
            print("With append mode selected, please choose a file to append to. ")
            raise ValueError
        except FileNotFoundError:
            print("Append target not found. ")
            raise FileNotFoundError
    if mode == 'wd' and directory_path == None:
        print("You must select a directory in wd mode. ")
        raise ValueError
    if mode != 'wd':
        file_without_handle: str = file_path.split(".")[0] # Filename string
        input_df = pd.read_csv(file_path, header=None)
    column_names = ["file", "word", "word_count", "word_dur", "phone", "closure_dur", "release_dur", "cog", "skew", "sd",
                    "fricative_f3", "vowel_dur", "f1_20", "f1_40", "f2_20", "f2_40", "f3_20", "f3_40", "UNK"]

    if mode == 'wd':
        files = os.listdir(directory_path)
        print(files)

        complete_df = pd.read_csv(directory_path + files[0], header=None)
        complete_df.columns = column_names
        df_list = [complete_df]

        for file in os.listdir(directory_path):
            print(file)
            current_df = pd.read_csv(directory_path + file, header=None)
            current_df.columns = column_names
            print(file)
            df_list.append(current_df)
        # TODO: Fix this:
        complete_df = pd.concat(df_list, ignore_index=True)
        complete_df.to_excel(directory_path + "baseline_data.xlsx", index=False)

    if mode == 'w':
        # TODO
        input_df.columns = column_names
        input_df.to_excel(file_without_handle + ".xlsx", index=False)
    if mode == 'a':
        # TODO: Investigate efficiency of appending to large files. read_excel seems to slow down as file gets bigger
        # https://stackoverflow.com/questions/28766133/faster-way-to-read-excel-files-to-pandas-dataframe
        append_target_df = pd.read_excel(append_target)
        output_df = pd.concat([input_df, append_target_df])
        output_df.to_excel(file_without_handle + ".xlsx", index=False)
def count_words(directory):
    '''
    A function that takes a directory of .csv files and adds a counter for words by filename
    :param directory:
    :return:
    '''
    files = os.listdir(directory)
    word_counter = WordCounter() # A mapping from words to their count
    current_file = files[0][0:6]
    for file in files:
        if file[0:6] != current_file:
            current_file = file[0:6]
            word_counter.reset()

        new_lines = ""
        with open(directory + file, encoding='utf-8') as my_file:
            for line in my_file.readlines():
                print(line)
                line_as_list = line.split(",")
                word_counter.add(line_as_list[1])
                line_as_list.insert(2, word_counter.counter[line_as_list[1]])
                new_lines += ",".join(str(element) for element in line_as_list)
        with open("6_countedcsv/" + file, "w", encoding='utf-8') as new_file:
            new_file.write(new_lines)
def postprocess_files():
    """
    This function serves as a wrapper for ALL functions after script outputs have been obtained.
    This function uses the default directories (i.e. it gets its script outputs from "3_ScriptOutputs".
    This function will write from a directory of .txt's to a single xlsx.
    :return:
    """
    for file in os.listdir("3_ScriptOutputs"):
        txt_to_csv("3_ScriptOutputs/" + file, "5_csvFiles/")
    count_words("5_csvFiles/")
    csv_to_xlsx(mode='wd', directory_path='6_countedcsv/')
    add_vowels("6_countedcsv/baseline_data.xlsx", "8_xlsx/")
def main():
    mode = input("[Pre] or [Po]st Process files?")
    setup_required = input("Setup directories? (select N if directories already made): Y/N")
    if setup_required == "Y":
        default_directories = input("Use default directory names? Y/N")
        if default_directories == "N":
            pass # TODO
    directory_dictionary = {"Input TextGrids": "1_Test TextGrids", "Preprocessed Files": "2_PreprocessedFiles", "Script Outputs": "3_ScriptOutputs", "Pickles": "3_Pickles",
                            "Readable Outputs": "4_ReadableOutputs", "csv Files": "5_csvFiles"} # A dictionary that maps directories necessary for processing -> directory names

    if mode == "Pre":
        files = os.listdir(directory_dictionary["Input TextGrids"])
        for file in files:
            preprocess_file(directory_dictionary["Input TextGrids"] + "/" + file, True, output_path="2_PreprocessedFiles/", pickle_path="3_Pickles/")
    if mode == "Po":
        # Generate your readable outputs
        #for output in os.listdir(directory_dictionary["Script Outputs"]):
        #    combine_files(python_output="3_Pickles/" + output[9:] + ".TextGrid.pickle", praat_output="3_ScriptOutputs/" + output, output_path="4_ReadableOutputs/")
        # Create your csv files
        for file in os.listdir("3_ScriptOutputs"):
            txt_to_csv(file_path="3_ScriptOutputs/" + file, output_path="5_csvFiles/")
        # Create your xlsx
        #csv_to_xlsx(mode='wd', directory_path="5_csvFiles/")
def pinyin_to_XSAMPA(vowel: str):
    """ Returns an X-SAMPA representation of a vowel given a pinyin string

    :param vowel: Vowel in pinyin
    :return: X-SAMPA IPA phone
    """
    if vowel == "i":
        return "ɻ"
    elif vowel == "ua":
        return "ua"
    elif vowel == "a":
        return "a"
    elif vowel == "ao":
        return "aʊ"
    elif vowel == "u":
        return "u"
    elif vowel == "ou":
        return "oʊ"
    elif vowel == "e":
        return "ɤ"
def add_vowels(file_path: str, output_path: str):
    table = pd.read_excel(file_path)
    vowels = []

    for index, row in table.iterrows():
        match = re.search(r"(?<=(ch|sh))[aeiou]+", row["word"])
        if match is not None:
            vowels.append(pinyin_to_XSAMPA(match.group()))
        else:
            print("Error. Word not found, instead found:")
            print(row["word"])
            vowels.append("")

    table["vowel"] = vowels
    table.to_excel(output_path + "complete_data.xlsx", index=False)
if __name__ == "__main__":
    #preprocess_file(file_path="1_Test TextGrids/046-3_2.TextGrid", modify=True, output_path="2_PreprocessedFiles/")
    #count_words("7_baselines/")
    #main()
    #txt_to_csv(file_path="0_Bin/scroutmodbaseline_female_finished.txt", output_path="7_baselines/")
    #csv_to_xlsx(mode='wd', directory_path="7_baselines/")
    '''
    my_df = pd.read_excel("5_csvFiles/baseline_data.xlsx")
    print(my_df.columns)
    new_df = pd.DataFrame(zip(my_df.cog, my_df.sd))
    fig = px.box(new_df)
    fig.show()
    '''
    #count_words("5_csvFiles/")
    #csv_to_xlsx(directory_path="6_countedcsv/", mode='wd')
    postprocess_files()
    #preprocess_file(modify=True, file_path="1_Test TextGrids/034-3_2-final.TextGrid",output_path="0_Log/


