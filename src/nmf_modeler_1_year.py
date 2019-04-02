import pandas as pd
import numpy as np
from scipy import sparse
from os import path
#from PIL import Image
#from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from collections import Counter, defaultdict
#import matplotlib.pyplot as plt
from datetime import datetime as dt
from sklearn import decomposition, datasets, model_selection, preprocessing, metrics

import os
import glob
import pickle

def get_dataframe(path):

    all_files =[]
    for f in range(1,366):
        all_files.append(path+"%d.json"%f)
    df = pd.concat((pd.read_json(f,keep_default_dates=False,lines=True) for f in all_files)) 
    df=df[df['term']<10]
    df['date']=pd.to_datetime(df['date'],yearfirst=True)
    df['day_of_week']=df['date'].dt.day
    df['month']=df['date'].dt.month
    return df


def get_items(df,most_common=10,least_common=5):
    df['total_of_items'] = 0
    stoppers = ['BAG CREDIT','SF Bag Charge','Gift Card Reload','8 OZ BIO TUB t3', '16OZ BIO TUB t4',
                 '32OZ BIO TUB t5','BOTTLE DEPOSIT','6PACK BEER SMALL C','PAID IN','Gift Card Sale','PACKAGED FOOD', ]  
    '''build a dictionary where the keys are the words
    in the dataframe items column'''
    
    items=[]
    item_dict = defaultdict(int)
    basket_counts=[]
    
    for basket in df['items']:
        basket_counts.append(len(basket))
        for item in basket:
            
            items.append(item[1])
            item_dict[item[1]] += 1
    
    items_set=set(items)
    
    '''add the most common words to the stopwords list'''
    stopwords=list([i[0] for i in Counter(item_dict).most_common(most_common)])
    
    for s in stoppers:
        stopwords.append(s)
        
    '''add items containing "CRV" to the stopwords list'''
    for item in items_set:
        if "crv" in item.lower():
            stopwords.append(item)
    
    '''add the least common words to the stopwords list'''
    for key,value in item_dict.items():
        if value < least_common:
            stopwords.append(key)
    print(type(stopwords) )  
    stopwords = set(stopwords)
    
    '''iterate through the baskets and add items to items_set
    if not in stopwords (too common or too uncommon)'''
    for stops in stopwords:
        try:
            items_set.remove(stops)
        except KeyError as k:
            continue

    return items_set,stopwords, item_dict, basket_counts

def build_matrix(df,items_set,stopwords,basket_counts):
    df['item_count']=basket_counts
    item_matrix = np.zeros((df.shape[0],len(items_set)))
    df_items= pd.DataFrame(item_matrix,columns=items_set)
    df=df.reset_index()
    df.pop('index')
    col_index_dict = dict(zip(items_set, range(len(items_set))))
    matrix = np.zeros(df_items.shape)
    
    for i in range(df.shape[0]):
        for item in df['items'][i]:
            #set matrix to boolean for item precence in basket:
            if item[1] not in stopwords:
                if item[2] > 0:
                    value = 1
                elif item[2] == 0:
                    value = 0
                else:
                    value = -1
                matrix[i,col_index_dict[ item[1] ]] = matrix[i,col_index_dict[ item[1] ]] + value
    sparse_matrix = sparse.csr_matrix(matrix)
    sparse_matrix = (sparse_matrix > 0).astype(int)
    
    return sparse_matrix

def fit_NMF(sparse_matrix,n_components=10,max_iter=250):
    from sklearn.decomposition import NMF
    model = NMF(n_components=n_components,max_iter=max_iter)
    W = model.fit_transform(sparse_matrix)
    H=model.components_
    model_iter = model.n_iter_
    return model,W,H,model_iter

if __name__ == '__main__':

    path = 's3://latent-customers/jsons/2018/'
    df = get_dataframe(path)
    items_set,stopwords,item_dict, basket_counts = get_items(df,most_common=5,least_common=5)
    sparse_matrix = build_matrix(df,items_set,stopwords,basket_counts)
    model,W,H,model_iter = fit_NMF(sparse_matrix,n_components=10,max_iter=250)
    pickle.dump(W,open('W.p','wb'))
    pickle.dump(H,open('H.p','wb'))

