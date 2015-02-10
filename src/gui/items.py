#!/usr/bin/python

""" Defines custom Items for the MonthTreeView. """

# authorship information
__authors__     = ['Philipp Metzner']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2014'
__license__     = 'GPL'

# maintanence information
__maintainer__  = 'Philipp Metzner'
__email__       = 'beth.aleph@yahoo.de'


from PyQt4 import QtGui 
from . import _FONT_ 

class CategoryItem(QtGui.QStandardItem):
    """ Represents a category item. """

    def __init__(self, text=""):
        super(CategoryItem, self).__init__(text)
        self.setEditable(False)
        self.setFont(_FONT_)

    def xmlTag(self):
        return 'category'
     

class DateItem(QtGui.QStandardItem):
    """ Represents a date item. """
    def __init__(self, text=""):
        super(DateItem, self).__init__(text)
        self.setEditable(False)


class EntryItem(QtGui.QStandardItem):
    """ Represents an entry item. """

    def __init__(self, text=""):
        super(EntryItem, self).__init__(text)

    def xmlTag(self):
        return 'entry'


class ExpenseItem(QtGui.QStandardItem):
    """ Represents an expense item. Accepts only float as text. """

    def __init__(self, text=""):
        super(ExpenseItem, self).__init__(text)
        if not len(text):
            text = '0'
        self.__value = float(text)

    def value(self):
        return self.__value 

    def setValue(self, value):
        self.__value = value 
        self.setText(str(value))
        

class SumItem(QtGui.QStandardItem):
    """ Represents a sum item. Set by the system. """

    def __init__(self, text=""):
        super(SumItem, self).__init__(text)
        if not len(text):
            text = '0'
        self.__value = float(text)
        self.setFont(_FONT_)
        self.setEditable(False)

    def increment(self, newValue, oldValue):
        self.__value = self.__value - oldValue + newValue 
        self.setText(str(self.__value))
        self.setEditable(False)

    def value(self):
        return self.__value 
