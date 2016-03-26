"""
The *glyphSequenceEdit* submodule
-----------------------------

The *glyphSequenceEdit* submodule provides a QLineEdit_ widget that besides its
text string can return a list of Glyph_ from the font specified in its
constructor.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
.. _QLineEdit: http://doc.qt.io/qt-5/qlineedit.html
"""
from defconQt.tools.textSplitter import splitText
from PyQt5.QtWidgets import QLineEdit


class GlyphSequenceEdit(QLineEdit):
    splitTextFunction = splitText

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self._font = font

    def glyphs(self):
        text = self.text()
        glyphNames = self.splitTextFunction(text, self._font.unicodeData)
        glyphs = [self._font[glyphName] for glyphName in glyphNames
                  if glyphName in self._font]
        return glyphs
