"""
The *glyphLineView* submodule
-----------------------------

The *glyphLineView* submodule provides widgets that render a list of Glyph_ or
:class:`GlyphRecord` along a line, with various display parameters.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
"""
from defcon import Glyph
from defconQt.tools import drawing
from PyQt5.QtCore import pyqtSignal, QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPalette
from PyQt5.QtWidgets import QScrollArea, QWidget


class GlyphLineWidget(QWidget):
    """
    The :class:`GlyphLineWidget` widget displays a list of :class:`GlyphRecord`
    objects on one or multiple line(s).

    Note that this widget does not perform text layout by itself, but the
    :class:`GlyphRecord` data structure can hold positioning information from
    a text shaping engine.

    # TODO: drag and drop
    """
    glyphActivated = pyqtSignal(Glyph)
    pointSizeModified = pyqtSignal(int)
    selectionModified = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setFocusPolicy(Qt.ClickFocus)

        self._showLayers = False
        self._layerDrawingAttributes = {}
        self._fallbackDrawingAttributes = dict(
            showGlyphFill=True,
            showGlyphStroke=False,
            showGlyphOnCurvePoints=False,
            showGlyphStartPoints=False,
            showGlyphOffCurvePoints=False,
            showGlyphPointCoordinates=False,
            showGlyphAnchors=False,
            showGlyphImage=False,
            showGlyphMargins=False,
            showFontVerticalMetrics=False,
            showFontPostscriptBlues=False,
            showFontPostscriptFamilyBlues=False,
        )

        self._pointSize = 150
        self._scale = 1.0
        self._inverseScale = 0.1
        self._upm = 1000
        self._descender = -250
        self._buffer = 15

        self._verticalFlip = False
        self._lineHeight = 1.1
        self._rightToLeft = False
        self._wrapLines = False

        self._backgroundColor = Qt.white
        self._glyphColor = Qt.black
        self._glyphSelectionColor = None
        self._notdefBackgroundColor = QColor(255, 204, 204)

        self._glyphRecords = []
        self._glyphRecordsRects = {}
        self._selected = None

    # ------------
    # External API
    # ------------

    def glyphRecords(self):
        """
        Returns the list of :class:`GlyphRecord` in the widgets. This may be
        empty.
        """
        return self._glyphRecords

    def setGlyphRecords(self, glyphRecords):
        """
        Sets the glyphRecords displayed by the widget to *glyphs*.

        *glyphs* may be a list of :class:`GlyphRecord` or a list of Glyph_, in
        which case they will be wrapped into :class:`GlyphRecord` classes with
        the font’s kerning applied if the *applyKerning* attribute is true.

        .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
        """
        # set the records into the view
        self._glyphRecords = glyphRecords
        upms = []
        descenders = []
        for glyphRecord in self._glyphRecords:
            glyph = glyphRecord.glyph
            font = glyph.font
            if font is not None:
                upm = font.info.unitsPerEm
                if upm is not None:
                    upms.append(upm)
                descender = font.info.descender
                if descender is not None:
                    descenders.append(descender)
        if upms:
            self._upm = max(upms)
        if descenders:
            self._descender = min(descenders)
        self._calcScale()
        self.setShowLayers(self._showLayers)
        self.adjustSize()
        self.update()

    def pointSize(self):
        """
        Returns this widget’s *pointSize*.
        """
        return self._pointSize

    def setPointSize(self, pointSize):
        """
        Sets the point size to *pointSize*. Must be greater than zero.

        The initial value is 150.
        """
        self._pointSize = int(pointSize)
        self._calcScale()
        self.adjustSize()
        self.update()

    def rightToLeft(self):
        """
        Returns this widget’s layout direction. Right-to-left if true.
        """
        return self._rightToLeft

    def setRightToLeft(self, value):
        """
        Sets the widget’s layout direction to right-to-left if *value* is true.

        The default is false.
        """
        self._rightToLeft = value
        self.adjustSize()
        self.update()

    def glyphColor(self):
        """
        Returns the color with which glyphs are rendered.
        """
        return self._glyphColor

    def setGlyphColor(self, color):
        """
        Sets the QColor_ *color* with which glyphs are rendered.

        The default is Qt.black.

        .. _QColor: http://doc.qt.io/qt-5/qcolor.html
        """
        self._glyphColor = color

    def backgroundColor(self):
        """
        Returns the color with which the widget’s background is paint.
        """
        return self._backgroundColor

    def setBackgroundColor(self, color):
        """
        Sets the QColor_ *backgroundColor* with which the widget’s background
        is paint.

        The default is Qt.white.

        .. _QColor: http://doc.qt.io/qt-5/qcolor.html
        """
        self._backgroundColor = color

    def notdefBackgroundColor(self):
        """
        Returns the color with which .notdef’s background is paint.
        """
        return self._notdefBackgroundColor

    def setNotdefBackgroundColor(self, color):
        """
        Sets the QColor_ *notdefBackgroundColor* with which .notdef’s
        background is paint.

        The default is QColor(255, 204, 204).

        .. _QColor: http://doc.qt.io/qt-5/qcolor.html
        """
        self._notdefBackgroundColor = color

    def showLayers(self):
        """
        Returns whether an overlay of each rendered glyph’s layers if
        displayed.
        """
        return self._showLayers

    def setShowLayers(self, value):
        """
        Displays an overlay of each rendered glyph’s layers if *value* is true.

        The default is false.
        """
        self._layerDrawingAttributes = {}
        self._showLayers = value
        if value:
            for record in self._glyphRecords:
                glyph = record.glyph
                layerSet = glyph.layerSet
                if layerSet is not None:
                    for layerName in layerSet.layerOrder:
                        self._layerDrawingAttributes[layerName] = dict(
                            showGlyphFill=True)
        self.update()

    def verticalFlip(self):
        """
        Returns whether glyphs are displayed vertically flipped.
        """
        return self._verticalFlip

    def setVerticalFlip(self, value):
        """
        Displays glyphs vertically flipped if *value* is true.

        The default is false.
        """
        self._verticalFlip = value
        self.update()

    def lineHeight(self):
        """
        Returns this widget’s line-height factor.
        """
        return self._lineHeight

    def setLineHeight(self, scale):
        """
        Sets the line-height factor to *scale*. 1.0 means no extra vertical
        space is added around each line of text.

        The default value is 1.1.
        """
        self._lineHeight = scale
        self.adjustSize()
        self.update()

    def wrapLines(self):
        """
        Returns whether glyph runs wrap at the viewport’s *width* boundary.
        """
        return self._wrapLines

    def setWrapLines(self, value):
        """
        Sets the widget to wrap glyphs at the viewport’s *width* boundary if
        *value* is true.

        The default is false.
        """
        self._wrapLines = value
        self.adjustSize()
        self.update()

    def drawingAttribute(self, attr, layerName):
        """
        Returns the suitable drawing attribute for string *attr* and
        *layerName*.

        If *layerName* is None, this returns a fallback attribute.
        """
        if layerName is None:
            return self._fallbackDrawingAttributes.get(attr)
        d = self._layerDrawingAttributes.get(layerName, {})
        return d.get(attr)

    def setDrawingAttribute(self, attr, value, layerName):
        """
        Sets attribute string *attr* to *value*. If *layerName* is not None,
        this value is specified for that given layer.

        The default values are:

        - *showGlyphFill=True*
        - *showGlyphStroke=False*
        - *showGlyphOnCurvePoints=False*
        - *showGlyphStartPoints=False*
        - *showGlyphOffCurvePoints=False*
        - *showGlyphPointCoordinates=False*
        - *showGlyphAnchors=False*
        - *showGlyphImage=False*
        - *showGlyphMargins=False*
        - *showFontVerticalMetrics=False*
        - *showFontPostscriptBlues=False*
        - *showFontPostscriptFamilyBlues=False*

        """
        if layerName is None:
            self._fallbackDrawingAttributes[attr] = value
        else:
            if layerName not in self._layerDrawingAttributes:
                self._layerDrawingAttributes[layerName] = {}
            self._layerDrawingAttributes[layerName][attr] = value
        self.update()

    def selected(self):
        """
        Returns the currently selected glyph’s index, or None if none are
        selected.
        """
        return self._selected

    def setSelected(self, value):
        """
        Sets *value*-th glyph as the selected glyph, or none if *value* is
        None.

        *value* should be less than the number of glyphRecords present in the
        widget.
        """
        self._selected = value
        if self._selected is not None and self._glyphRecordsRects is not None:
            parent = self.parent()
            if isinstance(parent, QScrollArea):
                rect = None
                for r, indexRecord in self._glyphRecordsRects.items():
                    if indexRecord == self._selected:
                        rect = QRectF(r)
                        break
                if rect is not None:
                    parent.ensureVisible(rect)
        self.update()

    # ------
    # Sizing
    # ------

    def _calcScale(self):
        scale = self._pointSize / self._upm
        if scale < .01:
            scale = 0.01
        self._scale = scale
        self._inverseScale = 1.0 / self._scale
        self._pointSize = self._upm * self._scale

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        width = height = self._buffer * 2
        if not self._wrapLines:
            for glyphRecord in self._glyphRecords:
                width += (glyphRecord.advanceWidth + glyphRecord.xPlacement +
                          glyphRecord.xAdvance) * self._scale
            height += self._pointSize * self._lineHeight
        else:
            parent = self.parent()
            curWidth = self._buffer * 2
            visibleWidth = parent.width() if parent is not None else self.width()
            lines = 1
            for glyphRecord in self._glyphRecords:
                gWidth = (glyphRecord.advanceWidth + glyphRecord.xPlacement +
                          glyphRecord.xAdvance) * self._scale
                # TODO: implement \n? do it correctly anyway
                if curWidth + gWidth > visibleWidth:
                    curWidth = self._buffer * 2 + gWidth
                    lines += 1
                else:
                    curWidth += gWidth
                width = max(curWidth, width)
            height += lines * self._pointSize * self._lineHeight
        return QSize(width, height)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            scale = pow(1.2, event.angleDelta().y() / 120.0)
            pointSize = round(self._pointSize * scale)
            if pointSize <= 0:
                return
            self.setPointSize(pointSize)
            self.pointSizeModified.emit(pointSize)
        else:
            super().wheelEvent(event)

    # --------
    # Painting
    # --------

    def drawGlyph(self, painter, glyph, rect, selection=False):
        # gather the layers
        layerSet = glyph.layerSet
        if layerSet is None or not self._showLayers:
            layers = [(glyph, None)]
        else:
            glyphName = glyph.name
            layers = []
            for layerName in reversed(layerSet.layerOrder):
                layer = layerSet[layerName]
                if glyphName not in layer:
                    continue
                g = layer[glyphName]
                if g == glyph:
                    layerName = None
                layers.append((g, layerName))

        self.drawGlyphBackground(painter, glyph, rect, selection=selection)

        for g, layerName in layers:
            # draw the image
            if self.drawingAttribute("showGlyphImage", layerName):
                self.drawImage(painter, g, layerName, rect)
            # draw the blues
            if layerName is None and self.drawingAttribute(
                    "showFontPostscriptBlues", None):
                self.drawBlues(painter, g, layerName, rect)
            if layerName is None and self.drawingAttribute(
                    "showFontPostscriptFamilyBlues", None):
                self.drawFamilyBlues(painter, g, layerName, rect)
            # draw the margins
            if self.drawingAttribute("showGlyphMargins", layerName):
                self.drawMargins(painter, g, layerName, rect)
            # draw the vertical metrics
            if layerName is None and self.drawingAttribute(
                    "showFontVerticalMetrics", None):
                self.drawVerticalMetrics(painter, g, layerName, rect)
            # draw the glyph
            if self.drawingAttribute("showGlyphFill", layerName) or \
                    self.drawingAttribute("showGlyphStroke", layerName):
                self.drawFillAndStroke(painter, g, layerName, rect)
            if self.drawingAttribute("showGlyphOnCurvePoints", layerName) or \
                    self.drawingAttribute(
                        "showGlyphOffCurvePoints", layerName):
                self.drawPoints(painter, g, layerName, rect)
            if self.drawingAttribute("showGlyphAnchors", layerName):
                self.drawAnchors(painter, g, layerName, rect)

        self.drawGlyphForeground(painter, glyph, rect, selection=selection)

    def drawGlyphBackground(self, painter, glyph, rect, selection=False):
        if glyph.name == ".notdef":
            painter.fillRect(QRectF(*rect), self._notdefBackgroundColor)
        if selection:
            if self._glyphSelectionColor is not None:
                selectionColor = self._glyphSelectionColor
            else:
                palette = self.palette()
                active = palette.currentColorGroup() != QPalette.Inactive
                selectionColor = palette.color(QPalette.Highlight)
                selectionColor.setAlphaF(.15 if active else .8)
            painter.fillRect(QRectF(*rect), selectionColor)

    def drawImage(self, painter, glyph, layerName, rect):
        drawing.drawGlyphImage(
            painter, glyph, self._inverseScale, rect,
            backgroundColor=self._backgroundColor)

    def drawBlues(self, painter, glyph, layerName, rect):
        drawing.drawFontPostscriptBlues(
            painter, glyph, self._inverseScale, rect,
            backgroundColor=self._backgroundColor)

    def drawFamilyBlues(self, painter, glyph, layerName, rect):
        drawing.drawFontPostscriptFamilyBlues(
            painter, glyph, self._inverseScale, rect,
            backgroundColor=self._backgroundColor)

    def drawVerticalMetrics(self, painter, glyph, layerName, rect):
        drawText = self.drawingAttribute(
            "showFontVerticalMetricsTitles", layerName) and \
            self._pointSize > 150
        drawing.drawFontVerticalMetrics(
            painter, glyph, self._inverseScale, rect, drawText=drawText,
            backgroundColor=self._backgroundColor, flipped=True)

    def drawMargins(self, painter, glyph, layerName, rect):
        drawing.drawGlyphMargins(
            painter, glyph, self._inverseScale, rect,
            backgroundColor=self._backgroundColor)

    def drawFillAndStroke(self, painter, glyph, layerName, rect):
        showFill = self.drawingAttribute("showGlyphFill", layerName)
        showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        fillColor = None
        if not self._showLayers:
            fillColor = self._glyphColor
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, rect, drawFill=showFill,
            drawStroke=showStroke, contourFillColor=fillColor,
            componentFillColor=fillColor,
            backgroundColor=self._backgroundColor)

    def drawPoints(self, painter, glyph, layerName, rect):
        drawStartPoint = self.drawingAttribute(
            "showGlyphStartPoints", layerName) and self._pointSize > 175
        drawOnCurves = self.drawingAttribute(
            "showGlyphOnCurvePoints", layerName) and self._pointSize > 175
        drawOffCurves = self.drawingAttribute(
            "showGlyphOffCurvePoints", layerName) and self._pointSize > 175
        drawCoordinates = self.drawingAttribute(
            "showGlyphPointCoordinates", layerName) and self._pointSize > 250
        drawing.drawGlyphPoints(
            painter, glyph, self._inverseScale, rect,
            drawStartPoint=drawStartPoint, drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=self._backgroundColor, flipped=True)

    def drawAnchors(self, painter, glyph, layerName, rect):
        drawText = self._pointSize > 50
        drawing.drawGlyphAnchors(
            painter, glyph, self._inverseScale, rect, drawText=drawText,
            backgroundColor=self._backgroundColor, flipped=True)

    def drawGlyphForeground(self, painter, glyph, rect, selection=False):
        pass

    # ------
    # Events
    # ------

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._unsubscribeFromGlyphs()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            selected = None
            for rect, recordIndex in self._glyphRecordsRects.items():
                if QRectF(*rect).contains(event.localPos()):
                    selected = recordIndex
            if self._selected == selected:
                return
            self._selected = selected
            self.selectionModified.emit(self._selected)
            self.update()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # TODO: we could possibly redo rects only on adjustSize()
        if self._rightToLeft:
            self.paintRightToLeft(painter, event.rect())
        else:
            self.paintLeftToRight(painter, event.rect())

    def paintLeftToRight(self, painter, rect):
        self._glyphRecordsRects = {}
        # draw the background
        painter.fillRect(rect, self._backgroundColor)
        # create some reusable values
        scale = self._scale
        upm = self._upm
        descender = self._descender
        ascender = upm + descender
        lineHeightOffset = (self._lineHeight - 1) * upm
        # offset for the buffer
        painter.save()
        painter.translate(self._buffer, self._buffer)
        # offset for the descender
        baselineShift = .5 * lineHeightOffset
        if self._verticalFlip:
            baselineShift -= descender
            yDirection = 1
        else:
            baselineShift += ascender
            yDirection = -1
        painter.scale(scale, scale)
        painter.translate(0, baselineShift)
        # flip
        painter.scale(1, yDirection)
        # draw the records
        left = self._buffer
        top = self._buffer + .5 * lineHeightOffset * scale
        height = upm * scale
        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            glyph = glyphRecord.glyph
            w = glyphRecord.advanceWidth
            h = glyphRecord.advanceHeight
            xP = glyphRecord.xPlacement
            yP = glyphRecord.yPlacement
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            # possibly go to the next line
            if self._wrapLines:
                incomingWidth = left + (w + xP + xA) * scale + self._buffer
                if incomingWidth > self.width():
                    top += upm * self._lineHeight * scale
                    painter.translate(
                        (self._buffer - left) * self._inverseScale, yDirection * upm * self._lineHeight)
                    left = self._buffer
            # handle offsets from the record
            top -= yP * scale
            glyphHeight = height + ((h + yA) * scale)
            glyphLeft = left + (xP * scale)
            glyphWidth = (w + xA) * scale
            # store the glyph rect for the alternate menu
            rect = (glyphLeft, top, glyphWidth, glyphHeight)
            self._glyphRecordsRects[rect] = recordIndex
            # handle placement
            if xP or yP:
                painter.translate(xP, yP)
            # draw the glyph
            rect = (-xP, descender - yP, w, upm)
            selection = self._selected == recordIndex
            self.drawGlyph(painter, glyph, rect, selection=selection)
            # shift for the next glyph
            painter.translate(w + xA - xP, h + yA - yP)
            left += glyphWidth
        painter.restore()

    def paintRightToLeft(self, painter, rect):
        self._glyphRecordsRects = {}
        # draw the background
        painter.fillRect(rect, self._backgroundColor)
        # create some reusable values
        scale = self._scale
        upm = self._upm
        descender = self._descender
        ascender = upm + descender
        lineHeightOffset = (self._lineHeight - 1) * upm
        # offset for the buffer
        painter.save()
        painter.translate(self.width() - self._buffer, self._buffer)
        # offset for the descender
        baselineShift = .5 * lineHeightOffset
        if self._verticalFlip:
            baselineShift -= descender
            yDirection = 1
        else:
            baselineShift += ascender
            yDirection = -1
        painter.scale(scale, scale)
        painter.translate(0, baselineShift)
        # flip
        painter.scale(1, yDirection)
        # draw the records
        left = self.width() - self._buffer
        top = self._buffer + .5 * lineHeightOffset * scale
        height = upm * scale
        previousXA = 0
        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            glyph = glyphRecord.glyph
            w = glyphRecord.advanceWidth
            h = glyphRecord.advanceHeight
            xP = glyphRecord.xPlacement
            yP = glyphRecord.yPlacement
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            # possibly go to the next line
            if self._wrapLines:
                incomingLeft = left - (w + xP + xA) * scale - self._buffer
                if incomingLeft < 0:
                    top += upm * self._lineHeight * scale
                    painter.translate(
                        (self.width() - self._buffer - left) * self._inverseScale, yDirection * upm * self._lineHeight)
                    left = self.width() - self._buffer
            # handle offsets from the record
            top -= yP * scale
            glyphHeight = height + ((h + yA) * scale)
            glyphLeft = left + ((-w + xP - xA) * scale)
            glyphWidth = (w + xA) * scale
            # store the glyph rect for the alternate menu
            rect = (glyphLeft, top, glyphWidth, glyphHeight)
            self._glyphRecordsRects[rect] = recordIndex
            # handle the placement
            if xP:
                xP += previousXA
            painter.translate(-w - xA + xP, yP)
            # draw the glyph
            rect = (-xP, descender - yP, w, upm)
            selection = self._selected == recordIndex
            self.drawGlyph(painter, glyph, rect, selection=selection)
            # shift for the next glyph
            painter.translate(-xP, h + yA - yP)
            left -= (w + xP + xA) * scale
            previousXA = xA
        painter.restore()


class GlyphLineView(QScrollArea):
    """
    The :class:`GlyphLineView` widget is a QScrollArea_ that contains a
    :class:`GlyphLineWidget`.

    It reimplements :class:`GlyphLineWidget` public API and handles
    notification support from the font.
    Its :func:`setGlyphs` function can wrap a list of Glyph_ into
    :class:`GlyphRecord` for convenience, and applies kerning values from the
    font if *applyKerning* is set to true in the constructor.

    Here’s a basic text example that shows a :class:`GlyphLineView` in a
    :class:`BaseWindow`:

    >>> from defconQt.controls.glyphLineView import GlyphLineView
    >>> window = BaseWindow()
    >>> glyphs = [font[c] for c in "hallo welt"]
    >>> area = GlyphLineView(window)
    >>> area.setGlyphs(glyphs)
    >>>
    >>> layout = QVBoxLayout(window)
    >>> layout.addWidget(area)
    >>> window.show()

    TODO: add sample image

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QScrollArea: http://doc.qt.io/qt-5/qscrollarea.html
    """
    glyphLineWidgetClass = GlyphLineWidget

    def __init__(self, applyKerning=False, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self._applyKerning = applyKerning
        self._glyphLineWidget = self.glyphLineWidgetClass(self)
        self.setWidget(self._glyphLineWidget)
        # reexport signals
        self.pointSizeModified = self._glyphLineWidget.pointSizeModified
        self.selectionModified = self._glyphLineWidget.selectionModified

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyphs(self, glyphRecords):
        handledGlyphs = set()
        handledFonts = set()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.addObserver(self, "_fontChanged", "Info.Changed")
            if self._applyKerning:
                font.kerning.addObserver(
                    self, "_kerningChanged", "Kerning.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        handledFonts = set()
        glyphRecords = self._glyphLineWidget.glyphRecords()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.removeObserver(self, "Info.Changed")
            if self._applyKerning:
                font.kerning.removeObserver(self, "Kerning.Changed")

    def _glyphChanged(self, notification):
        self._glyphLineWidget.update()

    def _kerningChanged(self, notification):
        glyphRecords = self._glyphLineWidget.glyphRecords()
        self._setKerningInGlyphRecords(glyphRecords)
        self._glyphLineWidget.update()

    def _fontChanged(self, notification):
        glyphRecords = self._glyphLineWidget.glyphRecords()
        self._glyphLineWidget.setGlyphRecords(glyphRecords)

    # ---------------
    # Kerning Support
    # ---------------

    def _lookupKerningValue(self, font, first, second):
        # TODO: this should be put into defcon
        kerning = font.kerning
        groups = font.groups
        # quickly check to see if the pair is in the kerning dictionary
        pair = (first, second)
        if pair in kerning:
            return kerning[pair]
        # get group names and make sure first and second are glyph names
        firstGroup = secondGroup = None
        if first.startswith("public.kern1"):
            firstGroup = first
            first = None
        else:
            for group, groupMembers in groups.items():
                if group.startswith("public.kern1"):
                    if first in groupMembers:
                        firstGroup = group
                        break
        if second.startswith("public.kern2"):
            secondGroup = second
            second = None
        else:
            for group, groupMembers in groups.items():
                if group.startswith("public.kern2"):
                    if second in groupMembers:
                        secondGroup = group
                        break
        # make an ordered list of pairs to look up
        pairs = [
            (first, second),
            (first, secondGroup),
            (firstGroup, second),
            (firstGroup, secondGroup)
        ]
        # look up the pairs and return any matches
        for pair in pairs:
            if pair in kerning:
                return kerning[pair]
        return 0

    def _setKerningInGlyphRecords(self, glyphRecords):
        previousGlyph = None
        previousFont = None
        for index, glyphRecord in enumerate(glyphRecords):
            glyph = glyphRecord.glyph
            font = glyph.font
            if previousGlyph is not None and font is not None and (
                    previousFont == font):
                kern = self._lookupKerningValue(
                    font, previousGlyph.name, glyph.name)
                if kern is None:
                    kern = 0
                glyphRecords[index - 1].xAdvance = kern
            previousGlyph = glyph
            previousFont = font

    # ------------
    # External API
    # ------------

    def glyphRecords(self):
        return self._glyphLineWidget.glyphRecords()

    def setGlyphRecords(self, glyphs):
        # unsubscribe from the old glyphs
        self._unsubscribeFromGlyphs()
        # test to see if glyph records are present
        needToWrap = False
        if glyphs:
            for attr in ("glyph", "xPlacement", "yPlacement", "xAdvance",
                         "yAdvance", "alternates"):
                if not hasattr(glyphs[0], attr):
                    needToWrap = True
                    break
        # wrap into glyph records if necessary
        if needToWrap:
            glyphRecords = []
            for glyph in glyphs:
                glyphRecord = GlyphRecord()
                glyphRecord.glyph = glyph
                glyphRecord.advanceWidth = glyph.width
                glyphRecords.append(glyphRecord)
            # apply kerning as needed
            if self._applyKerning:
                self._setKerningInGlyphRecords(glyphRecords)
        else:
            glyphRecords = glyphs
        # set the records into the view
        self._glyphLineWidget.setGlyphRecords(glyphRecords)
        # subscribe to the new glyphs
        self._subscribeToGlyphs(glyphRecords)

    def pointSize(self):
        return self._glyphLineWidget.pointSize()

    def setPointSize(self, pointSize):
        self._glyphLineWidget.setPointSize(pointSize)

    def rightToLeft(self):
        return self._glyphLineWidget.rightToLeft()

    def setRightToLeft(self, value):
        self._glyphLineWidget.setRightToLeft(value)

    def glyphColor(self):
        return self._glyphLineWidget.glyphColor()

    def setGlyphColor(self, color):
        self._glyphLineWidget.setGlyphColor(color)

    def backgroundColor(self):
        return self._glyphLineWidget.backgroundColor()

    def setBackgroundColor(self, color):
        self._glyphLineWidget.setBackgroundColor(color)

    def notdefBackgroundColor(self):
        return self._glyphLineWidget._notdefBackgroundColor

    def setNotdefBackgroundColor(self, color):
        self._glyphLineWidget.setNotdefBackgroundColor(color)

    def showLayers(self):
        return self._glyphLineWidget.showLayers()

    def setShowLayers(self, value):
        self._glyphLineWidget.setShowLayers(value)

    def verticalFlip(self):
        return self._glyphLineWidget.verticalFlip()

    def setVerticalFlip(self, value):
        self._glyphLineWidget.setVerticalFlip(value)

    def wrapLines(self):
        return self._glyphLineWidget.wrapLines()

    def setWrapLines(self, value):
        if value:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._glyphLineWidget.setWrapLines(value)

    def selected(self):
        return self._glyphLineWidget.selected()

    def setSelected(self, value):
        self._glyphLineWidget.setSelected(value)

    def drawingAttribute(self, attr, layerName=None):
        return self._glyphLineWidget.drawingAttribute(attr, layerName)

    def setDrawingAttribute(self, attr, value, layerName=None):
        self._glyphLineWidget.setDrawingAttribute(attr, layerName, value)

# ------------------
# Basic Glyph Record
# ------------------


class GlyphRecord(object):
    """
    A :class:`GlyphRecord` is a glyph data structure that can accomodate
    information suitable to text layout, namely positioning and alternates.
    """
    __slots__ = ["glyph", "xPlacement", "yPlacement", "xAdvance", "yAdvance",
                 "advanceWidth", "advanceHeight", "alternates"]

    def __init__(self):
        self.glyph = None
        self.xPlacement = 0
        self.yPlacement = 0
        self.xAdvance = 0
        self.yAdvance = 0
        self.advanceWidth = 0
        self.advanceHeight = 0
        self.alternates = []
