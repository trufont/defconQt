"""
The *glyphSequenceEdit* submodule
-----------------------------

The *glyphSequenceEdit* submodule provides a QLineEdit_ widget that besides its
text string can return a list of Glyph_ from the font specified in its
constructor.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
.. _QLineEdit: http://doc.qt.io/qt-5/qlineedit.html
"""
from defconQt.tools.textSplitter import (
    characterToGlyphName, compileStack, escapeText, splitText)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QCompleter, QLineEdit


def _glyphs(self):
    text = self.text()
    glyphNames = self.splitTextFunction(
        text, self._font.unicodeData)
    glyphs = [self._font[glyphName] for glyphName in glyphNames
              if glyphName in self._font]
    return glyphs


class GlyphSequenceComboBox(QComboBox):
    splitTextFunction = staticmethod(splitText)

    def __init__(self, font, parent=None):
        super().__init__(parent)
        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseSensitive)
        self.setCompleter(completer)
        self.setEditable(True)
        self._font = font

    glyphs = _glyphs

    def text(self):
        return self.currentText()

    def setText(self, text):
        self.setEditText(text)


class GlyphSequenceEdit(QLineEdit):
    splitTextFunction = staticmethod(splitText)

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self._font = font

    glyphs = _glyphs
