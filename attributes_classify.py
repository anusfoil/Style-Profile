from sklearn import tree, svm
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report
from asynchrony import *


def classify():
    
    meta_attributes = compute_all_attributes().dropna() # remove data with no attribute

    artists_counts=meta_attributes['artist_id'].value_counts() # remove class with few data
    filtered_labels = artists_counts[artists_counts>15].index
    meta_attributes = meta_attributes[meta_attributes['artist_id'].isin(filtered_labels)]

    meta_attributes = meta_attributes.sample(frac=1) # shuffle
    N = len(meta_attributes)
    attributes_train, attributes_test = meta_attributes.iloc[:int(N*0.8), :], meta_attributes.iloc[int(N*0.8):, :]

    X = list(zip(*[attributes_train[attri] for attri in ATTRIBUTES]))
    Y = attributes_train['artist_id'].tolist()

    # clf = tree.DecisionTreeClassifier()
    clf = svm.SVC()
    # clf = AdaBoostClassifier(n_estimators=100)
    # clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, max_depth=1, random_state=0)
    # clf = MLPClassifier(alpha=1e-5, hidden_layer_sizes=(128, 64, 32), random_state=1, warm_start=True)
    clf = clf.fit(X, Y)

    y_true = attributes_test['artist_id'].tolist()
    y_pred = clf.predict(list(zip(*[attributes_test[attri] for attri in ATTRIBUTES])))
    print(classification_report(y_true, y_pred))


if __name__ == "__main__":
    classify()