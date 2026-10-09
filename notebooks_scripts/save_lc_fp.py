import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import glob
import pickle
import io
import requests
from astropy.io import fits

path_save = "data_csv"
file_list_path = glob.glob(path_save+'/file_list*')
print(file_list_path)

def load_pickle_file(file_list_path_i):
  oid_list_vs_all = []
  for pp in file_list_path_i:
    with open(pp, 'rb') as file:
      objs_path_vs = pickle.load(file)

    oid_list_vs = [x[0].split('/')[-2] for x in objs_path_vs]
    oid_list_vs_all.extend(oid_list_vs)
  return oid_list_vs_all
print(file_list_path[0])

oid_list_vs = load_pickle_file([file_list_path[0]])
path_save_lc = "hack_colombia_lc_oct_26/sn"
path_save_fplc = "hack_colombia_fp_lc_oct_26/sn"

os.makedirs(os.path.join(path_save_lc), exist_ok=True)
os.makedirs(os.path.join(path_save_fplc), exist_ok=True)



def get_id_saved(path_save_lc, oid_list_vs):
	list_save_u = glob.glob(f"{path_save_lc}/*/*csv.gz")
	print(f'len {path_save_lc}: {len(list_save_u)}')

	ids_ready = [str(x.split('/')[-1].split('_')[0]) for x in list_save_u]
	oid_list_vs_m = [x for x in oid_list_vs if x not in ids_ready]
	print(f'missing {path_save_lc}: {len(oid_list_vs_m)}')

	return oid_list_vs_m



oid_list_vs_m = get_id_saved(path_save_lc, oid_list_vs)
oid_list_fpvs_m = get_id_saved(path_save_fplc, oid_list_vs)

for idx, oid in enumerate(oid_list_vs):

	if oid in oid_list_vs_m:

		sources_url = "https://api.lsst.fink-portal.org/api/v1/sources"
		payload = {
		  "diaObjectId": str(oid),
		  "columns": "r:diaSourceId, r:midpointMjdTai, r:psfFlux, r:psfFluxErr, r:band, r:reliability, r:scienceFlux, r:scienceFluxErr, r:ra, r:dec"
		}
		response = requests.post(sources_url, json=payload)

		if response.status_code == 200:
			os.makedirs(os.path.join(path_save_lc,f"{oid}"), exist_ok=True)
			try:
				light_curve_df = pd.read_json(io.BytesIO(response.content))
				print(f"Target diaObjectId found saving lc: {oid}")
				light_curve_df.to_csv(os.path.join(path_save_lc,f"{oid}/{oid}_lc.csv.gz"))
				
			except:
				print(f"No diaObjectId found for lc {oid}")
				continue
		else:
			print(f"Error fetching sources lc: {response.status_code}")
			continue

	if oid in oid_list_fpvs_m:
		sources_url_fp = "https://api.lsst.fink-portal.org/api/v1/fp"
		payload_fp = {
		  "diaObjectId": str(oid),
		  "columns": "r:diaForcedSourceId, r:midpointMjdTai, r:psfFlux, r:psfFluxErr, r:band, r:scienceFlux, r:scienceFluxErr, r:ra, r:dec"
		}
		response_fp = requests.post(sources_url_fp, json=payload_fp)

	
		if response_fp.status_code == 200:
			os.makedirs(os.path.join(path_save_fplc,f"{oid}"), exist_ok=True)
			try:
				light_curve_df_fp = pd.read_json(io.BytesIO(response_fp.content))
				print(f"Target diaObjectId found saving forced lc: {oid}")
				light_curve_df_fp.to_csv(os.path.join(path_save_fplc,f"{oid}/{oid}_fp_lc.csv.gz"))
			except:
				print(f"No diaObjectId found for fp {oid}")
				continueß
		else:
			print(f"Error fetching sources fp: {response_fp.status_code}")
			continue



print("DONE")