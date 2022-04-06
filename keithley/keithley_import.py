# Jim Furches

import os
import argparse
from dataclasses import dataclass
from typing import List, Tuple

# needed for manual logs
import yaml
# read excel files
import pandas as pd
# can retrieve the time
from xml.dom.minidom import Element, parse as parse_xml

# dates and localizing from utc to our time
from datetime import datetime
import pytz

# cache expensive operations as properties
from functools import cached_property

from tqdm import tqdm

from abc import ABC, abstractmethod



@dataclass(frozen=True, repr=False)
class Cell:
    """Class representing the location of a cell on a wafer"""

    wafer: str
    grid: str
    subgrid: str
    cell: str

    def __str__(self):
        return '(' + ','.join([self.wafer, self.grid, self.subgrid, self.cell]) + ')'

class Run(ABC):
    """Abstract class representing a Keithley run. See `NormalRun` or `ObservationRun`"""

    @cached_property
    def _data(self) -> pd.DataFrame:
        """Returns a data frame reading the excel file from keithley. Caches the result"""

        xls_file = '{}/data@1[{}].xls'.format(self._folder(), self.run_num)
        return pd.read_excel(xls_file)
    
    @cached_property
    def _keithley_time(self) -> datetime:
        """Loads the XML config file of the run and gets the time in Eastern time"""

        xml_file = f'{self._folder()}/run.xml'
        doc = parse_xml(xml_file)

        time_el: Element = doc.getElementsByTagName("Time")[0]

        s: str = time_el.firstChild.data
        s = s.replace('T', ' ')[:-1]
        s = s[:s.index('.')]

        # parse from iso after removing T and Z
        d = datetime.fromisoformat(s).replace(tzinfo=pytz.UTC)
        tz = pytz.timezone('US/Eastern')
        loc = d.astimezone(tz)

        return loc
    
    @abstractmethod
    def _folder(self) -> str:
        """Get the folder of the run"""

        pass
    
    @abstractmethod
    def _csv_filename(self) -> str:
        """Get the CSV name compatible with the naming convention for the rest of this repo"""

        pass

    def _extra(self) -> str:
        """Any extra comments generated programmatically to be included in the CSV"""

        return None

    def to_csv(self, dir):
        """Saves this run to a CSV using the naming convention inside the directory
        
        Parameters
        ----------
        dir : str
            The directory in which to save the CSV
        """

        filename = self._csv_filename()
        # omitting file makes pandas return CSV as a string
        contents = self._data.to_csv(index=False, line_terminator='\n')

        # tack on any extras to the comments, starting with a newline
        comments = self.comment + (f'\n{self._extra()}' if self._extra() else '')

        # write CSV with comments
        with open(dir + '/' + filename, 'w') as f:
            lines = [
                '---',
                comments,
                '---',
                contents
            ]

            f.writelines('%s\n' % line for line in lines)
    
    @staticmethod
    def format_date(d: datetime) -> str:
        return d.strftime(r'%y%m%d%H%M%S')

@dataclass(frozen=True)
class NormalRun(Run):
    """Represents any Set, Form, or Reset operation"""

    run_num: int
    op: str
    position: Cell
    icc: str
    rr: float
    step: float
    time: datetime = None
    start: float = 0
    end: float = 0
    comment: str = ''

    def _folder(self) -> str:
        folder_name = 'Reset' if self.op.lower() == 'reset' else 'Set'
        return '{}/Run{}'.format(folder_name, self.run_num)
    
    def _voltage_range(self) -> Tuple[int, int]:
        """Returns the minimum and maximum A probe voltage during the test"""

        return int(self._data.AV.min()), int(self._data.AV.max())
    
    def _csv_filename(self) -> str:
        activity = self.op.lower()
        date = Run.format_date(self._keithley_time)
        vmin, vmax = self._voltage_range()

        # swap order for reset
        if self.op == 'reset':
            vmax, vmin = vmin, vmax

        name = f'{self.position}_{date}_{activity}_{vmin}_{vmax}_{self.rr}_{self.icc}.csv'

        return name

@dataclass(frozen=True)
class ObservationRun(Run):
    """Represents any Observe run"""

    run_num: int
    op: str
    position: Cell
    icc: str
    time: datetime = None
    bias: float = 0
    comment: str = ''

    def _folder(self) -> str:
        return f'Observe/Run{self.run_num}'
    
    def _csv_filename(self) -> str:
        date = Run.format_date(self._keithley_time)
        # get voltage bias of A probe from data and assume it's on copper
        vbias = self._data.AV.values[0]
        name = f'{self.position}_{date}_observe_0_{vbias:.3f}_{self.icc}.csv'

        return name

    def _state(self) -> str:
        """Predicts the state of an observe operation from the data
        
        Return
        ------
        `Set` if the effective resistance of the cell is < 10 kOhm, otherwise `Reset`
        """

        r = abs(self._data.AV[0] / self._data.AI[0])

        return 'Set' if r <= 1e5 else 'Reset'
    
    def _extra(self) -> str:
        # include the predicted observe state with an asterisk to indicate it came from an algorithm
        # and could in rare cases be wrong
        return f'State: {self._state()}*'

def load_yml_file(filename: str) -> List[Run]:
    """Loads the yml experiment log and parses the Runs from it"""

    with open(filename) as f:
        d: dict[str, dict] = yaml.load(f, yaml.Loader)
    
    runs = []

    # caching things to allow the user to omit redudant information
    # and instead just document what changes
    old_params = {
        'reset': {'op': 'reset'},
        'set': {},
        'observe': {'op': 'observe'}
    }
    old_pos = {}

    for run_name, v in d.items():
        # parse the name of the run. ex: 'Reset 168' -> ['reset', 168]
        type, run_num = run_name.split(' ')
        type = type.lower()
        v.update({'run_num': int(run_num)})

        # retrieve old cache values specific to this run type
        old = old_params[type]
        # merge cache with new data, not overwriting new information
        # later values take precedence over earlier ones
        # so the order is cached parameters -> cached cell position -> new data
        v = {**old, **old_pos, **v} 
        new = v.copy()
        
        # don't pass comments in the cache
        if 'comment' in new:
            del new['comment']
        # we handle position separately, so don't include it in per-run type cache
        if 'position' in new:
            del new['position']
        
        # update
        old_params[type] = new

        if 'subgrid' not in v['position']:
            v['position']['subgrid'] = '-1,-1'
        old_pos['position'] = v['position']

        # parse the position into Cell object and pass it into our current Run
        v['position'] = Cell(**v['position'])

        if type == 'observe':
            r = ObservationRun(**v)
        else:
            r = NormalRun(**v)
        
        runs.append(r)
    
    return runs

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('yml_file', type=str)
    parser.add_argument('output_dir', type=str)
    args = parser.parse_args()
 
    try:
        os.makedirs(args.output_dir)
    except FileExistsError:
        pass

    runs = load_yml_file(args.yml_file)

    for run in tqdm(runs):
        run.to_csv(args.output_dir)