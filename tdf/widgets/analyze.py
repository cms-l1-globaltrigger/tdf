# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#

"""TDF Memory Dump Analyzer
"""

import datetime
import time
import uuid
import math
import sys, os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from tdf.core import binutils
from tdf.core.settings import TDF
from tdf.core.images import *
from tdf.mp7.images import *

# -----------------------------------------------------------------------------
#  Constants.
# -----------------------------------------------------------------------------

PatternResyncGap = '505050bc'
"""Objects containing this pattern are considered to be masked by a gap."""

ObjectMapping = (
    'muon',
    'eg', 'tau', 'jet',
    'ett', 'ht', 'etm', 'htm',
    'extcond',
)
"""Ordered object mapping used to display the data columns."""

# -----------------------------------------------------------------------------
#  Helpers.
# -----------------------------------------------------------------------------

class Colors:
    """Palette of TANGO theme colors."""
    Red     = '#CC0000'
    Green   = '#4E9A06'
    Yellow  = '#C4A000'
    Blue    = '#3465A4'
    Magenta = '#75507B'
    Cyan    = '#06989A'
    Gray    = '#AAAAAA'

def decodeColumn(column):
    """Calculate object name and index from column index (eg. column 5 is Muon[4]).
    Returns tuple (name, index) on success or (None, 0) if column can not be
    matched to an object.
    """
    offset = 0
    for name in ObjectMapping:
        count = getattr(TDF, name.upper()).count
        if column < offset + count:
            return name, column - offset
        offset += count
    return None, 0

# -----------------------------------------------------------------------------
#  Factory functions.
# -----------------------------------------------------------------------------

def createIcon(name, category = 'actions'):
    """Factory function, creates a multi resolution gnome theme icon."""
    icon = QIcon()
    for size in 16, 24, 32, 64, 128:
        icon.addFile("/usr/share/icons/gnome/{size}x{size}/{category}/{name}.png".format(**locals()))
    return icon

# -----------------------------------------------------------------------------
#  Exceptions.
# -----------------------------------------------------------------------------

class FileReadError(RuntimeError): pass
class NoSuchFileError(RuntimeError): pass
class UnknownFileTypeError(RuntimeError): pass

def exceptionHandler(f):
    """Function decorator returning a exception handler function."""
    def _critical(title, *args):
        QMessageBox.critical(None, title, " ".join((str(arg) for arg in args)))
    def _exceptionHandler(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except FileReadError, exception:
            _critical("Read error", "<strong>Failed to read from file:</strong><br/>", exception)
        except NoSuchFileError, exception:
            _critical("No such file", "<strong>No such file to open:</strong><br/>", exception)
        except UnknownFileTypeError, exception:
            _critical("Unknown filetype", "<strong>Unknown file type:</strong><br/>", exception)
        except:
            raise
    return _exceptionHandler

# -----------------------------------------------------------------------------
#  Main window class.
# -----------------------------------------------------------------------------

class MainWindow(QMainWindow):

    AppTitle = "TDF Analyzer"
    AppVersion = __version__

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        # Setup main window.
        self.setWindowTitle(self.AppTitle)
        self.setWindowIcon(createIcon('utilities-system-monitor', 'apps'))
        self.resize(1000, 700)

        # Create menus, toolbars and status bar.
        self.createActions()
        self.createToolbars()
        self.createMenubar()
        self.createStatusbar()

        # Setup central MDI area.
        self.mdiArea = MdiArea(self)
        self.setCentralWidget(self.mdiArea)

        # Setup timed watchdog.
        timer = QTimer(self)
        timer.timeout.connect(self.onWatchdogEvent)
        timer.start(1000)

    def createActions(self):
        """Create actions used in menu bar and tool bars."""

        # Action for opening a new connections file.
        self.openAct = QAction("&Open...", self)
        self.openAct.setShortcut(QKeySequence.Open)
        self.openAct.setStatusTip("Open an existing file")
        self.openAct.setIcon(createIcon('document-open'))
        self.openAct.triggered.connect(self.onOpen)

        self.closeAct = QAction(self.tr("&Close"), self)
        self.closeAct.setShortcuts(QKeySequence.Close)
        self.closeAct.setStatusTip(self.tr("Close the current file"))
        self.closeAct.triggered.connect(self.onClose)

        # Action to quit the application.
        self.quitAct = QAction( "&Quit", self)
        self.quitAct.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q))
        self.quitAct.setStatusTip("Exit")
        self.quitAct.triggered.connect(self.onQuit)

        # Action for refreshing readable items.
        self.refreshAct = QAction("&Refresh", self)
        self.refreshAct.setShortcut(QKeySequence.Refresh)
        self.refreshAct.setStatusTip("Refresh by reading data from file")
        self.refreshAct.setIcon(createIcon('view-refresh'))
        self.refreshAct.setEnabled(False)
        self.refreshAct.triggered.connect(self.onRefresh)

        # Action for toggling status bar.
        self.statusbarAct = QAction("&Statusbar", self)
        self.statusbarAct.setCheckable(True)
        self.statusbarAct.setChecked(True)
        self.statusbarAct.setStatusTip("Show or hide the statusbar in the current window")
        self.statusbarAct.toggled.connect(self.onToggleStatusBar)

        # Actions to show online contents help.
        self.contentsAct = QAction("&Contents", self)
        self.contentsAct.setShortcut(QKeySequence(Qt.Key_F1))
        self.contentsAct.triggered.connect(self.onContents)

        # Actions to show about dialog.
        self.aboutAct = QAction("&About", self)
        self.aboutAct.triggered.connect(self.onAbout)

    def createToolbars(self):
        """Create tool bars and setup their behaviors (floating or static)."""

        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.addAction(self.openAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.refreshAct)

        # Create action for toggling the tool bar here.
        self.toolbarAct = self.toolbar.toggleViewAction() # Get predefined action from toolbar.
        self.toolbarAct.setStatusTip("Show or hide the toolbar in the current window")

    def createMenubar(self):
        """Create menu bar with entries."""

        # Menu entry for file actions.
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        # Menu entry for view actions.
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.refreshAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.toolbar.toggleViewAction())
        self.viewMenu.addAction(self.statusbarAct)

        # Menu entry for help actions.
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.contentsAct)
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.aboutAct)

    def createStatusbar(self):
        """Create status bar and content."""
        self.statusBar()
        self.statusBar().showMessage("Ready.")

    @pyqtSlot()
    def onOpen(self):
        """Select a connections file using a file open dialog."""
        filename = QFileDialog.getOpenFileName(self,
            "Open connection file", os.getcwd(), "Memory dumps (*.txt *.dat);;All files (*)")
        # Return if user did not select a file.
        if not filename:
            return
        self.loadDocument(filename)

    @pyqtSlot()
    def onClose(self):
        self.mdiArea.closeDocument()

    @pyqtSlot()
    def onQuit(self):
        self.close()

    @pyqtSlot()
    @exceptionHandler
    def onRefresh(self):
        document = self.mdiArea.currentDocument()
        if document:
            document.reload()

    @pyqtSlot()
    def onToggleStatusBar(self):
        """Toggles the visibility of the status bar."""
        self.statusBar().setVisible(self.statusbarAct.isChecked())

    @pyqtSlot()
    def onContents(self):
        url = 'http://gtmtca2.hephy.oeaw.ac.at/redmine/projects/tdf/wiki'
        QMessageBox.information(self, "Contents", QString("<p>Please refer to: <a href=\"%1\">%1</a></p>").arg(url))

    @pyqtSlot()
    def onAbout(self):
        QMessageBox.information(self, "About", QString(
            "<p><strong>%1</strong></p><p>Graphical TDF tool for viewing and "
            "analyzing memory images. This software is written in Python using "
            "the PyQt4 toolkit.</p>"
            "<p>Version %2</p>"
            "<p>Authors: Bernhard Arnold <a href=\"mailto:bernhard.arnold"
            "@cern.ch\">&lt;bernhard.arnold@cern.ch&gt;</a></p>").arg(self.AppTitle).arg(self.AppVersion)
        )

    @pyqtSlot()
    def onWatchdogEvent(self):
        """Perform some checks in a constant watchdog interval."""
        self.mdiArea.checkTimestamps()

    @exceptionHandler
    def loadDocument(self, filename):
        """Load document from filename."""
        filename = os.path.abspath(str(filename))
        if not os.path.isfile(filename):
            raise NoSuchFileError(filename)
        # Do not open files twice, just reload them.
        for index in range(self.mdiArea.count()):
            widget = self.mdiArea.widget(index)
            if widget:
                if filename == widget.filename:
                    self.mdiArea.setCurrentIndex(index)
                    widget.reload()
                    return
        # Else load from file and create new document tab.
        self.statusBar().showMessage("Loading...", 2500)
        document = Document(filename, self)
        index = self.mdiArea.addTab(document, createIcon('ascii', 'mimetypes'), os.path.basename(filename))
        self.mdiArea.setCurrentIndex(index)

        # After loading a conenction file, it is possible to refresh the current module.
        self.refreshAct.setEnabled(True)
        self.statusBar().showMessage("Successfully loaded file", 2500)

    def showMessage(self, message, timeout = 0):
        self.statusBar().showMessage(message, timeout)

# -----------------------------------------------------------------------------
#  MDI Area class.
# -----------------------------------------------------------------------------

class MdiArea(QTabWidget):

    def __init__(self, parent = None):
        super(MdiArea, self).__init__(parent)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)

        # Close document by clicking on the tab close button.
        self.tabCloseRequested.connect(self.closeDocument)

    def currentDocument(self):
        return self.widget(self.currentIndex())

    def documents(self):
        for index in range(self.count()):
            yield self.widget(index)

    @pyqtSlot()
    def closeDocument(self):
        """Close an document by index or current active document.
        Provided for convenience.
        """
        index = self.currentIndex()
        # Finally remove tab by index.
        self.removeTab(index)
        return True

    @pyqtSlot()
    def checkTimestamps(self):
        for document in self.documents():
            document.checkTimestamp()

# -----------------------------------------------------------------------------
#  Document class.
# -----------------------------------------------------------------------------

class Document(QWidget):
    """Document widget displaying a data table view and a object preview box."""

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        self.filename = os.path.abspath(filename)

        self.timestamp = os.path.getmtime(self.filename)
        self.tableView = self.createTableView()
        self.previewWidget = self.createPreviewWidget()
        self.warningLabel = self.createWarningLabel()
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tableView)
        splitter.addWidget(self.previewWidget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout = QVBoxLayout()
        layout.addWidget(self.warningLabel, 0)
        layout.addWidget(splitter, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.reloadCounter = 0
        # Load the file.
        QCoreApplication.instance().processEvents()
        self.reload()

    def createTableView(self):
        """Create the data table view."""
        tableView = QTableView(self)
        # Make only single cells selectable.
        tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        # Hide the default grid.
        tableView.setShowGrid(False)
        # Disable sorting.
        tableView.setSortingEnabled(False)
        # Set a monospace font for cell content (as hex values are displayed).
        tableView.setFont(QFont("Monospace", 10))
        # Prevent resizing of the horizontal and vertical headers.
        horizontalHeader = tableView.horizontalHeader()
        horizontalHeader.setResizeMode(QHeaderView.Fixed)
        horizontalHeader.setStretchLastSection(True)
        verticalHeader = tableView.verticalHeader()
        verticalHeader.setResizeMode(QHeaderView.Fixed)
        verticalHeader.setDefaultSectionSize(20)
        return tableView

    def createPreviewWidget(self):
        textEdit = QTextEdit(self)
        textEdit.setReadOnly(True)
        textEdit.setAutoFillBackground(True)
        return textEdit

    def createWarningLabel(self):
        label = QLabel(self)
        label.setObjectName("warningLabel")
        label.setStyleSheet(
            "padding: 16px;"
            "border: 1px solid #ce8720;"
            "background-color: #f9ac3a;"
        )
        label.hide()
        return label

    def reload(self):
        """Reload data from file."""
        self.reloadCounter += 1
        image = self.loadImage(self.filename)
        model = DataTableModel(image, self)
        self.tableView.setModel(model)
        # Make sure to not resize for 3564 lines but only for the first, the
        # row-count must be overwritten.
        # Replacing the class method by a temporary fake function.
        if self.reloadCounter <= 1:
            rowCount = model.rowCount
            def fakeRowCount(parent): return 1
            model.rowCount = fakeRowCount # replace
            self.tableView.resizeColumnsToContents()
            model.rowCount = rowCount # restore
        self.tableView.update()
        # Attach signals to new assigned model instance.
        self.tableView.selectionModel().currentChanged.connect(self.updatePreview)
        self.clearWarning()

    def loadImage(self, filename):
        """Load image from different file types."""
        image = SimSpyMemoryImage()
        # Set of read functions to try
        for loader in (image.read, image.read_testvector):
            try:
                with open(self.filename, 'rb') as fs:
                    loader(fs)
                    # Update filestamp from loaded file.
                    self.timestamp = os.path.getmtime(filename)
                    return image
            except ValueError:
                pass # Ignore file format error and continue with next read method.
            except IOError:
                raise FileReadError(filename)
        # If no read attempt succeeded then bil out with an exception.
        raise UnknownFileTypeError(filename)

    def updatePreview(self, current, previous):
        """Update the object preview."""
        # Get the objects raw value.
        value = current.data(Qt.UserRole).toInt()[0]
        bx = current.row()
        name, index = decodeColumn(current.column())
        # Bail out if no such object.
        if not name:
            self.previewWidget.clear()
            return
        # Get object settings instance.
        objectSettings = getattr(TDF, name.upper())
        # Hex representation of object.
        hexValue = objectSettings.hexstr(value)
        # Calculate full object name.
        fullName = '{0}[{1}]'.format(name, index) if objectSettings.count > 1 else name

        text = [
            "<p><strong>Object: {fullName}</strong></p>",
            "<p><strong>BX: {bx}</strong></p>",
            "<p><strong>Value:</strong> 0x{hexValue}</p>",
            "<hr/>",
        ]

        table = []
        for key, value in objectSettings.decode(value).items():
            value = int(value)
            scalar = ''
            # Quick and dirty scaling...
            if key in ('et', 'pt'):
                scalar = '{0:.1f} GeV'.format(value * .5)
            table.append("".join([
                "<tr>",
                "<td><strong>{key}</strong></td>",
                "<td>{value}</td>",
                "<td>0x{value:x}</td>",
                "<td>{scalar}</td>",
                "</tr>",
            ]).format(**locals()))
        if table:
            text.append("<table width=\"100%\">")
            text.extend([
                "<tr style=\"background-color: #eee;\">",
                "<th>Attribute</th>",
                "<th>Dec</th>",
                "<th>Hex</th>",
                "<th>Scalar</th>",
                "</tr>",
            ])
            text.extend(table)
            text.append("</table>")
        self.previewWidget.setHtml('\n'.join(text).format(**locals()))

    def clearWarning(self):
        """Clear the warning badge located at the top of the document."""
        self.warningLabel.clear()
        self.warningLabel.hide()

    def showWarning(self, message):
        """Show a warning badge displaying a message located at the top of the document."""
        self.warningLabel.setText(message)
        self.warningLabel.show()

    def checkTimestamp(self):
        timestamp = os.path.getmtime(self.filename)
        if timestamp > self.timestamp:
            self.showWarning("<strong>The file {self.filename} changed on disk.</strong> Reload (hit F5) to see the changes.".format(**locals()))
        else:
            self.clearWarning()

class DataTableModel(QAbstractTableModel):

    def __init__(self, image, parent = None, *args):
        super(DataTableModel, self).__init__(parent, *args)
        self.data = {}
        # So ugly...
        self.data['muon'] = image.muons()
        self.data['eg'] = image.egs()
        self.data['tau'] = image.taus()
        self.data['jet'] = image.jets()
        self.data['ett'] = [image.ett()]
        self.data['ht'] = [image.ht()]
        self.data['etm'] = [image.etm()]
        self.data['htm'] = [image.htm()]
        self.data['extcond'] = [image.extconds()]
        self.image = image
        self.headerdata = []
        while True:
            name, index = decodeColumn(len(self.headerdata))
            if not name: break
            self.headerdata.append("{0}[{1}]".format(name, index) if getattr(TDF, name.upper()).count > 1 else name)

    def rowCount(self, parent):
        return TDF.ORBIT_LENGTH

    def columnCount(self, parent):
        return len(self.headerdata)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        name, idx = decodeColumn(index.column())
        if role == Qt.UserRole:
            if name:
                obj = getattr(TDF, name.upper())
                return QVariant(self.data.get(name)[idx][index.row()])
        elif role == Qt.DisplayRole:
            if name:
                obj = getattr(TDF, name.upper())
                return QVariant(obj.hexstr(self.data.get(name)[idx][index.row()]))
        elif role == Qt.ForegroundRole:
            if name:
                obj = getattr(TDF, name.upper())
                if self.data.get(name)[idx][index.row()] == 0:
                    return QVariant(QBrush(QColor(Colors.Gray)))
                if PatternResyncGap in obj.hexstr(self.data.get(name)[idx][index.row()]):
                    return QVariant(QBrush(QColor(Colors.Magenta)))
        return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(col))
        return QVariant()
