"""Prototype of the "Stylize End Side" geometry, rendered with the REAL Strand class.

Produces preview PNGs for the concept doc. Documentation helper only.
"""
import os, sys, math
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "src")))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (QColor, QImage, QPainter, QPainterPath, QPainterPathStroker,
                         QTransform, QPen, QBrush, QFont)
app = QApplication(sys.argv[:1])
from strand import Strand

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mockups'))
os.makedirs(OUT, exist_ok=True)
SCALE = 2  # render at 2x for crisp doc images


# ---------------------------------------------------------------- profile curves
def profile_points(shape, half, amount, tilt_deg, offset, steps=24):
    """Return the end-edge profile as a list of local-frame points running from
    y=-half to y=+half. Local frame: origin at the endpoint, +x = outward along
    the tangent, y across the strand width. `half` is the half visible width.

    shape:  'flat' | 'angled' | 'rounded' | 'pointed' | 'notched' | 'concave'
    amount: 0..1 (roundness / tip depth / notch depth as fraction of the width)
    tilt_deg: rotates the whole profile about the endpoint (angled cut)
    offset: extend (+) / trim (-) along the tangent, px
    """
    pts = []
    w = 2 * half
    if shape in ('flat', 'angled'):
        pts = [QPointF(0, -half), QPointF(0, half)]
    elif shape == 'rounded':
        r = amount * half  # 0 -> flat, 1 -> semicircle
        for i in range(steps + 1):
            y = -half + w * i / steps
            # superellipse-ish: circle arc of radius `half` scaled to depth r
            x = r * math.sqrt(max(0.0, 1 - (y / half) ** 2))
            pts.append(QPointF(x, y))
    elif shape == 'pointed':
        depth = amount * w
        pts = [QPointF(0, -half), QPointF(depth, 0), QPointF(0, half)]
    elif shape == 'notched':
        depth = amount * w
        pts = [QPointF(0, -half), QPointF(-depth, 0), QPointF(0, half)]
    elif shape == 'concave':
        r = amount * half
        for i in range(steps + 1):
            y = -half + w * i / steps
            x = -r * math.sqrt(max(0.0, 1 - (y / half) ** 2))
            pts.append(QPointF(x, y))
    tr = QTransform()
    tr.translate(offset, 0)
    tr.rotate(tilt_deg)
    return _fit_to_band([tr.map(p) for p in pts], half)


def _fit_to_band(pts, half):
    """After a tilt the profile no longer reaches y = +-half. Extend its first
    and last segments straight on until they do, so the cut spans the whole
    strand cross-section (a 45-degree cut across a strand is longer than W)."""
    def hit(a, b, target_y):
        d = b - a
        if abs(d.y()) < 1e-9:
            return b
        t = (target_y - a.y()) / d.y()
        return QPointF(a.x() + d.x() * t, target_y)
    first = hit(pts[1], pts[0], -half if pts[0].y() < pts[-1].y() else half)
    last = hit(pts[-2], pts[-1], half if pts[0].y() < pts[-1].y() else -half)
    return [first] + pts[1:-1] + [last]


def end_frame(strand, side):
    """(point, outward angle) of the given end in canvas coords."""
    t = strand.calculate_cubic_tangent(0.0001 if side == 0 else 0.9999)
    if t.manhattanLength() == 0:
        t = strand.end - strand.start
    ang = math.atan2(t.y(), t.x())
    if side == 0:
        ang += math.pi  # outward = backwards at the start
    return (strand.start if side == 0 else strand.end), ang


def _chord_extended(prof, half):
    """Points where the profile's chord (first->last point), continued past
    both ends, reaches |y| = 1.5*half. For a straight or tilted cut that is the
    cut line itself; for rounded/pointed/notched profiles (whose ends share
    the same x) it is the perpendicular. Only a curved body bulges beyond
    |y| = half right behind its endpoint, and the cut continues straight
    through that bulge instead of carving a wedge or leaving a step."""
    ylim = 1.5 * half
    a, b = prof[0], prof[-1]
    d = b - a
    if abs(d.y()) < 1e-9:
        return QPointF(a.x(), -ylim), QPointF(b.x(), ylim)
    sgn = 1 if d.y() > 0 else -1
    ta = (-sgn * ylim - a.y()) / d.y()
    tb = (sgn * ylim - a.y()) / d.y()
    return (QPointF(a.x() + d.x() * ta, a.y() + d.y() * ta),
            QPointF(a.x() + d.x() * tb, a.y() + d.y() * tb))


def _remove_region(prof, half):
    """Local-frame region OUTWARD of the profile (x = P(y)): what the end
    style cuts away from the flat-capped body."""
    first, last = _chord_extended(prof, half)
    big = 40 * half
    poly = QPainterPath()
    poly.moveTo(first)
    for p in prof:
        poly.lineTo(p)
    poly.lineTo(last)
    poly.lineTo(QPointF(big, last.y()))
    poly.lineTo(QPointF(big, first.y()))
    poly.closeSubpath()
    return poly


def styled_end_geometry(strand, side, style):
    """Return dict(outer, inner, side_line, cap_edge) QPainterPaths in canvas coords.

    The profile P(y) is the OUTER boundary of the strand footprint at that end.
    With shape='flat', tilt=0, offset=0 it sits at x = stroke_width, which is
    exactly where today's straight side line ends, so the default reproduces
    the current rendering. The fill is the footprint inset by stroke_width on
    every side (long edges and cap alike), and the side-line band is the part
    of that inset ring that runs along the profile.

    outer     - stroke-colour footprint
    inner     - fill-colour footprint (outer inset by stroke_width)
    side_line - the band drawn in the side-line colour along the end edge
    cap_edge  - the open profile curve (dialog preview / debugging)
    """
    W = strand.width + 2 * strand.stroke_width
    sw = strand.stroke_width
    half = W / 2
    pt, ang = end_frame(strand, side)
    tr = QTransform().translate(pt.x(), pt.y())
    tr.rotate(math.degrees(ang))

    prof = profile_points(style['shape'], half, style.get('amount', 0.5),
                          style.get('tilt', 0.0), sw + style.get('offset', 0.0))
    remove = tr.map(_remove_region(prof, half))

    # Extension region: from the endpoint plane to the profile, inside the width band
    depth = 4 * W
    add_region = QPainterPath()
    for poly in _add_polygons(prof):
        add_region = add_region.united(tr.map(poly))

    path = strand.get_path()
    st = QPainterPathStroker(); st.setWidth(W); st.setJoinStyle(Qt.MiterJoin); st.setCapStyle(Qt.FlatCap)
    outer = st.createStroke(path).subtracted(remove).united(add_region)

    ring_st = QPainterPathStroker(); ring_st.setWidth(2 * sw); ring_st.setJoinStyle(Qt.MiterJoin)
    ring = ring_st.createStroke(outer).intersected(outer)
    inner = outer.subtracted(ring)

    first, last = _chord_extended(prof, half)
    edge = QPainterPath(); edge.moveTo(first)
    for p in prof + [last]:
        edge.lineTo(p)
    edge_c = tr.map(edge)
    band_st = QPainterPathStroker(); band_st.setWidth(2 * sw + 1.0); band_st.setCapStyle(Qt.FlatCap); band_st.setJoinStyle(Qt.MiterJoin)
    side_line = ring.intersected(band_st.createStroke(edge_c))
    return dict(outer=outer, inner=inner, side_line=side_line, cap_edge=edge_c, remove=remove, ring=ring)


def _add_polygons(prof, x0=-1.0):
    """Simple polygons between the plane x = x0 (just behind the endpoint) and
    the profile, one per run of profile points ahead of that plane. Built
    directly, without boolean ops on degenerate input, because Qt's path
    clipper mis-handles a box minus an arc and zero-area slivers."""
    polys = []
    run = []
    def cross(a, b):
        t = (x0 - a.x()) / (b.x() - a.x())
        return QPointF(x0, a.y() + (b.y() - a.y()) * t)
    def flush(run):
        if len(run) >= 2:
            poly = QPainterPath(); poly.moveTo(x0, run[0].y())
            for q in run:
                poly.lineTo(q)
            poly.lineTo(x0, run[-1].y()); poly.closeSubpath()
            polys.append(poly)
    prev = None
    for p in prof:
        ahead = p.x() > x0
        if prev is not None and (prev.x() > x0) != ahead:
            c = cross(prev, p)
            if ahead:
                run = [c]
            else:
                run.append(c); flush(run); run = []
        if ahead:
            run.append(p)
        prev = p
    flush(run)
    return polys


def _rect(x, y, w, h):
    r = QPainterPath(); r.addRect(x, y, w, h); return r


def dilate(path, r):
    """Offset a closed path outward by r (shadow extension)."""
    st = QPainterPathStroker(); st.setWidth(2 * r); st.setJoinStyle(Qt.RoundJoin); st.setCapStyle(Qt.RoundCap)
    return path.united(st.createStroke(path))


# ---------------------------------------------------------------- rendering
def make_strand(start, end, cp1, cp2, color, width=46, stroke=4):
    s = Strand(QPointF(*start), QPointF(*end), width, QColor(*color), QColor(0, 0, 0), stroke)
    s.control_point1 = QPointF(*cp1); s.control_point2 = QPointF(*cp2)
    s.update_shape(); s.update_side_line()
    return s


def paint_styled(p, strand, geo, side_color=None):
    p.setPen(Qt.NoPen)
    p.setBrush(strand.stroke_color); p.drawPath(geo['outer'])
    p.setBrush(strand.color); p.drawPath(geo['inner'])
    p.setBrush(side_color or strand.stroke_color); p.drawPath(geo['side_line'])


def new_image(w, h):
    img = QImage(w * SCALE, h * SCALE, QImage.Format_ARGB32_Premultiplied)
    img.fill(QColor(255, 255, 255))
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing); p.scale(SCALE, SCALE)
    return img, p


def label(p, x, y, text, size=11, color=QColor(40, 40, 40), bold=False):
    f = QFont('DejaVu Sans', size); f.setBold(bold); p.setFont(f); p.setPen(color)
    p.drawText(QPointF(x, y), text)


STYLES = [
    ('Straight (current)', dict(shape='flat')),
    ('Angled 30°',         dict(shape='angled', tilt=30)),
    ('Angled -45°',        dict(shape='angled', tilt=-45)),
    ('Rounded 100%',       dict(shape='rounded', amount=1.0)),
    ('Rounded 40%',        dict(shape='rounded', amount=0.4)),
    ('Pointed 60%',        dict(shape='pointed', amount=0.6)),
    ('Pointed 30% + tilt', dict(shape='pointed', amount=0.3, tilt=20)),
    ('Notched 40%',        dict(shape='notched', amount=0.4)),
    ('Concave 70%',        dict(shape='concave', amount=0.7)),
    ('Straight, extend +40', dict(shape='flat', offset=40)),
    ('Straight, trim -30', dict(shape='flat', offset=-30)),
    ('Rounded + extend',   dict(shape='rounded', amount=1.0, offset=25)),
]


def render_gallery():
    cols, cw, ch = 3, 250, 120
    rows = math.ceil(len(STYLES) / cols)
    img, p = new_image(cols * cw, rows * ch + 10)
    for i, (name, style) in enumerate(STYLES):
        cx = (i % cols) * cw; cy = (i // cols) * ch
        s = make_strand((cx + 20, cy + 60), (cx + 175, cy + 60), (cx + 70, cy + 40), (cx + 130, cy + 80), (200, 170, 230))
        s.has_circles = [True, False]  # start attached (drawn plain here), end free
        geo = styled_end_geometry(s, 1, style)
        # faint dashed marker: the untouched endpoint / anchor
        paint_styled(p, s, geo)
        p.setPen(QPen(QColor(59, 164, 36), 1.2, Qt.DashLine)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(s.end, 5, 5)
        label(p, cx + 14, cy + 108, name, 10)
    p.end(); img.save(os.path.join(OUT, 'gallery_end_styles.png'))


def render_anatomy():
    """Left: today's free end (real Strand.draw). Right: the same end stylized (pointed, tilted)."""
    img, p = new_image(560, 130)
    s = make_strand((20, 65), (240, 65), (80, 35), (180, 95), (200, 170, 230))
    s.has_circles = [True, False]
    s.draw(p)
    p.setPen(QPen(QColor(59, 164, 36), 1.5, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawEllipse(s.end, 7, 7)
    s2 = make_strand((300, 65), (520, 65), (360, 35), (460, 95), (200, 170, 230))
    s2.has_circles = [True, False]
    geo = styled_end_geometry(s2, 1, dict(shape='pointed', amount=0.5, tilt=15))
    paint_styled(p, s2, geo)
    p.setPen(QPen(QColor(59, 164, 36), 1.5, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawEllipse(s2.end, 7, 7)
    p.end(); img.save(os.path.join(OUT, 'anatomy_before_after.png'))


def render_layers():
    """Exploded view of the four geometry layers that share one profile (no text; captions in the doc)."""
    img, p = new_image(760, 120)
    style = dict(shape='pointed', amount=0.5, tilt=15)
    for i in range(4):
        x0 = i * 190
        s = make_strand((x0 + 15, 60), (x0 + 150, 60), (x0 + 55, 40), (x0 + 115, 80), (200, 170, 230))
        s.has_circles = [True, False]
        geo = styled_end_geometry(s, 1, style)
        p.setPen(Qt.NoPen)
        if i == 0:
            p.setBrush(QColor(0, 0, 0)); p.drawPath(geo['outer'])
        elif i == 1:
            p.setBrush(QColor(0, 0, 0, 40)); p.drawPath(geo['outer'])
            p.setBrush(s.color); p.drawPath(geo['inner'])
        elif i == 2:
            p.setBrush(QColor(0, 0, 0, 40)); p.drawPath(geo['outer'])
            p.setBrush(QColor(20, 110, 200)); p.drawPath(geo['side_line'])
        else:
            p.setBrush(QColor(0, 0, 0, 60)); p.drawPath(dilate(geo['outer'], 16))
            p.setBrush(QColor(0, 0, 0, 40)); p.drawPath(geo['outer'])
    p.end(); img.save(os.path.join(OUT, 'geometry_layers.png'))


def render_shadow_and_mask():
    """A styled end that stops inside another strand: the shadow it casts and the
    mask intersection both follow the styled profile, not the old flat cap."""
    img, p = new_image(720, 230)
    cases = [('Today: straight end', dict(shape='flat')),
             ('Stylized: angled 35\u00b0, trimmed 6 px', dict(shape='angled', tilt=35, offset=-6)),
             ('Stylized: pointed 50%', dict(shape='pointed', amount=0.5))]
    for k, (title, style) in enumerate(cases):
        x0 = k * 240
        under = make_strand((x0 + 160, 10), (x0 + 160, 225), (x0 + 160, 80), (x0 + 160, 160), (120, 200, 170), 46, 4)
        over = make_strand((x0 + 20, 118), (x0 + 172, 118), (x0 + 70, 85), (x0 + 130, 150), (200, 170, 230), 46, 4)
        over.has_circles = [True, False]
        under.draw(p)
        geo = styled_end_geometry(over, 1, style)
        p.save()
        p.setClipPath(_stroked(under))
        for j in range(3):
            p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 30))
            p.drawPath(dilate(geo['outer'], 20 - j * 6))
        p.restore()
        paint_styled(p, over, geo)
        mask = _stroked(under).intersected(geo['outer'])
        p.setPen(QPen(QColor(220, 60, 60), 1.5, Qt.DashLine)); p.setBrush(QColor(220, 60, 60, 45))
        p.drawPath(mask)
    p.end(); img.save(os.path.join(OUT, 'shadow_and_mask.png'))


def _stroked(s):
    st = QPainterPathStroker(); st.setWidth(s.width + 2 * s.stroke_width); st.setCapStyle(Qt.FlatCap); st.setJoinStyle(Qt.MiterJoin)
    return st.createStroke(s.get_path())


def render_dialog_preview(style, side_color=None, w=300, h=150, fname='preview.png'):
    """The live preview that sits inside the dialog: the real strand's free end."""
    img, p = new_image(w, h)
    s = make_strand((-60, h / 2), (w - 90, h / 2), (30, h / 2 - 30), (w - 140, h / 2 + 30), (200, 170, 230))
    s.has_circles = [True, False]
    geo = styled_end_geometry(s, 1, style)
    p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 45)); p.drawPath(dilate(geo['outer'], 16))
    paint_styled(p, s, geo, side_color)
    p.setPen(QPen(QColor(59, 164, 36), 1.5, Qt.DashLine)); p.setBrush(Qt.NoBrush)
    p.drawEllipse(s.end, 6, 6)
    p.end(); img.save(os.path.join(OUT, fname))


if __name__ == '__main__':
    render_gallery(); render_anatomy(); render_layers(); render_shadow_and_mask()
    render_dialog_preview(dict(shape='pointed', amount=0.5, tilt=15), fname='preview_pointed.png')
    render_dialog_preview(dict(shape='angled', tilt=30, offset=10), QColor(200, 40, 40), fname='preview_angled_red.png')
    print('ok')
