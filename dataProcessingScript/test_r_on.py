from resistanceAnalyzer.datahandler import DataHandler
from glob import glob

import matplotlib.pyplot as plt
import seaborn as sns

from tqdm import tqdm

sns.set_palette('pastel')

if __name__ == '__main__':
    output_dir = '../r_on_test_plots'
    g = glob('../data/*.csv')

    # enumerate all CSVs
    for f in tqdm(g):
        dh = DataHandler(f)

        # Skip observe for now
        if dh.activity() == 'observe':
            continue
        
        dh.plot(f'{output_dir}/{dh.metadata.csvFileName}.png')