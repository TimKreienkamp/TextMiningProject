"""
Created on Tue Jun  9 10:24:53 2015

@author: timkreienkamp
"""
################################################################
# 0. Load Data and Libraries
################################################################


import pandas as pd
import numpy as np
from nltk.stem import *
from h2o import *
from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer, TfidfTransformer
from sklearn.preprocessing import LabelEncoder 
from sklearn.metrics import accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.cross_validation import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC, SVC
from nltk import word_tokenize
import string
import chardet
import nltk
import matplotlib.pyplot as plt
from sklearn.grid_search import GridSearchCV as gsc
import lda

raw_data = pd.read_csv("/users/timkreienkamp/documents/studium/data_science/tm_project/textminingproject/data/speech_data.csv")

raw_data = raw_data.dropna()
# sanity check
print raw_data.iloc[1:5,:]

with open("../data/stopwords.txt", 'r') as stopword_file:
    stopwords = stopword_file.read()

stopwords = stopwords.split('\n')
raw_data.party.apply(lambda x: x.strip("*"))
raw_data.party.apply(lambda x: x.strip("*"))


corpus = raw_data.speech.tolist()

################################################################
# 1. Data preparation
################################################################


stemmer = SnowballStemmer("german")

table = string.maketrans("","")
def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed

def tokenize(text):
    tokens = nltk.tokenize.WordPunctTokenizer().tokenize(text)
    stems = stem_tokens(tokens, stemmer)

    return stems


for i in range(0,len(corpus)):
    corpus[i] = corpus[i].lower()
    corpus[i] = corpus[i].translate(table, string.punctuation)
    corpus[i] = corpus[i].decode('utf8')


tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words=stopwords)
tfs = tfidf.fit_transform(np.asarray(corpus))


col_sums = np.sum(tfs.toarray(), axis = 0)
indices = np.argsort(col_sums)
indices = indices.tolist()

tf_idf_ranking = np.sort(col_sums)[::-1]

encoder = LabelEncoder()
y = encoder.fit_transform(raw_data.party)



plt.plot(tf_idf_ranking[5000:10000])

################################################################
# 2. Grid Search Experiments
################################################################

# setting up the parameter search space

param_grid_linear_svc = {'C':[0.001, 0.01, 0.1, 1.0, 2.0]}
param_grid_log_reg = {'C': [0.001, 0.01, 0.1, 1, 1.0, 2.0]}
param_grid_rf = {'n_estimators': [50, 100, 200]}

# setting up the function search space
model_dict = {'linear_svm':{'clf':LinearSVC(dual = False, penalty = "l1"), 'param_grid' : param_grid_linear_svc},
              "logistic" :{'clf': LogisticRegression(penalty = "l1"), 'param_grid' : param_grid_log_reg},
                "RF": {'clf': RandomForestClassifier(), 'param_grid': param_grid_rf}
                
                }
     
# a function to run gridsearches with multiple base model           
def test_models(model_dict, nfolds, X, y, score):
    results = {}
    for model_key in model_dict.keys():
        print model_key 
        base_model = model_dict[model_key]['clf']
        grid = model_dict[model_key]['param_grid']
        gs_cv = gsc(estimator = base_model, param_grid = grid, cv = StratifiedKFold(y, n_folds = nfolds, random_state = 2), scoring = score)
        gs_fit = gs_cv.fit(X, y)
        dict_ = {}
        best_score = gs_fit.best_score_
        print best_score
        best_params = gs_fit.best_params_
        dict_['best_score'] = best_score
        dict_['best_params'] = best_params
        results[model_key] = dict_
    return results
  
# running the experiments    
        
highest_n = [200, 500, 750, 1000, 2000, 3000, 4000, 5000, 7500, 10000, 12500, 15000] 
for n in highest_n:
    print n
    X = tfs.toarray()[:,[indices[::-1][0:n]][0]]
    results = test_models(model_dict, 6, X, y, "f1_weighted")
    
    overall_results[str(n)] = results


##### some hustle to get it all in the format ggplot2 wants it 

best_scores_svm = []
best_scores_logistic = []
best_scores_rf = []

for i in range(i, len(highest_n)):
    n = highest_n[i]
    best_scores_svm.append(overall_results[str(n)]["linear_svm"]["best_score"])
    best_scores_logistic.append(overall_results[str(n)]["logistic"]["best_score"])
    best_scores_rf.append(overall_results[str(n)]["RF"]["best_score"])
        
model_svm = np.repeat("Linear SVM", len(best_scores_svm)).tolist()
model_log = np.repeat("Logistic Regression", len(best_scores_svm)).tolist()
model_rf = np.repeat("Random Forest", len(best_scores_svm)).tolist()

model_ = []
model_.extend(model_svm)
model_.extend(model_log)
model_.extend(model_rf)

best_scores = []
best_scores.extend(best_scores_svm)
best_scores.extend(best_scores_logistic)
best_scores.extend(best_scores_rf)

highest_n_list = []
highest_n_list.extend(highest_n)
highest_n_list.extend(highest_n)
highest_n_list.extend(highest_n)



results_grid_benchmarking = pd.DataFrame({'Base Model': model_, 'F1_Score': best_scores, "N highest ranked tf_idfs": highest_n_list})

# save results for visualisation
results_grid_benchmarking.to_csv("../data/results_grid_benchmarking.csv", index = False)



##############################################################################
#3. LDA Feature Construction
##############################################################################



