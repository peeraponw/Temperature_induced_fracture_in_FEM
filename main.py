from configparser import ConfigParser
from airtable import Airtable
import sys
import json


config = ConfigParser()
config.read('config.cfg')

sim_list = ['rve01']


def fetch_airtable(sim_name):
    airtable = Airtable(base_key, table_name, api_key)
    res = airtable.get_all(view='Join', formula=f"({{sim_name}}='{sim_name}')")

    with open(sim_name+'.json', 'w') as f:
        json.dump(res[0]['fields'], f)

for sim_name in sim_list:
    callAirtable(sim_name)
