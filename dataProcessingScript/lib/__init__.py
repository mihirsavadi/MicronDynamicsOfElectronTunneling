# Mihir Savadi
# 23rd February 2021

import numpy as np
import time
import matplotlib.pyplot as plt
import os
import shutil
import glob
import typing
from datetime import datetime
from collections import OrderedDict

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils