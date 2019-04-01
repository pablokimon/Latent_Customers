def get_items(df,most_common=50,least_common=5):

    '''build a dictionary where the keys are the words
    in the dataframe items column'''
    item_dict = defaultdict(int)
    for basket in df['items']:
        for item in basket:
            item_dict[item[1]] += 1   
    '''add the most common words to the stopwords list'''
    stopwords = list([i[0] for i in Counter(item_dict).most_common(most_common)])
    '''add the least common words to the stopwords list'''
    for key,value in item_dict.items():
        if value <5:
            stopwords.append(key)

    '''iterate through the baskets and add items to items_set
    if not in stopwords (too common or too uncommon)'''
    items = []
    for basket in df['items']:
        for item in basket:
            if item[1] in stopwords:
                continue
            else:
                items.append(item[1])
    items_set=set(items)

    return items_set,stopwords