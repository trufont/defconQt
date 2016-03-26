"""
The *glyphView* submodule
-----------------------------

The *glyphView* submodule provides widgets that render a Glyph_, with
various display parameters.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
"""
from defconQt.tools import drawing, platformSpecific
from PyQt5.QtCore import pyqtSignal, QPointF, QRectF, QSize, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QScrollArea, QWidget

UIFont = platformSpecific.otherUIFont()


class GlyphWidget(QWidget):
    pointSizeChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.ClickFocus)
        self._glyph = None
        self._scrollArea = None

        # drawing attributes
        self._layerDrawingAttributes = {}
        self._fallbackDrawingAttributes = dict(
            showGlyphFill=False,
            showGlyphStroke=True,
            showGlyphOnCurvePoints=True,
            showGlyphStartPoints=True,
            showGlyphOffCurvePoints=True,
            showGlyphPointCoordinates=False,
            showGlyphAnchors=True,
            showGlyphImage=True,
            showGlyphMargins=True,
            showFontVerticalMetrics=True,
            showFontVerticalMetricsTitles=True,
            showFontPostscriptBlues=False,
            showFontPostscriptFamilyBlues=False,
        )

        # cached vertical metrics
        self._unitsPerEm = 1000
        self._descender = -250
        self._capHeight = 750
        self._ascender = 750

        # drawing data cache
        self._drawingRect = None
        self._scale = 1.0
        self._inverseScale = 0.1
        self._impliedPointSize = 1000

        # drawing calculation
        self._centerVertically = True
        self._centerHorizontally = True
        self._noPointSizePadding = 200
        self._verticalCenterYBuffer = 0

        self._backgroundColor = Qt.white

    # --------------
    # Custom Methods
    # --------------

    def drawingRect(self):
        return self._drawingRect

    def inverseScale(self):
        return self._inverseScale

    def scale(self):
        return self._scale

    def setScale(self, scale):
        self._scale = scale
        if self._scale <= 0:
            self._scale = .01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._unitsPerEm * self._scale
        self.pointSizeChanged.emit(self._impliedPointSize)
        self.adjustSize()

    def glyph(self):
        return self._glyph

    def setGlyph(self, glyph):
        self._glyph = glyph
        self._font = None
        if glyph is not None:
            font = self._font = glyph.font
            if font is not None:
                self._unitsPerEm = font.info.unitsPerEm
                if self._unitsPerEm is None:
                    self._unitsPerEm = 1000
                self._descender = font.info.descender
                if self._descender is None:
                    self._descender = -250
                self._ascender = font.info.ascender
                if self._ascender is None:
                    self._ascender = self._unitsPerEm + self._descender
                self._capHeight = font.info.capHeight
                if self._capHeight is None:
                    self._capHeight = self._ascender
            self.setScale(self._scale)
        self.update()

    def scrollArea(self):
        return self._scrollArea

    def setScrollArea(self, scrollArea):
        scrollArea.setWidget(self)
        self._scrollArea = scrollArea

    # fitting

    def centerOn(self, pos):
        """
        Centers this widget’s *scrollArea* on QPointF_ *pos*.

        .. _QPointF: http://doc.qt.io/qt-5/qpointf.html
        """
        scrollArea = self._scrollArea
        if scrollArea is None:
            return
        hSB = scrollArea.horizontalScrollBar()
        vSB = scrollArea.verticalScrollBar()
        viewport = scrollArea.viewport()
        hValue = hSB.minimum() + hSB.maximum() - (
            pos.x() - viewport.width() / 2)
        hSB.setValue(hValue)
        vSB.setValue(pos.y() - viewport.height() / 2)

    def _getGlyphWidthHeight(self):
        if self._glyph is None:
            return 0, 0
        bottom = self._descender
        top = max(self._capHeight, self._ascender,
                  self._unitsPerEm + self._descender)
        width = self._glyph.width
        height = -bottom + top
        return width, height

    def fitScaleMetrics(self):
        """
        Scales and centers the viewport around the font’s metrics.
        """
        fitHeight = self._scrollArea.height()
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphHeight += self._noPointSizePadding * 2
        self.setScale(fitHeight / glyphHeight)
        self.centerOn(self.mapFromCanvas(
            QPointF(glyphWidth / 2, self._descender + (top - bottom) / 2)))

    def fitScaleBBox(self):
        """
        Scales and centers the viewport around the *glyph*’s bounding box.
        """
        if self._glyph is None:
            return
        if self._glyph.bounds is None:
            self.fitScaleMetrics()
            return
        left, bottom, right, top = self._glyph.bounds
        # TODO: should maybe fit w height or width
        fitHeight = self._scrollArea.height()
        glyphHeight = top - bottom
        glyphHeight += self._noPointSizePadding * 2
        self.setScale(fitHeight / glyphHeight)
        glyphWidth = right - left
        self.centerOn(self.mapFromCanvas(
            QPointF(left + glyphWidth / 2, bottom + (top - bottom) / 2)))

    # position mapping

    def mapFromCanvas(self, pos):
        """
        Maps *pos* from glyph canvas to this widget’s coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        """
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        x = (pos.x() - xOffsetInv) * self._scale
        y = (pos.y() - yOffsetInv) * (- self._scale) + self.height()
        return pos.__class__(x, y)

    def mapToCanvas(self, pos):
        """
        Maps *pos* from this widget’s to glyph canvas coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        """
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        x = pos.x() * self._inverseScale + xOffsetInv
        y = (pos.y() - self.height()) * (- self._inverseScale) + yOffsetInv
        return pos.__class__(x, y)

    def mapRectFromCanvas(self, rect):
        x, y, w, h = rect.getRect()
        origin = self.mapFromCanvas(QPointF(x, y))
        w *= self._scale
        h *= self._scale
        return rect.__class__(origin.x(), origin.y() - h, w, h)

    def mapRectToCanvas(self, rect):
        x, y, w, h = rect.getRect()
        origin = self.mapToCanvas(QPointF(x, y))
        w *= self._inverseScale
        h *= self._inverseScale
        return rect.__class__(origin.x(), origin.y() - h, w, h)

    # --------------------
    # Notification Support
    # --------------------

    def glyphChanged(self):
        # TODO: we could adjustSize() only when glyph width changes
        self.adjustSize()
        self.update()

    def fontChanged(self):
        self.setGlyph(self._glyph)

    # ---------------
    # Display Control
    # ---------------

    def drawingAttribute(self, attr, layerName):
        if layerName is None:
            return self._fallbackDrawingAttributes.get(attr)
        d = self._layerDrawingAttributes.get(layerName, {})
        return d.get(attr)

    def setDrawingAttribute(self, attr, value, layerName):
        if layerName is None:
            self._fallbackDrawingAttributes[attr] = value
        else:
            if layerName not in self._layerDrawingAttributes:
                self._layerDrawingAttributes[layerName] = {}
            self._layerDrawingAttributes[layerName][attr] = value
        self.update()

    def showFill(self):
        return self.drawingAttribute("showGlyphFill", None)

    def setShowFill(self, value):
        self.setDrawingAttribute("showGlyphFill", value, None)

    def showStroke(self):
        return self.drawingAttribute("showGlyphStroke", None)

    def setShowStroke(self, value):
        self.setDrawingAttribute("showGlyphStroke", value, None)

    def showMetrics(self):
        return self.drawingAttribute("showGlyphMargins", None)

    def setShowMetrics(self, value):
        self.setDrawingAttribute("showGlyphMargins", value, None)
        self.setDrawingAttribute("showFontVerticalMetrics", value, None)

    def showImage(self):
        return self.drawingAttribute("showGlyphImage", None)

    def setShowImage(self, value):
        self.setDrawingAttribute("showGlyphImage", value, None)

    def showMetricsTitles(self):
        return self.drawingAttribute("showFontVerticalMetricsTitles", None)

    def setShowMetricsTitles(self, value):
        self.setDrawingAttribute("showFontVerticalMetricsTitles", value, None)

    def showOnCurvePoints(self):
        return self.drawingAttribute("showGlyphOnCurvePoints", None)

    def setShowOnCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphStartPoints", value, None)
        self.setDrawingAttribute("showGlyphOnCurvePoints", value, None)

    def showOffCurvePoints(self):
        return self.drawingAttribute("showGlyphOffCurvePoints", None)

    def setShowOffCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphOffCurvePoints", value, None)

    def showPointCoordinates(self):
        return self.drawingAttribute("showGlyphPointCoordinates", None)

    def setShowPointCoordinates(self, value):
        self.setDrawingAttribute("showGlyphPointCoordinates", value, None)

    def showAnchors(self):
        return self.drawingAttribute("showGlyphAnchors", None)

    def setShowAnchors(self, value):
        self.setDrawingAttribute("showGlyphAnchors", value, None)

    def showBlues(self):
        return self.drawingAttribute("showFontPostscriptBlues", None)

    def setShowBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptBlues", value, None)

    def showFamilyBlues(self):
        return self.drawingAttribute("showFontPostscriptFamilyBlues", None)

    def setShowFamilyBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptFamilyBlues", value, None)

    def backgroundColor(self):
        return self._backgroundColor

    def setBackgroundColor(self, color):
        self._backgroundColor = color

    # ---------------
    # Drawing helpers
    # ---------------

    def drawImage(self, painter, glyph, layerName):
        drawing.drawGlyphImage(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawBlues(self, painter, glyph, layerName):
        drawing.drawFontPostscriptBlues(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawFamilyBlues(self, painter, glyph, layerName):
        drawing.drawFontPostscriptFamilyBlues(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawVerticalMetrics(self, painter, glyph, layerName):
        drawText = self._impliedPointSize > 175
        drawing.drawFontVerticalMetrics(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawText=drawText)

    def drawMargins(self, painter, glyph, layerName):
        drawing.drawGlyphMargins(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawFillAndStroke(self, painter, glyph, layerName):
        showFill = self.drawingAttribute("showGlyphFill", layerName)
        showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawFill=showFill, drawStroke=showStroke)

    def drawPoints(self, painter, glyph, layerName):
        drawStartPoints = self.drawingAttribute(
            "showGlyphStartPoints", layerName) and self._impliedPointSize > 175
        drawOnCurves = self.drawingAttribute(
            "showGlyphOnCurvePoints", layerName) and \
            self._impliedPointSize > 175
        drawOffCurves = self.drawingAttribute(
            "showGlyphOffCurvePoints", layerName) and \
            self._impliedPointSize > 175
        drawCoordinates = self.drawingAttribute(
            "showGlyphPointCoordinates", layerName) and \
            self._impliedPointSize > 250
        drawing.drawGlyphPoints(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawStartPoints=drawStartPoints, drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=Qt.white)

    def drawAnchors(self, painter, glyph, layerName):
        if not self._impliedPointSize > 175:
            return
        drawing.drawGlyphAnchors(
            painter, glyph, self._inverseScale, self._drawingRect)

    # ---------------
    # QWidget methods
    # ---------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(UIFont)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # draw the background
        painter.fillRect(rect, self._backgroundColor)
        if self._glyph is None:
            return

        # apply the overall scale
        painter.save()
        # + translate and flip
        painter.translate(0, self.height())
        painter.scale(self._scale, -self._scale)

        # move into position
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        painter.translate(-xOffsetInv, -yOffsetInv)

        # gather the layers
        layerSet = self._glyph.layerSet
        if layerSet is None:
            layers = [(self._glyph, None)]
        else:
            glyphName = self._glyph.name
            layers = []
            for layerName in reversed(layerSet.layerOrder):
                layer = layerSet[layerName]
                if glyphName not in layer:
                    continue
                glyph = layer[glyphName]
                if glyph == self._glyph:
                    layerName = None
                layers.append((glyph, layerName))

        for glyph, layerName in layers:
            # draw the image
            if self.drawingAttribute("showGlyphImage", layerName):
                self.drawImage(painter, glyph, layerName)
            # draw the blues
            if layerName is None and self.drawingAttribute(
                    "showFontPostscriptBlues", None):
                self.drawBlues(painter, glyph, layerName)
            if layerName is None and self.drawingAttribute(
                    "showFontPostscriptFamilyBlues", None):
                self.drawFamilyBlues(painter, glyph, layerName)
            # draw the margins
            if self.drawingAttribute("showGlyphMargins", layerName):
                self.drawMargins(painter, glyph, layerName)
            # draw the vertical metrics
            if layerName is None and self.drawingAttribute(
                    "showFontVerticalMetrics", None):
                self.drawVerticalMetrics(painter, glyph, layerName)
            # draw the glyph
            if self.drawingAttribute("showGlyphFill", layerName) or \
                    self.drawingAttribute("showGlyphStroke", layerName):
                self.drawFillAndStroke(painter, glyph, layerName)
            if self.drawingAttribute("showGlyphOnCurvePoints", layerName) or \
                    self.drawingAttribute("showGlyphOffCurvePoints",
                                          layerName):
                self.drawPoints(painter, glyph, layerName)
            if self.drawingAttribute("showGlyphAnchors", layerName):
                self.drawAnchors(painter, glyph, layerName)
        painter.restore()

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        # pick the width and height
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphWidth = glyphWidth * self._scale
        glyphHeight = glyphHeight * self._scale
        xOffset = 1000 * 2 * self._scale
        yOffset = xOffset
        width = glyphWidth + xOffset
        height = glyphHeight + yOffset
        # calculate and store the vertical centering offset
        maxHeight = max(height, self.height())
        self._verticalCenterYBuffer = (maxHeight - glyphHeight) / 2.0
        # calculate and store the drawing rect
        diff = width - glyphWidth
        xOffset = round((diff / 2) * self._inverseScale)
        yOffset = self._verticalCenterYBuffer * self._inverseScale
        yOffset -= self._descender
        w = width * self._inverseScale
        h = height * self._inverseScale
        self._drawingRect = (-xOffset, -yOffset, w, h)
        return QSize(width, height)

    def showEvent(self, event):
        super().showEvent(event)
        self.fitScaleBBox()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = pow(1.2, event.angleDelta().y() / 120.0)
            oldScale = self._scale
            newScale = self._scale * factor
            if newScale < 1e-2 or newScale > 1e3:
                return
            if self._scrollArea is not None:
                # compute new scrollbar position
                # http://stackoverflow.com/a/32269574/2037879
                hSB = self._scrollArea.horizontalScrollBar()
                vSB = self._scrollArea.verticalScrollBar()
                pos = event.pos()
                scrollBarPos = QPointF(hSB.value(), vSB.value())
                deltaToPos = (self.mapToParent(pos) - self.pos()) / oldScale
                delta = deltaToPos * (newScale - oldScale)
            self.setScale(newScale)
            self.update()
            if self._scrollArea is not None:
                hSB.setValue(scrollBarPos.x() + delta.x())
                vSB.setValue(scrollBarPos.y() + delta.y())
        else:
            super().wheelEvent(event)


class GlyphView(QScrollArea):
    glyphWidgetClass = GlyphWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self._glyphWidget = self.glyphWidgetClass(self)
        self._glyphWidget.setScrollArea(self)

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.font
            if font is not None:
                font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyph(self):
        if self._glyphWidget is not None:
            glyph = self._glyphWidget.glyph()
            if glyph is not None:
                glyph.removeObserver(self, "Glyph.Changed")
                font = glyph.font
                if font is not None:
                    font.info.removeObserver(self, "Info.Changed")

    def _glyphChanged(self, notification):
        self._glyphWidget.glyphChanged()

    def _fontChanged(self, notification):
        self._glyphWidget.fontChanged()

    # --------------
    # Public Methods
    # --------------

    def glyph(self):
        return self._glyphWidget.glyph()

    def setGlyph(self, glyph):
        self._unsubscribeFromGlyph()
        self._subscribeToGlyph(glyph)
        self._glyphWidget.setGlyph(glyph)

    def drawingAttribute(self, attr, layerName=None):
        return self._glyphWidget.drawingAttribute(attr, layerName)

    def setDrawingAttribute(self, attr, value, layerName=None):
        self._glyphWidget.setDrawingAttribute(attr, value, layerName)

    # convenience

    def showFill(self):
        return self.drawingAttribute("showGlyphFill")

    def setShowFill(self, value):
        self.setDrawingAttribute("showGlyphFill", value)

    def showStroke(self):
        return self.drawingAttribute("showGlyphStroke")

    def setShowStroke(self, value):
        self.setDrawingAttribute("showGlyphStroke", value)

    def showMetrics(self):
        return self.drawingAttribute("showGlyphMargins")

    def setShowMetrics(self, value):
        self.setDrawingAttribute("showGlyphMargins", value)
        self.setDrawingAttribute("showFontVerticalMetrics", value)
        self.setDrawingAttribute("showFontVerticalMetricsTitles", value)

    def showImage(self):
        return self.drawingAttribute("showGlyphImage")

    def setShowImage(self, value):
        self.setDrawingAttribute("showGlyphImage", value)

    def showOnCurvePoints(self):
        return self.drawingAttribute("showGlyphOnCurvePoints")

    def setShowOnCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphOnCurvePoints", value)

    def showOffCurvePoints(self):
        return self.drawingAttribute("showGlyphOffCurvePoints")

    def setShowOffCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphOffCurvePoints", value)

    def showPointCoordinates(self):
        return self.drawingAttribute("showGlyphPointCoordinates")

    def setShowPointCoordinates(self, value):
        self.setDrawingAttribute("showGlyphPointCoordinates", value)

    def showAnchors(self):
        return self.drawingAttribute("showGlyphAnchors")

    def setShowAnchors(self, value):
        self.setDrawingAttribute("showGlyphAnchors", value)

    def showBlues(self):
        return self.drawingAttribute("showFontPostscriptBlues")

    def setShowBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptBlues", value)

    def showFamilyBlues(self):
        return self.drawingAttribute("showFontPostscriptFamilyBlues")

    def setShowFamilyBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptFamilyBlues", value)

    def backgroundColor(self):
        return self._glyphWidget.backgroundColor()

    def setBackgroundColor(self, color):
        self._glyphWidget.setBackgroundColor(color)
