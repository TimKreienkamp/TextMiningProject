# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 20:36:18 2015

@author: timkreienkamp
"""

import pandas as pd
import numpy as np
from nltk.stem import *
from h2o import *

raw_data = pd.read_csv("/users/timkreienkamp/documents/studium/data_science/tm_project/textminingproject/data/speech_data.csv")

raw_data = raw_data.dropna()
# sanity check
print raw_data.iloc[1:5,:]

with open("../data/stopwords.txt", 'r') as stopword_file:
    stopwords = stopword_file.read()

stopwords = stopwords.split('\n')
raw_data.party.apply(lambda x: x.strip("*"))
#######data exploration#########


######data preparation##########


from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer, TfidfTransformer
from sklearn.preprocessing import LabelEncoder 
from sklearn.metrics import accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.cross_validation import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC, SVC


vectorizer = CountVectorizer(min_df=1)
encoder = LabelEncoder()

transformer = TfidfTransformer()


corpus = raw_data.speech

X = vectorizer.fit_transform(corpus)
X_tf_idf = transformer.fit_transform(X)


y = encoder.fit_transform(raw_data.party)


log_reg = LogisticRegression(penalty = "l1", verbose = 5)
svm_ = LinearSVC(penalty = 'l1', dual = False)
sgd_ = SGDClassifier(loss = "hinge", penalty = "l1", alpha = 0.0001)
svm_rbf = SVC()

cv = StratifiedKFold(y, n_folds = 6, random_state = 2)

accuracy_log_reg_list = []
accuracy_svm_list = []
accuracy_sgd_list = []
accuracy_svm_rbf_list = []

f1_log_reg_list = []
f1_svm_list = []
f1_sgd_list = []
f1_svm_rbf_list = []

X_tf_idf = tfs
i = 1 
for traincv, testcv in cv:
    print i
    log_reg_fit = log_reg.fit(X_tf_idf[traincv], y[traincv])
    svm_fit = svm_.fit(X_tf_idf[traincv], y[traincv])
    sgd_fit = sgd_.fit(X_tf_idf[traincv], y[traincv])
    #svm_rbf_fit = svm_rbf.fit(X_tf_idf[traincv], y[traincv])
    
    preds_log_reg = log_reg_fit.predict(X_tf_idf[testcv])
    preds_svm = svm_fit.predict(X_tf_idf[testcv])
    preds_sgd = sgd_fit.predict(X_tf_idf[testcv])
    #preds_svm_rbf = svm_rbf.predict(X_tf_idf[testcv])
    
    accuracy_log = accuracy_score(y[testcv], preds_log_reg)
    accuracy_svm = accuracy_score(y[testcv], preds_svm)
    accuracy_sgd  = accuracy_score(y[testcv], preds_sgd)
    #accuracy_svm_rbf = accuracy_score(y[testcv], preds_svm_rbf)
    
    f1_log_reg = f1_score(y[testcv], preds_log_reg)
    f1_svm = f1_score(y[testcv], preds_svm)
    f1_sgd = f1_score(y[testcv], preds_sgd)
    #f1_svm_rbf = f1_score(y[testcv], preds_svm_rbf)
    
    accuracy_log_reg_list.append(accuracy_log)
    accuracy_svm_list.append(accuracy_svm)
    accuracy_sgd_list.append(accuracy_sgd)
    #accuracy_svm_rbf_list.append(accuracy_svm_rbf)
    f1_log_reg_list.append(f1_log_reg)
    f1_svm_list.append(f1_svm)
    f1_sgd_list.append(f1_sgd)
    #f1_svm_rbf_list.append(f1_svm_rbf)
    
    
    i += 1

overall_log_reg = np.mean(accuracy_log_reg_list)
overall_svm = np.mean(accuracy_svm_list)
overall_sgd = np.mean(accuracy_sgd_list)
#overall_svm_rbf = np.mean(accuracy_svm_rbf_list)
mean_f1_log_reg = np.mean(f1_log_reg_list)
mean_f1_svm= np.mean(f1_svm_list)
mean_f1_sgd = np.mean(f1_sgd_list)
#mean_f1_svm_rbf = np.mean(f1_svm_rbf_list)


print "Accuracy log_reg :" + str(overall_log_reg)
print "Accuracy svm :" + str(overall_svm)
print "Accuracy sgd :" + str(overall_sgd)
#print "Accuracy SVM (RBD): " + str(overall_svm_rbf)

print "f1 log_reg :" + str(mean_f1_log_reg)
print "f1 svm :" + str(mean_f1_svm)
print "f1 Sgd :" + str(mean_f1_sgd)
#print "f1 Svm RBF: " + str(mean_f1_svm_rbf)

gbt = GradientBoostingClassifier()
accuracy_gbt_list = []
for traincv, testcv in cv:
    print i
    svm_fit = svm_.fit(X_tf_idf[traincv], y[traincv])
    X_ = svm_fit.transform(X_tf_idf[traincv]).toarray()
    X_test = svm_fit.transform(X_tf_idf[testcv]).toarray()
    gbt_fit = rf().fit(X_, y[traincv])
    gbt_preds = gbt_fit.predict(X_test)
    accuracy_gbt = accuracy_score(y[testcv], gbt_preds)
    accuracy_gbt_list.append(accuracy_gbt)

print np.mean(accuracy_rf_list)