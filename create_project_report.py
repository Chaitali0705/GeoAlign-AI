from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont


OUT = Path("reports") / "GeoAlign_AI_Technical_Project_Report.docx"
FIG_DIR = Path("reports") / "figures"
NAVY = "17365D"
LIGHT_BLUE = "EAF2F8"
PALE_BLUE = "F6F9FC"
GRAY = "D9E1E8"
TEXT = RGBColor(0, 0, 0)


def image_font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(Path("C:/Windows/Fonts") / name, size)


def centered(draw, box, text, font, fill):
    left, top, right, bottom = box
    bounds = draw.multiline_textbbox((0, 0), text, font=font, align="center", spacing=5)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.multiline_text(((left + right - width) / 2, (top + bottom - height) / 2), text, font=font, fill=fill, align="center", spacing=5)


def make_architecture_diagram() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "architecture.png"
    canvas = Image.new("RGB", (1600, 870), "white")
    draw = ImageDraw.Draw(canvas)
    title_font, box_font, small_font = image_font(36, True), image_font(25, True), image_font(20)
    draw.text((70, 42), "Independent Parcel Alignment Architecture", font=title_font, fill="#17365D")
    stages = [
        ("Input data", "Official parcels\nSatellite image\nBoundary hints"),
        ("Visual evidence", "Gradient and Canny edges\nOptional hint fusion"),
        ("Local alignment", "Outline ring template\nFFT cross-correlation"),
        ("Robust spatial prior", "RANSAC affine drift\nTrusted anchor plots"),
        ("Local refinement", "Clipped residual field\nInverse-distance weighting"),
        ("Decision and output", "Corrected or flagged\nConfidence and GeoJSON"),
    ]
    x, y, w, h, gap = 105, 160, 400, 185, 80
    boxes = []
    for index, (label, detail) in enumerate(stages):
        row, col = divmod(index, 3)
        bx, by = x + col * (w + gap), y + row * 330
        boxes.append((bx, by, bx + w, by + h))
        draw.rounded_rectangle(boxes[-1], radius=18, fill="#F4F8FC", outline="#17365D", width=4)
        centered(draw, (bx + 18, by + 24, bx + w - 18, by + 84), label, box_font, "#17365D")
        centered(draw, (bx + 28, by + 90, bx + w - 28, by + h - 22), detail, small_font, "#1F2937")
    for i in (0, 1, 3, 4):
        a, b = boxes[i], boxes[i + 1]
        ymid = (a[1] + a[3]) // 2
        draw.line((a[2], ymid, b[0] - 18, ymid), fill="#4D6E93", width=5)
        draw.polygon([(b[0] - 18, ymid - 10), (b[0] - 18, ymid + 10), (b[0], ymid)], fill="#4D6E93")
    for i in range(3):
        a, b = boxes[i], boxes[i + 3]
        xmid = (a[0] + a[2]) // 2
        draw.line((xmid, a[3], xmid, b[1] - 18), fill="#4D6E93", width=4)
        draw.polygon([(xmid - 10, b[1] - 18), (xmid + 10, b[1] - 18), (xmid, b[1])], fill="#4D6E93")
    canvas.save(path)
    return path


def make_technique_diagram() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "technique_stack.png"
    canvas = Image.new("RGB", (1600, 790), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((70, 40), "AI ML and Spatial Reasoning Technique Stack", font=image_font(36, True), fill="#17365D")
    techniques = [
        ("Computer vision", "Scharr gradients and Canny edges\nturn imagery into field-boundary evidence"),
        ("Signal processing", "FFT cross-correlation searches\nfor the best outline translation"),
        ("Robust estimation", "RANSAC identifies a village-wide\ndrift model while rejecting outliers"),
        ("Spatial learning", "Inverse-distance residual interpolation\nadapts the global model locally"),
        ("Uncertainty decision", "Evidence features, area checks, and\nthresholds determine correct or flag"),
    ]
    x, y, w, h = 90, 155, 1420, 102
    colors = ["#EAF2F8", "#F4F8FC", "#EAF2F8", "#F4F8FC", "#EAF2F8"]
    for i, (name, detail) in enumerate(techniques):
        by = y + i * 120
        draw.rounded_rectangle((x, by, x + w, by + h), radius=16, fill=colors[i], outline="#AABED3", width=3)
        draw.rounded_rectangle((x + 18, by + 16, x + 355, by + h - 16), radius=10, fill="#17365D")
        centered(draw, (x + 38, by + 28, x + 335, by + h - 28), name, image_font(24, True), "white")
        centered(draw, (x + 390, by + 18, x + w - 25, by + h - 18), detail, image_font(22), "#1F2937")
        if i < len(techniques) - 1:
            cx = x + w // 2
            draw.line((cx, by + h, cx, by + h + 15), fill="#4D6E93", width=4)
            draw.polygon([(cx - 9, by + h + 15), (cx + 9, by + h + 15), (cx, by + h + 28)], fill="#4D6E93")
    canvas.save(path)
    return path


def make_performance_chart() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "performance.png"
    canvas = Image.new("RGB", (1600, 880), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((70, 40), "Independent Full Village Performance Summary", font=image_font(36, True), fill="#17365D")
    # Left chart: IoU
    left, top, right, bottom = 120, 170, 760, 650
    draw.rectangle((left, top, right, bottom), outline="#718096", width=2)
    for tick in range(0, 6):
        y = bottom - tick * (bottom - top) / 5
        draw.line((left, y, right, y), fill="#DCE5EE", width=1)
        draw.text((left - 58, y - 12), f"{tick/5:.1f}", font=image_font(18), fill="#475569")
    draw.text((left, top - 38), "Median IoU on six public truths", font=image_font(24, True), fill="#1F2937")
    values = [("Official\ninput", 0.584, "#94A3B8"), ("Independent\nprediction", 0.884, "#118054")]
    for i, (label, value, color) in enumerate(values):
        bx = 265 + i * 250
        bh = (bottom - top) * value
        draw.rectangle((bx, bottom - bh, bx + 145, bottom), fill=color)
        centered(draw, (bx - 20, bottom + 18, bx + 165, bottom + 74), label, image_font(20, True), "#1F2937")
        draw.text((bx + 28, bottom - bh - 35), f"{value:.3f}", font=image_font(22, True), fill=color)
    # Right chart: decisions
    left2, top2, right2, bottom2 = 910, 170, 1510, 650
    draw.rectangle((left2, top2, right2, bottom2), outline="#718096", width=2)
    draw.text((left2, top2 - 38), "Decision distribution across 2,457 plots", font=image_font(24, True), fill="#1F2937")
    for tick in range(0, 6):
        y = bottom2 - tick * (bottom2 - top2) / 5
        draw.line((left2, y, right2, y), fill="#DCE5EE", width=1)
        draw.text((left2 - 64, y - 12), f"{tick*300}", font=image_font(18), fill="#475569")
    counts = [("Corrected", 1892, "#118054"), ("Flagged", 565, "#BC5B21")]
    for i, (label, value, color) in enumerate(counts):
        bx = 1040 + i * 235
        bh = (bottom2 - top2) * value / 1500
        draw.rectangle((bx, bottom2 - bh, bx + 135, bottom2), fill=color)
        centered(draw, (bx - 15, bottom2 + 20, bx + 150, bottom2 + 55), label, image_font(19, True), "#1F2937")
        draw.text((bx + 26, bottom2 - bh - 35), f"{value:,}", font=image_font(22, True), fill=color)
    draw.rounded_rectangle((140, 735, 1460, 830), radius=14, fill="#F4F8FC", outline="#AABED3", width=2)
    centered(draw, (160, 748, 1440, 818), "All 6 public reference plots improved   |   Median centroid error: 2.739 m   |   Invalid output geometries: 0", image_font(24, True), "#17365D")
    canvas.save(path)
    return path


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell, color: str = GRAY) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=110, start=110, bottom=110, end=110) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    node = OxmlElement("w:tblHeader")
    node.set(qn("w:val"), "true")
    tr_pr.append(node)


def set_font(run, size=10.5, bold=False, color=TEXT, name="Aptos") -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def remove_bottom_rule(paragraph_or_style) -> None:
    """Remove Word's built-in Title style border so the cover remains clean."""
    element = paragraph_or_style._element
    p_pr = element.find(qn("w:pPr"))
    if p_pr is None:
        return
    border = p_pr.find(qn("w:pBdr"))
    if border is not None:
        p_pr.remove(border)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    set_font(run, 8.5, color=RGBColor(75, 85, 99))
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def add_para(doc, text="", style=None, after=6, before=0, alignment=None):
    p = doc.add_paragraph(style=style)
    if alignment is not None:
        p.alignment = alignment
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.16
    run = p.add_run(text)
    set_font(run)
    return p


def add_bullet(doc, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.12
    run = p.add_run(text)
    set_font(run, 10.25)


def heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(15 if level == 1 else 9)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    set_font(run, 15 if level == 1 else 12, bold=True)
    return p


def add_figure(doc, image_path: Path, caption: str, width: float = 6.65) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.add_run().add_picture(str(image_path), width=Inches(width))
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(9)
    run = caption_paragraph.add_run(caption)
    set_font(run, 8.7, color=RGBColor(75, 85, 99))


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False
    header = table.rows[0]
    set_repeat_table_header(header)
    for index, text in enumerate(headers):
        cell = header.cells[index]
        if widths:
            cell.width = Inches(widths[index])
        set_cell_shading(cell, NAVY)
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(str(text))
        set_font(run, 9, bold=True, color=RGBColor(255, 255, 255))
    for row_index, row_data in enumerate(rows):
        row = table.add_row()
        for index, text in enumerate(row_data):
            cell = row.cells[index]
            if widths:
                cell.width = Inches(widths[index])
            set_cell_shading(cell, PALE_BLUE if row_index % 2 else "FFFFFF")
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 and len(headers) <= 3 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(text))
            set_font(run, 9.2)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def build() -> None:
    doc = Document()
    architecture_figure = make_architecture_diagram()
    technique_figure = make_technique_diagram()
    performance_figure = make_performance_chart()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)

    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    styles["Normal"]._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    styles["Normal"].font.size = Pt(10.5)
    for name in ("Title", "Heading 1", "Heading 2"):
        styles[name].font.name = "Aptos Display" if name == "Title" else "Aptos"
        styles[name]._element.rPr.rFonts.set(qn("w:ascii"), styles[name].font.name)
        styles[name]._element.rPr.rFonts.set(qn("w:hAnsi"), styles[name].font.name)
        styles[name].font.color.rgb = TEXT
    remove_bottom_rule(styles["Title"])

    footer = section.footer
    add_page_number(footer.paragraphs[0])

    # Cover page
    for _ in range(5):
        doc.add_paragraph()
    title = doc.add_paragraph(style="Title")
    remove_bottom_rule(title)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(14)
    run = title.add_run("GeoAlign AI Technical Project Report")
    set_font(run, 28, bold=True)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(36)
    run = subtitle.add_run("Satellite imagery, geospatial computer vision, and confidence aware boundary correction")
    set_font(run, 14, color=RGBColor(71, 85, 105))
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in ("Project Report", f"Prepared for academic review", f"Date: {date.today().strftime('%d %B %Y')}"):
        r = meta.add_run(line + "\n")
        set_font(r, 11, color=RGBColor(71, 85, 105))
    doc.add_page_break()

    heading(doc, "Executive Summary")
    add_para(doc, "GeoAlign AI addresses the displacement of official cadastral parcel boundaries from the actual field edges visible in satellite imagery. The solution processes a complete village at once, estimates likely map drift from reliable visual evidence, corrects plots only when the evidence is strong, and flags ambiguous plots rather than forcing a movement. The ML-enabled full-village run processed 2,457 plots, corrected 1,892 and flagged 565. On six public reference plots, median Intersection over Union improved from 0.584 for the official boundaries to 0.884 for the predictions. All six reference plots improved, and the final GeoJSON export contains no invalid geometries.")
    add_para(doc, "The approach is intentionally a hybrid geospatial AI system rather than a data-hungry deep-learning model. Its core uses computer vision, FFT correlation, robust RANSAC fitting, local spatial interpolation, and a mandatory Random Forest confidence estimator trained on synthetic parcel displacements. The six public truths are reserved for evaluation and are not used as training labels.")

    heading(doc, "1 Project Context and Objectives")
    add_para(doc, "Historical land maps were often drawn on paper and later georeferenced onto satellite imagery. During that conversion, an official parcel can retain approximately the right shape while appearing several metres away from the real field on the ground. The project aims to correct placement errors while avoiding changes to parcels whose satellite evidence is weak, whose geometry is unreliable, or whose recorded area suggests that the problem is not merely a translation.")
    add_table(doc, ["Objective", "Project response"], [
        ["Locate real field edges", "Derive an edge-affinity surface from satellite imagery and optional boundary hints."],
        ["Estimate parcel displacement", "Match each cadastral outline against nearby satellite edges using FFT cross-correlation."],
        ["Avoid false matches", "Fit a robust village-wide affine prior with RANSAC and require agreement with local evidence."],
        ["Communicate uncertainty", "Return an evidence-based confidence value for corrected parcels and flag uncertain plots."],
        ["Support review", "Export valid GeoJSON and provide a browser viewer for overlay and parcel-level inspection."],
    ], widths=[1.65, 5.15])

    heading(doc, "2 Data Inputs and Representation")
    add_para(doc, "The pipeline operates on a village bundle. Vector parcel geometry begins in WGS84 longitude and latitude coordinates, while satellite imagery is read in its own raster coordinate reference system. For distance-sensitive operations such as translations, areas, and residuals, the pipeline converts calculations to a local UTM coordinate system so that values are measured in metres.")
    add_table(doc, ["Input", "Format", "Use in the pipeline"], [
        ["Official parcels", "input.geojson", "Contains plot numbers, polygon or multipolygon geometry, recorded area fields, and survey metadata."],
        ["Satellite image", "imagery.tif", "Provides the primary visual evidence from which field boundaries are detected."],
        ["Boundary hint raster", "boundaries.tif", "Optional secondary evidence layer; it supports but does not replace imagery-derived edges."],
        ["Public example truths", "example_truths.geojson", "Used only after prediction for directional public evaluation, not for fitting the alignment."],
    ], widths=[1.45, 1.45, 3.9])
    add_para(doc, "The output is predictions.geojson in WGS84. Every output feature preserves the plot number and carries a status of corrected or flagged. Corrected features include a confidence score and a short method note. Flagged features retain the official placement except when a source geometry must be normalized to remain valid for GIS tools.")

    heading(doc, "3 End to End Architecture")
    add_para(doc, "The architecture separates evidence generation, geometric inference, robust spatial regularization, and decision making. This separation makes each stage inspectable and allows the final viewer to explain why a plot was moved or retained.")
    add_table(doc, ["Stage", "Main operation", "Output"], [
        ["1 Load and prepare", "Read GeoJSON and GeoTIFF inputs, preserve plot identifiers, choose a local metric CRS.", "Metric parcel geometry and raster access handles."],
        ["2 Build visual evidence", "Convert local RGB image patches into an edge-affinity surface using gradients, Canny edges, smoothing, and optional hints.", "Edge map where high values indicate likely boundaries."],
        ["3 Local alignment", "Rasterize the parcel outline as a ring and cross-correlate it against the edge map within an adaptive search radius.", "Candidate east north shift, edge score, score improvement, and peak sharpness."],
        ["4 Global and local drift", "Use reliable local matches as anchors for an affine RANSAC transformation, then interpolate clipped local residuals.", "A stable village prior with controlled local adaptation."],
        ["5 Decision and export", "Combine evidence, area reliability, movement limits, and confidence thresholds; correct or flag each plot.", "Contract-valid GeoJSON plus review-ready method notes."],
        ["6 Visual review", "Overlay the satellite preview, official shapes, and predictions in a browser viewer.", "Human-readable quality assurance interface."],
    ], widths=[1.2, 3.65, 1.95])
    add_figure(doc, architecture_figure, "Figure 1. End-to-end architecture from source data to explainable parcel output.")

    heading(doc, "4 Data Processing Pipeline")
    heading(doc, "4.1 Patch extraction and coordinate handling", 2)
    add_para(doc, "For each plot, the system transforms the official polygon from WGS84 into the satellite image coordinate reference system. It crops a padded image patch around that plot. Padding is large enough to support the possible search movement, while avoiding the cost of processing the entire village image for every parcel. The corresponding optional boundary-hint patch is resampled to the same patch extent and shape.")
    heading(doc, "4.2 Edge-affinity generation", 2)
    add_para(doc, "The RGB image is converted to grayscale. A Scharr gradient detects intensity transitions, while Canny edge detection emphasizes sharper contours. The two signals are combined and smoothed to reduce high-frequency texture caused by crops, roofs, and noise. If a boundary-hint raster is available, it is fused as a lower-weight supporting signal. The result is normalized to a 0 to 1 edge-affinity surface.")
    heading(doc, "4.3 Parcel outline matching", 2)
    add_para(doc, "The system rasterizes the parcel boundary as a thin buffered ring rather than matching the entire polygon interior. This reduces sensitivity to crop appearance and focuses the objective on visible field boundaries. FFT cross-correlation efficiently evaluates many translations at once. The local search radius scales with the square root of parcel area and is capped so that small parcels do not jump to distant unrelated edges.")
    heading(doc, "4.4 Quality signals", 2)
    add_para(doc, "Each candidate match records three important signals. Edge support measures how much of the shifted outline falls on likely boundaries. Improvement compares support before and after shifting. Peak-to-sidelobe ratio measures whether the best correlation peak is clearly better than nearby alternatives. High peak sharpness and positive improvement indicate that the local correction is less ambiguous.")
    heading(doc, "4.5 AI and ML techniques used", 2)
    add_para(doc, "The project contains deterministic AI techniques and a trained machine-learning component. The computer-vision and spatial methods generate interpretable evidence. The Random Forest model learns a non-linear relationship between those evidence features and synthetic recovery quality. It is trained without public hand-aligned truths: known synthetic translations are applied to parcels, the matcher attempts recovery, and the resulting IoU becomes the learning target.")
    add_table(doc, ["Technique", "Category", "Role in the project"], [
        ["Scharr gradients and Canny edges", "Computer vision", "Extract likely field boundaries from RGB satellite imagery."],
        ["FFT cross-correlation", "Signal processing", "Search rapidly for the translation where a parcel outline best aligns with image edges."],
        ["RANSAC affine fitting", "Robust machine learning", "Fit village drift from reliable anchors while rejecting outlier local matches."],
        ["Inverse-distance residual field", "Spatial learning", "Adapt the global drift model locally using nearby inlier residuals."],
        ["Random Forest regression", "Supervised ML on synthetic labels", "Predict recovery IoU from evidence features for standard confidence scoring."],
    ], widths=[2.0, 1.65, 3.15])
    add_figure(doc, technique_figure, "Figure 2. Hybrid AI, ML, and spatial-reasoning technique stack.")

    heading(doc, "5 Spatial Correction Model")
    heading(doc, "5.1 Robust affine village prior", 2)
    add_para(doc, "Not every local match is trustworthy. The pipeline selects anchors only when the local image evidence is usable, the peak is sufficiently sharp, and the shifted ring improves edge support. RANSAC fits an affine transformation from official anchor centroids to their locally matched positions. Because RANSAC repeatedly fits candidate models while rejecting outliers, a few plots matched to roads or building edges do not dominate the village correction.")
    heading(doc, "5.2 Locally adaptive residual drift field", 2)
    add_para(doc, "A single affine transform represents coherent village-wide drift but may not capture local bending caused by historical map georeferencing. The project therefore calculates residual displacement at affine inlier anchors and interpolates nearby residuals using inverse-distance weighting. Residual magnitude is clipped before being added to the affine shift. This is the principal refinement over a purely global model: it can adapt to gradual local distortion while retaining a conservative global prior.")
    heading(doc, "5.3 Correct or flag decision", 2)
    add_para(doc, "A sharp local match is accepted when it is strong on its own. A moderately sharp match is accepted when it agrees with the spatial prior. Otherwise, the village prior is used only if the overall confidence remains adequate. Parcels are flagged when image evidence is poor or conflicting, movement is implausibly large, the parcel appears already aligned, or the map area and recorded area have a large mismatch. This restraint is essential because moving an already correct plot can reduce overall accuracy.")

    heading(doc, "6 Confidence Model and Output Interpretation")
    add_para(doc, "Confidence is not a claim that every high-scoring parcel is perfectly correct. In the completed full-village run, it is an evidence-based score derived from local edge strength, improvement after movement, peak sharpness, local agreement with the spatial prior, and parcel-area reliability. Corrected plots have a confidence range of approximately 0.341 to 0.833, with a median near 0.444.")
    add_para(doc, "The Random Forest regression model is part of every standard GeoAlign AI run. It uses peak sharpness, edge support, support improvement, predicted shift, parcel area, and area ratio, then trains on synthetic translation-and-recovery experiments. The completed full-village run trained on 320 synthetic recovery examples, produced valid output for all 2,457 plots, and saved the fitted model artifact for reproducibility.")
    add_table(doc, ["Output status", "Meaning", "Geometry returned"], [
        ["corrected", "Visual and spatial evidence passed the decision rules.", "Predicted translated parcel boundary plus confidence and method note."],
        ["flagged", "Evidence is insufficient, conflicting, or the situation is likely not a placement-only error.", "Official parcel geometry retained, with a reason in the method note."],
    ], widths=[1.25, 3.05, 2.5])

    heading(doc, "7 Evaluation Results")
    add_para(doc, "The full independent run was evaluated against the available public example truths. These six examples are a small directional sample rather than a sufficient training set or complete estimate of hidden-set performance. They were not used to fit the alignment parameters.")
    add_table(doc, ["Metric", "Official input", "Independent prediction", "Interpretation"], [
        ["Plots processed", "2,457", "2,457", "Complete village output was generated."],
        ["Corrected plots", "Not applicable", "1,892", "Plots with adequate correction evidence."],
        ["Flagged plots", "Not applicable", "565", "Conservative retention for ambiguous or inconsistent cases."],
        ["Median IoU on 6 public truths", "0.584", "0.884", "+0.300 median improvement."],
        ["Median centroid error", "Not reported here", "2.739 m", "Typical remaining centre displacement after correction."],
        ["Public plots improved", "Baseline", "6 of 6", "All available public examples improved."],
        ["Invalid output geometries", "Not applicable", "0", "Final GeoJSON passed geometry validation."],
    ], widths=[2.0, 1.35, 1.55, 1.9])
    add_figure(doc, performance_figure, "Figure 3. Verified independent full-village performance and decision distribution.")
    add_para(doc, "A separate public reference benchmark achieved a median public IoU of 0.891 on a different validation setup. That number was used only as an exploratory comparison target. The 0.884 result reported above belongs to the independent implementation described in this report.")

    heading(doc, "8 Web Based Visual Review")
    add_para(doc, "A lightweight browser viewer supports human review of the results. The user uploads a PNG or JPEG satellite preview, the independent prediction GeoJSON, and optionally the official input GeoJSON. After entering the geographic extent of the preview image, the viewer overlays parcel boundaries. Blue represents official input geometry, green represents corrected predictions, and orange represents flagged plots. Clicking a plot displays its identifier, status, confidence, and method note.")
    add_para(doc, "The viewer is not part of the inference model. Its purpose is explainability and quality assurance. It allows reviewers to inspect high-confidence examples, borderline corrections, and flagged parcels rather than treating the GeoJSON output as a black box.")

    heading(doc, "9 Design Trade Offs")
    add_table(doc, ["Decision", "Benefit", "Trade off and mitigation"], [
        ["Classical computer vision instead of deep learning", "Works with limited labelled truth and remains interpretable.", "May miss semantic field cues; future work can add learned segmentation after more labels are available."],
        ["Outline matching instead of filled-polygon matching", "Focuses on boundaries and reduces sensitivity to crop colour.", "Weak where field edges are visually absent; use flagging rather than forced correction."],
        ["Per-plot image patches", "Uses local detail and avoids materializing a huge village-wide edge map.", "Repeated patch processing costs time; raster handles are reused to reduce overhead."],
        ["Global affine prior plus local residuals", "Balances stability and local adaptability.", "Residual interpolation can propagate local error; residuals are anchored only on inliers and clipped."],
        ["Conservative flagging", "Protects against over-correction and supports restraint.", "Reduces correction coverage; flagged parcels are explicitly exposed for manual review."],
        ["Public truths only for evaluation", "Avoids direct public-sample overfitting.", "Small public sample produces uncertain aggregate metrics; hidden-set validation remains necessary."],
    ], widths=[1.75, 2.35, 2.7])

    heading(doc, "10 Limitations and Risk Controls")
    add_bullet(doc, "Satellite images can contain shadows, tree cover, roofs, tracks, and crop texture that resemble field boundaries. The quality gates and RANSAC model reduce but cannot eliminate this risk.")
    add_bullet(doc, "A translation improves placement but cannot repair a fundamentally incorrect parcel shape or an area-record inconsistency. Those cases are intentionally flagged.")
    add_bullet(doc, "The public reference set contains only six truths. The reported improvement is encouraging but should not be interpreted as a complete estimate of generalization.")
    add_bullet(doc, "The Random Forest confidence model is trained with synthetic translations, so its real-world calibration should be confirmed on a larger held-out hand-aligned dataset.")
    add_bullet(doc, "The current method mainly applies rigid translations. Complex local rotation, scaling, or parcel reshaping is deliberately avoided because it could create topological conflicts among adjacent cadastral plots.")
    add_bullet(doc, "Valid geometry normalization is applied only to rare invalid source records. The decision remains flagged so the system does not falsely claim a confident correction.")

    heading(doc, "11 Future Refinement Scope")
    add_table(doc, ["Priority", "Refinement", "Expected value"], [
        ["High", "Obtain a larger held-out hand-aligned truth set across villages.", "Enables statistically credible calibration and comparison of design choices."],
        ["High", "Add topology-aware joint optimization for neighboring parcels.", "Can reduce gaps and overlaps while preserving shared boundaries."],
        ["High", "Improve confidence calibration with held-out or carefully simulated displacement data.", "Makes confidence scores more reliable for review prioritization."],
        ["Medium", "Use semantic segmentation or foundation-model features when labelled data permits.", "Can distinguish crop fields from roads, roofs, and vegetation more effectively."],
        ["Medium", "Support constrained rotation and scale refinement after translation.", "May improve fit where historical distortion is not purely translational."],
        ["Medium", "Prioritize human review by uncertainty and impact.", "Focuses manual effort on low-confidence or high-area parcels."],
        ["Low", "Parallelize patch matching and cache image transforms.", "Reduces full-village processing time without changing the decision logic."],
    ], widths=[0.85, 3.55, 2.4])

    heading(doc, "12 Reproducibility and Delivery")
    add_para(doc, "GeoAlign AI is organized as an independent repository with a fresh Git history. The core pipeline is in fieldalign/pipeline.py and the trained confidence estimator is in fieldalign/ml_confidence.py. The run_full.ps1 script trains the model, processes the full village, and invokes evaluate.py to validate the output and report public-truth metrics. The final prediction output and saved model are stored in data/vadnerbhairav. The viewer, validation demonstration assets, sample preview generator, visual QA shortlist, and teacher demonstration documents are included with the project.")
    add_para(doc, "For reproducibility, the only inference inputs are the challenge-provided GeoJSON and imagery files. Public example truths are excluded from the alignment fit. Large raster inputs are kept out of Git because they are challenge data, while code, documentation, evaluation logic, and generated prediction artifacts can be versioned separately.")

    heading(doc, "Conclusion")
    add_para(doc, "The project demonstrates an end-to-end approach to satellite-assisted parcel-boundary correction. It combines local visual evidence with robust village-scale and locally adaptive spatial reasoning, then makes a conservative correction-or-flag decision. The completed independent run improved all six available public reference parcels and produced a valid village-wide output. The next research step is not to overfit to the small public sample, but to strengthen validation, topology handling, and confidence calibration with broader independent ground truth.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.core_properties.title = "GeoAlign AI Technical Project Report"
    doc.core_properties.subject = "Project architecture, data processing, evaluation, trade-offs, and future refinement"
    doc.core_properties.author = ""
    doc.save(OUT)
    print(OUT.resolve())


if __name__ == "__main__":
    build()
