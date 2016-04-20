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
from PyQt5.QtWidgets import (
    QGroupBox, QProxyStyle, QStyle, QStyleOption, QWidget)

__all__ = ["AccordionGroup", "AccordionBox"]


class AccordionProxy(QProxyStyle):

    def drawPrimitive(self, element, option, painter, widget):
        if element == QStyle.PE_IndicatorCheckBox and isinstance(
                widget, QGroupBox):
            element_ = QStyle.PE_IndicatorBranch
            option_ = QStyleOption()
            option_.initFrom(widget)
            option_.rect = option.rect
            option_.rect.translate(0, 1)
            option_.state |= QStyle.State_Children
            if widget.isChecked():
                option_.state |= QStyle.State_Open
            super(AccordionProxy, self).drawPrimitive(element_, option_, painter, widget)
        else:
            super(AccordionProxy, self).drawPrimitive(element, option, painter, widget)


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


class AccordionBox(QGroupBox):
    """
    A QGroupBox_ that can fold/unfold to reveal or hide its contents.

    .. _QGroupBox: http://doc.qt.io/qt-5/qgroupbox.html
    """

    def __init__(self, title=None, parent=None):
        super(AccordionBox, self).__init__(title, parent)
        self.setCheckable(True)
        self.setFlat(True)
        self.setStyle(AccordionProxy())
        self.toggled.connect(self._togglePanel)

    def _togglePanel(self, value):
        groupBox = self.sender()
        for child in groupBox.children():
            if isinstance(child, QWidget):
                child.setVisible(value)
