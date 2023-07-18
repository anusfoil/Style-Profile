import os, sys, glob, hook
import warnings
sys.path.insert(0, "../partitura")
sys.path.insert(0, "../")
from tests import test_performance_codec
import partitura as pt
import parangonar as pa
import matplotlib.pyplot as plt
from collections import defaultdict
import pandas as pd
import numpy as np
from tqdm import tqdm
import numpy.lib.recfunctions as rfn


VIENNA_MATCH_DIR = "../Datasets/vienna4x22/match/"
VIENNA_MUSICXML_DIR = "../Datasets/vienna4x22/musicxml/"
VIENNA_PERFORMANCE_DIR = "../Datasets/vienna4x22/midi/"

ASAP_DIR = "../Datasets/asap-dataset-alignment/"
ASAP_MATCH = "../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/Yeletskiy07M_note_alignments/note_alignment.tsv"
ASAP_MUSICXML = "../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/xml_score.musicxml"
ASAP_PERFORMANCE = "../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/Yeletskiy07M.mid"

BMZ_MATCH_DIR = "../Datasets/pianodata-master/match"
BMZ_MUSICXML_DIR = "../Datasets/pianodata-master/xml/"

ATEPP_DIR = "../Datasets/ATEPP-1.1"
ATEPP_META_DIR = "../Datasets/ATEPP-1.1/ATEPP-metadata-1.3.csv"


# # path to the match
# match_fn = os.path.join(VIENNA_MATCH_DIR, 'Mozart_K331_1st-mov_p01.match')
# # match_fn = os.path.join(VIENNA_MATCH_DIR, 'Chopin_op10_no3_p01.match')
# # Path to the MusicXML file
# score_fn = os.path.join(VIENNA_MUSICXML_DIR, 'Mozart_K331_1st-mov.musicxml')
# # score_fn = os.path.join(VIENNA_MUSICXML_DIR, 'Chopin_op10_no3.musicxml')
# # Load the score into a `Part` object
# score = pt.load_musicxml(score_fn)

def load_dataset_pf(datasets=['ASAP'], return_metadata=False):
    """load the performance features for the given dataset from the saved
    .npy arrays. Return list of numpy arrays.

    Args:
        dataset (str): dataset to process. Defaults to 'ASAP'.
        return_metadata (bool): return a dict with the list of composer and performer of the features. optional.  
    """

    pf_paths = []
    meta_dict = defaultdict(list)
    for dataset in datasets:
        if dataset == "VIENNA422":
            pf_paths.extend(glob.glob(os.path.join(VIENNA_MATCH_DIR, "*.npy")))
            meta_dict["composer"].extend([path.split("/")[4].split("_")[0] for path in pf_paths])
            meta_dict["performer"].extend([path.split("/")[4].split("_")[-3] for path in pf_paths])

        if dataset == "ASAP":
            pf_paths.extend(glob.glob(os.path.join(ASAP_DIR, "**/*.npy"), recursive=True))
            meta_dict["composer"].extend([path.split("/")[3] for path in pf_paths])
            meta_dict["performer"].extend([path.split("/")[-1].split("_")[0] for path in pf_paths])

        if dataset == "ATEPP":
            pf_paths.extend(glob.glob(os.path.join(ATEPP_DIR, "**/*.npy"), recursive=True))
            meta_csv = pd.read_csv(ATEPP_META_DIR)
            
            path = pf_paths[0]
            print(meta_csv[meta_csv['midi_path'].str.contains(path.split("/")[-1][:5])]['artist'].item())
            
            meta_dict["performer"].extend([meta_csv[meta_csv['midi_path'].str.contains(
                                            path.split("/")[-1][:5])]['artist'] for path in pf_paths])
            meta_dict['performer'] = [info.item() if len(info) == 1 else "unfound" for info in meta_dict['performer'] ]
            meta_dict["composer"].extend( [path.split("/")[3] for path in pf_paths])
        if dataset == "BMZ":
            pf_paths.extend(glob.glob(os.path.join(BMZ_MATCH_DIR, "**/*.npy"), recursive=True))
            composer = [path.split("/")[-1].split("_")[0] for path in pf_paths]
            meta_dict["composer"].extend(composer)
            meta_dict["performer"].extend(["Magdaloff" if c == "chopin" else "Zeillinger" for c in composer])

    pf = [np.load(path, allow_pickle=True) for path in pf_paths]
    if return_metadata:
        return pf, meta_dict
    
    return pf



def atepp_alignment():
    """redo the alignment of ATEPP dataset using parangonar"""

    score_paths, performance_paths = [], []
    all_performances = glob.glob(os.path.join(ATEPP_DIR, "**/*[0-9].mid"), recursive=True)
    for pp in all_performances:
        route = "/".join(pp.split("/")[:-1]) + "/"
        sp = glob.glob(route + "*.mxl") + glob.glob(route + "*.musicxml") 
        if len(sp):
            score_paths.append(sp[0])
            performance_paths.append(pp)

    for sp, pp in zip(score_paths, performance_paths):
        score = pt.load_score(filename= sp)
        performance = pt.load_performance_midi(filename=pp)

        # compute note arrays from the loaded score and performance
        pna = performance.note_array()
        sna = score.note_array()

        # match the notes in the note arrays
        sdm = pa.AutomaticNoteMatcher()
        pred_alignment = sdm(sna, pna)

        outdir = pp[:-4] + ".match"
        pa.match.save_parangonada_csv(pred_alignment, performance, score, outdir=outdir)
        alignment = pt.io.importparangonada.load_parangonada_alignment(filename= outdir)

    return pred_alignment


def process_dataset_pf(datasets=['ASAP']):
    """process the performance features for the given dataset. Save the 
    computed features in the form of numpy arrays in the same directory as 
    performance data.

    Args:
        datasets (list): dataset to process. Defaults to ['ASAP'].
    """

    for dataset in datasets:
        if "VIENNA422" in dataset:
            performance_paths = glob.glob(os.path.join(VIENNA_PERFORMANCE_DIR, "*[!e].mid"))
            alignment_paths = [(VIENNA_MATCH_DIR + pp.split("/")[-1][:-4] + ".match") for pp in performance_paths]
            score_paths = [(VIENNA_MUSICXML_DIR + pp.split("/")[-1][:-8] + ".musicxml") for pp in performance_paths]
            performance_paths = [None] * len(alignment_paths) # don't use the given performance, use the aligned.
        if "ASAP" in dataset:
            performance_paths = glob.glob(os.path.join(ASAP_DIR, "**/*[!e].mid"), recursive=True)
            alignment_paths = [(pp[:-4] + "_note_alignments/note_alignment.tsv") for pp in performance_paths]
            score_paths = [os.path.join("/".join(pp.split("/")[:-1]), "xml_score.musicxml") for pp in performance_paths]
        if "ATEPP" in dataset:
            alignment_paths = glob.glob(os.path.join(ATEPP_DIR, "**/*_match.txt"), recursive=True)
            performance_paths = [(aa[:-10] + ".mid") for aa in alignment_paths]
            score_paths = [glob.glob(os.path.join("/".join(pp.split("/")[:-1]), "*xml"))[0] for pp in performance_paths]
        if "BMZ" in dataset:
            alignment_paths = glob.glob(os.path.join(BMZ_MATCH_DIR, "**/*.match"), recursive=True)
            alignment_paths = [p for p in alignment_paths if (("Take" not in p) and ("mozart" not in p))]
            score_paths = [BMZ_MUSICXML_DIR + ap.split("/")[-1][:-6] + ".xml" for ap in alignment_paths]
            performance_paths = [None] * len(alignment_paths) # don't use the given performance, use the aligned.
        

        prev_s_path = None
        for s_path, p_path, a_path in tqdm(zip(score_paths, performance_paths, alignment_paths)):

            # parsing error
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/Scherzo_No._4_in_E_Major,_Op._54,_B._148/score.xml':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/Nocturne_No.13_in_C_minor,_Op._48_No._1/score.xml':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/24_Preludes,_Op._28/No._7_in_A_Major:_Andantino/score.xml':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No.4_in_E_flat,_K.282/2._Menuetto_I-II/score.xml':
                continue
            if s_path == "../Datasets/pianodata-master/xml/chopin_op35_Mv3.xml": # BMZ
                continue
            if s_path == '../Datasets/asap-dataset-alignment/Chopin/Scherzos/31/xml_score.musicxml': # ASAP
                continue
            if s_path == '../Datasets/asap-dataset-alignment/Ravel/Gaspard_de_la_Nuit/1_Ondine/xml_score.musicxml': # ASAP
                continue
            if a_path == '../Datasets/asap-dataset-alignment/Beethoven/Piano_Sonatas/23-1/LiuC02M_note_alignments/note_alignment.tsv':
                continue # tempo_grad floating point error
            if s_path == '../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/xml_score.musicxml': # ASAP tempo
                continue

            if (os.path.exists(s_path) and os.path.exists(a_path)):

                if prev_s_path == s_path:
                    pf, score = compute_performance_features(s_path, a_path, p_path, score=score)
                else:
                    pf, score = compute_performance_features(s_path, a_path, p_path)

                if dataset == "ASAP":
                    np.save(f"{p_path[:-4]}_perf_features.npy", pf)
                if (dataset == "BMZ") or (dataset == "VIENNA422"):
                    np.save(f"{a_path[:-6]}_perf_features.npy", pf) 
                if (dataset == "ATEPP"):
                    np.save(f"{a_path[:-4]}_perf_features.npy", pf)                 
                prev_s_path = s_path
            else:
                print(f"Data incomplete for {a_path}")

    return 


def compute_performance_features(score_path, alignment_path, performance_path=None, score=None, append_pe=False):
    """compute the performance feature given score, alignment and performance path.

    
    
    Args:
        dataset (str, optional): _description_. Defaults to 'ASAP'.
    """
    if alignment_path[-5:] == "match":
        performance, alignment = pt.load_match(alignment_path)
    elif alignment_path[-3:] == "tsv":
        alignment = pt.io.importparangonada.load_alignment_from_ASAP(alignment_path)
    else: # case for ATEPP with nakamura alignment
        _, _, _, alignment = pt.load_nakamuramatch(alignment_path)

    if isinstance(score, type(None)): # if no loaded score from previous round
        score = pt.load_musicxml(score_path)
        # if doesn't match the version in alignment, unfold the score.
        if ('score_id' in alignment[0]) and ("-" in alignment[0]['score_id']): 
            score = pt.score.unfold_part_maximal(pt.score.merge_parts(score.parts)) 

    if not isinstance(performance_path, type(None)): # use the performance if it's given
        performance = pt.load_performance(performance_path)

    pf, res = pt.musicanalysis.compute_performance_features(score, performance, alignment, feature_functions="all")
    # hook()

    # append the performance encodings to the pf 
    if append_pe:
        parameters, snote_ids = pt.musicanalysis.encode_performance(score, performance, alignment)
        pf = rfn.merge_arrays([pf, parameters], flatten=True)
    return pf, score


if __name__ == "__main__":

    # atepp_alignment()
    process_dataset_pf(datasets=[
                                # "BMZ",
                                # "VIENNA422",
                                # "ASAP",
                                "ATEPP",
                                ])
    
    # load_dataset_pf(datasets=[
    #                         # "BMZ",
    #                         # "VIENNA422",
    #                         "ASAP",
    #                         # "ATEPP",
    #                         ])
