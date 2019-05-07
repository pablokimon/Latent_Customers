import re
import json
import os

'''This is the regex which consumes toshiba/IBM ACE transactionlogs.txt and converts them into wonderful jsons.
It will break, its amazing it worked this well. Test it on lots of samples of tlogs.
Use an online regex builder if you get stuck.

'''

def pos_float(s):
    #this function sets values followed by a + or - to the correct sign
    if s[-1]=="-":
        return -float(s[:-1])
    elif s[-1]=='+':
        return float(s[:-1])
    else:
        return float(s)

def parse_entry(entry):
    #this functions parses each transaction

    #setting the header format regex
    header_re = r"\s+DATE\s+TIME\s+TERM\s+TRANS\s+OPER\s+GROSS\+\s+GROSS-\s+NET\s+TRAN TYPE\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
    match = re.search(header_re, entry)
    if match is None:
        return None
    transinfo = match.groups()
    #skip transactions not of the type 'Checkout'
    if transinfo[8]!='Checkout':
        return None
    #matches lines containing item description (including many symbols), price and department number.
    item_re = r"^ (\w+)?\s+([\w \-,\+.'\"\\\/%&]+?)\s+(\d+\.\d+-?)\s+\w?\s+Dept\s+(\d+)"
    items = re.findall( item_re, entry, flags=re.MULTILINE )
    
    #matches lines with 'Account' numbers for credit cards and other misc charge accounts
    account_re = r"\s[Account]+\s+\d+$"
    account = re.findall(account_re,entry,flags=re.MULTILINE )
    
    #define the names of the items to match and return
    ret = {'date':transinfo[0],
           'time':transinfo[1],
           'term':int(transinfo[2]),
           'trans':int(transinfo[3]),
           'oper':int(transinfo[4]),
           'gross+':pos_float(transinfo[5]),
           'gross-':pos_float(transinfo[6]),
           'net':pos_float(transinfo[7]),
           'type':transinfo[8],
          'account':account}
    
    items = [(x[0].strip(), x[1].strip(), pos_float(x[2]), int(x[3])) for x in items]
    
    ret['items'] = items
    
    return ret

def parse_transaction_file(fn):
    #comsumes the raw text file transactionlogs.txt
    raw = open(fn, encoding="latin1").read()
    
    # remove page headers
    headerre = re.compile( r" +Auto Report: (\b.*)\s+Entry: (\b.*)\s+TRANSACTION SUMMARY LOG REPORT  - STORE\s+(.+)\s+PREVIOUS PERIOD - (\S+)\s+Reported at:\s+(\S+ \S+)\s+",
                     flags=re.MULTILINE)
    headerless, ct = re.subn(headerre, "", raw)
    
    # remove page footers
    pageless, ct = re.subn(r'\n +Page \d+.*\n', "\n", headerless)
    
    # split at ======
    entries = re.split(r"\n=+\n", pageless)
    
    trans = []
    for i, entry in enumerate( entries ):
        x = parse_entry(entry)
        if x is not None: trans.append(x)
            
    return trans

def pos_to_json(fn_in, fn_out):
    trns = parse_transaction_file(fn_in)
    
    fpout = open(fn_out,"w")
    for trn in trns:
        fpout.write( json.dumps(trn) )
        fpout.write("\n")
    fpout.close()


#itereate through all subfolders seeking tlogs to process!
for subdir, dirs, files in os.walk('./tlogs'):
    for file in files:
        #print os.path.join(subdir, file)
        filepath = subdir + os.sep + file

        if filepath.endswith("*log.txt"):
            pass
            #print (filepath)


#if __name__ == '__main__':
year=input('What year data would you like to process?')
json_path ='./data/jsons/%s'% year
tlog_path='./data/tlogs/%s'% year

if not os.path.exists(tlog_path):
    print("Directory " , tlog_path ,  "Does not exist")
if not os.path.exists(json_path):
    os.makedirs(json_path)
    print("Directory " , json_path ,  " Created ")
else:    
    print("Directory " , json_path ,  " already exists")    


for i,f in enumerate(os.walk(tlog_path)):
    #iterete through all folders
    for ff in f:
        if type(ff)!='list':
            #when it find a tlog path:
            if str(ff).startswith(tlog_path):
                path = ff
        for fff in ff:
            #when it finds a transaction log:
            if fff=="transactionlog.txt":
                #process it with the above functions:
                pos_to_json(path+'/'+fff,json_path+'/'+'%d.json'%i)