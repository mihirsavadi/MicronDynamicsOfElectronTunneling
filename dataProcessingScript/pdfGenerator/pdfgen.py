# Mihir Savadi 24th February 2021

# got help from https://www.blog.pythonlibrary.org/2021/09/28/python-101-how-to-generate-a-pdf/
# and https://vonkunesnewton.medium.com/generating-pdfs-with-reportlab-ced3b04aedef

from matplotlib.pyplot import savefig
from lib import *
from utils.csvItem import csvItem

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils

class pdfGen :
    """Class to take generated matplotlib plot objects and other cell information, and create a pdf of them, in the
        established format.
    """

    def __init__(self, csvItemObjList: list([csvItem]), summaryDict: dict, pdfDumpPath: str) -> None:
        """Takes in a list of csvItem objects to generate a PDF file from. Note that this list needs to be time ordered
        and only have cells of one coordinate -- this is all handled by the dataBaseCollator class. Also takes in an
        ordered dictionary containing summary information about the cell in question. Also takes in a the path to
        produce the final pdf as a string.

        Parameters
        ----------
        csvItemObjList : typing.List 
            see function description

        summaryDict : ordered dictionary


        pdfDumpPath : str
            see function description
        """
        cellCoord = csvItemObjList[0].targetCellCoord
        cellSummaryDict = summaryDict[cellCoord]
        
        # setup document
        doc = SimpleDocTemplate(
            pdfDumpPath + f"/({cellCoord})_plots.pdf",
            pagesize=letter,
            rightMargin=35, leftMargin=35,
            topmargin=10, bottommargin=18,
        )
        styles = getSampleStyleSheet()

        flowables = [] # this is the series of items to be produced in our pdf

        # add heading
        flowables.append(Paragraph('('+cellCoord+') Plots and Summary', styles["Heading1"]))

        # add summary details
        flowables.append(Paragraph(f"- Cell Size = {cellSummaryDict['cellSize']}", styles["BodyText"]))
        flowables.append(Paragraph(f"- Number of Times Accessed = {cellSummaryDict['timesAccessed']}", 
            styles["BodyText"]))
        flowables.append(Paragraph(f"- Last Stimulated = {cellSummaryDict['lastAccessed']}", styles["BodyText"]))
        flowables.append(Paragraph(f"-------------------------------------------------", styles["BodyText"]))

        # add sections with plots for each csv
        tempImageDir = pdfDumpPath+f'tempImgs/'
        os.makedirs(tempImageDir)
        for i, csvObj in enumerate(csvItemObjList) :
            plots = csvObj.getPlots()

            flowables.append(Paragraph(f"Stimulated at {csvObj.timeStamp_time12hr} on {csvObj.timeStamp_year}/{csvObj.timeStamp_month}/{csvObj.timeStamp_day} ", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Activity = {csvObj.activity}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Start Voltage = {csvObj.startVoltage}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"End Voltage = {csvObj.endVoltage}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Ramp Rate = {csvObj.rampRate}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Compliance Current = {csvObj.complianceCurrent}{csvObj.complianceCurrentUnits}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Platinum Voltage = {csvObj.platinumVoltage}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Copper Voltage = {csvObj.copperVoltage}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Run Folder Name = {csvObj.runFolderName}", 
                styles["BodyText"]))
            flowables.append(Paragraph(f"Comments = {csvObj.comments}", 
                styles["BodyText"]))

            if type(plots['probe A plot']) != str :
                imgDir = tempImageDir+f'{i}_tempFigA.jpg'
                plots['probe A plot'].savefig(imgDir,bbox_inches='tight',dpi=100)
                flowables.append(self.__getImage(imgDir, 400))
                plt.close(plots['probe A plot']) # do this to save memory

            if type(plots['probe B plot']) != str :
                imgDir = tempImageDir+f'{i}_tempFigB.jpg'
                plots['probe B plot'].savefig(imgDir,bbox_inches='tight',dpi=100)
                flowables.append(self.__getImage(imgDir, 400))
                plt.close(plots['probe B plot']) # do this to save memory

            if type(plots['probe C plot']) != str :
                imgDir = tempImageDir+f'{i}_tempFigC.jpg'
                plots['probe C plot'].savefig(imgDir,bbox_inches='tight',dpi=100)
                flowables.append(self.__getImage(imgDir, 400))
                plt.close(plots['probe C plot']) # do this to save memory

            flowables.append(Paragraph(f"-------------------------------------------------", 
                styles["BodyText"]))

        doc.build(flowables)

        shutil.rmtree(tempImageDir)

    def __getImage(self, path, width=1):
        """Makes resizing images to scale easy
        """
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        return Image(path, width=width, height=(width * aspect))

