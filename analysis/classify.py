import sys
sys.path.insert(0,'..')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import graphviz
from sklearn import tree, svm
from sklearn.preprocessing import normalize
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score, cross_validate
from sklearn.metrics import classification_report
from sklearn.inspection import permutation_importance
from scipy.stats import f_oneway
from params import *
import hook

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

def classify(meta_attributes, plot=False):
    
    meta_attributes = meta_attributes.drop(columns=[x for x in ALL_ATTRIBUTES if x not in ATTRIBUTES])
    meta_attributes = meta_attributes.dropna()
    print(len(meta_attributes))
    print(meta_attributes.columns)

    division = 'artist'

    artists_counts=meta_attributes[division].value_counts() # remove class with few data
    filtered_labels = artists_counts[artists_counts>50].index
    meta_attributes = meta_attributes[meta_attributes[division].isin(filtered_labels)]
    print(filtered_labels)

    meta_attributes = meta_attributes.sample(frac=1) # shuffle

    X = list(zip(*[meta_attributes[attri] for attri in ATTRIBUTES]))
    # X = normalize(X)
    y = meta_attributes[division].tolist()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=0)


    # clf = tree.DecisionTreeClassifier()
    clf = RandomForestClassifier()
    # clf = svm.SVC()
    # clf = AdaBoostClassifier(n_estimators=100)
    # clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=1, random_state=0)
    # clf = MLPClassifier(alpha=1e-3, hidden_layer_sizes=(128, 64, 32), random_state=1, warm_start=True)
    clf = clf.fit(X_train, y_train)

    if (type(clf) == tree.DecisionTreeClassifier) and plot:
        dot_data = tree.export_graphviz(clf, out_file=None, 
                                        feature_names=ATTRIBUTES,  
                                        class_names=filtered_labels,
                                        filled=True)
        graph = graphviz.Source(dot_data, format="png") 
        graph.render("decision_tree_graphivz")
        # hook()

    if (type(clf) == RandomForestClassifier) and plot:
        impurity_importances = clf.feature_importances_
        # print(list(zip(ATTRIBUTES, impurity_importances)))
        std = np.std([tree.feature_importances_ for tree in clf.estimators_], axis=0)

        forest_importances = pd.Series(impurity_importances, index=ATTRIBUTES)
        fig, ax = plt.subplots()
        forest_importances.plot.bar(yerr=std, ax=ax)
        ax.set_title("Feature importances using MDI")
        ax.set_ylabel("Mean decrease in impurity")
        fig.tight_layout()
        hook()

    scores = cross_val_score(clf, X, y, cv=5, scoring="accuracy")
    print(f"accuracy: {round(scores.mean(), 3)}±{round(scores.std(), 3)}")
    scores = cross_val_score(clf, X, y, cv=5, scoring="f1_weighted")
    print(f"f1_weighted: {round(scores.mean(), 3)}±{round(scores.std(), 3)}")
    # hook()
    # y_pred = clf.predict(X_test)
    # print(classification_report(y_test, y_pred))


if __name__ == "__main__":
    classify(pd.read_csv(ATEPP_ATTRIBUTES) )
    # anova()