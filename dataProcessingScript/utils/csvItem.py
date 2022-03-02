# Mihir Savadi 23rd February 2021

from lib import *
from utils.csvParser import csvParser

class csvItem :
    """Takes in the path to one single CSV, parses all the information in it from its file name and its contents
        (according to the protocol laid out in section 2.4 of the summary document), and holds it in fields. This makes
        handling each csv's data easy in the parent class 'dataBaseCollator', where each csv is just an object of this
        class.
    """

    def __init__(self, csvPath: str) :

        # MUST MAINTAIN ORDER BELOW. Variables within this class are order dependent.

        self.csvPathString = csvPath                 # just a place to store the path of the CSV
        self.csvFileName   = self.__getCSVfileName() # gets the file name with rest of path removed

        self.isThreeProbe  = self.__isThreeProbe()   # if two probe then this is true

        # coordinates of cells involved. If 2 probe then only target cell is valid.
        cellCoords = self.__getCellCoord()
        self.targetCellCoord   = cellCoords['cell_t'] 
        self.neighborCellCoord = cellCoords['cell_n']  

        timeDict = self.__getTimeStamp()
        self.timeStamp_whole    = timeDict['whole']
        self.timeStamp_year     = timeDict['year']
        self.timeStamp_month    = timeDict['month'] 
        self.timeStamp_day      = timeDict['day'] 
        self.timeStamp_hour     = timeDict['hour']     # in 24hr format
        self.timeStamp_minute   = timeDict['minute']
        self.timeStamp_second   = timeDict['second']
        self.timeStamp_time12hr = timeDict['time12hr'] # e.g. 10:53pm
        self.timeStamp_time24hr = timeDict['time24hr'] # e.g. 1410

        self.activity           = self.__getCellActivity()

        activityParameters = self.__getActivityParameters()
        self.startVoltage           = activityParameters['startV']
        self.endVoltage             = activityParameters['endV']
        self.rampRate               = activityParameters['rampRate'] # in volts per second
        self.complianceCurrent      = activityParameters['complianceCurrent'] 
        self.complianceCurrentUnits = activityParameters['complianceCurrentUnits']
        self.platinumVoltage        = activityParameters['platinumV']
        self.copperVoltage          = activityParameters['copperV']
        self.runFolderName          = activityParameters['runFolderName']

        self.__csvParserObject = csvParser(csvPath)
        self.comments = self.__csvParserObject.comments   # whatever comments were at the top of the file 
        self.title    = self.__csvParserObject.title      # the title for each column in the csv

        # these contain lists of floats containing each column in the csv for 2-probe measurements probeC will be
        # unpopulated obviously
        axisObject = self.__getAxis()
        self.timeAxis       = axisObject['timeAxis']
        self.probeA_voltage = axisObject['probeA_voltage']
        self.probeA_current = axisObject['probeA_current']
        self.probeB_voltage = axisObject['probeB_voltage']
        self.probeB_current = axisObject['probeB_current']
        self.probeC_voltage = axisObject['probeC_voltage']
        self.probeC_current = axisObject['probeC_current']

    def __getCSVfileName(self) -> str :
        """gets the name of the file with the rest of the path removed

        Returns
        -------
        str
            name of the file with the rest of the path removed
        """
        fileName = ''
        for i in range(-1, -(len(self.csvPathString)+1), -1) :
            if self.csvPathString[i] == '/' :
                break
            else:
                fileName = self.csvPathString[i] + fileName

            fileName = fileName.replace(' ', '')

        return fileName

    def __isThreeProbe(self) -> bool :
        """Returns false if csv is a 3 probe measurement, true if not

        Returns
        -------
        bool
        """
        isThreeProbe = False

        fileNameSplit = self.csvFileName.split('_')
        if fileNameSplit[0][0] == '(' and fileNameSplit[1][0] == '(' :
            isThreeProbe = True

        return isThreeProbe

    def __getCellCoord(self) -> typing.List[str] :
        """List of strings, at most two entries. One if 2-probe, 2 if 3-probe. Each entry corresponds to the coordinate
        of the cell involved.

        Returns
        -------
        typing.List[str]
        """
        cellCoords = {}
        fileNameSplit = self.csvFileName.split('_')
        if self.isThreeProbe :
            cellCoords['cell_t'] = fileNameSplit[0][1:-1] # remove the brackets
            cellCoords['cell_n'] = fileNameSplit[1][1:-1] # remove the brackets
            return cellCoords
        else :
            cellCoords['cell_t'] = fileNameSplit[0][1:-1] # remove the brackets
            cellCoords['cell_n'] = '<2 probe measurement, so no neighbor cell>'
            return cellCoords

    def __getTimeStamp(self) -> typing.Dict :
        """Returns a dictionary detailing year month day hour minute in string, e.g. 2021 February 23 10.53pm

        Returns
        -------
        typing.Dict
        """
        time = {}
        fileNameSplit = self.csvFileName.split('_')

        if self.isThreeProbe :
            timeString = fileNameSplit[2]
        else :
            timeString = fileNameSplit[1]

        time['year'] = f'20{timeString[0:2]}'
        
        time['month'] = datetime.strptime(timeString[2:4], "%m").strftime("%B")

        time['day'] = timeString[4:6]

        time['hour'] = timeString[6:8]
        time['minute'] = timeString[8:10]

        # check if seconds included or not
        if len(timeString) == 12 :
            time['whole'] = int(timeString)
            time['second']  = timeString[10:]
            time['time24hr'] = timeString[6:]
            time['time12hr'] = datetime.strptime(timeString[6:], "%H%M%S").strftime("%I:%M:%S%p")
        else:
            time['whole'] = int(timeString+'00')
            time['second']  = '00'
            time['time24hr'] = timeString[6:10]
            time['time12hr'] = datetime.strptime(timeString[6:10], "%H%M").strftime("%I:%M%p")

        return time

    def __getCellActivity(self) -> str :
        """Gets activity that cell was undergoing. Only valid for 2 probe. Can be form, reset, set, or observe

        Returns
        -------
        str
        """
        if self.isThreeProbe :
            return '<csv is 3-probe measurement. No Activity Value>'
        else :
            return self.csvFileName.split('_')[2].lower()

    def __getActivityParameters(self) -> typing.Dict :
        """Returns the activity parameters for the cell in the csv depending on which activity it was undergoing and
        whether it was 2 probe or 3 probe. So depending, some fields may not be populated. Please see section 2.4 of the
        summary document.

        Returns
        -------
        typing.Dict
            _description_
        """
        aParams = {}

        fileNameSplit = self.csvFileName.split('_')

        if self.isThreeProbe :
            aParams['startV']                 = '<3 probe, so invalid>'
            aParams['endV']                   = '<3 probe, so invalid>'
            aParams['rampRate']               = '<3 probe, so invalid>'
            aParams['complianceCurrent']      = '<3 probe, so invalid>'
            aParams['complianceCurrentUnits'] = '<3 probe, so invalid>'
            aParams['platinumV']              = '<platinum voltage should be entered in comments>'
            aParams['copperV']                = '<platinum voltage should be entered in comments>'
            aParams['runFolderName']          = fileNameSplit[:-4]

        else :
            aParams['runFolderName']          = '<2 probe, so invalid>'

            if self.activity in ['form', 'reset', 'set'] :
                aParams['startV']                 = fileNameSplit[3] + 'V'
                aParams['endV']                   = fileNameSplit[4] + 'V'
                aParams['rampRate']               = fileNameSplit[5] + 'V/s'
                aParams['complianceCurrent']      = float(fileNameSplit[-1][:-6])
                aParams['complianceCurrentUnits'] = fileNameSplit[-1][-6:-4]
                aParams['platinumV']              = '<platinum voltage should be entered in comments>'
                aParams['copperV']                = '<platinum voltage should be entered in comments>'

            elif self.activity == 'observe' :
                aParams['startV']                 = '<2 probe observe activity, so invalid>'
                aParams['endV']                   = '<2 probe observe activity, so invalid>'
                aParams['rampRate']               = '<2 probe observe activity, so invalid>'
                aParams['complianceCurrent']      = float(fileNameSplit[-1][:-6])
                aParams['complianceCurrentUnits'] = fileNameSplit[-1][-6:-4]
                aParams['platinumV']              = fileNameSplit[3] + 'V'
                aParams['copperV']                = fileNameSplit[4] + 'V'

            else :
                aParams['startV']                 = f'<{self.activity} is an invalid 2 probe activity parameter>'
                aParams['endV']                   = f'<{self.activity} is an invalid 2 probe activity parameter>'
                aParams['rampRate']               = f'<{self.activity} is an invalid 2 probe activity parameter>'
                aParams['complianceCurrent']      = f'<{self.activity} is an invalid 2 probe activity parameter>'
                aParams['complianceCurrentUnits'] = f'<{self.activity} is an invalid 2 probe activity parameter>'
                aParams['platinumV']              = f'<{self.activity} is an invalid 2 probe activity parameter>'
                aParams['copperV']                = f'<{self.activity} is an invalid 2 probe activity parameter>'

        return aParams

    def __getAxis(self) -> typing.Dict :
        """Returns each of the axis' as column vectors -- materialized in python as a 1 dimension list of floats.

        Returns
        -------
        typing.Dict
        """
        axisDict = {}

        if 'Time' in self.__csvParserObject.title :
            axisDict['timeAxis'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('Time')]
        else :
            axisDict['timeAxis'] = '<no column named time in CSV>'
            raise Exception(f'{self.csvFileName} has no time axis. This needs to be fixed.')

        if 'AV' in self.__csvParserObject.title and 'AI' in self.__csvParserObject.title : 
            axisDict['probeA_voltage'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('AV')]
            axisDict['probeA_current'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('AI')]
        else :
            axisDict['probeA_voltage'] = '<no A probe voltage column in CSV>'
            axisDict['probeA_current'] = '<no A probe current column in CSV>'

        if 'BV' in self.__csvParserObject.title and 'BI' in self.__csvParserObject.title : 
            axisDict['probeB_voltage'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('BV')]
            axisDict['probeB_current'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('BI')]
        else :
            axisDict['probeB_voltage'] = '<no B probe voltage column in CSV>'
            axisDict['probeB_current'] = '<no B probe current column in CSV>'

        if 'CV' in self.__csvParserObject.title and 'CI' in self.__csvParserObject.title : 
            axisDict['probeC_voltage'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('CV')]
            axisDict['probeC_current'] = self.__csvParserObject.columns[self.__csvParserObject.title.index('CI')]
        else :
            axisDict['probeC_voltage'] = '<no C probe voltage column in CSV>'
            axisDict['probeC_current'] = '<no C probe current column in CSV>'

        return axisDict

    def getPlots(self) -> typing.Dict :
        """Generates matplotlib objects for the csv at and returns a dictionary of matplotlib figure objects with all
            csv details plotted. This function is public, because pre-emptively running it in the constructor for many
            objects will destroy the host machine's memory -- so call it only when needed.

        Returns
        -------
            Dictionary for of matplotlib figure objects that are plots for each probe -- index's are 'probe A plot',
            'probe B plot', and 'probe C plot'
        """

        plots = {}

        AProbeExists = (type(self.probeA_voltage) != str)
        BProbeExists = (type(self.probeB_voltage) != str)
        CProbeExists = (type(self.probeC_voltage) != str)

        if AProbeExists :
            A_probe_plots        = plt.figure() 
            A_probe_plots.subplots_adjust(wspace=0, hspace=0.45)
            A_probe_plots.suptitle('Probe A plots', fontsize=16)

            time_voltage_plot    = A_probe_plots.add_subplot(2, 1, 1)
            time_current_plot    = time_voltage_plot.twinx()
            voltage_current_plot = A_probe_plots.add_subplot(2, 1, 2)

            time_voltage_plot.set_xlabel("Time (seconds)", fontsize='small')
            time_voltage_plot.set_ylabel("Voltage ($V$)", fontsize='small', color='red')
            time_voltage_plot.set_title("Voltage and Current against Time", fontsize='small', weight = 'bold')
            time_voltage_plot.plot(self.timeAxis, self.probeA_voltage, color='red')
            time_voltage_plot.set_xticks(np.arange(0, int(max(self.timeAxis))+1, 1))
            time_voltage_plot.set_yticks(np.linspace(min(self.probeA_voltage), max(self.probeA_voltage), 5))
            time_voltage_plot.tick_params(axis='y', colors="red")

            time_current_plot.set_xlabel("Time (seconds)", fontsize='small')
            time_current_plot.set_ylabel("Current ($A$)", fontsize='small', color="blue")
            time_current_plot.plot(self.timeAxis, self.probeA_current, color="blue")
            time_current_plot.set_xticks(np.arange(0, int(max(self.timeAxis))+1, 1))
            time_current_plot.set_yticks(np.linspace(min(self.probeA_current), max(self.probeA_current), 5))
            time_current_plot.tick_params(axis='y', colors="blue")

            voltage_current_plot.set_xlabel("Voltage ($V$)", fontsize='small')
            voltage_current_plot.set_ylabel("Current ($A$)", fontsize='small')
            voltage_current_plot.set_title('Current against Voltage', fontsize='small', weight = 'bold')
            voltage_current_plot.plot(self.probeA_voltage, self.probeA_current)
            voltage_current_plot.set_xticks(np.linspace(min(self.probeA_voltage), max(self.probeA_voltage), 5))
            voltage_current_plot.set_yticks(np.linspace(min(self.probeA_current), max(self.probeA_current), 5))

            plots['probe A plot'] = A_probe_plots

        else :
            plots['probe A plot'] = '<does not exist>'

        if BProbeExists :
            B_probe_plots        = plt.figure() 
            B_probe_plots.subplots_adjust(wspace=0, hspace=0.45)
            B_probe_plots.suptitle('Probe B plots', fontsize=16)

            time_voltage_plot    = B_probe_plots.add_subplot(2, 1, 1)
            time_current_plot    = time_voltage_plot.twinx()
            voltage_current_plot = B_probe_plots.add_subplot(2, 1, 2)

            time_voltage_plot.set_xlabel("Time (seconds)", fontsize='small')
            time_voltage_plot.set_ylabel("Voltage ($V$)", fontsize='small', color='red')
            time_voltage_plot.set_title("Voltage and Current against Time", fontsize='small', weight = 'bold')
            time_voltage_plot.plot(self.timeAxis, self.probeB_voltage, color='red')
            time_voltage_plot.set_xticks(np.arange(0, int(max(self.timeAxis))+1, 1))
            time_voltage_plot.set_yticks(np.linspace(min(self.probeB_voltage), max(self.probeB_voltage), 5))
            time_voltage_plot.tick_params(axis='y', colors="red")

            time_current_plot.set_xlabel("Time (seconds)", fontsize='small')
            time_current_plot.set_ylabel("Current ($A$)", fontsize='small', color="blue")
            time_current_plot.plot(self.timeAxis, self.probeB_current, color="blue")
            time_current_plot.set_xticks(np.arange(0, int(max(self.timeAxis))+1, 1))
            time_current_plot.set_yticks(np.linspace(min(self.probeB_current), max(self.probeB_current), 5))
            time_current_plot.tick_params(axis='y', colors="blue")

            voltage_current_plot.set_xlabel("Voltage ($V$)", fontsize='small')
            voltage_current_plot.set_ylabel("Current ($A$)", fontsize='small')
            voltage_current_plot.set_title('Current against Voltage', fontsize='small', weight = 'bold')
            voltage_current_plot.plot(self.probeB_voltage, self.probeB_current)
            voltage_current_plot.set_xticks(np.linspace(min(self.probeB_voltage), max(self.probeB_voltage), 5))
            voltage_current_plot.set_yticks(np.linspace(min(self.probeB_current), max(self.probeB_current), 5))

            plots['probe B plot'] = B_probe_plots
            
        else :
            plots['probe B plot'] = '<does not exist>'

        
        if CProbeExists :
            A_probe_plots        = plt.figure() 
            A_probe_plots.subplots_adjust(wspace=0, hspace=0.45)
            A_probe_plots.suptitle('Probe B plots', fontsize=16)

            time_voltage_plot    = A_probe_plots.add_subplot(2, 1, 1)
            time_current_plot    = time_voltage_plot.twinx()
            voltage_current_plot = A_probe_plots.add_subplot(2, 1, 2)

            time_voltage_plot.set_xlabel("Time (seconds)", fontsize='small')
            time_voltage_plot.set_ylabel("Voltage ($V$)", fontsize='small', color='red')
            time_voltage_plot.set_title("Voltage and Current against Time", fontsize='small', weight = 'bold')
            time_voltage_plot.plot(self.timeAxis, self.probeC_voltage, color='red')
            time_voltage_plot.set_xticks(np.arange(0, int(max(self.timeAxis))+1, 1))
            time_voltage_plot.set_yticks(np.linspace(min(self.probeC_voltage), max(self.probeC_voltage), 5))
            time_voltage_plot.tick_params(axis='y', colors="red")

            time_current_plot.set_xlabel("Time (seconds)", fontsize='small')
            time_current_plot.set_ylabel("Current ($A$)", fontsize='small', color="blue")
            time_current_plot.plot(self.timeAxis, self.probeC_current, color="blue")
            time_current_plot.set_xticks(np.arange(0, int(max(self.timeAxis))+1, 1))
            time_current_plot.set_yticks(np.linspace(min(self.probeC_current), max(self.probeC_current), 5))
            time_current_plot.tick_params(axis='y', colors="blue")

            voltage_current_plot.set_xlabel("Voltage ($V$)", fontsize='small')
            voltage_current_plot.set_ylabel("Current ($A$)", fontsize='small')
            voltage_current_plot.set_title('Current against Voltage', fontsize='small', weight = 'bold')
            voltage_current_plot.plot(self.probeC_voltage, self.probeC_current)
            voltage_current_plot.set_xticks(np.linspace(min(self.probeC_voltage), max(self.probeC_voltage), 5))
            voltage_current_plot.set_yticks(np.linspace(min(self.probeC_current), max(self.probeC_current), 5))

            plots['probe B plot'] = A_probe_plots

        else :
            plots['probe C plot'] = '<does not exist>'

        return plots
