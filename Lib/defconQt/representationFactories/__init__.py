from defcon import Glyph, Component, Image, registerRepresentationFactory
from defconQt.representationFactories.glyphCellFactory import (
    GlyphCellFactory)
from defconQt.representationFactories.glyphViewFactory import (
    NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory,
    ComponentQPainterPathFactory, OutlineInformationFactory, QPixmapFactory)
from defconQt.representationFactories.qPainterPathFactory import (
    QPainterPathFactory)

# TODO: add a glyph pixmap factory parametrized on glyph size
# TODO: fine-tune the destructive notifications
_glyphFactories = {
    "defconQt.QPainterPath": (QPainterPathFactory, None),
    "defconQt.NoComponentsQPainterPath": (
        NoComponentsQPainterPathFactory, None),
    "defconQt.OnlyComponentsQPainterPath": (
        OnlyComponentsQPainterPathFactory, None),
    "defconQt.GlyphCell": (GlyphCellFactory, None),
    "defconQt.OutlineInformation": (
        OutlineInformationFactory,
        ("Glyph.Changed", "Glyph.SelectionChanged")),
}
_componentFactories = {
    "defconQt.QPainterPath": (
        ComponentQPainterPathFactory, ("Component.Changed",
                                       "Component.BaseGlyphDataChanged")),
}
_imageFactories = {
    "defconQt.QPixmap": (
        QPixmapFactory, ("Image.FileNameChanged", "Image.ColorChanged",
                         "Image.ImageDataChanged"))
}


def registerAllFactories():
    for name, (factory, destructiveNotifications) in _glyphFactories.items():
        registerRepresentationFactory(
            Glyph, name, factory,
            destructiveNotifications=destructiveNotifications)
    for name, (factory, destructiveNotifications) in \
            _componentFactories.items():
        registerRepresentationFactory(
            Component, name, factory,
            destructiveNotifications=destructiveNotifications)
    for name, (factory, destructiveNotifications) in _imageFactories.items():
        registerRepresentationFactory(
            Image, name, factory,
            destructiveNotifications=destructiveNotifications)
