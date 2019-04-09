# Reverse Engineering Shopping Lists 
## 10,000,000 grocery baskets, 10 trips to the store.
 

<img src = "./img/rgci/RGCI_logo_final_small.png" width="250" />

Rainbow Grocery is a 25,000 square foot Natural Food store that does about $1,000,000 in sale per week.
They have been a fixture of San Francisco since 1975 and have a register system designed in the 80's.
Rainbow Grocery doesn’t have a method to analyse their customers baskets.

# The Problem: How can Rainbow Grocery analyse their customers without a loyalty program?

Rainbow is unique in that it is: 
* vegetarian 
* maintains a selection of 30,000 items

With an emphasis on:
* fresh produce
* bulk ingredients (from oats to beans and spices to teas)
* extensive supplements and body care sections

## Discovering customer types from transactions without a loyalty program!
Rainbow has no loyalty program as of Spring 2019.

Everyday the register spits out a giant text file (2000 printable pages) of that day's 2000-3000 transactions.
<p align="middle">
<img src = "./img/rgci/TLOG1.png" width="250" />
<img src = "./img/rgci/TLOG2.png" width="250" />
<img src = "./img/rgci/TLOG3.png" width="250" />
</p>

Can we use data science to make sense of this stream of text and find the types of shoppers?

## Hello Non-Negative Matrix Factorization!

NMF is an unsupervised learning model that can be used to find topic similiarity between documents based on the words they contain. Treating each transaction as a document and each item's unique 13 character description as a word I will discover the latent dimensions of shopping baskets hidden in this history of purchases.

# Step 1. Parse the Data

Using a regex file I found on the web, i modified it to parse the transactionlog.txt ('tlogs') into useable elements. Date, time, total, cashier, lane, items, price and department code were all waiting to be pulled from a consistently formated text file.
Writing the results into a json format allowed for them to be quickly read into a pandas dataframe.

# Step 2. Prepare the Matrix

The item data was extracted as a list of list which I iterated through, adding the item to a dictionary with a running count of the items, ultimately yielding a dictionary of all the items in the all the baskets, and their total count.  I developed a "stop words" list to remove common items which made basket similarites worse. Bag Credits and bottle deposits were linking too many baskets because they were present in many baskets but were not actual items that lend any insight into shopping habits.  
Bananas were in 112832 of the 831284 baskets, roughly 1 in 8 baskets, or 13.5% of transactions and Hass Avocados were in 10% of baskets.
Removing both of these items allowed a greater differentiation between baskets.



