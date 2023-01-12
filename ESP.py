import os, copy
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm
from expressions.asynchrony import *
from expressions.tempo import *
from expressions.articulation import *
from expressions.dynamics import *
from expressions.phrasing import *
from utils import * 

ATTRIBUTES = ["sp_async_delta", "sp_async_cor_onset", "sp_async_cor_vel",
                "sp_duration_percentage", "sp_key_overlap_ratio", "sp_kor_repeated", "sp_kor_staccato", "sp_kor_legato"
                "sp_tempo_std",
                "sp_dynamics_agreement", "sp_dynamics_consistency_std",
                "sp_phrasing_w", "sp_phrasing_q"
                ]


class ExpressionStyleProfile(object):
    def __init__(self, perf_file, score_file, match_file=None):
        self.perf_file = perf_file
        self.score_file = score_file

        if match_file:
            self.match_file = match_file
            print("using provided match file")
        else: # generating match file
            align_perf_score(self.perf_file, self.score_file)
            self.match_file = self.perf_file[:-4] + "_match.csv"

        print("parsing_match...")
        self.match = self.parse_match(self.match_file)
        self.match = self.validate_match(self.match)
        self.match = self.parse_score_features_to_match(self.match)   

        print("getting attributes...")
        self.attributes = self.get_attributes()

        return        

    def __str__(self):
        result = ""
        for k, v in self.attributes.items(): 
            result += f"{k}: {round(v, 4)}\n"
        return result

    def get_attributes(self, verbose=False):

        """asynchorny attributes"""
        onset_groups = get_async_groups(self.match)
        result = async_attributes(onset_groups, self.match)

        """tempo_attributes"""
        result.update(tempo_attributes(self.match))

        """articulation_attributes"""
        result.update(articulation_attributes(self.match))

        """dynamics_attributes"""
        result.update(dynamics_attributes(self.match))

        """phrasing_attributes"""
        result.update(phrasing_attributes(self.match))   

        return result

    def plot_tempo(self, smoothing_window=0):
        """plot the tempo curve of the piece"""
        tempo = self.match['tempo']
        if smoothing_window:
            kernel = np.ones(smoothing_window) / smoothing_window
            tempo = np.convolve(tempo, kernel, mode='same')

        plt.step(match['score_time'], tempo)
        plt.grid()
        plt.xlabel("beats")
        plt.ylabel("bpm")
        plt.title(f"Tempo curve with smoothing window {smoothing_window}")
        plt.show()
        return 


    def parse_match(self, match_file):
        """
        parse the raw match from .txt file or .csv file. Normalize score time and add measure information
        doesn't validate or add score markings

        returns: pandas dataframe with matched notes information
        """

        if (match_file[-4:] == ".csv"):
            match = pd.read_csv(match_file)

        else:
            columns = ["ID", "onset_time", "offset_time", "spelled_pitch", "onset_velocity", 
                "offset_velocity", "channel", "match_status", "score_time", "score_dur", "voice", 
                "note_ID", "error_index", "skip_index"]
            with open(match_file, "r") as f:
                lines = f.readlines()
                match = [line.split() for line in lines if line[:2] != "//"]
                match = pd.DataFrame(match)
                match.columns = columns

                match.onset_time = match.onset_time.astype(float)
                match.offset_time = match.offset_time.astype(float)
                match.error_index = match.error_index.astype(int)

                """normalize score time by ticks per quarter note"""
                TPQN = int(re.search(r"\d+", lines[4]).group(0))
                match.score_time = match.score_time.astype(float) / TPQN
                match.score_dur = match.score_dur.astype(float) / TPQN	

                """parse measures from the note id information """
                match['measure'] = match['note_ID'].apply(get_measure)
        
        return match

    def validate_match(self, match):

        # large trunck of extra notes: might be repeat
        error_note = match[match['error_index'] != 0]
        if len(error_note) > 0.5 * len(match):
            print("match not valid; to much error notes!")
            return None

        return match[match['error_index'] == 0] 


    def parse_score_features_to_match(self, match):
        """ For general information like tempo or markings from score,  we pre-compute them 
            and update on the match file to save as csv.

        updated information: 
            offset: score offset = score_start + score_dur
            ibi: annotated in an on-event basis  
            tempo: in beats-per-minute
            dynamics: marking on the event.  
            articulation: marking on the event.
        """

        match_with_offset = get_score_offsets(match)
        match_with_marking = parse_score_markings(match_with_offset, self.score_file) # dynamics and articulation
        match_marking_tempo = calculate_tempo(match_with_marking) 

        # if not yet, save the updated match file. (second half of expression for dealing with nan)
        if ((match_marking_tempo == match) | ((match_marking_tempo != match_marking_tempo) & (match != match))).all().all():
            match_marking_tempo.to_csv(self.match_file)

        return match_marking_tempo


def process_ATEPP():
    """process the entire ATEPP dataset with ESP and write the attributes"""

    meta_csv = pd.read_csv(DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)

    # only include those who have a valid alignment
    meta_attributes = meta_attributes[~meta_attributes['valid_match'].isna()]
    
    for attribute in ATTRIBUTES:
        meta_attributes[attribute] = np.nan
    for idx, row in tqdm(meta_attributes.iterrows()):
        # if ("Barcarolle_Op._60" in match_file) or ("Barcarolle_in_F-Sharp_Major,_Op._60" in match_file):
        #     continue

        esp = ExpressionStyleProfile(
            f"{DATA_DIR}/{row['midi_path']}",
            f"{DATA_DIR}/{row['score_path']}",
            match_file=f"{DATA_DIR}/{row['valid_match']}")

        attributes = esp.get_attributes()

        for k, v in attributes.items():
            meta_attributes.at[idx, k] = v
    
    meta_attributes.to_csv("attributes.csv", index=False)
    return meta_attributes


if __name__ == "__main__":

    # esp = ExpressionStyleProfile("examples/mozart_match.csv", "examples/mozart.xml")
    # esp.get_attributes()
    # print(esp)

    process_ATEPP()