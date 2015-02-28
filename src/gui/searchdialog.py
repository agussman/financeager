#!/usr/bin/python

""" Defines the SearchDialog Popup for the Financeager application. """

# define authorship information
__authors__     = ['Philipp Metzner']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2014'
__license__     = 'GPL'

# maintanence information
__maintainer__  = 'Philipp Metzner'
__email__       = 'beth.aleph@yahoo.de'


from PyQt4.QtGui import QDialog, QStandardItem, QStandardItemModel,\
    QHeaderView, QDialogButtonBox 
from PyQt4.QtCore import Qt, QDate 
from items import ResultItem
from . import loadUi

class SearchDialog(QDialog):
    """
    SearchDialog class for the Financeager application.
    """

    def __init__(self, parent=None):
        """
        Loads the ui layout file. 
        Populates the model and does some layout adjustments. 
        
        :param      parent | FinanceagerWindow 
        """
        super(SearchDialog, self).__init__(parent)
        loadUi(__file__, self)

        self.__model = QStandardItemModel(self.tableView)
        # sorts model according to Item.data, Item.text 
        self.__model.setSortRole(Qt.UserRole + 1) 
        self.__model.setHorizontalHeaderLabels(
                ['Name', 'Value', 'Date', 'Category'])
        self.tableView.setModel(self.__model)
        self.__sortOrder = 1 #Descending order

        self.tableView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.tableView.adjustSize()
        self.setFixedSize(self.size())
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(False)
        # CONNECTIONS
        self.findButton.clicked.connect(self.displaySearchResult)
        self.tableView.horizontalHeader().sectionClicked.connect(self.sortByColumn)

    def keyPressEvent(self, event):
        """
        Reimplementation. 
        Avoids triggering the OK button when pressing Enter. Considered a
        common reaction when searching for stuff.
        """
        if event.key() == Qt.Key_Enter:
            return 
        super(SearchDialog, self).keyPressEvent(event)

    def displaySearchResult(self):
        """
        Searches for the pattern given by the user in all months of the current
        year. If specified, only the respective expenditures or receipts are
        scanned. 
        If a match is found, new items are cloned and appended to the table.
        """
        pattern = unicode(self.lineEdit.text())
        if not len(pattern):
            self.__model.setItem(0, 0, ResultItem('No pattern specified.'))
            return 
        self.setWindowTitle('Search for \'%s\'' % pattern)
        pattern = pattern.upper()
        monthsTabWidget = self.parent().monthsTabWidget 
        self.__model.clear()
        self.__model.setHorizontalHeaderLabels(
                ['Name', 'Value', 'Date', 'Category'])
        for m in range(12):
            if self.expendituresButton.isChecked():
                modelList = [monthsTabWidget.widget(m).expendituresModel()]
            elif self.receiptsButton.isChecked():
                modelList = [monthsTabWidget.widget(m).receiptsModel()]
            elif self.bothButton.isChecked():
                modelList = [monthsTabWidget.widget(m).expendituresModel(),
                    monthsTabWidget.widget(m).receiptsModel()]
            for model in modelList:
                for r in range(model.rowCount()):
                    category = model.item(r)
                    for e in range(category.rowCount()):
                        entry = category.child(e)
                        name = unicode(entry.text())
                        if name.upper().find(pattern) > -1:
                            value = category.child(e, 1).value()
                            date = category.child(e, 2).data()
                            self.__model.appendRow([ResultItem(name),
                                ResultItem(value), ResultItem(date),
                                ResultItem(category.text())])
        if not self.__model.hasChildren():
            self.__model.setItem(0, 0, ResultItem('No match found.'))

    def sortByColumn(self, col):
        """
        Called when a section of the horizontalHeader of the model is clicked.
        Toggles the sortOrder from descending to ascending and vice versa. 
        Finally the respective column is sorted. 

        :param      col | int 
        """
        self.__sortOrder = not self.__sortOrder  
        self.__model.sort(col, self.__sortOrder)
