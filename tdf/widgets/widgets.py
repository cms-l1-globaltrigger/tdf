# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/widgets/widgets.py $
# Last committed    : $Revision: 3178 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2014-09-11 17:24:16 +0200 (Thu, 11 Sep 2014) $
#

"""Collection of common used widgets.
"""

__version__ = '$Revision: 3178 $'

from PyQt4 import QtCore, QtGui

class IconLabel(QtGui.QLabel):
    """A label with a left icon and a text.
    Attribute *icon* can be a resource string, a *QPixmap* or a *QIcon* object,
    attribute *text* is the descriptive text of the label.
    """
    def __init__(self, icon, text, parent = None):
        super(IconLabel, self).__init__(parent)
        self.iconLabel = QtGui.QLabel(self)
        self.textLabel = QtGui.QLabel(text, self)
        self.setIcon(icon)
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.iconLabel)
        layout.addWidget(self.textLabel)
        self.setLayout(layout)
    def icon(self, icon):
        return QtGui.QIcon(self.iconLabel.pixmap())
    def setIcon(self, icon):
        if isinstance(icon, str):
            icon = QtGui.QPixmap(icon)
        elif isinstance(icon, QtGui.QIcon):
            icon = icon.pixmap()
        self.iconLabel.setPixmap(icon)
    def text(self, icon):
        return self.textLabel.text()
    def setText(self, icon):
        self.textLabel.setText(text)
