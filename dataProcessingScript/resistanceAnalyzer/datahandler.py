import numpy as np
import pandas as pd
from scipy.stats import linregress

from functools import cached_property

from ..utils.csvItem import csvItem
from ..utils.csvParser import csvParser

class DataHandler:
    def __init__(self, csv_file: str, set_thresh=0.9, linear_thresh=1e-1):
        self.file = csv_file

        # parse using Mihir's algorithm
        self.metadata = csvItem(csv_file)

        # import the data
        self.df = self.__get_dataframe()

        self.set_thresh = set_thresh
        self.linear_thresh = linear_thresh
    
    def activity(self) -> str:
        return self.metadata.activity

    def is_two_probe(self) -> bool:
        return not self.metadata.isThreeProbe
    
    def __get_dataframe(self) -> pd.DataFrame:
        parser = csvParser(self.file)
        df = pd.DataFrame({title: col for title, col in zip(parser.title, parser.columns)})

        return df
    
    @cached_property
    def set_voltage(self):
        if not self.activity() in ['set', 'form']:
            raise Exception(f"set_voltage() called on data from {self.activity()}: {self.file}")
        
        units = {'uA': 1e-6, 'mA': 1e-3}
        icc = float(self.metadata.complianceCurrent) * units.get(self.metadata.complianceCurrentUnits, 1)

        # we're going to assume that the cell has set after it achieves 90% of Icc
        threshold = self.set_thresh * icc

        series = self.df['AI'].values >= threshold
        d = np.diff(series)

        # to avoid janky starting curves, take the last time the current crossed the threshold
        crosses = np.argwhere(d)

        if len(crosses) == 0:
            return None

        idx = crosses[-1][0]
        voltage = self.df.at[idx, 'AV']

        return voltage

    @cached_property
    def __linear_idx(self):
        # theory here is that the 2nd derivative of the linear portion of the current data will be 0,
        # while the sudden nonlinear jumps will have a nonzero 2nd derivative that we can detect
        #
        # Formula comes from https://en.wikipedia.org/wiki/Finite_difference#Higher-order_differences (see second order central)

        i = self.df['AI'].values
        v = self.df['AV'].values
        dv = np.mean(np.diff(v))
        di2 = np.convolve(i, np.array([1, -2, 1]), mode='valid')

        didv2 = di2 / dv ** 2

        # check for large jumps in 2nd derivative
        series = np.abs(didv2) >= self.linear_thresh
        d = np.diff(series)

        jumps = np.argwhere(d)

        if len(jumps) == 0:
            return None

        # first instance of a major jump
        idx = np.min(jumps) + 1   # add +1 since this index really starts at 1 for the data series due to the mode='valid' in convolution
        
        return idx
    
    @cached_property
    def linear_voltage_regime(self):
        v = self.df['AV'].values

        if self.__linear_idx:
            v = v[:self.__linear_idx]

        return v.min(), v.max()

    @cached_property
    def resistance(self):
        if not self.activity() == 'reset':
            raise Exception(f"resistance() called on data from {self.activity()}: {self.file}")
        
        idx = self.__linear_idx
        i = self.df['AI'].values
        v = self.df['AV'].values

        if idx is not None:
            i, v = i[:idx], v[:idx]

        # now we will take the data up until idx and perform a linear fit to it to obtain the resistance
        s_on, _, r, _, _ = linregress(v[:idx], i[:idx])
        r_on = 1 / s_on     # slope of IV curve is conductance
        self.r2 = r ** 2 # store R^2 value from linear fit too

        return r_on
    
    def plot(self, outfile: str):
        import matplotlib.pyplot as plt
        import seaborn as sns
        sns.set_palette('pastel')

        fig = plt.figure(figsize=(10, 4), dpi=300)
        fig.patch.set_facecolor('white')
        sns.lineplot(x=self.df.AV, y=self.df.AI)
        plt.xlabel("Voltage $V$ [V]")
        plt.ylabel("Current $I$ [A]")

        if self.activity() in ['set', 'form']:
            if self.set_voltage is None:
                plt.title(f'{self.activity()}: No thresh detected')
            else:
                plt.title(f'{self.activity()}: {self.set_voltage:.2f} V')
                plt.vlines(self.set_voltage, self.df.AI.min(), self.df.AI.max(), colors='r')

        elif self.activity() == 'reset':
            if self.resistance is None:
                plt.title('reset: Too nonlinear')
            else:
                plt.title(f'Reset: (R_on = {self.resistance:.2f} Ω, R2 = {self.r2:.3f})')
                x_min, x_max = self.linear_voltage_regime
                plt.axvspan(x_min, x_max, facecolor='0.9', zorder=-100)
        
        plt.savefig(outfile)
        plt.close()
