"""Screenshot the REAL layer-button context menu (NumberedLayerButton.show_context_menu)
with the proposed 'Stylize End Side' row injected, using the app's own HoverLabel /
button-row widgets and menu stylesheet. Documentation helper only."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "src")))
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QWidgetAction, QFrame
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QColor
app = QApplication(sys.argv[:1])
from numbered_layer_button import NumberedLayerButton, HoverLabel
from strand import Strand
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mockups'))
os.makedirs(OUT, exist_ok=True)
THEME = 'default'

class _Canvas:
    strands = []
    def __getattr__(self, name):
        return lambda *a, **k: None

class LayerPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.multi_select_mode = False
        self.layer_buttons = []
        self.language_code = 'en'
        self.canvas = _Canvas()
    def __getattr__(self, name):
        return lambda *a, **k: None

def capture_menu(strand, inject=None):
    panel = LayerPanel()
    btn = NumberedLayerButton(strand.layer_name, 1, QColor('purple'), parent=panel)
    panel.layer_buttons.append(btn); panel.canvas.strands.append(strand)
    captured = []
    real_exec = QMenu.exec_
    QMenu.exec_ = lambda self, *a, **k: (captured.append(self), None)[1]
    try:
        btn.show_context_menu(QPoint(5, 5))
    finally:
        QMenu.exec_ = real_exec
    menu = captured[0]
    if inject: inject(menu, btn)
    return menu, btn

def rehost(menu, btn):
    texts = []
    for action in menu.actions():
        w = action.defaultWidget() if isinstance(action, QWidgetAction) else None
        if w is not None and hasattr(w, 'text'): texts.append(w.text())
        elif w is not None and w.layout() is not None:
            for i in range(w.layout().count()):
                c = w.layout().itemAt(i).widget()
                if c and hasattr(c, 'text'): texts.append(c.text())
    width = btn.calculate_menu_width(texts) + 30
    frame = QFrame(); frame.setObjectName('menuFrame')
    frame.setStyleSheet('#menuFrame { background-color: #F0F0F0; border: 1px solid #ABABAB; }')
    outer = QVBoxLayout(frame); outer.setContentsMargins(1, 3, 1, 3); outer.setSpacing(0)
    for action in menu.actions():
        if action.isSeparator():
            line = QFrame(); line.setFixedHeight(1)
            line.setStyleSheet('background-color: #C6C6C6; border: none; margin: 0px 4px;')
            outer.addSpacing(2); outer.addWidget(line); outer.addSpacing(2)
        elif isinstance(action, QWidgetAction) and action.defaultWidget():
            w = action.defaultWidget(); w.setParent(None); outer.addWidget(w); w.setVisible(True)
    frame.setFixedWidth(max(width, frame.sizeHint().width()))
    frame.adjustSize(); frame.setFixedHeight(frame.sizeHint().height())
    return frame

def grab(widget, name):
    widget.show(); app.processEvents(); widget.adjustSize(); app.processEvents()
    pm = widget.grab(); path = os.path.join(OUT, name); pm.save(path); widget.hide()
    print('wrote', path, pm.width(), pm.height())

def find_row_index(menu, text):
    for i, a in enumerate(menu.actions()):
        w = a.defaultWidget() if isinstance(a, QWidgetAction) else None
        if w is not None and hasattr(w, 'text') and w.text().startswith(text):
            return i
    return None

LINE_STYLE = """
    QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
    QPushButton:hover { background-color: #333333; color: white; }
    QLabel { color: black; background-color: transparent; padding: 2px; }
"""

def inject_stylize_row(menu, btn, free_ends=('end',), hovered=None):
    """The proposed row, built exactly like the existing Line/Arrow/Dash/Circle rows
    (src/numbered_layer_button.py:946-1005): QLabel on the left, one flat QPushButton
    per FREE end on the right, same stylesheet."""
    row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(5, 1, 5, 1)
    lab = QLabel('Stylize End Side'); h.addWidget(lab)
    for side in free_ends:
        b = QPushButton('Start\u2026' if side == 'start' else 'End\u2026'); b.setFlat(True)
        if hovered == side:
            b.setStyleSheet('QPushButton { background-color: #333333; color: white; border: none; text-align: right; }')
        h.addWidget(b)
    for child in row.findChildren(QWidget):
        if not child.styleSheet(): child.setStyleSheet(LINE_STYLE)
    act = QWidgetAction(menu); act.setDefaultWidget(row)
    anchor = find_row_index(menu, 'Close the Knot')
    actions = menu.actions()
    line_idx = None
    for i, a in enumerate(actions):
        w = a.defaultWidget() if isinstance(a, QWidgetAction) else None
        if w is not None and w.layout() is not None:
            c = w.layout().itemAt(0).widget()
            if isinstance(c, QLabel) and c.text() == 'Line': line_idx = i
    if anchor is not None:
        before = actions[anchor + 1] if anchor + 1 < len(actions) else None
        menu.insertAction(before, act) if before else menu.addAction(act)
    else:
        # both ends free: no Close the Knot row -> sit right after the Line row's separator
        sep = QWidgetAction(menu); sep.setSeparator(True)
        target = actions[line_idx + 1] if line_idx is not None and line_idx + 1 < len(actions) else None
        if target is not None:
            menu.insertAction(target, act)
        else:
            menu.addAction(act)

if __name__ == '__main__':
    # 1) today's menu for a strand with one free end (start attached, end free)
    s = Strand(QPointF(0, 0), QPointF(120, 40), 46, set_number=1, layer_name='1_2')
    s.has_circles = [True, False]
    menu, btn = capture_menu(s)
    grab(rehost(menu, btn), 'menu_current_one_free_end.png')
    # 2) proposed: same menu with the Stylize End Side row (one free end -> one button)
    s2 = Strand(QPointF(0, 0), QPointF(120, 40), 46, set_number=1, layer_name='1_2')
    s2.has_circles = [True, False]
    menu, btn = capture_menu(s2, lambda m, b: inject_stylize_row(m, b, ('end',), hovered='end'))
    grab(rehost(menu, btn), 'menu_proposed_one_free_end.png')
    # 3) proposed: both ends free -> two buttons
    s3 = Strand(QPointF(0, 0), QPointF(120, 40), 46, set_number=1, layer_name='1_1')
    s3.has_circles = [False, False]
    menu, btn = capture_menu(s3, lambda m, b: inject_stylize_row(m, b, ('start', 'end')))
    grab(rehost(menu, btn), 'menu_proposed_two_free_ends.png')
    # 4) the layer button itself with the green attachable strip
    panel = LayerPanel()
    b = NumberedLayerButton('1_2', 1, QColor(200, 170, 230), parent=panel)
    b.set_attachable(True)
    b.setFixedSize(100, 40)
    grab(b, 'layer_button_attachable.png')
