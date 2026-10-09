import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
# import pyvo as vo
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import glob


path_save = "data_csv"


df_all = pd.read_csv(os.path.join(path_save,'alerce_vs_bogus_classifier2_probgt08.csv.gz'))
list_save = pd.read_csv(os.path.join(path_save,'diff_path_ready.csv.gz'))['loc'].tolist()


oid_list_bogus = df_all.query('class_name == "bogus"').sample(n=50000, random_state=84)['oid'].tolist()
print(f'total {len(oid_list_bogus)}')

path_save = "hack_colombia_stamps_oct_26/bogus"

list_save_here = glob.glob(f"{path_save}/*/*diff*npy")
print(f'len here {len(list_save_here)}')

list_save_u = list_save + list_save_here
ids_ready = [int(x.split('/')[-1].split('_')[0]) for x in list_save_u]
oid_list_vs = [x for x in oid_list_bogus if x not in ids_ready]
print(f'missing {len(oid_list_vs)}')

import io
import os
import requests
from astropy.io import fits  # Optional: only if you want to inspect them right away

# Base URL for the Fink LSST API
API_URL = "https://api.lsst.fink-portal.org/api/v1/cutouts"


# Cutout types available from Rubin LSST: 'Science', 'Template', or 'Difference'
stamp_kinds = ["Science", "Template", "Difference"]

for idx, oid in enumerate(oid_list_vs):

    # Step 1: Get the list of diaSourceId for the object
    sources_url = "https://api.lsst.fink-portal.org/api/v1/sources"
    payload = {
        "diaObjectId": str(oid),
        "columns": "r:diaSourceId,r:midpointMjdTai",
    }

    response = requests.post(sources_url, json=payload)

    if response.status_code == 200:
        try:
          target_source_id = response.json()[-1]["r:diaSourceId"]
          print(f"Target diaSourceId found: {target_source_id}")
        except:
          print(f"No diaSourceId found for {oid}")
          continue
    else:
        print(f"Error fetching sources: {response.status_code}")



    for kind in stamp_kinds:
        print(f"Downloading {kind} stamp for {oid}...")

        # Construct payload
        payload = {
            "diaSourceId": str(target_source_id),
            "kind": kind,
            "output-format": "FITS"  # You can also use 'PNG' if preferred
        }

        os.makedirs(os.path.join(path_save,f"{oid}"), exist_ok=True)

        try:
            # Send POST request to Fink API
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200 and response.content:

              # Read FITS bytes directly from memory
              fits_bytes = io.BytesIO(response.content)

              with fits.open(fits_bytes, ignore_missing_simple=True) as hdul:
                  # Extract image matrix as a NumPy array (typically extension 0 or 1 depending on layout)
                  img_data = hdul[0].data

                  # In case the primary extension is empty (header-only), fall back to extension 1
                  if img_data is None and len(hdul) > 1:
                      img_data = hdul[1].data

                  if img_data is not None:
                      # Define output file path

                      # Save as a standard binary numpy file

                      np.save(os.path.join(path_save,f"{oid}/{oid}_{kind.lower()}_cutout.npy"), img_data)
                      print(f" Successfully saved: {idx}. {oid} (Shape: {img_data.shape})")
                  else:
                      print(f" Warning: No array data found in FITS for ID {oid}")

            else:
                print(f"Failed to fetch {kind} for {oid}: HTTP {response.status_code}")

        except Exception as e:
            print(f"An error occurred while fetching {oid}: {e}")

