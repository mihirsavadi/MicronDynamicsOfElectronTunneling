# Mihir Savadi
# 23rd February 2021

from lib import *

class csvParser : 
    """This file contains functions to extract comments, title row, and columns from each csv, according to the format
        established in the project summary document.
    """

    def __init__(self, csvPath: str) :
        """Constructor that creates an object containing the comments, title, and columns of the csv in question

        Parameters
        ----------
        csvPath : str
            the path to the csv in question
        """

        # converting the input csv to a list of lines represented as strings, for the other private methods to use
        # 'lines' is a list where each entry represents a line in the csv
        file = open(csvPath, 'r')

        self._lines = [line for line in file]

        self.__lastCommentLineIdx = -1 # this is modified by self.__extractTitle() if comments are included

        file.close()

        # all the public fields
        self.path     = csvPath

        # these need to be excecuted in order here since methods have order dependency
        self.comments = self.__extractComments()
        self.title    = self.__extractTitle()
        self.columns  = self.__extractColumns()

    def __extractComments(self) -> str :
        """Returns string of comments in a csv

        Parameters
        ----------

        Returns
        -------
        str
            the comment in the csv in question
        """
        comments = ''

        # for case that comments were added

        if self._lines[0].replace(" ", "") == '---\n' :
        
            commentsStarted = False
            for i, line in enumerate(self._lines) :

                if line.replace(" ", "") == '---\n' and commentsStarted == False :
                    commentsStarted = True
                    continue
                    
                if commentsStarted == True :
                    if line.replace(" ", "") == '---\n' :
                        self.__lastCommentLineIdx = i
                        break
                    else:
                        comments += line

            if comments[-1] == '\n':
                comments = comments[:-1]

        else :

            comments = "No comments were added."

        return comments

    def __extractTitle(self) -> typing.List[str] :
        """Returns the Title of the CSV in question

        Returns
        -------
        str
            a list of strings, where each entry is the title of the respective column of the csv
            
        """
        
        return self._lines[self.__lastCommentLineIdx+1][:-1].split(',')

    def __extractColumns(self) -> typing.List[typing.List[float]] :
        """Returns the columns of data from the CSV in question

        Parameters
        ----------

        Returns
        -------
        List[List[float]]
            a list of lists, where each entry in each secondary list is a float. Each secondary list represents the
            respective column of the CSV
        """
        columns = []
        firstLine = self._lines[self.__lastCommentLineIdx+2][:-1].split(',')
        for i in range(0, len(self.title)) :
            columns.append([float(firstLine[i])])

        for line in self._lines[self.__lastCommentLineIdx+3:] :
            # skip blank lines
            if len(line.strip()) == 0:
                continue

            splitLine = line[:-1].split(',')
            for j in range(0, len(self.title)) :
                columns[j].append(float(splitLine[j]))

        return columns