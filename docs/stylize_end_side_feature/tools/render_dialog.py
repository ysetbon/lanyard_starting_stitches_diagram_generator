"""Qt mockup of the proposed 'Stylize End Side' dialog, styled like the app's
WidthConfigDialog (light theme stylesheet, hand-built OK/Cancel buttons) with the
live preview drawn by the geometry prototype. Documentation helper only."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")
sys.argv = sys.argv[:1]
from end_styles import *  # noqa (creates the QApplication, imports Strand)
from end_styles import _stroked
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSlider, QSpinBox,
                             QCheckBox, QPushButton, QToolButton, QFrame, QButtonGroup, QSizePolicy, QWidget)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QIcon

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mockups'))
os.makedirs(OUT, exist_ok=True)

LIGHT = """
QDialog { background-color: #F5F5F5; color: black; }
QLabel { color: black; }
QSpinBox, QDoubleSpinBox, QSlider { background-color: white; color: black; border: 1px solid #CCC; border-radius: 3px; padding: 2px; min-height: 26px; }
QSpinBox:hover, QDoubleSpinBox:hover, QSlider:hover { border: 1px solid #999; }
QSlider::groove:horizontal { height: 6px; background: #DDD; border-radius: 3px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; background: #FFFFFF; border: 1px solid #888; border-radius: 7px; }
QSlider::sub-page:horizontal { background: #6E8FB5; border-radius: 3px; }
QPushButton, QDialogButtonBox QPushButton { background-color: #F0F0F0; color: #000000; border: 1px solid #BBBBBB; border-radius: 5px; padding: 10px; min-width: 80px; font-weight: bold; }
QPushButton:hover { background-color: #E0E0E0; }
QToolButton { background-color: #FFFFFF; color: black; border: 1px solid #CCC; border-radius: 5px; padding: 4px; }
QToolButton:checked { background-color: #DCE6F5; border: 2px solid #4A6FA5; }
QToolButton:hover { border: 1px solid #999; }
QCheckBox { color: black; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #888; border-radius: 3px; background: white; }
QCheckBox::indicator:checked { background: #4A6FA5; border: 1px solid #4A6FA5; }
QFrame#section { background-color: #FFFFFF; border: 1px solid #DDDDDD; border-radius: 6px; }
QLabel#sectionTitle { font-weight: bold; color: #333; }
QLabel#hint { color: #666; }
"""


def shape_icon(shape, amount=0.5, tilt=0.0, size=(56, 34)):
    """Tiny real-geometry icon of a strand end for the shape picker."""
    w, h = size
    img = QImage(w * 2, h * 2, QImage.Format_ARGB32_Premultiplied); img.fill(Qt.transparent)
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing); p.scale(2, 2)
    s = Strand(QPointF(-30, h / 2), QPointF(w - 16, h / 2), 16, QColor(200, 170, 230), QColor(0, 0, 0), 2)
    s.control_point1 = QPointF(-10, h / 2); s.control_point2 = QPointF(w - 30, h / 2)
    s.update_shape(); s.update_side_line()
    geo = styled_end_geometry(s, 1, dict(shape=shape, amount=amount, tilt=tilt))
    paint_styled(p, s, geo)
    p.end()
    return QIcon(QPixmap.fromImage(img))


def preview_pixmap(style, side_color=None, w=380, h=120):
    img = QImage(w * 2, h * 2, QImage.Format_ARGB32_Premultiplied); img.fill(QColor(255, 255, 255))
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing); p.scale(2, 2)
    # light grid like the canvas
    p.setPen(QPen(QColor(0, 0, 0, 18), 1))
    for gx in range(0, w, 27): p.drawLine(gx, 0, gx, h)
    for gy in range(0, h, 27): p.drawLine(0, gy, w, gy)
    under = make_strand((w - 95, -10), (w - 95, h + 10), (w - 95, 30), (w - 95, 90), (120, 200, 170))
    under.draw(p)
    s = make_strand((-40, h / 2), (w - 88, h / 2), (60, h / 2 - 30), (w - 150, h / 2 + 30), (200, 170, 230))
    s.has_circles = [True, False]
    geo = styled_end_geometry(s, 1, style)
    p.save(); p.setClipPath(_stroked(under))
    for j in range(3):
        p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 30)); p.drawPath(dilate(geo['outer'], 20 - j * 6))
    p.restore()
    paint_styled(p, s, geo, side_color)
    p.setPen(QPen(QColor(59, 164, 36), 1.5, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawEllipse(s.end, 6, 6)
    p.end()
    pm = QPixmap.fromImage(img); pm.setDevicePixelRatio(2)
    return pm


def section(title):
    f = QFrame(); f.setObjectName('section')
    v = QVBoxLayout(f); v.setContentsMargins(12, 10, 12, 12); v.setSpacing(8)
    t = QLabel(title); t.setObjectName('sectionTitle'); v.addWidget(t)
    return f, v


def build_dialog(state):
    d = QDialog(); d.setWindowTitle('Stylize End Side'); d.setStyleSheet(LIGHT)
    d.setMinimumWidth(640)
    root = QVBoxLayout(d); root.setSpacing(10)

    head = QLabel(f"Layer <b>{state['layer']}</b> — <b>{state['side']}</b> side")
    root.addWidget(head)

    # Preview
    pf, pv = section('Preview')
    pl = QLabel(); pl.setPixmap(preview_pixmap(state['style'], state.get('side_color')))
    pl.setAlignment(Qt.AlignCenter); pv.addWidget(pl)
    hint = QLabel('Changes show on the canvas immediately. Cancel puts the end back exactly as it was.')
    hint.setObjectName('hint'); hint.setWordWrap(True); pv.addWidget(hint)
    root.addWidget(pf)

    # End shape
    sf, sv = section('End Shape')
    row = QHBoxLayout(); row.setSpacing(6)
    group = QButtonGroup(d); group.setExclusive(True)
    shapes = [('flat', 'Straight'), ('angled', 'Angled'), ('rounded', 'Rounded'),
              ('pointed', 'Pointed'), ('notched', 'Notched'), ('concave', 'Concave')]
    for key, text in shapes:
        b = QToolButton(); b.setCheckable(True); b.setText(text)
        b.setIcon(shape_icon(key, 0.6, 30 if key == 'angled' else 0)); b.setIconSize(QSize(56, 34))
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon); b.setFixedWidth(92)
        b.setChecked(key == state['style']['shape'])
        group.addButton(b); row.addWidget(b)
    sv.addLayout(row)

    grid = QGridLayout(); grid.setHorizontalSpacing(10); grid.setVerticalSpacing(8)
    # Tilt
    grid.addWidget(QLabel('Tilt'), 0, 0)
    tilt = QSlider(Qt.Horizontal); tilt.setRange(-60, 60); tilt.setValue(int(state['style'].get('tilt', 0)))
    grid.addWidget(tilt, 0, 1)
    grid.addWidget(QLabel(f"{int(state['style'].get('tilt', 0)):+d}°"), 0, 2)
    # Depth
    depth_enabled = state['style']['shape'] in ('rounded', 'pointed', 'notched', 'concave')
    dl = QLabel('Depth'); grid.addWidget(dl, 1, 0)
    depth = QSlider(Qt.Horizontal); depth.setRange(0, 100); depth.setValue(int(state['style'].get('amount', 0.5) * 100))
    depth.setEnabled(depth_enabled); dl.setEnabled(depth_enabled)
    grid.addWidget(depth, 1, 1)
    dv = QLabel(f"{int(state['style'].get('amount', 0.5) * 100)} %"); dv.setEnabled(depth_enabled); grid.addWidget(dv, 1, 2)
    # Extend / trim
    grid.addWidget(QLabel('Extend / Trim'), 2, 0)
    ext = QSpinBox(); ext.setRange(-54, 108); ext.setValue(int(state['style'].get('offset', 0))); ext.setSuffix(' px')
    ext.setFixedWidth(120)
    grid.addWidget(ext, 2, 1, alignment=Qt.AlignLeft)
    eh = QLabel('+ extends past the endpoint, − trims. The endpoint itself never moves.')
    eh.setObjectName('hint'); eh.setWordWrap(True)
    grid.setColumnStretch(1, 1)
    sv.addLayout(grid); sv.addSpacing(8); sv.addWidget(eh)
    root.addWidget(sf)

    # Side line
    lf, lv = section('Side Line')
    show = QCheckBox('Show side line'); show.setChecked(state.get('line_visible', True)); lv.addWidget(show)
    g2 = QGridLayout(); g2.setHorizontalSpacing(10)
    g2.addWidget(QLabel('Thickness'), 0, 0)
    th = QSpinBox(); th.setRange(1, 40); th.setValue(state.get('line_width', 4)); th.setSuffix(' px'); th.setFixedWidth(120)
    g2.addWidget(th, 0, 1, alignment=Qt.AlignLeft)
    g2.addWidget(QLabel('Color'), 1, 0)
    crow = QHBoxLayout()
    swatch = QPushButton(); swatch.setFixedSize(44, 26)
    c = state.get('side_color') or QColor(0, 0, 0)
    swatch.setStyleSheet(f'background-color: {c.name()}; border: 1px solid #666; border-radius: 3px; min-width: 0; padding: 0;')
    crow.addWidget(swatch)
    use = QCheckBox('Use stroke color'); use.setChecked(state.get('side_color') is None); crow.addWidget(use); crow.addStretch()
    g2.addLayout(crow, 1, 1)
    g2.setColumnStretch(1, 1)
    lv.addLayout(g2)
    root.addWidget(lf)

    if state.get('two_free_ends'):
        both = QCheckBox('Apply to both free ends'); both.setChecked(False); root.addWidget(both)

    # Buttons (hand-built like WidthConfigDialog)
    br = QHBoxLayout()
    reset = QPushButton('Reset to Straight'); br.addWidget(reset); br.addStretch()
    ok = QPushButton('OK'); cancel = QPushButton('Cancel'); br.addWidget(ok); br.addWidget(cancel)
    root.addLayout(br)
    return d


def grab(widget, name):
    widget.show(); app.processEvents(); widget.adjustSize(); app.processEvents()
    pm = widget.grab(); path = os.path.join(OUT, name); pm.save(path); widget.hide()
    print('wrote', path, pm.width(), pm.height())


if __name__ == '__main__':
    grab(build_dialog(dict(layer='1_2', side='End', style=dict(shape='pointed', amount=0.5, tilt=15, offset=0),
                           line_visible=True, line_width=4, side_color=None, two_free_ends=False)),
         'dialog_pointed.png')
    grab(build_dialog(dict(layer='1_1', side='Start', style=dict(shape='angled', tilt=-35, offset=12),
                           line_visible=True, line_width=6, side_color=QColor(190, 40, 40), two_free_ends=True)),
         'dialog_angled_two_ends.png')
    grab(build_dialog(dict(layer='1_2', side='End', style=dict(shape='flat', tilt=0, offset=0),
                           line_visible=True, line_width=4, side_color=None, two_free_ends=False)),
         'dialog_default.png')
