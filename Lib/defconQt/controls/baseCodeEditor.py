"""
The *baseCodeEditor* submodule
------------------------------

The *baseCodeEditor* submodule provides language-agnostic code editor parts,
including a search widget, goto dialog and code highlighter.
"""
from defconQt.tools import platformSpecific
from PyQt5.QtCore import pyqtSignal, QRegularExpression, QSize, Qt
from PyQt5.QtGui import (
    QColor, QIntValidator, QPainter, QSyntaxHighlighter, QTextCursor)
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QLineEdit, QPlainTextEdit, QVBoxLayout,
    QWidget)
import re

__all__ = ["GotoLineDialog", "BaseCodeHighlighter", "BaseCodeEditor"]

# -------------------
# Search/Jump dialogs
# -------------------


# TODO: search widget


class GotoLineDialog(QDialog):
    """
    A QDialog_ that asks for a line number to the user.

    The result may be passed to the :func:`scrollToLine` function of
    :class:`BaseCodeEditor`.

    .. _QDialog: http://doc.qt.io/qt-5/qdialog.html
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Go to…"))

        self.lineEdit = QLineEdit(self)
        validator = QIntValidator(self)
        validator.setMinimum(1)
        self.lineEdit.setValidator(validator)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.lineEdit)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    @classmethod
    def getLineNumber(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        newLine = dialog.lineEdit.text()
        if newLine is not None:
            newLine = int(newLine)
        return (newLine, result)

# ------------
# Line numbers
# ------------


class LineNumberArea(QWidget):

    def __init__(self, editor):
        super().__init__(editor)

    def sizeHint(self):
        return QSize(self.parent().lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.parent().lineNumberAreaPaintEvent(event)

# ----------------
# Syntax highlight
# ----------------


class BaseCodeHighlighter(QSyntaxHighlighter):
    """
    A QSyntaxHighlighter_ that highlights code using QRegularExpression_
    (perl regexes).
    Append a tuple of (pattern, format) to the *highlightingRules* attribute to
    get started.

    - *pattern*: a string describing a regex.
    - *format*: a QTextCharFormat_ describing text formatting for the given
      block.

    .. _QRegularExpression: http://doc.qt.io/qt-5/qregularexpression.html
    .. _QSyntaxHighlighter: http://doc.qt.io/qt-5/qsyntaxhighlighter.html
    .. _QTextCharFormat: http://doc.qt.io/qt-5/qtextcharformat.html
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []

    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            regex = QRegularExpression(pattern)
            i = regex.globalMatch(text)
            while i.hasNext():
                match = i.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
        self.setCurrentBlockState(0)


# -------------------
# Whitespace Guessing
# -------------------

_whitespaceRE = re.compile("([ \t]+)")


def _guessMinWhitespace(text):
    # gather all whitespace at the beginning of a line
    whitespace = set()
    for line in text.splitlines():
        # skip completely blank lines
        if not line.strip():
            continue
        # store the found whitespace
        m = _whitespaceRE.match(line)
        if m is not None:
            whitespace.add(m.group(1))
    # if nothing was found, fallback to four spaces
    if not whitespace:
        return "    "
    # get the smallest whitespace increment
    whitespace = min(whitespace)
    # if the whitespace starts with a tab, use a single tab
    if whitespace.startswith("\t"):
        return "\t"
    # use what was found
    return whitespace


class BaseCodeEditor(QPlainTextEdit):
    """
    A language-agnostic, abstract code editor. Displays line numbers and
    supports arbitrary indent pattern (Tab/Alt+Tab will add/remove indent,
    Return keeps indent).

    - *indent*: the basic indent pattern. 4-spaces by default.
    - *lineNumbersVisible*: whether line numbers are displayed. True by
      default.
    - *openBlockDelimiter*: a string that indicates a new block. If set, this
      will add an additional level of indent if Return key is pressed after
      such string. None by default.
    - *shouldGuessWhiteSpace*: whether whitespace should be inferred when
      :func:`setPlainText` is called.
    """
    openBlockDelimiter = None
    indentChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(platformSpecific.fixedFont())
        self._indent = "    "
        self._lineNumbersVisible = True
        self._shouldGuessWhitespace = True

        self.lineNumbers = LineNumberArea(self)
        # kick-in geometry update before arming signals
        self.updateLineNumberAreaWidth()
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

    # --------------
    # Custom methods
    # --------------

    def indent(self):
        """
        Returns this widget’s indent pattern.
        """
        return self._indent

    def setIndent(self, indent):
        """
        Sets this widget’s atomic indent pattern to the string *indent*.

        The default is four spaces.
        """
        if self._indent == indent:
            return
        self._indent = indent
        self.indentChanged.emit()

    def lineNumbersVisible(self):
        """
        Returns whether line numbers are displayed.
        """
        return self._lineNumbersVisible

    def setLineNumbersVisible(self, value):
        """
        Sets whether line numbers should be displayed on the left margin.

        The default is true.
        """
        self._lineNumbersVisible = value
        self.lineNumbers.setVisible(value)
        self.updateLineNumberAreaWidth()

    def shouldGuessWhitespace(self):
        """
        Returns whether this widget infers whitespace when text is set.
        """
        return self._shouldGuessWhitespace

    def setShouldGuessWhitespace(self, value):
        """
        Sets whether this widget should infer whitespace when
        :func:`setPlainText` is called.

        The default is true.
        """
        self._shouldGuessWhitespace = value

    def scrollToLine(self, number):
        """
        Scrolls this widget’s viewport to the line *number* and sets the text
        cursor to that line.
        """
        self.moveCursor(QTextCursor.End)
        textBlock = self.document().findBlockByLineNumber(number - 1)
        self.setCursor(QTextCursor(textBlock))

    # ------------
    # Line numbers
    # ------------

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumbers)
        painter.fillRect(event.rect(), QColor(230, 230, 230))
        d = event.rect().topRight()
        a = event.rect().bottomRight()
        painter.setPen(Qt.darkGray)
        painter.drawLine(d.x(), d.y(), a.x(), a.y())
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(
                self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.drawText(4, top, self.lineNumbers.width() - 8,
                                 self.fontMetrics().height(), Qt.AlignRight,
                                 number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self):
        if not self._lineNumbersVisible:
            return 0
        digits = 1
        top = max(1, self.blockCount())
        while top >= 10:
            top /= 10
            digits += 1
        # Avoid too frequent geometry changes
        if digits < 3:
            digits = 3
        return 10 + self.fontMetrics().width('9') * digits

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumbers.scroll(0, dy)
        else:
            self.lineNumbers.update(0, rect.y(), self.lineNumbers.width(),
                                    rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def updateLineNumberAreaWidth(self, newBlockCount=None):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumbers.setGeometry(cr.left(), cr.top(),
                                     self.lineNumberAreaWidth(), cr.height())

    # ------------
    # Autocomplete
    # ------------

    def findLineIndentLevel(self, cursor=None):
        if cursor is None:
            cursor = self.textCursor()
        indent = 0
        cursor.select(QTextCursor.LineUnderCursor)
        lineLength = len(cursor.selectedText()) // len(self._indent)
        cursor.movePosition(QTextCursor.StartOfLine)
        while lineLength > 0:
            cursor.movePosition(QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor, len(self._indent))
            if cursor.selectedText() == self._indent:
                indent += 1
            else:
                break
            # Now move the anchor back to the position()
            # shouldn't NoMove work here?
            # cursor.movePosition(QTextCursor.NoMove)
            cursor.setPosition(cursor.position())
            lineLength -= 1
        cursor.movePosition(QTextCursor.EndOfLine)
        return indent

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            cursor = self.textCursor()
            indentLvl = self.findLineIndentLevel()
            if self.openBlockDelimiter is not None:
                cursor.movePosition(QTextCursor.PreviousCharacter,
                                    QTextCursor.KeepAnchor)
                if cursor.selectedText() == self.openBlockDelimiter:
                    indentLvl += 1
            super().keyPressEvent(event)
            newLineSpace = "".join(self._indent for _ in range(indentLvl))
            cursor = self.textCursor()
            cursor.insertText(newLineSpace)
        elif key == Qt.Key_Backspace or (
                key == Qt.Key_Tab and event.modifiers() & Qt.AltModifier):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.PreviousCharacter,
                                QTextCursor.KeepAnchor,
                                len(self._indent))
            if cursor.selectedText() == self._indent:
                cursor.removeSelectedText()
            else:
                super().keyPressEvent(event)
        elif key == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText(self._indent)
        else:
            super().keyPressEvent(event)

    # --------------
    # Other builtins
    # --------------

    def setPlainText(self, text):
        super().setPlainText(text)
        if self._shouldGuessWhitespace and text is not None:
            indent = _guessMinWhitespace(text)
            self.setIndent(indent)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            font = self.font()
            newPointSize = font.pointSize() + event.angleDelta().y() / 120.0
            if newPointSize < 6:
                return
            font.setPointSize(newPointSize)
            self.setFont(font)
        else:
            super().wheelEvent(event)
