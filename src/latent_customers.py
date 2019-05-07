import pandas as pd
import numpy as np
from scipy import sparse
from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import os
import glob
import time
from sklearn.decomposition import NMF
from sklearn import decomposition, datasets, model_selection, preprocessing, metrics
# if running in a jupyter notebook run this line as well:
#%matplotlib inline
'''
These functions will expect a couple directories:
    ./jsons/ full of beautiful jsons prepared by the makeJSONS.py
    ./img/ to store the beautiful wordclouds this package will generate
    '''
def json_to_df(path):
    '''
    This function requires you provide the path to the folder containing the processed jsons to be processed. 
    This function expects jsons created by the makeJSONS.py provided in this repo.
    See further notes below, especially if you encounter issues running this.
    '''
    all_files = glob.glob(os.path.join(path, "*.json"))
    #the text files provide a date in a strange YY/MM/DD format which we will deal with later as pandas doesn't handle it well
    df = pd.concat((pd.read_json(f,keep_default_dates=False,lines=True) for f in all_files)) 
    # limits the types of transactions to only "Checkout" type (no returns, voids, etc.)
    df=df[df['type']=='Checkout']
    # then drop the type column as its no longer necessary
    df.drop(columns='type',inplace=True)
    #limits the data to lanes 1-9. CHANGE THIS LINE IF YOU NEED DIFFERENT LANES INCLUDED
    df=df[df['term']<10]
    #converts the date column to datetime object and handles the 'year first' format
    df['date']=pd.to_datetime(df['date'],yearfirst=True)
    #add a day of the week column
    df['day_of_week']=df['date'].dt.day_name()
    #add a month column
    df['month']=df['date'].dt.month
    #add an hour column
    df['hour']=pd.to_datetime(df['time']).dt.hour
    #returns a dataframe
    return df


def get_items(df,most_common=10,least_common=5):
    '''This function is vital and provides several necessary steps:
    1. extracts the items from the list of items in each transaction
    2. creates a set of items from the corpus of transactions
    3. creates a list of stopwords
    4. creates a dictionary of items and their running count in the corpus of transactions
    5. creates a list of counts of items per transaction
    6. returns all these objects
    '''
    # a special list of items which are not important and only clogged up the results. these will vary by store and data set.
    stoppers = ['BAG CREDIT','SF Bag Charge','Gift Card Reload','8 OZ BIO TUB t3', '16OZ BIO TUB t4',
                 '32OZ BIO TUB t5','8 OZ PLSTC TUB t3','16 OZ PLSTC TUB t4','BOTTLE DEPOSIT',
                 '6PACK BEER SMALL C','PAID IN','Gift Card Sale','PACKAGED FOOD' ] 
    stopwords =[]
    items=[]
    item_dict = defaultdict(int)
    basket_counts=[]

    '''build a dictionary where the keys are the words
    in the dataframe items column'''
    for basket in df['items']:
        basket_counts.append(len(basket))
        for item in basket:
            if item[0]=='MP':
                pass
            items.append(item[1])
            item_dict[item[1]] += 1
    #create a set of items
    items_set=set(items)

    '''add the n most common words to the stopwords list'''
    stopwords=list([i[0] for i in Counter(item_dict).most_common(most_common)])
            
    '''add predetermined stoppers to stopwords list'''
    for s in stoppers:
        stopwords.append(s)
        
    '''add items containing "CRV" (california redemption value; i.e. bottle deposits) to the stopwords list'''
    for item in items_set:
        if "crv" in item.lower():
            stopwords.append(item)
    
    '''add the m least common words to the stopwords list'''
    for key,value in item_dict.items():
        if value < least_common:
            stopwords.append(key)
    stopwords_set = set(stopwords)
    
    '''iterate through the baskets and add items to items_set
    if not in stopwords (too common or too uncommon)'''
    for stops in stopwords_set:
        if stops in items_set:
            items_set.remove(stops)
   
    #return all these wonderful objects for use later
    return items_set,stopwords_set, item_dict, basket_counts

def build_matrix(df,items_set,stopwords,dept_to_exclude=()):
    '''This funciton requires a dataframe, a set of items, a list of stopwords, and optional any departments to exclude in tuple form'''
    
    '''create a separate item dataframe'''
    item_matrix = np.zeros((df.shape[0],len(items_set)))
    df_items = pd.DataFrame(item_matrix,columns=items_set)
    df = df.reset_index()
    df.pop('index')
    col_index_dict = dict(zip(items_set, range(len(items_set))))
    
    '''create the transaciton/item dictionary '''
    #make an empty defaultdict
    matrix_dict = defaultdict(int)
    #loop through the rows(transactions) in the dataframe:
    for i in range(df.shape[0]):
        #loop through the list of items per transaction:
        for item in df['items'][i]:
            #set matrix to boolean for item precence in basket:
            if item[1] not in stopwords and item[3] not in dept_to_exclude:
                #to update the value of the item, if its positive add a 1, if its negative subtract a 1
                if item[2] > 0:
                    value = 1
                elif item[2] == 0:
                    value = 0
                else:
                    value = -1
                #update the value of the item for that transaction by adding either a 1 or a -1
                #this accounts for +1,+1,-1 situation, yielding +1 instead of ending setting it to -1
                matrix_dict[i,col_index_dict[item[1]]] += value
    
    '''THIS IS IMPORTANT!!!'''
    #converts transaction/item dictionary into an actual sparse matrix
    rows, cols, vals = [], [], []
    for key, value in matrix_dict.items():
        rows.append(key[0])
        cols.append(key[1])
        vals.append(matrix_dict[key])
    sparse_matrix = sparse.csr_matrix((vals, (rows, cols)))


    #change negative values in matrix to 0 NMF doesn't like negatives. It's in its name for goodness sake!
    sparse_matrix = (sparse_matrix > 0).astype(int)
    #check the sum of 0 items in the matrix, 
    # just how sparse is this thing? 
    sum_of_zeros=sum(np.sum(sparse_matrix,axis=1)==0)
    # how many baksets are we ignoring?
    print(sum_of_zeros / sparse_matrix.shape[0],"% of zero weight baskets")

    return sparse_matrix


def fit_NMF(sparse_matrix_,n_components_,max_iter=250):
    '''This function takes a sparse matrix, the number of components (topics) and max iterations allowed'''
    from sklearn.decomposition import NMF
    model = NMF(n_components=n_components_,max_iter=max_iter)
    W = model.fit_transform(sparse_matrix_) # (transactions, topics)
    H=model.components_ # (topics,items)
    model_iter = model.n_iter_ 
    #display at console the number of iterations and the shape of the decomposed matrices
    print('iterations:',model_iter,'W shape:',W.shape,'H shape:',H.shape)
    
    #calculate the strength of each topic my making it a hard classifier and scoring each topic accordingly
    #make w a matrix of zeros shaped like W
    w = np.zeros_like(W)
    #
    w[np.arange(len(W)), W.argmax(1)] = 1
    topic_strength = np.sum(w,axis=0)
    topic_strength = np.round(topic_strength/topic_strength.sum(),2)
    for i,t in enumerate(topic_strength):
        print('topic %d strength: %f '%(i,t))
    
    return model,W,H,model_iter,topic_strength

def print_top_items(model, feature_names, n_top_words):
    '''This fuction requires a model, a list of items, and the number of top words per topic
    to create words clouds and lists of items for the n_top_words in each topic'''
    topic_dict = defaultdict()
    topics_list =[]
    fig = plt.figure(1,figsize=(100,100))
    #itereate through each topic and create words clouds
    for topic_idx, topic in enumerate(model.components_):
        print(topic_strength[topic_idx],"Topic #%d of %d:" %( topic_idx,number_of_components))
        #topic_string=(" ".join([feature_names[i]for i in topic.argsort()[:-n_top_words - 1:-1]]))
        topic_string=[feature_names[i]for i in topic.argsort()[:-n_top_words - 1:-1]]
        topic_dict[topic_idx]=topic_string
        topics_list.append(topic_string)
        print(topic_string)

        #create wordclouds, remove spaces between words
        wordcloud = WordCloud(max_font_size=500, max_words=1000, background_color="white").generate(str(topic_string).replace(" ", '').replace("'",""))
        #wordcloud = WordCloud(max_font_size=500, max_words=1000, background_color="white").generate(str(topic_string).replace("'","").replace(",",""))
        ax = fig.add_subplot(1,number_of_components,topic_idx+1)
        ax.imshow(wordcloud)
        ax.axis("off")
        # Display the generated image:
        #plt.figure(1,figsize=(10,10))
        '''plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()'''
        #plt.savefig('topic%d.png'%topic_idx)
        #plt.close()
        img_time=str(time.time()).split('.')[0]
        wordcloud.to_file('./img/2018/%s.topic%d.png'%(img_time,topic_idx))
        print('<img src="./img/2018/%s.topic%d.png">'%(img_time,topic_idx))

    #create a matrix to compare the similarities of different topics top words
    topic_compare = np.zeros([len(topic_dict),len(topic_dict)])
    #fill the topic_compare matrix with count of similar words to other matricies
    for topic in topic_dict:
        for item in topic_dict[topic]:
            for topic2 in topic_dict:
                if item in topic_dict[topic2]:
                    topic_compare[topic,topic2]+=1
    #display the results
    print ('topic similarity matix:')
    print (topic_strength)            
    print(topic_compare)

    topic_matrix=np.array(topics_list).T
    print (topic_matrix.shape)
    topic_df = pd.DataFrame(topic_matrix,columns=topic_strength)
    #create markdown friendly dataframe of top items per topic
    import tabulate 
    print(tabulate.tabulate(topic_df.values,topic_df.columns, tablefmt="pipe")) 
    return topic_dict,topics_list
    

#run it all from the command line:
if __name__ == '__main__':

    number_of_components = int(input('How many topics would you like to decompose into?'))
    
    print("Building Dataframe")
    df = json_to_df(input('path to jsons'))
    
    print('Building item set and stopwords')
    items_set,stopwords_set, item_dict, basket_counts = get_items(df,most_common=5,least_common=30)
    
    input("item set is ready, proceed?")
    print('Building sparse matrix')
    sparse_matrix = build_matrix(df,items_set,stopwords_set)
    
    input("matrix ready, proceed?")
    print('fitting model')
    model,W,H,model_iter,topic_strength = fit_NMF(sparse_matrix,n_components_=number_of_components,max_iter=250)
    
    input("model is ready, proceed?")
    n_top_words=int(input('How many top words would you like to see?'))
    topic_dict,topics_list = print_top_items(model,list(items_set),n_top_words)

