# Jim Furches

# Adapted from `pdfgen.py`

from dataclasses import dataclass

import pandas
from resistanceAnalyzer.cellanalyzer import CellAnalyzer
from utils.csvItem import csvItem

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreakIfNotEmpty, Table, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils

from typing import Iterable, Dict, List, OrderedDict

import matplotlib.pyplot as plt
import seaborn as sns

import os
import shutil

class CellAnalyzerReport:
    """Class that takes in CSV files, analyzes the properties of the cells using the CellAnalyzer, and creates
    a special pdf report containing that information
    """

    def __init__(self, csvItems: List[csvItem], summaryDict: Dict[str, object], pdfFolder: str):
        """Takes in a list of csvItem objects to generate a PDF file from and outputs a pdf in folder path

        Parameters
        ----------
        csvItems : List[csvItem] 
            Chronological list of CSV files all belonging to a single cell

        summaryDict : Dict[str, object]
            Cell usage summary dict created by databaseCollator

        pdfFolder : str
            Folder in which to save PDF file
        """

        self.cellCoord = csvItems[0].targetCellCoord
        self.pdfFolder = pdfFolder
        self.pdf_name = f"{pdfFolder}/({self.cellCoord})_characteristics.pdf"

        self.items = csvItems

        cellSummaryDict = summaryDict[self.cellCoord]
        self.cellSize = cellSummaryDict['cellSize']
        self.timesAccessed = cellSummaryDict['timesAccessed']
        self.lastAccessed = cellSummaryDict['lastAccessed']

        self.df = pandas.DataFrame(columns=['Cycle', 'Set Icc', 'Set Voltage', 'R_on', 'R2'])
        self.summaryTable = [["Cycle #", "Set Icc (μA)", "Set Voltage (V)", "R_on (Ω)", "R2"]]

        self.state = ProcessState(1, None, None, None, None)
        self.prevState = self.state
        
    def generateReport(self):
        self.tmpDir = f'{self.pdfFolder}/tmp'
        os.makedirs(self.tmpDir)

        # setup document
        doc = SimpleDocTemplate(
            self.pdf_name,
            pagesize=letter,
            rightMargin=35, leftMargin=35,
            topmargin=10, bottommargin=18,
        )

        styles = getSampleStyleSheet()

        # this is the series of items to be produced in our pdf
        flowables = [    
            # add heading
            Paragraph(f'({self.cellCoord}) Characteristics', styles["Heading1"]),
            Paragraph(f'——————————————————————————————————', styles["Heading2"]),
            ListFlowable(
                [
                    Paragraph(f"<b>Cell Size:</b> {self.cellSize}", styles["BodyText"]),
                    Paragraph(f"<b>Times Accessed:</b> {self.timesAccessed}", styles["BodyText"]),
                    Paragraph(f"<b>Last Measurement:</b> {self.lastAccessed}", styles["BodyText"])
                ],
                bulletType='bullet'
            ),
            Paragraph("Summary", styles["Heading4"])
        ]

        pages = []

        for i, page in enumerate(self.items):
            if page.activity == 'observe':
                continue

            for flowable in self.__generatePage(page, i):
                pages.append(flowable)
            
            # put each operation on its own page
            if i < len(self.items) - 1:
                pages.append(PageBreakIfNotEmpty())
        
        summaryTableFlowable = Table(self.summaryTable)
        flowables.append(summaryTableFlowable)
        flowables.append(self.__getIccRonPlot())
        flowables.append(PageBreakIfNotEmpty())

        flowables += pages

        if len(flowables) > 0:
            doc.build(flowables)

        shutil.rmtree(self.tmpDir)
    
    def __generatePage(self, page: csvItem, i: int) -> List:
        """Takes a CSV item and returns a list of flowables. Does not work on observe"""

        ca = CellAnalyzer(page)

        # header
        styles = getSampleStyleSheet()
        flowables = [
            Paragraph(ca.activity(), styles["Heading2"]),
            Paragraph(f'——————————————————————————————————', styles["Heading2"])
        ]

        props = OrderedDict({
            'Time': page.timeStamp_time12hr,
            'Icc': f'{page.complianceCurrent:.1f}{page.complianceCurrentUnits}',
            'Voltage Range': f'{page.startVoltage}  →  {page.endVoltage}',
            'Target Ramp Rate': f'{page.rampRate}',
            'True Ramp Rate': f'{ca.ramp_rate:.3f} V/s*',
            'Cycle': self.state.cycle
        })

        if ca.activity() == 'reset':
            # successful reset
            if ca.resistance:
                self.state.r_on = ca.resistance
                self.state.r2 = ca.r2

                if self.state.set_icc is None:
                    self.state.set_icc = self.prevState.set_icc
                    self.state.set_voltage = self.prevState.set_voltage

                props['Resistance'] = f'{ca.resistance:.2f} Ω'
                props['Linear Fit R2'] = f'{ca.r2:.3f}'
            
            else:
                props['Error'] = 'Too nonlinear/failed'

        else:
            # successful set/form
            if ca.set_voltage:
                self.state.set_icc = page.complianceCurrent
                self.state.set_voltage = ca.set_voltage

                props['Set Voltage'] = f'{ca.set_voltage:.2f} V'

            else:
                props['Error'] = 'Set failed'
        
        if self.state.is_complete_cycle():
            self.df = self.df.append({
                'Cycle': self.state.cycle,
                'Set Icc': self.state.set_icc,
                'Set Voltage': self.state.set_voltage,
                'R_on': self.state.r_on,
                'R2': self.state.r2
            }, ignore_index=True)

            self.summaryTable.append([self.state.cycle, self.state.set_icc, f'{self.state.set_voltage:.2f}', f'{self.state.r_on:.2f}', f'{self.state.r2:.3f}'])
            self.prevState = self.state
            self.state = ProcessState(self.state.cycle + 1, None, None, None, None)
    
        # add the properties as a bulleted list
        flowables.append(ListFlowable(
            [Paragraph(f'<b>{k}:</b> {v}', styles['BodyText']) for k, v in props.items()],
            bulletType='bullet'
        ))

        # add comments from user
        flowables.append(Paragraph(page.comments, styles['BodyText']))

        # generate the plot
        plotName = f'{self.tmpDir}/ca_plot_{i}.png'
        ca.plot(plotName)
        flowables.append(self.__getImage(plotName, width=400))

        return flowables


    def __getImage(self, path, width=1):
        """Makes resizing images to scale easy
        """
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        return Image(path, width=width, height=(width * aspect))
    
    def __getIccRonPlot(self) -> Image:
        path = f"{self.tmpDir}/r_on_plot.png"

        fig = plt.figure(dpi=300)
        fig.patch.set_facecolor('white')
        sns.scatterplot(data=self.df.loc[self.df.R2 >= 0.98, :], x="Set Icc", y="R_on")
        plt.title("Resistance")
        plt.xlabel("$I_{cc}$ [μA]")
        plt.ylabel("$R_{on}$ [Ω]")
        plt.savefig(path)
        plt.close()

        return self.__getImage(path, width=400)

@dataclass
class ProcessState:
    cycle: int
    set_icc: str
    set_voltage: float
    r_on: float
    r2: float

    def is_complete_cycle(self):
        return self.cycle \
            and self.set_icc \
            and self.set_voltage \
            and self.r_on \
            and self.r2