# -*- coding: utf-8 -*-
"""
The *accordionBox* submodule
----------------------------

The *accordionBox* submodule provides a container widget that can fold/unfold
to reveal or hide its contents, in the form of :class:`AccordionBox`.

:class:`AccordionGroup` is a set of AccordionBox that can be used to ensure
only one is open at a time.
"""
from __future__ import absolute_import
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import (
    QGroupBox, QProxyStyle, QStyle, QStylePainter, QStyleOptionGroupBox,
    QWidget)

__all__ = ["AccordionGroup", "AccordionBox"]


class AccordionGroup(QObject):
    """
    In some situations it is useful to have exclusive :class:`AccordionBox`
    objects, i.e. only one in a series is open at a time.

    One simple way of achieving this is to group the box widgets together in
    an :class:`AccordionGroup`.

    Here’s an example on adding two accordions to a QWidget_ *myWidget*:

    >>> from defconQt.controls.accordionBox import AccordionGroup
    >>> group = AccordionGroup()
    >>> acc1 = group.createAccordion("Glyph", myWidget)
    >>> acc2 = group.createAccordion("Preview", myWidget)
    >>> acc1.setChecked(True)
    >>> acc2.setChecked(True)
    >>> acc1.isChecked()
    False

    TODO: add sample image

    Here we create a new accordion group. Since the accordion group is
    exclusive by default, only one of the accordions in the group is checked
    at a time.

    .. _QWidget: http://doc.qt.io/qt-5/qwidget.html
    """

    def __init__(self, parent=None):
        super(AccordionGroup, self).__init__(parent)
        self._accordions = set()
        self._currentAccordion = None
        self._exclusive = True

    def _accordionToggled(self):
        accordion = self.sender()
        if self._exclusive:
            if accordion.isChecked():
                self._setCurrentAccordion(accordion)
            elif accordion == self._currentAccordion:
                self._setCurrentAccordion(None)

    def _setCurrentAccordion(self, accordion):
        prevAccordion = self._currentAccordion
        if prevAccordion is not None:
            prevAccordion.toggled.disconnect(self._accordionToggled)
            prevAccordion.setChecked(False)
            prevAccordion.toggled.connect(self._accordionToggled)
        self._currentAccordion = accordion

    def addAccordion(self, accordion):
        """
        Adds the :class:`AccordionBox` *accordion* to this group, if absent.
        """
        if accordion not in self._accordions:
            self._accordions.add(accordion)
            accordion.toggled.connect(self._accordionToggled)
        if self._exclusive and accordion.isChecked():
            self._setCurrentAccordion(accordion)

    def createAccordion(self, title=None, parent=None):
        """
        Creates an :class:`AccordionBox` with string *title* and QWidget_
        *parent* and adds it to this group.

        .. _QWidget: http://doc.qt.io/qt-5/qwidget.html
        """
        accordion = AccordionBox(title, parent)
        self.addAccordion(accordion)
        return accordion

    def removeAccordion(self, accordion):
        """
        Removes the :class:`AccordionBox` *accordion* from this group, if
        present.
        """
        if accordion in self._accordions:
            self._accordions.remove(accordion)
            accordion.toggled.disconnect(self._accordionToggled)
        if self._currentAccordion == accordion:
            self._setCurrentAccordion = None

    def accordions(self):
        """
        Returns the set of this group’s actions. This may be empty.
        """
        return self._accordions

    def isExclusive(self):
        """
        Whether this group is exclusive. The default is true.
        """
        return self._exclusive

    def setExclusive(self, exclusive):
        """
        If *exclusive* is true, only one accordion in the accordion group can
        ever be unfolded at any time. If the user chooses another checkable
        accordion in the group, the one they chose becomes active and the one
        that was active becomes inactive.
        """
        self._exclusive = exclusive
        if exclusive:
            for accordion in self._accordions:
                if accordion.isChecked():
                    if self._currentAccordion is None:
                        self._setCurrentAccordion(accordion)
                    else:
                        accordion.setChecked(False)
        else:
            self._currentAccordion = None

    def currentAccordion(self):
        """
        Returns the currently unfolded accordion in the group, or None if none
        are unfolded.
        """
        return self._currentAccordion


class AccordionProxy(QProxyStyle):

    def subControlRect(self, control, option, subControl, widget):
        rect = super().subControlRect(control, option, subControl, widget)
        if subControl == QStyle.SC_GroupBoxContents:
            x1, y1, x2, y2 = rect.getCoords()
            # XXX: cross-platform hazard
            # also why do we have to do this?
            x1 -= 8
            x2 += 8
            rect.setCoords(x1, y1, x2, y2)
        return rect


class AccordionBox(QGroupBox):
    """
    A QGroupBox_ that can fold/unfold to reveal or hide its contents.

    .. _QGroupBox: http://doc.qt.io/qt-5/qgroupbox.html
    """

    def __init__(self, title=None, parent=None):
        super(AccordionBox, self).__init__(title, parent)
        #self.setCheckable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFlat(True)
        # TODO: should this really be in the base widget?
        font = self.font()
        font.setCapitalization(QFont.AllUppercase)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        font.setPointSize(8)
        self.setFont(font)
        palette = self.palette()
        palette.setColor(QPalette.WindowText, QColor(120, 120, 120))
        self.setPalette(palette)
        self.setStyle(AccordionProxy())
        self.toggled.connect(self._togglePanel)

    def initStyleOption(self, option):
        super().initStyleOption(option)
        option.lineWidth = 0
        option.subControls ^= QStyle.SC_GroupBoxFrame

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionGroupBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QStyle.CC_GroupBox, option)

    def _togglePanel(self, value):
        groupBox = self.sender()
        for child in groupBox.children():
            if isinstance(child, QWidget):
                child.setVisible(value)
