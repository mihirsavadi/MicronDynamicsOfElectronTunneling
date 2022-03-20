# Mihir Savadi 24th February 2021

from resistanceAnalyzer.report import CellAnalyzerReport
from lib import *
from utils.csvItem import csvItem
from utils.cellSizeDataBase import cellSizes
from pdfGenerator.pdfgen import pdfGen

from tqdm import tqdm

class dataBaseCollator :
    """ This class employs the csvItem and pdfGen class to provide a single wrapper to deal with the entire database
        in one shot.
    """

    def __init__(self, pathToData: str, pathToDump: str) :

        self.pathToData       = pathToData
        self.pathToDumpReport = pathToDump
        os.makedirs(self.pathToDumpReport)

        # first convert all csv's in the data base into a list csvItem objects
        self.csvData = self.__organizeCSVs()
        
        self.summaryDict = self.__generateSummaryReport()

        # then create a pdf for each of these sublists using the pdfGenerator class and put them in a new reports
        # folder.
        for key,value in tqdm(self.csvData.items()) :
            pdfGen(value, self.summaryDict, self.pathToDumpReport)
            CellAnalyzerReport(value, self.summaryDict, self.pathToDumpReport).generateReport()


    def __organizeCSVs(self) -> OrderedDict :
        """Takes in the path where all the CSV's are, and spits an ordered dictionary where each entry contains time
        ordered list of csvItem's for only one cell. There is an entry for every cell.

        Returns
        -------
        OrderedDict
            See function description.
        """

        csvFileNames = os.listdir(self.pathToData)

        # first fill up entire dictionary
        cellDataDict = OrderedDict()
        for csv in csvFileNames :
            csvItemObject = csvItem(self.pathToData + csv)

            # if target cell doesn't exist in dict create empty list then append to it, otherwise just append.
            if cellDataDict.get(f'{csvItemObject.targetCellCoord}') == None :
                cellDataDict[f'{csvItemObject.targetCellCoord}'] = []

            cellDataDict[f'{csvItemObject.targetCellCoord}'].append(csvItemObject)

            # do same as above but for target cell. also check first if there is even a target cell to begin with.
            if csvItemObject.neighborCellCoord[0] != '<' :
                
                if cellDataDict.get(f'{csvItemObject.neighborCellCoord}') == None :
                    cellDataDict[f'{csvItemObject.neighborCellCoord}'] = []

                cellDataDict[f'{csvItemObject.neighborCellCoord}'].append(csvItemObject)

        # then time order each entry in the dictionary
        def sortingKey(csvItemObj: csvItem) -> int :
            return csvItemObj.timeStamp_whole

        for key, value in cellDataDict.items() :
            value.sort(key=sortingKey)

        return cellDataDict
        
    def __generateSummaryReport(self) -> dict:
        """Generates a summary report as a text file at the 'pathToDumpReport' directory. Includes information about
            the cells accessed, their size, when it was last accessed, and number of times stimulated. Returns a dict
            containing all this information.

        Returns
        -------
        dict
        """
        summaryReportDict = OrderedDict()

        for key, value in self.csvData.items() :
            cellSummaryDict = OrderedDict()

            firstCSV = value[0]

            cell_t_split = firstCSV.targetCellCoord.split(',')
            arrayCoordinates = f'({cell_t_split[1]},{cell_t_split[2]})'

            cellSummaryDict["cellSize"] = cellSizes[arrayCoordinates]

            cellSummaryDict['timesAccessed'] = len(value)

            cellSummaryDict['lastAccessed'] = f'{value[-1].timeStamp_year}/{value[-1].timeStamp_month}/{value[-1].timeStamp_day} at {value[-1].timeStamp_time12hr}'

            summaryReportDict[key] = cellSummaryDict

        outputTextFile = ["Cell Coordinate,Cell Size,no. of times stimulated,last stimulated"]
        for key, value in summaryReportDict.items() :
            outputTextFile.append(f"({key}),{value['cellSize']},{value['timesAccessed']},{value['lastAccessed']}")

        file = open(self.pathToDumpReport+f'/cellsUsedSummary.txt', 'w')
        for line in outputTextFile :
            file.write(line+'\n')
        file.close()

        return summaryReportDict