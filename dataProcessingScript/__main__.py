# Mihir Savadi
# 23rd February 2021

from lib import *

from utils.csvParser import csvParser
from utils.csvItem import csvItem
from utils.base import dataBaseCollator
from pdfGenerator.pdfgen import pdfGen

if __name__ == "__main__":

    now = datetime.now()
    timeFormat = "%Y-%b-%d-%I%M%p_%Ss"

    # simply instantiate a dataBaseCollator object and the report files will be created
    db = dataBaseCollator('./data/', f'./testDump/report_{now.strftime(timeFormat)}/')