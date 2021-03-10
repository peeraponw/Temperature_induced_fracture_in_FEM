from configparser import ConfigParser
from airtable import Airtable
import sys, os, glob
import json
from jinja2 import Environment, FileSystemLoader

config = ConfigParser()
config.read('config.cfg')

sim_list = ['rve01']


def fetch_airtable(sim_name):
    api_key = config['query']['api_key']
    base_key = config['query']['base_key']
    table_name = config['query']['table_name']
    
    airtable = Airtable(base_key, table_name, api_key)
    res = airtable.get_all(view='Join', formula=f"({{sim_name}}='{sim_name}')")

    with open(sim_name+'.json', 'w') as f:
        json.dump(res[0]['fields'], f)
def clean_files(pattern):
    for f in glob.glob(pattern):
        os.remove(f)

for sim_name in sim_list:
    # get json file from airtable
    fetch_airtable(sim_name)
    # load file from folder templates
    env = Environment(loader=FileSystemLoader("templates"))
    abq_template = env.get_template('abq.py')
    # render template
    abq_template.stream(sim_name=sim_name).dump(f"{sim_name}.py")
    os.system(f"abaqus cae noGUI={sim_name}.py")
    
    
    
    
    # clean the directory
    clean_files("abaqus*") # delete all temp files by ABAQUS
    clean_files(f"{sim_name}*") # delete all intermediate files by this script
    