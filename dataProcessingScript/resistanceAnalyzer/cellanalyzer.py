# Author: Jim Furches

import numpy as np
import pandas as pd
from scipy.stats import linregress

from functools import cached_property

from utils.csvItem import csvItem

class CellAnalyzer:
    """Class that can extract characteristics from cell IV curves and provides interpretable graphs
    
    Currently only supports 2-probe measurements.
    """

    def __init__(self, csvItem: csvItem, set_thresh: float=0.9, linear_thresh: float=5e-3):
        """Constructs the R_on data handler
        
        Parameters
        ----------
        csvItem : csvItem
            Item containing metadata of the CSV file
        set_thresh : float
            Hyperparameter controlling detection of Set/Form voltage. See `set_voltage()` for more info
        linear_thresh : float
            Hyperparameter controlling 
        """
        # parse using Mihir's algorithm
        self.metadata = csvItem

        # import the data to numpy/pandas
        self.df = self.__get_dataframe()

        self.set_thresh = set_thresh
        self.linear_thresh = linear_thresh
    
    def activity(self) -> str:
        return self.metadata.activity

    def is_two_probe(self) -> bool:
        return not self.metadata.isThreeProbe
    
    def __get_dataframe(self) -> pd.DataFrame:
        """Takes the csv file and returns a pandas data frame"""
        df = pd.DataFrame({
            'AI': self.metadata.probeA_current,
            'AV': self.metadata.probeA_voltage,
            'Time': self.metadata.timeAxis
        })

        return df
    
    @cached_property
    def set_voltage(self):
        """Calculates the set voltage for a set or form CSV file
        
        Checks when the current crosses `set_thresh * Icc`. Result is cached
        after first calculation.

        Returns
        -------
        voltage : float or None
            Returns voltage of the last crossing instance. Returns `None` if 
            no crossing is found (e.g. non-conductive cell that remains in nano-Ampère range)
        """
        if not self.activity() in ['set', 'form']:
            raise Exception(f"set_voltage() called on data from {self.activity()}: {self.file}")
        
        # get the compliance current from the CSV file name
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

        # argwhere will return output in form of shape (n_crossings, 1),
        # so take the last instance and then remove the value from the 0d np array
        idx = crosses[-1][0]
        voltage = self.df.at[idx, 'AV'] # get the voltage at the crossing

        return voltage

    @cached_property
    def __linear_idx(self):
        """Returns the first index of data corresponding to a nonlinear jump. Used internally"""

        # theory here is that the 2nd derivative of the linear portion of the current data will be 0,
        # while the sudden nonlinear jumps will have a nonzero 2nd derivative
        # so this gives us a signal and we compare the jumps against the `linear_thresh` hyperparameter
        #
        # Formula comes from https://en.wikipedia.org/wiki/Finite_difference#Higher-order_differences (see second order central derivative formula)

        i = self.df['AI'].values
        v = self.df['AV'].values

        # take the average voltage steps as 'dv' for derivative di/dv
        dv = np.mean(np.diff(v))
        # use convolution to perform the second order formula, will crop off first and last data element
        di2 = np.convolve(i, np.array([1, -2, 1]), mode='valid')

        didv2 = di2 / dv ** 2

        # check for large jumps in 2nd derivative against hyperparameter
        # giving a binary signal
        series = np.abs(didv2) >= self.linear_thresh
        # take difference of binary signal to find 'crossing points'
        d = np.diff(series)

        jumps = np.argwhere(d)

        if len(jumps) == 0:
            return None

        # first instance of a major jump
        idx = np.min(jumps) + 1   # add +1 since this index really starts at 1 for the data series due to the mode='valid' in convolution
        
        return idx
    
    @cached_property
    def linear_voltage_regime(self):
        """Returns the region where the algorithm thinks the curve is sufficiently linear
        
        Only works on reset curves

        Returns
        -------
        (v_min, v_max) : A tuple consisting of the linear voltage region
        """
        v = self.df['AV'].values

        if self.__linear_idx:
            v = v[:self.__linear_idx]

        return v.min(), v.max()

    @cached_property
    def resistance(self):
        """Tries to determine the R_on for a cell using the reset curve
        
        After calculation, the R2 value of the linear fit will be stored in the `r2` property.
        Makes use of `linear_thresh` hyperparameter. Value is cached after first call, accessed by property not method.

        On resistance is calculated by fitting a line to linear region of IV curve. Then, resistance is 1 / slope of that line.

        Returns
        -------
        resistance : float or None
            Detected R_on of the cell, or `None` if the data was too nonlinear
        r2 : float
            Linear best fit quality, indirectly returned in property `r2`.
        """
        if not self.activity() == 'reset':
            raise Exception(f"resistance() called on data from {self.activity()}")
        
        idx = self.__linear_idx
        i = self.df['AI'].values
        v = self.df['AV'].values

        # crop data if we found nonlinearities
        if idx is not None:
            i, v = i[:idx], v[:idx]

        # now we will take the data up until idx and perform a linear fit to it to obtain the resistance
        s_on, _, r, _, _ = linregress(v[:idx], i[:idx])
        r_on = 1 / s_on     # slope of IV curve is conductance
        self.r2 = r ** 2    # store R^2 value from linear fit too

        return r_on
    
    @cached_property
    def ramp_rate(self) -> float:
        """Calculates the true ramp rate of the data in V/s"""
    
        if self.activity() == 'observe':
            raise Exception(f"ramp_rate() called on data from observe")

        v = np.abs(self.df['AV'].values)
        series = v >= 1
        d = np.diff(series)

        crosses = np.argwhere(d)

        if len(crosses) == 0:
            return self.df['AV'][-1] / self.df['Time'][-1]
        
        else:
            idx = crosses[0][0]

            return self.df['AV'][idx] / self.df['Time'][idx]


    def plot(self, outfile: str):
        """Plots IV-curve annotated with what the algorithm interpreted from the data, and saves in `outfile`"""

        import matplotlib.pyplot as plt
        import seaborn as sns
        sns.set_palette('pastel')

        # create high quality figure and plot IV curve
        fig = plt.figure(figsize=(10, 4), dpi=300)
        fig.patch.set_facecolor('white')
        sns.lineplot(x=self.df.AV, y=self.df.AI)
        plt.xlabel("Voltage $V$ [V]")
        plt.ylabel("Current $I$ [A]")

        # here we draw a vertical red line at the voltage where the cell was set
        # and put the voltage in the title
        if self.activity() in ['set', 'form']:
            if self.set_voltage is None:
                plt.title(f'{self.activity()}: No thresh detected')
            else:
                plt.title(f'{self.activity()}: {self.set_voltage:.2f} V')
                plt.vlines(self.set_voltage, self.df.AI.min(), self.df.AI.max(), colors='r')

        # draw a light gray background region behind where the data was linear
        # and put the resistance/R2 values in the title
        elif self.activity() == 'reset':
            if self.resistance is None:
                plt.title('reset: Too nonlinear')
            else:
                plt.title(f'Reset: (R_on = {self.resistance:.2f} Ω, R2 = {self.r2:.3f})')
                x_min, x_max = self.linear_voltage_regime
                plt.axvspan(x_min, x_max, facecolor='0.95', zorder=-100)
        
        plt.savefig(outfile)
        plt.close()
