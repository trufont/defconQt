# -*- coding: utf-8 -*-
from __future__ import division, absolute_import
from defconQt.tools import drawing, platformSpecific
from defconQt.tools.drawing import colorToQColor
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import (
    QColor, QFontMetrics, QLinearGradient, QPainter, QPixmap)

GlyphCellHeaderHeight = 13
GlyphCellMinHeightForHeader = 40
GlyphCellMinHeightForMetrics = 90

cellHeaderBaseColor = QColor(230, 230, 230)
cellHeaderSidebearingsColor = QColor(240, 240, 240)
cellHeaderLineColor = QColor(170, 170, 170)
cellMetricsLineColor = QColor.fromRgbF(0, 0, 0, .08)
cellMetricsFillColor = QColor.fromRgbF(0, 0, 0, .08)

headerFont = platformSpecific.otherUIFont()

# TODO: allow top or bottom headers
# TODO: fine-tune dirty appearance
# TODO: show a symbol for content present on other layers


def GlyphCellFactory(glyph, width, height, drawLayers=False, drawMarkColor=True, drawHeader=None, drawMetrics=None, pixelRatio=1.0):
    if drawHeader is None:
        drawHeader = height >= GlyphCellMinHeightForHeader
    if drawMetrics is None:
        drawMetrics = height >= GlyphCellMinHeightForMetrics
    obj = GlyphCellFactoryDrawingController(glyph=glyph, font=glyph.font, width=width, height=height, drawLayers=False, drawMarkColor=drawMarkColor, drawHeader=drawHeader, drawMetrics=drawMetrics, pixelRatio=pixelRatio)
    return obj.getPixmap()


class GlyphCellFactoryDrawingController(object):
    """
    This draws the cell with the layers stacked in this order:

    ------------------
    header text
    ------------------
    header background
    ------------------
    foreground
    ------------------
    glyph
    ------------------
    vertical metrics
    ------------------
    horizontal metrics
    ------------------
    background
    ------------------

    Subclasses may override the layer drawing methods to customize
    the appearance of cells.
    """

    def __init__(self, glyph, font, width, height, pixelRatio=1.0,
                 drawLayers=False, drawMarkColor=True, drawHeader=True, drawMetrics=False):
        self.glyph = glyph
        self.font = font
        self.pixelRatio = pixelRatio
        self.width = width
        self.height = height
        self.bufferPercent = .15
        self.shouldDrawHeader = drawHeader
        self.shouldDrawLayers = drawLayers
        self.shouldDrawMarkColor = drawMarkColor
        self.shouldDrawMetrics = drawMetrics

        self.headerHeight = 0
        if drawHeader:
            self.headerHeight = GlyphCellHeaderHeight
        availableHeight = (height - self.headerHeight) * (
            1.0 - (self.bufferPercent * 2))
        descender = font.info.descender or -250
        unitsPerEm = font.info.unitsPerEm or 1000
        self.buffer = height * self.bufferPercent
        self.scale = availableHeight / unitsPerEm
        self.xOffset = (width - (glyph.width * self.scale)) / 2
        self.yOffset = abs(descender * self.scale) + self.buffer

    def getPixmap(self):
        pixmap = QPixmap(self.width * self.pixelRatio, self.height * self.pixelRatio)
        pixmap.setDevicePixelRatio(self.pixelRatio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(0, self.height)
        painter.scale(1, -1)
        bodyRect = (0, 0, self.width, self.height-self.headerHeight)
        headerRect = (0, 0, self.width, self.headerHeight)
        # background
        painter.save()
        painter.translate(0, self.height-self.headerHeight)
        painter.scale(1, -1)
        self.drawCellBackground(painter, bodyRect)
        painter.restore()
        # glyph
        if self.shouldDrawMetrics:
            self.drawCellHorizontalMetrics(painter, bodyRect)
            self.drawCellVerticalMetrics(painter, bodyRect)
        painter.save()
        painter.setClipRect(0, 0, self.width, self.height-self.headerHeight)
        painter.translate(self.xOffset, self.yOffset)
        painter.scale(self.scale, self.scale)
        self.drawCellGlyph(painter)
        painter.restore()
        # foreground
        painter.save()
        painter.translate(0, self.height-self.headerHeight)
        painter.scale(1, -1)
        self.drawCellForeground(painter, bodyRect)
        painter.restore()
        # header
        if self.shouldDrawHeader:
            painter.save()
            painter.translate(0, self.height)
            painter.scale(1, -1)
            self.drawCellHeaderBackground(painter, headerRect)
            self.drawCellHeaderText(painter, headerRect)
            painter.restore()
        return pixmap

    def drawCellBackground(self, painter, rect):
        if self.shouldDrawMarkColor:
            markColor = self.glyph.markColor
            if markColor is not None:
                color = colorToQColor(markColor)
                markGradient = QLinearGradient(
                    0, 0, 0, self.height - GlyphCellHeaderHeight)
                markGradient.setColorAt(1.0, color)
                markGradient.setColorAt(0.0, color.lighter(115))
                painter.fillRect(*(rect+(markGradient,)))

    def drawCellHorizontalMetrics(self, painter, rect):
        xMin, yMin, width, height = rect
        font = self.font
        scale = self.scale
        yOffset = self.yOffset
        lines = set((0, font.info.descender, font.info.xHeight,
                     font.info.capHeight, font.info.ascender))
        painter.setPen(cellMetricsLineColor)
        for y in lines:
            if y is None:
                continue
            y = round((y * scale) + yMin + yOffset)
            drawing.drawLine(painter, xMin, y, xMin + width, y)

    def drawCellVerticalMetrics(self, painter, rect):
        xMin, yMin, width, height = rect
        glyph = self.glyph
        scale = self.scale
        xOffset = self.xOffset
        left = round((0 * scale) + xMin + xOffset)
        right = round((glyph.width * scale) + xMin + xOffset)
        rects = [
            (xMin, yMin, left - xMin, height),
            (xMin + right, yMin, width - xMin + right, height)
        ]
        for rect in rects:
            painter.fillRect(*(rect+(cellMetricsFillColor,)))

    def drawCellGlyph(self, painter):
        if self.shouldDrawLayers:
            layers = self.font.layers
            for layerName in reversed(layers.layerOrder):
                layer = layers[layerName]
                if self.glyph.name not in layer:
                    continue
                layerColor = None
                if layer.color is not None:
                    layerColor = colorToQColor(layer.color)
                if layerColor is None:
                    layerColor = Qt.black
                glyph = layer[self.glyph.name]
                path = glyph.getRepresentation("defconQt.QPainterPath")
                painter.fillPath(path, layerColor)
        else:
            path = self.glyph.getRepresentation("defconQt.QPainterPath")
            painter.fillPath(path, Qt.black)

    def drawCellForeground(self, painter, rect):
        pass

    def drawCellHeaderBackground(self, painter, rect):
        xMin, yMin, width, height = rect
        # background
        baseColor = cellHeaderBaseColor
        sidebearingsColor = cellHeaderSidebearingsColor
        if self.glyph.dirty:
            baseColor = baseColor.darker(125)
            sidebearingsColor = sidebearingsColor.darker(110)
        painter.fillRect(xMin, yMin, width, height, baseColor)
        # sidebearings
        realPixel = 1 / self.pixelRatio
        painter.fillRect(QRectF(xMin, yMin, realPixel, height), sidebearingsColor)
        painter.fillRect(QRectF(
            xMin + width - 2 * realPixel, yMin, 2 * realPixel, height), sidebearingsColor)
        # bottom line
        y = yMin + height
        painter.setPen(cellHeaderLineColor)
        drawing.drawLine(painter, xMin, y, xMin + width, y)

    def drawCellHeaderText(self, painter, rect):
        xMin, yMin, width, height = rect
        metrics = QFontMetrics(headerFont)
        minOffset = painter.pen().width()

        painter.setFont(headerFont)
        painter.setPen(QColor(80, 80, 80))
        name = metrics.elidedText(
            self.glyph.name, Qt.ElideRight, width - 2)
        painter.drawText(
            1, 0, width - 2, height - minOffset,
            Qt.TextSingleLine | Qt.AlignCenter | Qt.AlignBottom, name)
