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
Everyday the register spits out a giant text file (2000 printable pages everyday) of the 2000-3000 daily transactions.
<p align="middle">
<img src = "./img/rgci/TLOG1.png" width="250" />
<img src = "./img/rgci/TLOG2.png" width="250" />
<img src = "./img/rgci/TLOG3.png" width="250" />
</p>

Can we use data science to make sense of this stream of text and find the types of shoppers?


## Hello Non-Negative Matrix Factorization!

NMF is super cool.



