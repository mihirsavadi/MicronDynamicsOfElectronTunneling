# Micron Dynamics of Electron Tunneling - Central Repository

This repository contains the database and data processing script that we used in our Senior Design Project, which
involves stimulating cells in novel ReRAM arrays to induce thermal energy transfer and observe associated electron
tunnelling and other quantum behavior.

The Summary Document detailing our entire project is available in
'./summary_paper/seniordesign_micronElectronTunneling_summary.pdf'

Please refer to section 2.4 of the Project Summary document for the data entry protocol that must be strictly followed.
The same summary document also details various nomenclature as well as the grid coordinate system that is used to
identify individual cells.

To run this script, assuming you are in this directory simply run 'python dataProcessingScript/\_\_main\_\_.py'

All our most up to date data is located at './data/'

All our script outputs are directed into './testDump/'

Note that the modules listed in 'dataProcessingScript/lib/\_\_init\_\_.py' are required to run the script. Most of them
are stock modules, for the rest, simply run 'pip install numpy matplotlib reportlab'.

There is an additional script in './keithley/' that automates the collation of logged data from the keithley machine
into the proprietary format described in the summary document. 

The python modules required to run all the scripts in this repository are as as follows:  
    - matplotlib  
    - reportlab  
    - numpy  
    - argparse  
    - yaml  
    - pandas  
    - pytz  
    - tqdm  

During the year long course of this project we maintained an internal google drive which contained all of our
deliverables and other course specific items, as well as footage etc. Because a lot of these files are too large for
github, they are not included in this github repository. Instead, they can be found 
[at this link](https://drive.google.com/file/d/1UdM93mss8CJoWbe4B_h3I2H1SIwsKGog/view?usp=sharing).