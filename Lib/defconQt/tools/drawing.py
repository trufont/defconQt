# -*- coding: utf-8 -*-
"""
The *drawing* submodule
--------------------------------

The *drawing* submodule provides common drawing functions for glyph views.
It was adapted from defconAppKit and has similar APIs.

Notes:

- All drawing is done in font units
- The *scale* argument is the factor to scale a glyph unit to a view unit
- The *rect* argument is the rect that the glyph is being drawn in

"""
from __future__ import division, absolute_import
import math
from defcon import Color
from PyQt5.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QPainter, QPainterPath, QPen, QTransform)
from PyQt5.QtWidgets import QApplication

# ------
# Colors
# ------

_defaultColors = dict(

    # General
    # -------

    background=QColor(Qt.white),

    # Font
    # ----

    # vertical metrics
    fontVerticalMetrics=QColor.fromRgbF(.4, .4, .4, .5),
    fontPostscriptBlues=QColor.fromRgbF(.5, .7, 1, .3),
    fontPostscriptFamilyBlues=QColor.fromRgbF(1, 1, .5, .3),

    # guidelines
    fontGuideline=QColor.fromRgbF(1, 0, 0, .5),

    # Glyph
    # -----

    # margins
    glyphMarginsFill=QColor.fromRgbF(.5, .5, .5, .11),
    glyphMarginsStroke=QColor.fromRgbF(.7, .7, .7, .5),
    # contour fill
    glyphContourFill=QColor.fromRgbF(.85, .85, .85, .5),
    # contour stroke
    glyphContourStroke=QColor.fromRgbF(0, 0, 0, 1),
    # component fill
    glyphComponentFill=QColor.fromRgbF(0, 0, 0, .4),
    # component stroke
    glyphComponentStroke=QColor.fromRgbF(0, 0, 0, 1),
    # points
    glyphOnCurvePoints=QColor(4, 100, 166, 190),
    glyphOtherPoints=QColor.fromRgbF(.6, .6, .6, 1),
    # anchors
    glyphAnchor=QColor(228, 96, 15, 200),
    # guidelines
    glyphGuideline=QColor.fromRgbF(.3, .4, .85, .5),
)


def colorToQColor(color):
    """
    Returns the QColor_ that corresponds to the defcon Color_ *color*.

    TODO: Color lacks online documentation.

    .. _Color: https://github.com/typesupply/defcon/blob/ufo3/Lib/defcon/objects/color.py
    .. _QColor: http://doc.qt.io/qt-5/qcolor.html
    """
    r, g, b, a = Color(color)
    return QColor.fromRgbF(r, g, b, a)


def defaultColor(name):
    """
    Returns a fallback QColor_ for a given *name*.

    TODO: name list?

    .. _QColor: http://doc.qt.io/qt-5/qcolor.html
    """
    return _defaultColors[name]

# ----------
# Primitives
# ----------


def drawLine(painter, x1, y1, x2, y2, lineWidth=0):
    """
    Draws a line from *(x1, y1)* to *(x2, y2)* with a thickness of *lineWidth*
    and using QPainter_ *painter*.

    Compared to the built-in ``painter.drawLine(…)`` method, this will disable
    antialiasing for horizontal/vertical lines.

    .. _`cosmetic pen`: http://doc.qt.io/qt-5/qpen.html#isCosmetic
    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    painter.save()
    if x1 == x2 or y1 == y2:
        painter.setRenderHint(QPainter.Antialiasing, False)
    pen = painter.pen()
    pen.setWidthF(lineWidth)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()


def drawTextAtPoint(painter, text, x, y, scale, xAlign="left", yAlign="bottom",
                    flipped=True):
    """
    Draws *text* at *(x, y)* with scale *scale* and a given QPainter_.

    - *xAlign* may be "left", "center" or "right" and specifies the alignment
      of the text (left-aligned text is painted to the right of *x*)
    - *yAlign* may be "top", "center" or "bottom" and specifies the y-positing
      of the text block relative to *y*

    TODO: support LTR http://stackoverflow.com/a/24831796/2037879

    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    fM = painter.fontMetrics()
    lines = text.splitlines()
    lineSpacing = fM.lineSpacing()
    if xAlign != "left" or yAlign != "bottom":
        width = scale * max(fM.width(line) for line in lines)
        height = scale * len(lines) * lineSpacing
        if xAlign == "center":
            x -= width / 2
        elif xAlign == "right":
            x -= width
        if yAlign == "center":
            y += height / 2
        elif yAlign == "top":
            y += height
    painter.save()
    if flipped:
        s = -scale
        height = fM.ascent() * scale
        y -= height
    else:
        s = scale
    painter.translate(x, y)
    painter.scale(scale, s)
    for line in lines:
        painter.drawText(0, 0, line)
        painter.translate(0, lineSpacing)
    painter.restore()

# ----
# Font
# ----

# Vertical Metrics


def drawFontVerticalMetrics(painter, glyph, scale, rect, drawLines=True,
                            drawText=True, color=None):
    """
    Draws vertical metrics of the Glyph_ *glyph* (ascender, descender,
    baseline, x-height, cap height) in the form of lines if *drawLines* is true
    and text if *drawText* is true using QPainter_ *painter*.

    *rect* specifies the rectangle which the lines will be drawn in (usually,
    that of the glyph’s advance width).

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    font = glyph.font
    if font is None:
        return
    if color is None:
        color = defaultColor("fontVerticalMetrics")
    painter.save()
    painter.setPen(color)
    # gather y positions
    toDraw = [
        (QApplication.translate("drawing", "Descender"),
            font.info.descender),
        (QApplication.translate("drawing", "Baseline"), 0),
        (QApplication.translate("drawing", "x-height"),
            font.info.xHeight),
        (QApplication.translate("drawing", "Cap height"),
            font.info.capHeight),
        (QApplication.translate("drawing", "Ascender"),
            font.info.ascender),
    ]
    positions = {}
    for name, position in toDraw:
        if position is None:
            continue
        if position not in positions:
            positions[position] = []
        positions[position].append(name)
    # create lines
    xMin = rect[0]
    xMax = xMin + rect[2]
    lines = []
    for y, names in positions.items():
        names = ", ".join(names)
        if y != 0:
            names = "%s (%d)" % (names, y)
        lines.append((y, names))
    # draw lines
    if drawLines:
        for y, names in lines:
            drawLine(painter, xMin, y, xMax, y)
    # draw text
    if drawText:
        fontSize = 9
        x = glyph.width + 6 * scale
        for y, text in lines:
            y -= (fontSize / 3.5) * scale
            drawTextAtPoint(painter, text, x, y, scale)
    painter.restore()

# Guidelines


def drawFontGuidelines(painter, glyph, scale, rect, drawLines=True,
                       drawText=True, color=None):
    """
    Draws the font guidelines of the Glyph_ *glyph* in the form of lines if
    *drawLines* is true and text if *drawText* is true using QPainter_
    *painter*.

    *rect* specifies the rectangle which the lines will be drawn in (usually,
    that of the glyph’s advance width).

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    if not (drawLines or drawText):
        return
    font = glyph.font
    if font is None:
        return
    if color is None:
        color = defaultColor("fontGuideline")
    _drawGuidelines(painter, glyph, scale, rect, font.guidelines, color=color)


def drawGlyphGuidelines(painter, glyph, scale, rect, drawLines=True,
                        drawText=True, color=None):
    if not (drawLines or drawText):
        return
    if color is None:
        color = defaultColor("glyphGuideline")
    _drawGuidelines(painter, glyph, scale, rect, glyph.guidelines, color=color)


def _drawGuidelines(painter, glyph, scale, rect, guidelines, drawLines=True,
                    drawText=True, color=None):
    if not (drawLines or drawText):
        return
    xMin, yMin, width, height = rect
    xMax = xMin + width
    yMax = yMin + height
    fontSize = 9
    for line in guidelines:
        color_ = color
        if color_ is None:
            if line.color:
                color_ = colorToQColor(line.color)
            else:
                color_ = defaultColor("glyphGuideline")
        painter.save()
        painter.setPen(color)
        line1 = None
        if None not in (line.x, line.y):
            if line.angle is not None:
                # make an infinite line that intersects *(line.x, line.y)*
                # 1. make horizontal line from *(line.x, line.y)* of length *diagonal*
                diagonal = math.sqrt(width**2 + height**2)
                line1 = QLineF(line.x, line.y, line.x + diagonal, line.y)
                # 2. set the angle
                # defcon guidelines are clockwise
                line1.setAngle(line.angle)
                # 3. reverse the line and set length to 2 * *diagonal*
                line1.setPoints(line1.p2(), line1.p1())
                line1.setLength(2 * diagonal)
            else:
                line1 = QLineF(xMin, line.y, xMax, line.y)
        textX = 0
        textY = 0
        if drawLines:
            if line1 is not None:
                # line
                drawLine(painter, line1.x1(), line1.y1(), line1.x2(), line1.y2())
                # point
                x, y = line.x, line.y
                smoothWidth = 8 * scale
                smoothHalf = smoothWidth / 2.0
                painter.save()
                pointPath = QPainterPath()
                x -= smoothHalf
                y -= smoothHalf
                pointPath.addEllipse(x, y, smoothWidth, smoothWidth)
                pen = QPen(color_)
                pen.setWidthF(1 * scale)
                painter.setPen(pen)
                painter.drawPath(pointPath)
                painter.restore()
            else:
                if line.y is not None:
                    drawLine(painter, xMin, line.y, xMax, line.y)
                elif line.x is not None:
                    drawLine(painter, line.x, yMin, line.x, yMax)
        if drawText and line.name:
            if line1 is not None:
                textX = line.x
                textY = line.y - 6 * scale
                xAlign = "center"
            else:
                if line.y is not None:
                    textX = glyph.width + 6 * scale
                    textY = line.y - (fontSize / 3.5) * scale
                elif line.x is not None:
                    textX = line.x + 6 * scale
                    textY = 0
                xAlign = "left"
            drawTextAtPoint(
                painter, line.name, textX, textY, scale, xAlign=xAlign)
        painter.restore()

# Blues


def drawFontPostscriptBlues(painter, glyph, scale, rect, color=None):
    """
    Draws a Glyph_ *glyph*’s blue values.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    font = glyph.font
    if font is None:
        return
    blues = []
    if font.info.postscriptBlueValues:
        blues += font.info.postscriptBlueValues
    if font.info.postscriptOtherBlues:
        blues += font.info.postscriptOtherBlues
    if not blues:
        return
    if color is None:
        color = defaultColor("fontPostscriptBlues")
    _drawBlues(painter, blues, rect, color)


def drawFontPostscriptFamilyBlues(painter, glyph, scale, rect, color=None):
    """
    Draws a Glyph_ *glyph*’s family blue values.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    font = glyph.font
    if font is None:
        return
    blues = []
    if font.info.postscriptFamilyBlues:
        blues += font.info.postscriptFamilyBlues
    if font.info.postscriptFamilyOtherBlues:
        blues += font.info.postscriptFamilyOtherBlues
    if not blues:
        return
    if color is None:
        color = defaultColor("fontPostscriptFamilyBlues")
    _drawBlues(painter, blues, rect, color)


def _drawBlues(painter, blues, rect, color):
    x = rect[0]
    w = rect[2]
    for yMin, yMax in zip(blues[::2], blues[1::2]):
        painter.fillRect(x, yMin, w, yMax - yMin, color)

# Image


def drawGlyphImage(painter, glyph, scale, rect):
    """
    Draws a Glyph_ *glyph*’s image.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    image = glyph.image
    pixmap = image.getRepresentation("defconQt.QPixmap")
    if pixmap is None:
        return
    painter.save()
    painter.setTransform(QTransform(*image.transformation), True)
    painter.translate(0, pixmap.height())
    painter.scale(1, -1)
    painter.drawPixmap(0, 0, pixmap)
    painter.restore()

# Margins


def drawGlyphMargins(painter, glyph, scale, rect, drawFill=True,
                     drawStroke=True, fillColor=None, strokeColor=None):
    """
    Draws a Glyph_ *glyph*’s margins, i.e. rectangles that stand beside the
    glyph’s sidebearings.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    if fillColor is None:
        fillColor = defaultColor("glyphMarginsFill")
    if strokeColor is None:
        strokeColor = defaultColor("glyphMarginsStroke")
    x, y, w, h = rect
    painter.save()
    if drawFill:
        left = QRectF(x, y, -x, h)
        right = QRectF(glyph.width, y, w - glyph.width, h)
        for rect in (left, right):
            painter.fillRect(rect, fillColor)
    if drawStroke:
        painter.setPen(strokeColor)
        drawLine(painter, 0, y, 0, y + h)
        drawLine(painter, glyph.width, y, glyph.width, y + h)
    painter.restore()

# Fill and Stroke


def drawGlyphFillAndStroke(
        painter, glyph, scale, rect, drawFill=True, drawStroke=True,
        contourFillColor=None, contourStrokeColor=None,
        componentFillColor=None, componentStrokeColor=None, strokeWidth=1.0):
    """
    Draws a Glyph_ *glyph* contours’ fill and stroke.

    Component fill is always drawn, component stroke is drawn if
    *componentStrokeColor* is not None.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    # get the layer color
    layer = glyph.layer
    layerColor = None
    if layer is not None and layer.color is not None:
        layerColor = colorToQColor(layer.color)
    # get the paths
    contourPath = glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
    componentPath = glyph.getRepresentation(
        "defconQt.OnlyComponentsQPainterPath")
    painter.save()
    # fill
    if drawFill:
        # contours
        if contourFillColor is None and layerColor is not None:
            contourFillColor = layerColor
        elif contourFillColor is None and layerColor is None:
            contourFillColor = defaultColor("glyphContourFill")
        painter.fillPath(contourPath, QBrush(contourFillColor))
    # components
    if componentFillColor is None and layerColor is not None:
        componentFillColor = layerColor
    elif componentFillColor is None and layerColor is None:
        componentFillColor = defaultColor("glyphComponentFill")
    painter.fillPath(componentPath, QBrush(componentFillColor))
    # stroke
    if drawStroke:
        # work out the color
        if contourStrokeColor is None and layerColor is not None:
            contourStrokeColor = layerColor
        elif contourStrokeColor is None and layerColor is None:
            contourStrokeColor = defaultColor("glyphContourStroke")
        # contours
        pen = QPen(contourStrokeColor)
        pen.setWidthF(strokeWidth * scale)
        painter.setPen(pen)
        painter.drawPath(contourPath)
    # components
    if componentStrokeColor is not None:
        pen = QPen(componentStrokeColor)
        pen.setWidthF(strokeWidth * scale)
        painter.setPen(pen)
        painter.drawPath(componentPath)
    painter.restore()

# points


def drawGlyphPoints(
        painter, glyph, scale, rect,
        drawStartPoints=True, drawOnCurves=True, drawOffCurves=True,
        drawCoordinates=False, onCurveColor=None,
        otherColor=None, backgroundColor=None):
    """
    Draws a Glyph_ *glyph*’s points.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    if onCurveColor is None:
        layer = glyph.layer
        if layer is not None and layer.color is not None:
            onCurveColor = colorToQColor(layer.color)
        else:
            onCurveColor = defaultColor("glyphOnCurvePoints")
    if otherColor is None:
        otherColor = defaultColor("glyphOtherPoints")
    if backgroundColor is None:
        backgroundColor = defaultColor("background")
    # get the outline data
    outlineData = glyph.getRepresentation("defconQt.OutlineInformation")
    points = []
    # start points
    if drawStartPoints and outlineData["startPoints"]:
        startWidth = startHeight = 15 * scale
        startHalf = startWidth / 2.0
        path = QPainterPath()
        for point, angle in outlineData["startPoints"]:
            x, y = point
            if angle is not None:
                path.moveTo(x, y)
                path.arcTo(x - startHalf, y - startHalf, startWidth,
                           startHeight, 180 - angle, 180)
                path.closeSubpath()
            else:
                path.addEllipse(
                    x - startHalf, y - startHalf, startWidth, startHeight)
        startPointColor = QColor(otherColor)
        aF = startPointColor.alphaF()
        startPointColor.setAlphaF(aF * .3)
        painter.fillPath(path, startPointColor)
    # handles
    if drawOffCurves and outlineData["offCurvePoints"]:
        painter.save()
        painter.setPen(otherColor)
        for pt1, pt2 in outlineData["bezierHandles"]:
            x1, y1 = pt1
            x2, y2 = pt2
            # TODO: should lineWidth account scale by default
            drawLine(painter, x1, y1, x2, y2, 1.0 * scale)
        painter.restore()
    # on curve
    if drawOnCurves and outlineData["onCurvePoints"]:
        width = 7 * scale
        half = width / 2.0
        smoothWidth = 8 * scale
        smoothHalf = smoothWidth / 2.0
        painter.save()
        path = QPainterPath()
        for point in outlineData["onCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            pointPath = QPainterPath()
            if point["smooth"]:
                x -= smoothHalf
                y -= smoothHalf
                pointPath.addEllipse(x, y, smoothWidth, smoothWidth)
            else:
                x -= half
                y -= half
                pointPath.addRect(x, y, width, width)
            path.addPath(pointPath)
        pen = QPen(onCurveColor)
        pen.setWidthF(1.5 * scale)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.restore()
    # off curve
    if drawOffCurves and outlineData["offCurvePoints"]:
        # points
        offWidth = 5 * scale
        offHalf = offWidth / 2.0
        path = QPainterPath()
        for point in outlineData["offCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            pointPath = QPainterPath()
            x -= offHalf
            y -= offHalf
            pointPath.addEllipse(x, y, offWidth, offWidth)
            path.addPath(pointPath)
        pen = QPen(otherColor)
        pen.setWidthF(3.0 * scale)
        painter.save()
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(backgroundColor))
        painter.restore()
    # coordinates
    if drawCoordinates:
        otherColor = QColor(otherColor)
        otherColor.setAlphaF(otherColor.alphaF() * .6)
        painter.save()
        painter.setPen(otherColor)
        for x, y in points:
            posX = x
            # TODO: We use + here because we align on top. Consider abstracting
            # yOffset.
            posY = y + 3
            x = round(x, 1)
            if int(x) == x:
                x = int(x)
            y = round(y, 1)
            if int(y) == y:
                y = int(y)
            text = "%d  %d" % (x, y)
            drawTextAtPoint(painter, text, posX, posY, scale,
                            xAlign="center", yAlign="top")
        painter.restore()

# Anchors


def drawGlyphAnchors(painter, glyph, scale, rect, drawAnchors=True,
                     drawText=True, color=None):
    """
    Draws a Glyph_ *glyph*’s anchors.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    if not glyph.anchors:
        return
    if color is None:
        color = defaultColor("glyphAnchor")
    fallbackColor = color
    anchorSize = 6 * scale
    anchorHalfSize = anchorSize / 2
    for anchor in glyph.anchors:
        if anchor.color is not None:
            color = colorToQColor(anchor.color)
        else:
            color = fallbackColor
        x = anchor.x
        y = anchor.y
        name = anchor.name
        painter.save()
        if drawAnchors:
            path = QPainterPath()
            path.addEllipse(x - anchorHalfSize, y - anchorHalfSize,
                            anchorSize, anchorSize)
            painter.fillPath(path, color)
        if drawText and name:
            painter.setPen(color)
            # TODO: we're using + before we shift to top, ideally this should
            # be abstracted w drawTextAtPoint taking a dy parameter that will
            # offset the drawing region from origin regardless of whether we
            # are aligning to top or bottom.
            y += 3 * scale
            drawTextAtPoint(painter, name, x, y, scale,
                            xAlign="center", yAlign="top")
        painter.restore()
