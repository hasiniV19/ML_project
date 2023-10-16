# -*- coding: utf-8 -*-
"""layer_8_190647X.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ve30GW6aKdTeuUDvDf7icjiqskxgYTJs

# Data loading
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
import numpy as np

# path to datasets
path_train = "/content/drive/MyDrive/SEM 7/Machine Learning/ML Project/layer_8/train.csv"
path_valid = "/content/drive/MyDrive/SEM 7/Machine Learning/ML Project/layer_8/valid.csv"
path_test = "/content/drive/MyDrive/SEM 7/Machine Learning/ML Project/layer_8/test.csv"

train = pd.read_csv(path_train)
valid = pd.read_csv(path_valid)
test = pd.read_csv(path_test)

LABELS = ["label_1", "label_2", "label_3", "label_4"]
FEATURES = [column for column in train.columns if column not in LABELS]
L1, L2, L3, L4 = "label_1", "label_2", "label_3", "label_4"

y_pred = {}

from sklearn.metrics import accuracy_score

"""# Standardization"""

from sklearn.preprocessing import RobustScaler

X_train = {}
X_valid = {}
y_train = {}
y_valid = {}
X_test = {}

for label in LABELS:
  train_df = train[train['label_2'].notna()] if label == 'label_2' else train
  valid_df = valid[valid['label_2'].notna()] if label == 'label_2' else valid
  test_df = test

  scaler = RobustScaler()
  X_train[label] = pd.DataFrame(scaler.fit_transform(train_df.drop(LABELS, axis=1)), columns=FEATURES)
  y_train[label] = train_df[label]
  X_valid[label] = pd.DataFrame(scaler.transform(valid_df.drop(LABELS, axis=1)), columns=FEATURES)
  y_valid[label] = valid_df[label]
  X_test[label]  = pd.DataFrame(scaler.transform(test_df.drop("ID", axis=1)), columns=FEATURES)

"""# Correlation functions"""

def get_corr_features(threshold, dataframe):
  """
      return correlated features
  """
  corr_matrix = dataframe.corr().abs()
  # mask to identify highly correlated features
  corr_mask = (corr_matrix > threshold) & (corr_matrix < 1)

  # find correlated features
  cols_drop = set()

  for col in corr_mask.columns:
    corr_cols = corr_mask[col][corr_mask[col]].index.tolist()
    if corr_cols:
      cols_drop.add(min(corr_cols, key=lambda x: dataframe[x].nunique()))  # Keep the column with fewer unique values

  return corr_cols

def get_weakly_corr_feat(dataframe, label_name, label_col_data, threshold=0.01):
  """
      returns a list of features names that have weak correlations with the label.
  """
  copy_df = dataframe.copy()

  copy_df[label_name] = label_col_data
  # calculate the correlation matrix
  corr_matrix = copy_df.corr()

  # Extract the column index of the specified label column
  label_col_index = corr_matrix.columns.get_loc(label_name)
  # label_col_index = corr_matrix_y.columns.get_loc(label_name)

  # Get the correlation values between features and the specified label
  corr_with_label = corr_matrix.iloc[:, label_col_index]

  # Filter for features that are weakly correlated with the label based on the threshold
  weakly_corr_features = corr_with_label[
      (corr_with_label.index != label_name) & (corr_with_label.abs() < threshold)
  ]

  return weakly_corr_features.index.tolist()

"""# PCA function"""

from sklearn.decomposition import PCA

def run_PCA(train_df, valid_df, test_df, threshold=0.95):
  pca = PCA(n_components=threshold, svd_solver='full')

  pca.fit(train_df)

  pca_train = pd.DataFrame(pca.transform(train_df))
  pca_valid = pd.DataFrame(pca.transform(valid_df))
  pca_test = pd.DataFrame(pca.transform(test_df))

  return pca_train, pca_valid, pca_test

"""# SVC function"""

from sklearn.svm import SVC
from sklearn.model_selection import RandomizedSearchCV

def run_SVC(param_dist, n_iter, x_train, y_train, cv=5, random_state=42):
  # Create an SVC classifier
  svc = SVC()

  # Create a RandomizedSearchCV object
  random_search = RandomizedSearchCV(estimator=svc, param_distributions=param_dist, n_iter=n_iter, cv=cv, scoring='accuracy', random_state=random_state)

  # Perform hyperparameter tuning
  random_search.fit(x_train, y_train)

  # Get the best model from Random Search
  best_model = random_search.best_estimator_
  best_params = random_search.best_params_

  return best_model, best_params

"""# Label 1

## Correlation
"""

train_cols_drop = get_corr_features(0.5, X_train[L1])

# remove correlated features from train data
train_label1 = X_train[L1].drop(columns=list(train_cols_drop)) # if inplace=True, object will modified. no object returned
# remove correlated features from valid data
valid_label1 = X_valid[L1].drop(columns=list(train_cols_drop))
# remove correlated features from test data
test_label1 = X_test[L1].drop(columns=list(train_cols_drop))

print(len(train_cols_drop))

train_label1.head()

new_train_cols_drop = get_weakly_corr_feat(train_label1, L1, y_train[L1])

# remove weakly correlated features
train_after_corr_l1 = train_label1.drop(columns=new_train_cols_drop)
# remove weakly correlated features
valid_after_corr_l1 = valid_label1.drop(columns=new_train_cols_drop)
# remove weakly correlated features
test_after_corr_l1 = test_label1.drop(columns=new_train_cols_drop)

train_after_corr_l1.head()

"""## PCA"""

pca_train_L1, pca_valid_L1, pca_test_L1 = run_PCA(train_after_corr_l1, valid_after_corr_l1, test_after_corr_l1)

"""## SVC"""

from sklearn.svm import SVC
from sklearn.model_selection import RandomizedSearchCV

# Define the parameter distribution for Random Search
param_dist = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': [0.001, 0.01, 0.1]
}

best_model, best_params = run_SVC(param_dist, 5, pca_train_L1, y_train[L1], 2, 42)

from sklearn.metrics import accuracy_score

y_pred_L1_valid = best_model.predict(pca_valid_L1)
y_pred_L1_test = best_model.predict(pca_test_L1)
accuracy_L1 = accuracy_score(y_valid[L1], y_pred_L1_valid)

print(f"Accuracy on test data - Label 1: {accuracy_L1}")

y_pred[L1] = y_pred_L1_test

print(y_pred[L1])

"""# Label 2

## Correlation
"""

train_cols_drop_L2 = get_corr_features(0.5, X_train[L2])

# remove correlated features from train data
train_label2 = X_train[L2].drop(columns=list(train_cols_drop_L2)) # if inplace=True, object will modified. no object returned
# remove correlated features from valid data
valid_label2 = X_valid[L2].drop(columns=list(train_cols_drop_L2))
# remove correlated features from test data
test_label2 = X_test[L2].drop(columns=list(train_cols_drop_L2))

print("Correlated columns", len(train_cols_drop_L2))

new_train_cols_drop_L2 = get_weakly_corr_feat(train_label2, L2, y_train[L2])

# remove weakly correlated features
train_after_corr_l2 = train_label2.drop(columns=new_train_cols_drop_L2)
# remove weakly correlated features
valid_after_corr_l2 = valid_label2.drop(columns=new_train_cols_drop_L2)
# remove weakly correlated features
test_after_corr_l2 = test_label2.drop(columns=new_train_cols_drop_L2)

train_after_corr_l2.head()

"""## PCA"""

pca_train_L2, pca_valid_L2, pca_test_L2 = run_PCA(train_after_corr_l2, valid_after_corr_l2, test_after_corr_l2)

"""## SVC"""

# Define the parameter distribution for Random Search
param_dist = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': [0.001, 0.01, 0.1]
}

best_model, best_params = run_SVC(param_dist, 5, pca_train_L2, y_train[L2], 2, 42)

y_pred_L2_valid = best_model.predict(pca_valid_L2)
y_pred_L2_test = best_model.predict(pca_test_L2)
accuracy_L2 = accuracy_score(y_valid[L2], y_pred_L2_valid)

print(f"Accuracy on test data - Label 2: {accuracy_L2}")

y_pred[L2] = y_pred_L2_test

"""# Label 3

## Correlation
"""

train_cols_drop_L3 = get_corr_features(0.5, X_train[L3])

# remove correlated features from train data
train_label3 = X_train[L3].drop(columns=list(train_cols_drop_L3)) # if inplace=True, object will modified. no object returned
# remove correlated features from valid data
valid_label3 = X_valid[L3].drop(columns=list(train_cols_drop_L3))
# remove correlated features from test data
test_label3 = X_test[L3].drop(columns=list(train_cols_drop_L3))

print("Correlated columns", len(train_cols_drop_L3))

new_train_cols_drop_L3 = get_weakly_corr_feat(train_label3, L3, y_train[L3])

# remove weakly correlated features
train_after_corr_l3 = train_label3.drop(columns=new_train_cols_drop_L3)
# remove weakly correlated features
valid_after_corr_l3 = valid_label3.drop(columns=new_train_cols_drop_L3)
# remove weakly correlated features
test_after_corr_l3 = test_label3.drop(columns=new_train_cols_drop_L3)

train_after_corr_l3.head()

"""## PCA"""

pca_train_L3, pca_valid_L3, pca_test_L3 = run_PCA(train_after_corr_l3, valid_after_corr_l3, test_after_corr_l3)

"""## SVC"""

# Define the parameter distribution for Random Search
param_dist = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': [0.001, 0.01, 0.1]
}

best_model, best_params = run_SVC(param_dist, 5, pca_train_L3, y_train[L3], 2, 42)

y_pred_L3_valid = best_model.predict(pca_valid_L3)
y_pred_L3_test = best_model.predict(pca_test_L3)
accuracy_L3 = accuracy_score(y_valid[L3], y_pred_L3_valid)

print(f"Accuracy on test data - Label 2: {accuracy_L3}")

y_pred[L3] = y_pred_L3_test

"""# Label 4

## Correlation
"""

train_cols_drop_L4 = get_corr_features(0.5, X_train[L4])

# remove correlated features from train data
train_label4 = X_train[L4].drop(columns=list(train_cols_drop_L4)) # if inplace=True, object will modified. no object returned
# remove correlated features from valid data
valid_label4 = X_valid[L4].drop(columns=list(train_cols_drop_L4))
# remove correlated features from test data
test_label4 = X_test[L4].drop(columns=list(train_cols_drop_L4))

print("Correlated columns", len(train_cols_drop_L4))

new_train_cols_drop_L4 = get_weakly_corr_feat(train_label4, L4, y_train[L4])

# remove weakly correlated features
train_after_corr_l4 = train_label4.drop(columns=new_train_cols_drop_L4)
# remove weakly correlated features
valid_after_corr_l4 = valid_label4.drop(columns=new_train_cols_drop_L4)
# remove weakly correlated features
test_after_corr_l4 = test_label4.drop(columns=new_train_cols_drop_L4)

train_after_corr_l4.head()

"""## PCA"""

pca_train_L4, pca_valid_L4, pca_test_L4 = run_PCA(train_after_corr_l4, valid_after_corr_l4, test_after_corr_l4)

"""## SVC"""

# Define the parameter distribution for Random Search
param_dist = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': [0.001, 0.01, 0.1]
}

best_model, best_params = run_SVC(param_dist, 5, pca_train_L4, y_train[L4], 2, 42)

y_pred_L4_valid = best_model.predict(pca_valid_L4)
y_pred_L4_test = best_model.predict(pca_test_L4)
accuracy_L4 = accuracy_score(y_valid[L4], y_pred_L4_valid)

print(f"Accuracy on test data - Label 4: {accuracy_L4}")

y_pred[L4] = y_pred_L4_test

"""# Write to CSV file"""

path = "/content/drive/MyDrive/SEM 7/Machine Learning/ML Project/layer_8/layer_8.csv"
list_of_ids = test["ID"]

result = {
    "ID": list_of_ids,
    L1: y_pred[L1],
    L2: y_pred[L2],
    L3: y_pred[L3],
    L4: y_pred[L4]
}

DF_result = pd.DataFrame(result)

DF_result.to_csv(path, index=False)