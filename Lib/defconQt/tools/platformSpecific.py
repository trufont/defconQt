"""
The *platformSpecific* submodule
--------------------------------

While most of the time Qt abstracts any platform difference transparently,
there are times where it explicitly chooses not to (for instance, the Enter key
on Windows corresponds to the Return key on OSX) so to leave control to the
user.

All such occurrences are stored in the *platformSpecific* submodule to make
such code obvious and self-contained.

Fear not, these occurrences are rather anecdotic as you may tell from the size
of this file.
"""
from __future__ import absolute_import
from PyQt5.QtGui import QFont, QFontDatabase
import sys

# -----
# Fonts
# -----


def fixedFont():
    """
    Returns a default fixed-pitch QFont_ for each supported platform.

    Returns "Consolas" instead of the default "Courier New" on Windows.

    TODO: test more

    .. _QFont: http://doc.qt.io/qt-5/qfont.html
    """
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    if sys.platform == "win32":
        # pick Consolas instead of Courier New
        font.setFamily("Consolas")
        font.setPointSize(11)
    return font


def otherUIFont():
    """
    Returns an auxiliary UI font.
    """
    font = QFont('Lucida Sans Unicode')
    font.insertSubstitution('Lucida Sans Unicode', 'Lucida Grande')
    font.insertSubstitution('Lucida Sans Unicode', 'Luxi Sans')
    if sys.platform == "darwin":
        pointSize = 11
    else:
        pointSize = 8
    font.setPointSize(pointSize)
    return font
