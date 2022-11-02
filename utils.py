import os, re, glob
import pandas as pd
from tqdm import tqdm

import hook

DATA_CSV = "../Datasets/ATEPP-1.1/ATEPP-metadata-1.1.csv"
DATA_DIR = "../Datasets/ATEPP-1.1/"

def parse_match(match_file):
    """returns: pandas dataframe with matched notes information
    Note: the missing notes are not included. 
    """
    columns = ["ID", "onset_time", "offset_time", "spelled_pitch", "onset_velocity", 
        "offset_velocity", "channel", "match_status", "score_time", "score_dur", "voice", 
        "note_ID", "error_index", "skip_index"]

    with open(match_file, "r") as f:
        
        lines = f.readlines()
        match = [line.split() for line in lines if line[:2] != "//"]
        match = pd.DataFrame(match)
        match.columns = columns

        """normalize score time by ticks per quarter note"""
        TPQN = int(re.search(r"\d+", lines[4]).group(0))
        match.score_time = match.score_time.astype(int) / TPQN
        match.score_dur = match.score_dur.astype(int) / TPQN	

    return match

def align_perf_score(perf, score, score_format="musicxml", use_matched=True):
    """using eita's alignment algorithm, save "_match.txt" files in dataset. Only run once
    perf: str without .mid extension, e.g "/import/c4dm-datasets/ATEPP/Sergei_Rachmaninoff/Etudes-Tableaux,_Op.39/No.6_in_A_Minor/00159"
    score: str without .mxl extension, e.g "/import/c4dm-datasets/ATEPP/Sergei_Rachmaninoff/Etudes-Tableaux,_Op.39/No.6_in_A_Minor/Rachmaninov_Etude-Tableau_op._39_no._6"
    output: 
    """
    if use_matched and os.path.exists(f"{perf}_match.txt"):
        return f"{perf}_match.txt"
    
    """escape parenthesis"""
    score = score.replace("(", "\(")
    score = score.replace(")", "\)")
    perf = perf.replace("(", "\(")
    perf = perf.replace(")", "\)")

    if score_format == "xml":
        os.system(f"./AlignmentTool_v190813/XMLToMIDIAlign.sh {score} {perf}")
    elif score_format == "musicxml":
        os.system(f"./AlignmentTool_v190813/MusicXMLToMIDIAlign.sh {score} {perf}")
    
    
    """remove the artifacts after matching"""
    if os.path.exists(f"{perf}_spr.txt"): 
        os.system(f"rm {perf}_spr.txt")
    if os.path.exists(f"{perf}_corresp.txt"):
        os.system(f"rm {perf}_corresp.txt")
    if os.path.exists(f"{score}_spr.txt"): 
        os.system(f"rm {score}_spr.txt")
    if os.path.exists(f"{score}_hmm.txt"): 
        os.system(f"rm {score}_hmm.txt")
    if os.path.exists(f"{score}_fmt3x.txt"): 
        os.system(f"rm {score}_fmt3x.txt")


    return f"{perf}_match.txt"

def generate_alignments():
    """generate _match.txt files for each performance-score pair, under the same directory. """
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    for perf, score in tqdm(zip(midi_list, score_list)):

        """remove extension"""
        perf = DATA_DIR + perf[:-4]
        score = DATA_DIR + ".".join(score.split(".")[:-1])

        if os.path.exists(score + ".mxl"):
            # unzip the mxl file
            score_dir = "/".join(score.split("/")[:-1])
            os.system(f"unzip -o {score}.mxl -d {score_dir}")

        if os.path.exists(score + ".musicxml"):
            align_perf_score(perf, score, score_format="musicxml")
        elif os.path.exists(score_dir + "/score.xml"):
            align_perf_score(perf, score_dir + "/score", score_format="xml")
        else:
            print("score doesn't exist! " + score)
            continue

def filter_unmatched():
    """filter out the pieces that"""
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    mxl_count, mxl_unmatched_count = 0, 0
    musicxml_count, musicxml_unmatched_count = 0, 0
    for perf, score in tqdm(zip(midi_list, score_list)):
        perf = DATA_DIR + perf[:-4]
        score = DATA_DIR + ".".join(score.split(".")[:-1])

        if os.path.exists(score + ".mxl"):
            mxl_count += 1
            if (not os.path.exists(perf + "_match.txt")):
                mxl_unmatched_count += 1

        if os.path.exists(score + ".musicxml"):
            musicxml_count += 1
            if (not os.path.exists(perf + "_match.txt")):
                musicxml_unmatched_count += 1

    print(f"{mxl_unmatched_count}/{mxl_count}")
    print(f"{musicxml_unmatched_count}/{musicxml_count}")


def remove_all_matched():
    all_match_files = glob.glob(f"{DATA_DIR}/**/*_match.txt", recursive=True)
    for file in all_match_files:
        file = file.replace("(", "\(")
        file = file.replace(")", "\)")
        os.system(f"rm {file}")

    return 

if __name__ == "__main__":
    # remove_all_matched()
    generate_alignments()
    # filter_unmatched()
    pass