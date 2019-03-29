import pandas as pd
import numpy as np
from scipy import sparse
from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
#%matplotlib inline
import rainbow
import os
import glob
from sklearn.decomposition import NMF
from sklearn import decomposition, datasets, model_selection, preprocessing, metrics

def json_to_df(path):
    all_files = glob.glob(os.path.join(path, "*.json"))
    df = pd.concat((pd.read_json(f,keep_default_dates=False,lines=True) for f in all_files)) 
    return df


def get_items(df,most_common=10,least_common=5):

    stoppers = ['BAG CREDIT','SF Bag Charge','Gift Card Reload','8 OZ BIO TUB t3', '16OZ BIO TUB t4',
                 '32OZ BIO TUB t5','BOTTLE DEPOSIT','6PACK BEER SMALL C','PAID IN','Gift Card Sale']

    
    '''build a dictionary where the keys are the words
    in the dataframe items column'''
    
    items=[]
    item_dict = defaultdict(int)
    
    for basket in df['items']:
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
        items_set.remove(stops)
  

    return items_set,stopwords, item_dict

def build_matrix(df,items_set):

    item_matrix = np.zeros((df.shape[0],len(items_set)))
    df_items = pd.DataFrame(item_matrix,columns=items_set)
    df = df.reset_index()
    df.pop('index')
    col_index_dict = dict(zip(items_set, range(len(items_set))))
    matrix = np.zeros(df_items.shape)
    #iterate through all rows and insert value of item at row of basket and column of item
    for i in range(df.shape[0]):
        for item in df['items'][i]:
            #set matrix to boolean for item precence in basket:
            if item[1] not in stopwords:
                matrix[i,col_index_dict[ item[1] ]] = matrix[i,col_index_dict[ item[1] ]] + item[2]
            '''if item[1] not in stopwords and item[2] > 0:
                matrix[i,col_index_dict[ item[1] ]] = 1
            if item[1] not in stopwords and item[2] < 0:
                matrix[i,col_index_dict[ item[1] ]] = 0'''
    matrix = (matrix > 0).astype(int)
    sparse_matrix = sparse.csr_matrix(matrix)

    return sparse_matrix


def fit_model(sparse_matrix,n_components=10,max_iter=200):

    model = NMF(n_components=n_components,max_iter=200 )
    W = model.fit_transform(sparse_matrix)
    H = model.components_
    return model,W,H

def print_top_items(model, feature_names, n_top_words):
    topics =[]
    for topic_idx, topic in enumerate(model.components_):
        print("Topic #%d:" % topic_idx)
        #topic_string=(" ".join([feature_names[i]for i in topic.argsort()[:-n_top_words - 1:-1]]))
        topic_string=str([feature_names[i]for i in topic.argsort()[:-n_top_words - 1:-1]])

        topics.append(topic_string)
        print(topic_string)
        #print()
        wordcloud = WordCloud(max_font_size=500, max_words=1000, background_color="white").generate(topic_string.replace(" ", "_").replace("'",""))

        # Display the generated image:
        plt.figure(1,figsize=(10,10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
        #plt.savefig('topic%d.png'%topic_idx)
        #plt.close()
        wordcloud.to_file('topic%d.png'%topic_idx)
    

if __name__ == '__main__':

    n_components = 10

    df = json_to_df('/Users/Sarah/galvanize/dsi-capstone/jsons/')

    items_set,stopwords,item_dict = get_items(df,most_common=5,least_common=30)
    input("stopwords are ready, proceed?")

    sparse_matrix = build_matrix(df,items_set)
    input("matrix ready, proceed?")
    model,W,H = fit_model(sparse_matrix,n_components=10,max_iter=200)
    input("model is ready, proceed?")
    print_top_items(model,list(items_set),20)

