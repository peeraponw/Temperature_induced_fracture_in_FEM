from configparser import ConfigParser
from airtable import Airtable
from shutil import copyfile
import sys, os, glob
import json
import time
from jinja2 import Environment, FileSystemLoader
import paramiko

config = ConfigParser()
config.read('config.cfg')

sim_list = ['rve17', 'rve18', 'rve19']
# sim_list = ['rve16']

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
    # get simtype and set explicit/implicit
    with open(sim_name+'.json', 'r') as g:
        data = json.load(g)
    simtype=data['simtype'][0]
    if simtype == 'explicit':	
        FORTRAN='fortranfile_EXP'
        mat='matEXP.inp'
    elif simtype == 'implicit':
        FORTRAN='fortranfile_IMP'
        mat='matIMP.inp'
    # load file from folder templates
    env = Environment(loader=FileSystemLoader("templates"))
    abq_template = env.get_template('abq.py')
    # render template
    abq_dict = {"sim_name": sim_name,
                "matfile": config['qsub']['matfile']
                }
    abq_template.stream(abq_dict).dump(f"{sim_name}.py")
    # run abaqus
    os.system(f"abaqus cae noGUI={sim_name}.py")
    t0 = time.time()
    while not os.path.exists(f"{sim_name}.inp") or time.time()-t0 > 5:
        print("Abaqus is running ... please wait")
        time.sleep(1)
    # create a folder at X-drive and copy input file
    if not os.path.exists(f"X:/{sim_name}"):
        os.mkdir(f"X:/{sim_name}")
    copyfile(f"{sim_name}.inp", f"X:/{sim_name}/{sim_name}.inp")
    # copy qsub file and render template to X-drive
    username = config['qsub']['username']
    qsub_dict = {"sim_name": sim_name,
                 "username": username,
                 "email": config['qsub']['email'],
                 "fortranfile": config['qsub'][FORTRAN]    
                }
    qsub_template = env.get_template('qsub.qsb')
    qsub_template.stream(qsub_dict).dump(f"X:/{sim_name}/{sim_name}.qsb")
    # copy material file
    mat_template = env.get_template(mat)
    mat_template.stream().dump(f"X:/{sim_name}/{config['qsub']['matfile']}")
    # submit job
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("tux202", username=username, password=config['qsub']['password'])
    
    if not os.path.exists(f"X:/{sim_name}/{sim_name}.lck"):
        stdin, stdout, stderr = ssh.exec_command(f"qsub /home_work/{username}/{sim_name}/{sim_name}.qsb")
        print(stdout.readlines())
    else:
        print(f"LCK file exists ... deleting")
        os.remove(glob.glob("*.lck")[0])
    
    # clean the directory
    clean_files("abaqus*") # delete all temp files by ABAQUS
    clean_files(f"{sim_name}*") # delete all intermediate files by this script
    