# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#

"""TDF Control GUI
A main window containing a central tab widget for handling multiple devices.
Each device tab consists of a tree widget holding the devices item tree. A
delegate class to edit writable items controls input.
"""

import sys, os
import time
import datetime
import uuid

from PyQt4 import QtCore, QtGui
import uhal

from tdf.core import binutils
from tdf.core.translator import ItemTranslator
from tdf.core.settings import TDF
from tdf.core.cfgreader import ConfigFileReader

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

# -----------------------------------------------------------------------------
#  Factory functions.
# -----------------------------------------------------------------------------

def createIcon(name, category = 'actions'):
    """Factory function, creates a multi resolution gnome theme icon."""
    icon = QtGui.QIcon()
    for size in 16, 24, 32, 64, 128:
        icon.addFile("/usr/share/icons/gnome/{size}x{size}/{category}/{name}.png".format(**locals()))
    return icon

# -----------------------------------------------------------------------------
#  Exception handler functions.
# -----------------------------------------------------------------------------

def isControlHubException(e):
    """Returns true if the exception *seems* to be control hub related exception."""
    return "ControlHub error" in e.what # No reliable way to disambiguate.

def handleException(e):
    """Exception handler raising proper message dialogs for different exception
    types. Attribute *e* is the cached exception object.
    """
    if type(e) is uhal.exception:
        if isControlHubException(e):
            QtGui.QMessageBox.critical(None, "ControlHub Error", str(e.what))
        else:
            QtGui.QMessageBox.critical(None, "Header/Read Error", str(e.what))
    elif type(e) is uhal.BitsSetWhichAreForbiddenByBitMask:
        QtGui.QMessageBox.critical(None, "Input Error", str(e.what))
    else:
        QtGui.QMessageBox.critical(None, "Unknown Error", str(e.what))

# -----------------------------------------------------------------------------
#  Custom uHAL node translator.
# -----------------------------------------------------------------------------

class OptItemTranslator(ItemTranslator):
    """Optimized translator for Control GUI. Returns an empty string on default."""

    def tr_default(self, node, values):
        """Default translator returns empty string (for GUI)"""
        return ''

# -----------------------------------------------------------------------------
#  Item node classes.
# -----------------------------------------------------------------------------

class AbstractNode(object):
    """Generic abstract node item to be used in conjunction with an item model."""

    def __init__(self, parent = None):
        self._children = []
        self._parent = parent

        if parent is not None:
            parent.addChild(self)

    def addChild(self, child):
        self._children.append(child)

    def child(self, row):
        return self._children[row]

    def children(self):
        return self._children

    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

class ItemNode(AbstractNode):
    """Custom uHAL node item to be ued in conjunction with an item model."""

    PermissionDict = {
        uhal.NodePermission.READ      : 'r',
        uhal.NodePermission.WRITE     : 'w',
        uhal.NodePermission.READWRITE : 'rw',
    }

    Translator = OptItemTranslator()
    """Static translator instance reading configuration from file only once."""

    # Node states.
    UnknownState = 0x0
    ReadState    = 0x1
    ErrorState   = 0x2

    def __init__(self, uhalNode, parent = None):
        """Attribute *node* is a uHAL item node."""
        super(ItemNode, self).__init__(parent)
        self._uhalNode = uhalNode
        self.setState(ItemNode.UnknownState)
        self.setCache("", "")

    def setState(self, state):
        """Set node's current state. Provided for convenience."""
        self._state = state

    def setCache(self, value, translation):
        """Set node's value and translation cache. Provided for convenience."""
        self._valueCache = value
        self._translationCache = translation

    def uhalNode(self):
        """Returns the uHAL item node."""
        return self._uhalNode

    def state(self):
        """Returns the state of the node, either *UnknownState*, *ReadState* or
        *ErrorState*."""
        return self._state

    def id(self):
        """Returns the item's ID."""
        return self.uhalNode().getId()

    def address(self):
        """Returns the item's address."""
        return self.tr_hex(self.uhalNode().getAddress())

    def mask(self):
        """Returns the item's mask."""
        return self.tr_hex(self.uhalNode().getMask())

    def permission(self):
        """Returns the item's access permission, either "r", "w" or "rw"."""
        return self.PermissionDict[self.uhalNode().getPermission()]

    def value(self):
        """Returns cached item's value as string. If item was not read an empty
        string is returned."""
        return self._valueCache

    def translation(self):
        """Returns cached transalted item's value as string. If item was not
        read or there is not translation available an empty string is returned."""
        return self._translationCache

    def description(self):
        """Returns item's description."""
        return self.uhalNode().getDescription()

    def isMemory(self):
        """Returns True if item is a memory."""
        return self.uhalNode().getSize() > 1

    def isUserWritable(self):
        """Returns true for writable items except for memories."""
        if self.uhalNode().getPermission() is not uhal.NodePermission.READ:
            if not self.isMemory():
                if not self.childCount():
                    return True
        return False

    def type(self):
        """Returns optional type defined in parameters section."""
        parameters = self.uhalNode().getParameters()
        if 'type' in parameters:
            return parameters['type']
        return None

    def read(self):
        """Read item value from hardware."""
        node = self._uhalNode
        params = node.getParameters()

        if node.getPermission() == uhal.NodePermission.WRITE:
            self.setCache("n/a", "(event/pulse item)")
            return

        try:
            if self.isMemory():
                result = node.readBlock(node.getSize())
                node.getClient().dispatch()
                values = result.value()
                self.setCache(
                    self.tr_hex(values[0]),
                    self.Translator.translate(node, values) or '{0}x{1} memory'.format(node.getSize(), TDF.DATA_WIDTH)
                )
            else:
                result = node.read()
                node.getClient().dispatch()
                value = result.value()
                self.setCache(self.tr_hex(value), self.Translator.translate(node, value))
            # On success, set state to read.
            self.setState(ItemNode.ReadState)
        except uhal.exception, e:
            print "*** read error, device={0}, id={1}".format(node.getClient(), node.getPath())
            if isControlHubException(e):
                self.setState(ItemNode.UnknownState)
                self.setCache("", "")
            else:
                self.setState(ItemNode.ErrorState)
                self.setCache("n/a", "")
            raise e

    def write(self, value):
        """Write value to hardware."""
        self.uhalNode().write(value)
        self.uhalNode().getClient().dispatch()

    def tr_hex(self, value):
        return ''.join(('0x', format(value, '08x')))

# -----------------------------------------------------------------------------
#  Delegate classes.
# -----------------------------------------------------------------------------

class ValueDelegate(QtGui.QItemDelegate):
    """Item delegate for editing value column entries (for writable items)."""

    # Signal emitted on refresh tree request.
    refresh = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super(ValueDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QtGui.QLineEdit(parent)
        editor.setFont(QtGui.QFont('Monospace'))
        editor.setMaxLength(10)
        editor.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        return editor

    def setEditorData(self, editor, index):
        """Set delegate editor to current value."""
        if index.isValid():
            try:
                value = int(str(index.data().toString()), 16)
                editor.setText('{0:x}'.format(value))
            except ValueError:
                editor.setText('0')

    def setModelData(self, editor, model, index):
        """Issue a write dispatch with value from editor, then requires a tree
        refresh by emitting the *refresh* signal.
        """
        value = int(str(editor.text()), 16)
        if index.isValid():
            # Fetch node reference behind displayed value.
            try:
                index.internalPointer().write(value)
            except uhal.BitsSetWhichAreForbiddenByBitMask, e:
                handleException(e)
            except uhal.exception, e:
                handleException(e)
            else:
                self.refresh.emit()

# -----------------------------------------------------------------------------
#  Model classes.
# -----------------------------------------------------------------------------

class ItemsModel(QtCore.QAbstractItemModel):
    """Custom model for uHAL item tree view."""

    IdColumn          = 0
    AddressColumn     = 1
    MaskColumn        = 2
    PermissionColumn  = 3
    ValueColumn       = 4
    TranslationColumn = 5
    DescriptionColumn = 6

    ColumnDict = {
        IdColumn          : "ID",
        AddressColumn     : "Address",
        MaskColumn        : "Mask",
        PermissionColumn  : "r/w",
        ValueColumn       : "Value",
        TranslationColumn : "Translation",
        DescriptionColumn : "Description",
    }

    def __init__(self, root, parent = None):
        super(ItemsModel, self).__init__(parent)
        self._rootNode = root
        self.monoFont = QtGui.QFont("Monospace")

    def rowCount(self, parent = QtCore.QModelIndex()):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        return parentNode.childCount()

    def columnCount(self, parent = QtCore.QModelIndex()):
        return len(self.ColumnDict)

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            if index.column() == self.IdColumn:
                return node.id()
            if index.column() == self.AddressColumn:
                return node.address()
            if index.column() == self.MaskColumn:
                return node.mask()
            if index.column() == self.PermissionColumn:
                return node.permission()
            if index.column() == self.ValueColumn:
                return node.value()
            if index.column() == self.TranslationColumn:
                return node.translation()
            if index.column() == self.DescriptionColumn:
                return node.description()

        if role == QtCore.Qt.FontRole:
            if index.column() == self.AddressColumn:
                return self.monoFont
            if index.column() == self.MaskColumn:
                return self.monoFont
            if index.column() == self.ValueColumn:
                return self.monoFont
            if index.column() == self.TranslationColumn:
                return self.monoFont

        if role == QtCore.Qt.TextAlignmentRole:
            if index.column() == self.AddressColumn:
                return QtCore.Qt.AlignRight
            if index.column() == self.MaskColumn:
                return QtCore.Qt.AlignRight
            if index.column() == self.ValueColumn:
                return QtCore.Qt.AlignRight
            if index.column() == self.TranslationColumn:
                return QtCore.Qt.AlignLeft

        if role == QtCore.Qt.ForegroundRole:
            # On error cast full row into red color.
            if node.state() == ItemNode.ErrorState:
                return QtGui.QBrush(QtGui.QColor(Colors.Red))
            if index.column() == self.AddressColumn:
                return QtGui.QBrush(QtGui.QColor(Colors.Green))
            if index.column() == self.MaskColumn:
                return QtGui.QBrush(QtGui.QColor(Colors.Green))
            if index.column() == self.PermissionColumn:
                return QtGui.QBrush(QtGui.QColor(Colors.Green))
            if index.column() == self.ValueColumn:
                return QtGui.QBrush(QtGui.QColor(Colors.Blue))
            if index.column() == self.TranslationColumn:
                return QtGui.QBrush(QtGui.QColor(Colors.Magenta))
            if index.column() == self.DescriptionColumn:
                return QtGui.QBrush(QtGui.QColor(Colors.Gray))

        if role == QtCore.Qt.ToolTipRole:
            if index.column() == self.TranslationColumn:
                return "type: {0}".format(node.type())

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.ColumnDict[section]

    def flags(self, index):
        if index.column() == self.ValueColumn:
            # Make only writable registers (not memories) editable.
            if index.internalPointer().isUserWritable():
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def parent(self, index):
        node = index.internalPointer()
        parentNode = node.parent()

        if parentNode == self._rootNode:
            return QtCore.QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent = QtCore.QModelIndex()):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)

        return QtCore.QModelIndex()

# -----------------------------------------------------------------------------
#  View classes.
# -----------------------------------------------------------------------------

class TreeView(QtGui.QTreeView):
    """Custom uHAL item tree view."""

    updateMessage = QtCore.pyqtSignal(str, int)

    def __init__(self, device, parent = None):
        super(TreeView, self).__init__(parent)
        self.device = device
        valueDelegate = ValueDelegate()
        valueDelegate.refresh.connect(self.refresh)
        self.setItemDelegate(valueDelegate)

    def resizeColumns(self):
        for column in (
            ItemsModel.AddressColumn,
            ItemsModel.MaskColumn,
            ItemsModel.PermissionColumn,
            ItemsModel.ValueColumn,
        ): self.resizeColumnToContents(column)
        self.setColumnWidth(ItemsModel.IdColumn, 256)
        self.setColumnWidth(ItemsModel.TranslationColumn, 160)

    def reverseExpand(self, index):
        """Expand recursively all parents of child *index*."""
        if index.isValid():
            if index.parent() and index.parent().isValid():
                self.expand(index.parent())
                self.reverseExpand(index.parent())

    def selectIndex(self, index):
        if index and index.isValid():
            self.selectionModel().clear()
            self.selectionModel().select(index, QtGui.QItemSelectionModel.SelectCurrent | QtGui.QItemSelectionModel.Rows)
            self.reverseExpand(index)
            self.scrollTo(index)

    def getRootNodes(self, node):
        """Unclean way to fetch root nodes by name (no convenient way provided by uHAL?)."""
        nodes = []
        for name in node.getNodes():
            if '.' not in name:
                nodes.append(node.getNode(name))
        nodes.sort(key = lambda node: '{0:08x}{1:08x}{2}'.format(node.getAddress(), node.getMask(), node.getId()))
        return nodes

    def populate(self, node, parent):
        """Traverse items and populate tree recursively."""

        n = ItemNode(node, parent)

        for child in self.getRootNodes(node):
            self.populate(child, n)

    def refresh(self):
        try:
            for child in self.rootNode.children():
                self.refreshRecursive(child)
        except uhal.exception, e:
            handleException(e)
            if isControlHubException(e):
                return
        # Emit signal to update the value and translation columns.
        self.model.dataChanged.emit(
            self.model.index(0, ItemsModel.ValueColumn),
            self.model.index(self.model.rowCount() - 1, ItemsModel.TranslationColumn)
        )

    def refreshRecursive(self, parent):
        try:
            parent.read()
        except uhal.exception, e:
            if isControlHubException(e):
                raise e
        for child in parent.children():
            self.refreshRecursive(child)

    def configure(self, filename):
        """Configure device from file."""
        valid_names = self.device.getNodes()
        # Minimum is not displaying label text... odd
        progress = QtGui.QProgressDialog("Loading configuration file...", "Abort", 0, 0, self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setWindowTitle(QtCore.QString("Configuring device %1...").arg(self.device.getClient().id()))
        progress.setWindowIcon(createIcon('system-run'))
        progress.resize(500, progress.height())
        progress.show()
        items = ConfigFileReader(filename).items()
        progress.setMaximum(len(items))
        try:
            # Check configuration file compatibility.
            for name, value in items:
                if name not in valid_names:
                    raise RuntimeError("Failed to configure from file {filename}\n"
                        "No such item \"{name}\"".format(**locals()))

            for i in range(len(items)):
                name, value = items[i]
                progress.setValue(i)
                progress.setLabelText(QtCore.QString("writing node %1 ...").arg(name))
                if len(items) < 100:
                    time.sleep(.040) # GUI users have so much time watching at the beautiful widgets ;)
                if len(items) < 250:
                    time.sleep(.025)
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                node = self.device.getNode(name)
                node.write(value)
                self.device.dispatch()
        except uhal.exception, e:
            progress.close()
            handleException(e)
            if isControlHubException(e):
                return
        except RuntimeError, message:
            progress.close()
            QtGui.QMessageBox.critical(None, "Configuration error", "Failed to configure from file: {message}".format(**locals()))
        except:
            progress.close()
            raise # Re-raise last exception
        finally:
            progress.close()
        self.refresh() # On success refresh

# -----------------------------------------------------------------------------
#  Multi device area class.
# -----------------------------------------------------------------------------

class DeviceTabWidget(QtGui.QTabWidget):

    updateMessage = QtCore.pyqtSignal(str, int)

    def __init__(self, parent = None):
        super(DeviceTabWidget, self).__init__(parent)
        self.setDocumentMode(True)

    def addDevice(self, device):
        widget = QtGui.QWidget(self)

        # Setup the tree view and create a model.
        widget.treeView = TreeView(device, widget)
        widget.treeView.rootNode = ItemNode(None) # top
        for node in widget.treeView.getRootNodes(device):
            widget.treeView.populate(node, widget.treeView.rootNode)
        widget.treeView.model = ItemsModel(widget.treeView.rootNode)
        widget.treeView.setModel(widget.treeView.model)
        widget.treeView.updateMessage.connect(self.showMessage)
        widget.treeView.refresh()
        widget.treeView.resizeColumns()

        # Setup find widget, pass the model to be searched.
        widget.findWidget = FindWidget(widget.treeView.model, widget)
        widget.findWidget.hide()
        widget.findWidget.currentMatch.connect(widget.treeView.selectIndex)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(widget.treeView)
        layout.addWidget(widget.findWidget)
        widget.setLayout(layout)

        self.addTab(widget, device.getClient().__str__())

    def showMessage(self, message, timeout):
        self.updateMessage.emit(message, timeout)

# -----------------------------------------------------------------------------
#  Embeded search widget class.
# -----------------------------------------------------------------------------

class Matches(object):
    """Matches container for FindWidget results."""
    def __init__(self, query = "", caseSensitive = False, matches = []):
        self.setMatches(query, caseSensitive, matches)
    def setMatches(self, query, caseSensitive, matches):
        self.query = query
        self.caseSensitive = caseSensitive
        self.matches = matches
        self.index = -1
    def nextMatch(self):
        if not self.count():
            return None
        self.index += 1
        if self.index >= self.count():
            self.index = 0
        return self.matches[self.index]
    def previousMatch(self):
        if not self.count():
            return None
        self.index -= 1
        if self.index < 0:
            self.index = self.count() - 1
        return self.matches[self.index]
    def count(self):
        return len(self.matches)

class FindWidget(QtGui.QWidget):

    currentMatch = QtCore.pyqtSignal(QtCore.QModelIndex)

    def __init__(self, model, parent = None):
        super(FindWidget, self).__init__(parent)
        self.model = model
        self.matches = Matches()
        self.selection = QtCore.QModelIndex()

        self.closeButton = QtGui.QPushButton(self)
        self.closeButton.clicked.connect(self.onHide)
        self.closeButton.setIcon(createIcon('window-close'))

        self.queryLineEdit = QtGui.QLineEdit(self)
        self.queryLineEdit.setMinimumWidth(300)
        self.queryLineEdit.textChanged.connect(self.onQueryChanged)
        self.queryLineEdit.returnPressed.connect(self.onNext)
        maxHeight = self.queryLineEdit.size().height()

        self.closeButton.setMaximumSize(maxHeight, maxHeight) # square

        self.clearButton = QtGui.QPushButton(self)
        self.clearButton.clicked.connect(self.onClear)
        self.clearButton.setMaximumSize(maxHeight, maxHeight) # square
        self.clearButton.setIcon(createIcon('edit-clear'))

        self.nextButton = QtGui.QPushButton("&Next", self)
        self.nextButton.setShortcut(QtGui.QKeySequence.FindNext)
        self.nextButton.clicked.connect(self.onNext)
        self.nextButton.setMaximumHeight(maxHeight)
        self.nextButton.setIcon(createIcon('go-next'))

        self.previousButton = QtGui.QPushButton("P&revious", self)
        self.previousButton.setShortcut(QtGui.QKeySequence.FindPrevious)
        self.previousButton.clicked.connect(self.onPrevious)
        self.previousButton.setMaximumHeight(maxHeight)
        self.previousButton.setIcon(createIcon('go-previous'))

        self.matchCaseCheckBox = QtGui.QCheckBox("&Match case", self)
        self.matchCaseCheckBox.toggled.connect(self.updateMatches)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.closeButton)
        layout.addWidget(self.queryLineEdit)
        layout.addWidget(self.clearButton)
        layout.addWidget(self.nextButton)
        layout.addWidget(self.previousButton)
        layout.addWidget(self.matchCaseCheckBox)
        layout.addStretch()
        self.setLayout(layout)

        # Update buttons enabled states accourding to query content (empty).
        self.updateButtons()

    def setSelection(self, index):
        self.selection = index

    def onHide(self):
        self.hide()

    def onShow(self):
        self.show()
        self.queryLineEdit.setFocus()
        self.queryLineEdit.selectAll()

    def onClear(self):
        self.queryLineEdit.clear()
        self.queryLineEdit.setFocus()

    def onQueryChanged(self):
        self.updateButtons()

    def onNext(self):
        self.updateMatches()
        self.currentMatch.emit(self.matches.nextMatch())

    def onPrevious(self):
        self.updateMatches()
        self.currentMatch.emit(self.matches.previousMatch())

    def updateButtons(self):
        enabled = self.queryLineEdit.text().length()
        self.clearButton.setEnabled(enabled)
        self.nextButton.setEnabled(enabled)
        self.previousButton.setEnabled(enabled)

    def updateMatches(self):
        query = self.queryLineEdit.text()
        caseSensitive = self.matchCaseCheckBox.isChecked()
        modelIndex = self.model.index(0, 0)
        matchFlags = QtCore.Qt.MatchContains | QtCore.Qt.MatchWrap | QtCore.Qt.MatchRecursive
        if self.matchCaseCheckBox.isChecked():
            matchFlags |= QtCore.Qt.MatchCaseSensitive
        if (self.matches.query != query) or (self.matches.caseSensitive != caseSensitive):
            if self.matchCaseCheckBox.isChecked():
                matchFlags |= QtCore.Qt.MatchCaseSensitive
            self.matches = Matches(query, caseSensitive, self.model.match(modelIndex, QtCore.Qt.DisplayRole, query, -1, matchFlags))

# -----------------------------------------------------------------------------
#  Main window class.
# -----------------------------------------------------------------------------

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("TDF Control")
        self.setWindowIcon(createIcon('system-run'))
        self.resize(1000, 700)

        self.createActions()
        self.createToolbars()
        self.createMenubar()
        self.createStatusbar()

        self.deviceTabWidget = DeviceTabWidget(self)
        self.deviceTabWidget.updateMessage.connect(self.showMessage)

        self.setCentralWidget(self.deviceTabWidget)

    def createActions(self):
        """Create actions used in menu bar and tool bars."""

        # Action for opening a new connections file.
        self.openAct = QtGui.QAction("&Open...", self)
        self.openAct.setShortcut(QtGui.QKeySequence.Open)
        self.openAct.setStatusTip("Open an existing file")
        self.openAct.setIcon(createIcon('document-open'))
        self.openAct.triggered.connect(self.fileOpen)

        # Action to quit the application.
        self.quitAct = QtGui.QAction( "&Quit", self)
        self.quitAct.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q))
        self.quitAct.setStatusTip("Exit")
        self.quitAct.triggered.connect(self.close)

        # Action for configure file from device.
        self.configureAct = QtGui.QAction("&Configure...", self)
        self.configureAct.setStatusTip("Configure device from file")
        self.configureAct.setIcon(createIcon('system-run'))
        self.configureAct.setEnabled(False)
        self.configureAct.triggered.connect(self.configure)

        # Action for refreshing readable items.
        self.refreshAct = QtGui.QAction("&Refresh", self)
        self.refreshAct.setShortcut(QtGui.QKeySequence.Refresh)
        self.refreshAct.setStatusTip("Refresh values from by reading from device")
        self.refreshAct.setIcon(createIcon('view-refresh'))
        self.refreshAct.setEnabled(False)
        self.refreshAct.triggered.connect(self.refresh)

        self.expandAllAct = QtGui.QAction("&Expand all", self)
        self.expandAllAct.setIcon(createIcon('list-add'))
        self.expandAllAct.setEnabled(False)
        self.expandAllAct.triggered.connect(self.expandAll)

        self.collapseAllAct = QtGui.QAction("&Collapse all", self)
        self.collapseAllAct.setIcon(createIcon('list-remove'))
        self.collapseAllAct.setEnabled(False)
        self.collapseAllAct.triggered.connect(self.collapseAll)

        # Action for toggling status bar.
        self.statusbarAct = QtGui.QAction("&Statusbar", self)
        self.statusbarAct.setCheckable(True)
        self.statusbarAct.setChecked(True)
        self.statusbarAct.setStatusTip("Show or hide the statusbar in the current window")
        self.statusbarAct.toggled.connect(self.toggleStatusBar)

        # Actions to find items by name.
        self.findAct = QtGui.QAction("&Find...", self)
        self.findAct.setEnabled(False)
        self.findAct.setShortcut(QtGui.QKeySequence.Find)
        self.findAct.triggered.connect(self.find)

        # Actions to show online contents help.
        self.contentsAct = QtGui.QAction("&Contents", self)
        self.contentsAct.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1))
        self.contentsAct.triggered.connect(self.contents)

        # Actions to show about dialog.
        self.aboutAct = QtGui.QAction("&About", self)
        self.aboutAct.triggered.connect(self.about)

    def createToolbars(self):
        """Create tool bars and setup their behaviors (floating or static)."""

        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.addAction(self.openAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.refreshAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.expandAllAct)
        self.toolbar.addAction(self.collapseAllAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.configureAct)

        # Create action for toggling the tool bar here.
        self.toolbarAct = self.toolbar.toggleViewAction() # Get predefined action from toolbar.
        self.toolbarAct.setStatusTip("Show or hide the toolbar in the current window")

    def createMenubar(self):
        """Create menu bar with entries."""

        # Menu entry for file actions.
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        # Menu entry for edit actions.
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.configureAct)

        # Menu entry for view actions.
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.refreshAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.expandAllAct)
        self.viewMenu.addAction(self.collapseAllAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.toolbar.toggleViewAction())
        self.viewMenu.addAction(self.statusbarAct)

        # Menu entry for file actions.
        self.searchMenu = self.menuBar().addMenu("&Search")
        self.searchMenu.addAction(self.findAct)

        # Menu entry for help actions.
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.contentsAct)
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.aboutAct)

    def createStatusbar(self):
        """Create status bar and content."""
        self.statusBar()
        self.statusBar().showMessage("Ready.")

    def toggleStatusBar(self):
        """Toggles the visibility of the status bar."""
        self.statusBar().setVisible(self.statusbarAct.isChecked())

    def fileOpen(self):
        """Select a connections file using a file open dialog."""

        filename = QtGui.QFileDialog.getOpenFileName(self,
            "Open connection file", '{TDF.ROOT_DIR}/etc/uhal'.format(**globals()), "uHAL connection file (*.xml)")

        # Return if user did not select a file.
        if not filename:
            return

        self.loadConnections(str(filename))

    def configure(self):
        """Configure device from file."""
        filename = QtGui.QFileDialog.getOpenFileName(self,
            "Open configuration file", '{TDF.ROOT_DIR}/etc/config'.format(**globals()), "TDF configuration file (*.cfg)")

        # Return if user did not select a file.
        if not filename:
            return

        widget = self.deviceTabWidget.widget(self.deviceTabWidget.currentIndex())
        widget.treeView.configure(str(filename))

    def refresh(self):
        widget = self.deviceTabWidget.widget(self.deviceTabWidget.currentIndex())
        widget.treeView.refresh()

    def expandAll(self):
        widget = self.deviceTabWidget.widget(self.deviceTabWidget.currentIndex())
        widget.treeView.expandAll()

    def collapseAll(self):
        widget = self.deviceTabWidget.widget(self.deviceTabWidget.currentIndex())
        widget.treeView.collapseAll()

    def find(self):
        widget = self.deviceTabWidget.widget(self.deviceTabWidget.currentIndex())
        widget.findWidget.onShow()
        widget.findWidget.queryLineEdit.setFocus()

    def contents(self):
        url = 'http://gtmtca2.hephy.oeaw.ac.at/redmine/projects/tdf/wiki'
        QtGui.QMessageBox.information(self, "Contents", QtCore.QString("<p>Please refer to: <a href=\"%1\">%1</a></p>").arg(url))

    def about(self):
        QtGui.QMessageBox.information(self, "About", QtCore.QString(
            "<p><strong>TDF Control</strong></p><p>Graphical TDF tool for "
            "viewing and editing items located on uHAL compatible devices. This"
            " software is written in Python using the PyQt4 toolkit.</p>"
            "<p>Version %1</p>"
            "<p>Authors: Bernhard Arnold <a href=\"mailto:bernhard.arnold"
            "@cern.ch\">&lt;bernhard.arnold@cern.ch&gt;</a>, Johannes Wittmann <a href=\"mailto:johannes.wittmann"
            "@cern.ch\">&lt;johannes.wittmann@cern.ch&gt;</a></p>").arg(TDF.VERSION)
        )

    def loadConnections(self, filename):
        # Create connection manager and fetch devices.
        cm = uhal.ConnectionManager('file://{filename}'.format(filename = os.path.abspath(filename)))

        self.deviceTabWidget.clear()

        for name in cm.getDevices():
            device = cm.getDevice(name)
            self.deviceTabWidget.addDevice(device)

        # After loading a conenction file, it is possible to refresh the current module.
        self.configureAct.setEnabled(True)
        self.findAct.setEnabled(True)
        self.refreshAct.setEnabled(True)
        self.expandAllAct.setEnabled(True)
        self.collapseAllAct.setEnabled(True)
        self.setWindowTitle("TDF Control - {filename}".format(filename = os.path.basename(filename)))

    def showMessage(self, message, timeout = 0):
        self.statusBar().showMessage(message, timeout)
