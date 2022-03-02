# Micron Dynamics of Electron Tunneling - Repository and Data Processing

This repository contains the database and data processing script that we used in our Senior Design Project, which
involves stimulating cells in novel ReRAM arrays to induce thermal energy transfer and observe associated electron
tunnelling and other quantum behavior.

The Summary Document detailing our entire project is available in './summary_paper/seniordesign_micronElectronTunneling_summary.pdf'

Please refer to section 2.4 of the Project Summary document for the data entry protocol that must be strictly followed.
The same summary document also details various nomenclature as well as the grid coordinate system that is used to
identify individual cells.

To run this script, assuming you are in this directory simply run 'python dataProcessingScript/\_\_main\_\_.py'

All the python modules required to run this script is located at 'dataProcessingScript/lib/\_\_init\_\_.py'

All our most up to date data is located at './data/'

All our script outputs are directed into './testDump/'

Note that the modules listed in 'dataProcessingScript/lib/\_\_init\_\_.py' are required to run the script. Most of them are stock modules, for the rest, simply run 'pip install numpy matplotlib reportlab'.