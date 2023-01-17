import numpy as np
import matplotlib.pyplot as plt

import partitura as pt
from expressions.asynchrony import *
from expressions.tempo import *
from expressions.articulation import *
from expressions.dynamics import *
from expressions.phrasing import *
from utils import * 

ATTRIBUTES = ["sp_async_delta", "sp_async_cor_onset", "sp_async_cor_vel",  "sp_async_cor_part",
                "sp_duration_percentage", "sp_key_overlap_ratio", "sp_kor_repeated", "sp_kor_staccato", "sp_kor_legato",
                "sp_tempo_std",
                "sp_dynamics_agreement", "sp_dynamics_consistency_std",
                "sp_phrasing_rubato_w", "sp_phrasing_rubato_q"
                ]


class ExpressionStyleProfile(object):
    def __init__(self, perf_file, score_file, match_file=None):
        self.perf_file = perf_file
        self.score_file = score_file
        self.valid = True

        if match_file:
            self.match_file = match_file
            print("using provided match file")
        else: # generating match file
            self.match_file = self.perf_file[:-4] + "_match.txt"
            if not os.path.exists(self.match_file):
                print("aligning...")
                align_perf_score(self.perf_file[:-4], ".".join(self.score_file.split(".")[:-1]), score_format=self.score_file.split(".")[-1])

            if not os.path.exists(self.match_file):
                print("no alignment generated!")
                self.valid = False
                return

        print("parsing_match...")
        self.match = self.parse_match(self.match_file)
        self.match = self.validate_match(self.match)
        if type(self.match) == pd.DataFrame:
            self.match = self.parse_score_features_to_match(self.match) 
            if not match_file:
                self.match_file = self.perf_file[:-4] + "_match.csv"
                self.match.to_csv(self.match_file, index=False) 

            print("getting attributes...")
            self.attributes = self.get_attributes()
        else:
            print("this match is not valid!")
            self.valid = False


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
        parse .match file with partitura package

        returns: pandas dataframe with matched notes information
        """

        if (match_file[-4:] == ".csv"):
            match = pd.read_csv(match_file)

        elif (match_file[-4:] == ".txt"):
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
                match.onset_velocity = match.onset_velocity.astype(int)

                """normalize score time by ticks per quarter note"""
                TPQN = int(re.search(r"\d+", lines[4]).group(0))
                match.score_time = match.score_time.astype(float) / TPQN
                match.score_dur = match.score_dur.astype(float) / TPQN	

                """parse measures from the note id information """
                match['measure'] = match['note_ID'].apply(get_measure)
        elif (match_file[-6:] == ".match"):
            match = dataframe_from_matchfile(match_file)
            match.to_csv(match_file.replace("match", "csv"), index=False)

            pass

        return match

    def validate_match(self, match):
        if 'error_index' not in match.columns:
            return match

        # large trunck of extra notes: might be repeat
        error_note = match[match['error_index'] != 0]
        if len(error_note) > 0.5 * len(match):
            print("match not valid; to much error notes!")
            return None

        # get rid of the extra column in the front
        match = match.loc[:, ~match.columns.str.contains('Unnamed')]

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
            match_marking_tempo.to_csv(self.match_file, index=False)

        return match_marking_tempo


