import re
import json

def pos_float(s):
    if s[-1]=="-":
        return -float(s[:-1])
    else:
        return float(s)

def parse_entry(entry):
    header_re = r"\s+DATE\s+TIME\s+TERM\s+TRANS\s+OPER\s+GROSS\+\s+GROSS-\s+NET\s+TRAN TYPE\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
    match = re.search(header_re, entry)
    if match is None:
        return None
    transinfo = match.groups()
    
    item_re = r"^( \w+)?\s+(([\w\-\+/%]+ ?)+)\s+(\d+\.\d+-?)\s+Dept\s+(\d+)"
    items = re.findall( item_re, entry, flags=re.MULTILINE )
    
    ret = {'date':transinfo[0],
           'time':transinfo[1],
           'term':int(transinfo[2]),
           'trans':int(transinfo[3]),
           'oper':int(transinfo[4]),
           'gross+':pos_float(transinfo[5]),
           'gross-':pos_float(transinfo[6]),
           'net':pos_float(transinfo[7]),
           'type':transinfo[8]}
    
    items = [(x[0].strip(), x[1].strip(), pos_float(x[3]), int(x[4])) for x in items]
    
    ret['items'] = items
    
    return ret

def parse_transaction_file(fn):
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

if __name__=='__main__':
    import sys
    
    if len(sys.argv)<3:
        print( "usage: %s transaction_filename output_filename"%sys.argv[0] )
        exit()
    
    fn_in = sys.argv[1]
    fn_out = sys.argv[2]
    
    pos_to_json(fn_in, fn_out)
    