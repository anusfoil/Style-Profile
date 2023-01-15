import sys
sys.path.insert(0,'..')
import numpy as np
import pandas as pd
from sklearn import tree, svm
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report
from scipy.stats import f_oneway
from params import *

import pandas as pd


def anova():

    meta_attributes = compute_all_attributes() 

    artists_counts=meta_attributes['artist_id'].value_counts() # remove class with few data
    filtered_labels = artists_counts[artists_counts>25].index
    meta_attributes = meta_attributes[meta_attributes['artist_id'].isin(filtered_labels)]

    for attribute in ATTRIBUTES:
        attribute_by_artist = [meta_attributes.loc[v][attribute].dropna().to_numpy() for k, v in meta_attributes.groupby('artist').groups.items()]
        attribute_by_artist = [l for l in attribute_by_artist if len(l)]
        anova = f_oneway(*attribute_by_artist)

        print(f"{attribute}: {anova.pvalue}")
        
    hook()
    return 

def classify(meta_attributes):
    
    # meta_attributes = meta_attributes.drop(columns=['sp_async_parts', 'sp_tempo_std'])
    # meta_attributes = meta_attributes.dropna()

    division = 'artist'

    artists_counts=meta_attributes[division].value_counts() # remove class with few data
    filtered_labels = artists_counts[artists_counts>20].index
    meta_attributes = meta_attributes[meta_attributes[division].isin(filtered_labels)]

    meta_attributes = meta_attributes.sample(frac=1) # shuffle
    N = len(meta_attributes)
    attributes_train, attributes_test = meta_attributes.iloc[:int(N*0.8), :], meta_attributes.iloc[int(N*0.8):, :]

    X = list(zip(*[attributes_train[attri] for attri in ATTRIBUTES]))
    Y = attributes_train[division].tolist()

    df = pd.DataFrame(X, Y)
    df = df[df[3] != np.float("-inf")]
    X = df.values.tolist()
    Y = df.index.tolist()

    # clf = tree.DecisionTreeClassifier()
    # clf = svm.SVC()
    # clf = AdaBoostClassifier(n_estimators=100)
    # clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, max_depth=1, random_state=0)
    clf = MLPClassifier(alpha=1e-5, hidden_layer_sizes=(128, 64, 32), random_state=1, warm_start=True)
    clf = clf.fit(X, Y)

    y_true = attributes_test['artist_id'].tolist()
    X_ = list(zip(*[attributes_test[attri] for attri in ATTRIBUTES]))
    df = pd.DataFrame(X_, y_true)
    df = df[df[3] != np.float("-inf")]
    X_ = df.values.tolist()
    y_true = df.index.tolist()    
    y_pred = clf.predict(X_)
    print(classification_report(y_true, y_pred))


if __name__ == "__main__":
    classify(pd.read_csv(ATEPP_ATTRIBUTES) )
    # anova()