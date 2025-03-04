#!/usr/bin/python3
# https://github.com/kvntng17/weighted-kmeans/blob/master/kmeans.py

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

import matplotlib 
matplotlib.use("TkAgg")
import matplotlib.pyplot as matplt

def load_csv(fn):
    # importing or loading the dataset
    dataset = pd.read_csv(fn)
    # for i, c in enumerate(dataset.columns):
    #     v = dataset.values[:,i]
    #     pass
    # distributing the dataset into two components X and Y
    packages = dataset.iloc[1:, 0].values
    weights = dataset.iloc[0, 1:].values
    weights = weights.astype(int)
    weights = np.insert(weights, 0, 0)
    # X = dataset.iloc[:, 1:8].values
    # X = dataset.iloc[:, 14:21].values
    # X = dataset.iloc[:, 23:40].values
    indicies = []
    # indicies += [*range(1, 8)]
    # indicies += [*range(14,21)]
    # indicies += [*range(23,40)]
    # indicies += [*range(42,48), *range(52,53), *range(57,58), 60]
    indicies += [*range(1, 6)]
    X = dataset.iloc[1:, indicies].values
    weights = weights[indicies]
    # y = dataset.iloc[:, 13].values
    return [packages, X, weights]

def pca(packages, X, weights):
    # Weights as frequency
    for i, wt in reversed(list(enumerate(weights))):
        if wt == 0:
            X = np.delete(X, np.s_[i], axis=1)  
        for _ in range(1, wt):
            X = np.c_[X, X[:, i]]

    # TBD: Remove no C/C++ package

    # Preprocessing - Normalizing the features
    X = StandardScaler().fit_transform(X)  
    # Principal Component Analysis
    pca = PCA(n_components = 4)
    pca_scores = pca.fit_transform(X)
    print(f'Explained variation per principal component: {pca.explained_variance_ratio_}')
    # pca_scores_df = pd.DataFrame(data = pca_scores, columns = ['principal component 1', 'principal component 2', 'principal component 3', 'principal component 4'])
    # K-means
    kmeans_model = KMeans(n_clusters=4, init='k-means++')
    kmeans_label = kmeans_model.fit_predict(pca_scores)
    kmeans_centroids = kmeans_model.cluster_centers_

    # Ploting
    matplt.figure(figsize=(10,10))
    uniq = np.unique(kmeans_label)
    for i in uniq:
        x = pca_scores[kmeans_label == i , 0]
        y = pca_scores[kmeans_label == i , 1]
        matplt.scatter(x, y, label = f'Cluster {i}')
        txts = packages[kmeans_label == i]
        for i, txt in enumerate(txts):
            matplt.annotate(txt, (x[i], y[i]))
    matplt.scatter(kmeans_centroids[:, 0], kmeans_centroids[:, 1], c='black', s=50, marker='x')
    matplt.legend()
    matplt.grid(True)
    matplt.xlabel('Principal Component - 1',fontsize=20)
    matplt.ylabel('Principal Component - 2',fontsize=20)
    matplt.title("Principal Component Analysis + K-Means Clustering",fontsize=20)
    matplt.show()

    # Ploting
    # [fig, ax] = matplt.subplots()
    # matplt.scatter(pca_scores_df.loc[:, 'principal component 1'], pca_scores_df.loc[:, 'principal component 2'], c = 'r', s = 50)
    # 
    # matplt.show()
    
    # plt.figure()
    # plt.figure(figsize=(10,10)) matplt.show()
    # plt.xticks(fontsize=12)
    # plt.yticks(fontsize=14)
 
    # 
    
    # targets = ['Benign', 'Malignant']
    # colors = ['r', 'g']
    # for target, color in zip(targets,colors):
    #     indicesToKeep = breast_dataset['label'] == target
    #     plt.scatter(pca_X_Df.loc[indicesToKeep, 'principal component 1'], pca_X_Df.loc[indicesToKeep, 'principal component 2'], c = color, s = 50)
    # plt.legend(targets,prop={'size': 15})

    return True

if __name__ == '__main__':
    # fp = './pca/stats-all-weighted-code-20230531-3.csv'
    # fp = './pca/stats-all-weighted-jemalloc-corrected.csv'
    fp = './pca/stats-all-weighted-rado-3.csv'
    [packages, X, weights] = load_csv(fp)
    pca(packages, X, weights)