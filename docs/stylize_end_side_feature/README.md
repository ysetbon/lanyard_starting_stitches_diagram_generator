# Stylize End Side — Product Concept

> Status: **concept only** — no application code has been changed. This folder holds the
> spec page ([`stylize_end_side.html`](stylize_end_side.html), self-contained, images inlined),
> the mockup images in [`mockups/`](mockups/), and the helper scripts in [`tools/`](tools/) that
> produced them.
>
> **The strands in the mockups are drawn by the app's real `Strand` class**: `tools/end_styles.py`
> is a working prototype of the proposed end geometry running on top of `Strand.get_path()`;
> `tools/render_menu.py` runs the real `NumberedLayerButton.show_context_menu` offscreen and
> injects the proposed row; `tools/render_dialog.py` builds the dialog mockup in Qt with the
> app's light dialog stylesheet.

## Summary

Right-clicking a layer button that has a **free end** (an end with `has_circles[side] == False`,
which is what the green strip on the button already signals) adds a **Stylize End Side** row to
the normal context menu, right under **Close the Knot**. The row is built like the existing
Line / Arrow / Dash / Circle rows: a label plus one flat button per free end (`Start…`, `End…`).

Each button opens a modal **Stylize End Side** dialog for that one end:

- **End Shape** — Straight (today), Angled, Rounded, Pointed, Notched, Concave
- **Tilt** (−60°…+60°), **Depth** (0–100 % of the width), **Extend / Trim** (px; the endpoint never moves)
- **Side Line** — show (same flag as Show/Hide End Line), thickness, colour (default: stroke colour)
- **Apply to both free ends** (only when the strand has two free ends), **Reset to Straight**, OK / Cancel

The dialog previews live on the canvas (like the shadow editor); Cancel restores the opening
snapshot; OK saves one undo step.

The key design rule: the end style is **one profile** `P(y)` in the end's tangent frame, and
four things are derived from it so they can never disagree — the outer footprint (stroke
colour), the inner fill (footprint inset by `stroke_width`), the side-line band, and the shadow
(footprint dilated by the blur radius). Masks intersect the same footprint, so a mask over a
styled end takes the new shape automatically. With the default settings the footprint is
pixel-identical to today's flat cap + side line.

## Files

| Path | What |
|---|---|
| `stylize_end_side.html` | The full spec: menu placement, dialog wording (English), end shapes, geometry model, everything that must update together, data model + translation keys, edge cases, implementation map with line refs |
| `mockups/gallery_end_styles.png` | Twelve end styles on the same strand |
| `mockups/anatomy_before_after.png` | Today's free end vs. a stylized one |
| `mockups/geometry_layers.png` | Outer footprint / inner fill / side-line band / shadow |
| `mockups/shadow_and_mask.png` | Shadow cast and mask intersection following the profile |
| `mockups/menu_current_one_free_end.png` | Today's context menu (real UI capture) |
| `mockups/menu_proposed_one_free_end.png`, `menu_proposed_two_free_ends.png` | Menu with the proposed row |
| `mockups/layer_button_attachable.png` | The green "has a free end" strip |
| `mockups/dialog_pointed.png`, `dialog_angled_two_ends.png`, `dialog_default.png` | Qt dialog mockups |
| `tools/end_styles.py` | Geometry prototype (`profile_points`, `styled_end_geometry`) + figure renderer |
| `tools/render_menu.py` | Real context-menu capture with the injected row |
| `tools/render_dialog.py` | Qt dialog mockup |

Regenerate everything with:

```
cd docs/stylize_end_side_feature/tools
QT_QPA_PLATFORM=offscreen python3 end_styles.py
QT_QPA_PLATFORM=offscreen python3 render_menu.py
QT_QPA_PLATFORM=offscreen python3 render_dialog.py
```

(The scripts import the app from `src/` read-only and write PNGs into `mockups/`.)
