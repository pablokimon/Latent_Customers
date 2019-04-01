def json_to_df(path):

    #path = '/Users/Sarah/galvanize/dsi-capstone/jsons/'
    all_files = glob.glob(os.path.join(path, "*.json"))
    df = pd.concat((pd.read_json(f,keep_default_dates=False,lines=True) for f in all_files)) 

    return df