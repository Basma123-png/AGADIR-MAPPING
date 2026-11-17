#!/usr/bin/env python3
"""
Générateur de PDF professionnels et académiques pour le projet AGADIR MAPPING.
Compile les 4 documents principaux et les 3 annexes au format PDF via ReportLab Platypus.
"""

import html
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT_DIR / "documentation"
ATLAS_DIR = DOC_DIR / "atlas_visualisations"


class NumberedCanvas(canvas.Canvas):
    """Canvas personnalisé à deux passes pour numéroter 'Page X / Y' avec en-têtes et pieds de page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Ne pas afficher sur la page de couverture
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # En-tête courant
        header_text = getattr(self, "doc_title", "AGADIR MAPPING — Rapport Officiel")
        self.drawString(2 * cm, 28.5 * cm, header_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(2 * cm, 28.3 * cm, 19 * cm, 28.3 * cm)

        # Pied de page
        footer_left = "Basma OUAARAB & Fatimaezzahrae ELHAMDIOUI | Encadré par Mr BENHRA Jamal"
        page_str = f"Page {self._pageNumber} sur {page_count}"
        self.drawString(2 * cm, 1.2 * cm, footer_left)
        self.drawRightString(19 * cm, 1.2 * cm, page_str)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.4 * cm, 19 * cm, 1.4 * cm)

        self.restoreState()


def create_cover_page(story, doc_title, subtitle, nature_doc):
    """Génère une page de couverture institutionnelle et élégante."""
    styles = getSampleStyleSheet()

    # Placeholders institutionnels
    inst_style = ParagraphStyle(
        "CoverInst",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E3A5F"),
        alignment=TA_CENTER,
    )

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("[Établissement Universitaire — Placeholder Officiel]", inst_style))
    story.append(Paragraph("[Filière / Département de Spécialité — Placeholder Officiel]", inst_style))
    story.append(Paragraph("[Année Universitaire 2025-2026]", ParagraphStyle("CoverYear", parent=inst_style, fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#64748B"))))

    # Cadre logo placeholder
    logo_table = Table([["[Emplacement Logo Établissement Universitaire]"]], colWidths=[15 * cm], rowHeights=[2.2 * cm])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#94A3B8")),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
    ]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(logo_table)
    story.append(Spacer(1, 1.2 * cm))

    # Titre Principal
    story.append(Paragraph("AGADIR MAPPING", ParagraphStyle(
        "CoverMainTitle",
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=30,
        textColor=colors.HexColor("#1E3A5F"),
        alignment=TA_CENTER,
    )))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="60%", thickness=2, color=colors.HexColor("#2878B5"), spaceAfter=15, spaceBefore=5))
    story.append(Paragraph(subtitle, ParagraphStyle(
        "CoverSubtitle",
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#263445"),
        alignment=TA_CENTER,
    )))

    story.append(Spacer(1, 1.5 * cm))

    # Boîte Nature du Document
    nature_table = Table([[Paragraph(f"<b>NATURE DU LIVRABLE :</b><br/>{nature_doc}", ParagraphStyle("NatureP", fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#1E3A5F"), alignment=TA_CENTER))]], colWidths=[14 * cm])
    nature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#2878B5")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F4F7FA")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(nature_table)

    story.append(Spacer(1, 2.0 * cm))

    # Auteurs et Encadrement
    authors_data = [
        [
            Paragraph("<b>Projet Réalisé par :</b><br/><b>Basma OUAARAB</b><br/><b>Fatimaezzahrae ELHAMDIOUI</b>", ParagraphStyle("AuthL", fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#263445"))),
            Paragraph("<b>Sous l'Encadrement de :</b><br/><b>Mr BENHRA Jamal</b><br/>Enseignant-Chercheur", ParagraphStyle("AuthR", fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#263445"), alignment=TA_RIGHT))
        ]
    ]
    authors_table = Table(authors_data, colWidths=[8 * cm, 8 * cm])
    authors_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(authors_table)

    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("Version Officielle 7.1.0 — Validation Expérimentale & Reproduction Certifiée", ParagraphStyle("CoverFooter", fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER)))
    story.append(PageBreak())


def clean_inline_md(text):
    """Nettoie et convertit les balises Markdown inline en balises XML simples compatibles ReportLab."""
    if not text:
        return ""
    # Remplacer les entités XML sensibles
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    # 1. Code spans `code`
    text = re.sub(r"`([^`]+)`", r"<font face='Courier' color='#1E3A5F'><b>\1</b></font>", text)
    # 2. Bold **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # 3. Italic *text* (éviter de matcher à l'intérieur de balises existantes)
    text = re.sub(r"(?<!\*)\*([^*<>]+)\*(?!\*)", r"<i>\1</i>", text)
    # 4. Links [text](url) -> <u>text</u>
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"<u>\1</u>", text)
    
    # Formules mathématiques LaTeX simples $math$ (uniquement si contenu purement alphabétique/math sans balises)
    text = re.sub(r"\$([a-zA-Z\d\\_{}\^+\-=/ \(\)]+)\$", r"<i>\1</i>", text)
    
    return text


def safe_paragraph(raw_text, style, prefix=""):
    """Crée un paragraphe ReportLab de façon sécurisée avec fallback en texte brut en cas d'erreur de balise."""
    cleaned = clean_inline_md(raw_text)
    full_html = f"{prefix}{cleaned}" if prefix else cleaned
    try:
        return Paragraph(full_html, style)
    except Exception:
        # Fallback sans balises XML
        plain_text = re.sub(r"<[^>]+>", "", full_html)
        plain_text = plain_text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        plain_text = plain_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        try:
            return Paragraph(plain_text, style)
        except Exception:
            return Paragraph("[Contenu textuel]", style)


def parse_markdown_table(table_lines):
    """Transforme des lignes Markdown '| col1 | col2 |' en Table Platypus stylisée."""
    rows = []
    for line in table_lines:
        parts = [p.strip() for p in line.split("|")]
        # Retirer les colonnes vides créées par les séparateurs de bord
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        if not parts:
            continue
        # Ignorer la ligne de séparation |:---|:---|
        if all(re.match(r"^:?-+:?$", p) for p in parts):
            continue
        rows.append(parts)

    if not rows:
        return None

    # Normalisation du nombre de colonnes
    col_count = max(len(r) for r in rows)
    normalized_rows = []
    p_style_head = ParagraphStyle("THP", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=colors.HexColor("#FFFFFF"), alignment=TA_CENTER)
    p_style_body = ParagraphStyle("TDP", fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=colors.HexColor("#263445"))

    for row_idx, r in enumerate(rows):
        padded_r = r + [""] * (col_count - len(r))
        cur_style = p_style_head if row_idx == 0 else p_style_body
        formatted_row = [safe_paragraph(c, cur_style) for c in padded_r]
        normalized_rows.append(formatted_row)

    # Répartition des largeurs sur 16 cm au total
    col_w = (16.0 * cm) / col_count
    col_widths = [col_w] * col_count

    t = Table(normalized_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A5F")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#FFFFFF")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    return t


def markdown_to_platypus(md_text, styles):
    """Convertit un texte Markdown structuré en liste d'éléments Platypus avec tables et images."""
    flowables = []

    h1_style = ParagraphStyle("H1_Custom", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=colors.HexColor("#1E3A5F"), spaceBefore=14, spaceAfter=8, keepWithNext=True)
    h2_style = ParagraphStyle("H2_Custom", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#2878B5"), spaceBefore=12, spaceAfter=6, keepWithNext=True)
    h3_style = ParagraphStyle("H3_Custom", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=colors.HexColor("#1E3A5F"), spaceBefore=8, spaceAfter=4, keepWithNext=True)
    body_style = ParagraphStyle("Body_Custom", fontName="Helvetica", fontSize=9, leading=13.5, textColor=colors.HexColor("#263445"), alignment=TA_JUSTIFY, spaceAfter=6)
    bullet_style = ParagraphStyle("Bullet_Custom", fontName="Helvetica", fontSize=9, leading=13, textColor=colors.HexColor("#263445"), leftIndent=15, spaceAfter=3)
    callout_style = ParagraphStyle("Callout_Custom", fontName="Helvetica-Oblique", fontSize=8.5, leading=12.5, textColor=colors.HexColor("#1E3A5F"), leftIndent=12, rightIndent=12)

    lines = md_text.split("\n")
    i = 0
    in_table = False
    table_lines = []

    while i < len(lines):
        line = lines[i].strip()

        # Gestion des tables markdown
        if line.startswith("|") and line.endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            # Traitement de la table accumulée
            in_table = False
            table_flowable = parse_markdown_table(table_lines)
            if table_flowable:
                flowables.append(Spacer(1, 4))
                flowables.append(table_flowable)
                flowables.append(Spacer(1, 6))
            table_lines = []

        if not line:
            i += 1
            continue

        # Ligne horizontale
        if line in ("---", "***", "___"):
            flowables.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#E2E8F0"), spaceAfter=8, spaceBefore=8))
            i += 1
            continue

        # Titres
        if line.startswith("# "):
            flowables.append(safe_paragraph(line[2:], h1_style))
        elif line.startswith("## "):
            flowables.append(safe_paragraph(line[3:], h2_style))
        elif line.startswith("### "):
            flowables.append(safe_paragraph(line[4:], h3_style))
        elif line.startswith("#### "):
            flowables.append(safe_paragraph(line[5:], h3_style, prefix="<b>"))
        elif line.startswith("- ") or line.startswith("* "):
            flowables.append(safe_paragraph(line[2:], bullet_style, prefix="• "))
        elif re.match(r"^\d+\.\s", line):
            num_match = re.match(r"^(\d+\.)\s*(.*)", line)
            flowables.append(safe_paragraph(num_match.group(2), bullet_style, prefix=f"<b>{num_match.group(1)}</b> "))
        elif line.startswith(">"):
            quote_text = line.lstrip("> ")
            callout_table = Table([[safe_paragraph(quote_text, callout_style)]], colWidths=[16 * cm])
            callout_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                ('LINELEFT', (0,0), (-1,-1), 2.5, colors.HexColor("#2878B5")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            flowables.append(Spacer(1, 4))
            flowables.append(callout_table)
            flowables.append(Spacer(1, 4))
        elif line.startswith("```"):
            # Bloc de code ou diagramme
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            escaped_code = [html.escape(cl).replace(" ", "&nbsp;") for cl in code_lines[:15]]
            code_text = "<br/>".join(escaped_code)
            code_para = Paragraph(f"<font face='Courier' size=7.5 color='#1E293B'>{code_text}</font>", ParagraphStyle("CodeP", fontName="Courier", fontSize=7.5, leading=10))
            code_table = Table([[code_para]], colWidths=[16 * cm])
            code_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            flowables.append(Spacer(1, 4))
            flowables.append(code_table)
            flowables.append(Spacer(1, 4))
        else:
            flowables.append(safe_paragraph(line, body_style))

        i += 1

    # Traitement d'une éventuelle table finale
    if in_table and table_lines:
        t = parse_markdown_table(table_lines)
        if t:
            flowables.append(t)

    return flowables


def build_pdf_document(output_pdf_path, md_file_path, doc_title, subtitle, nature_doc, figures_to_embed=None):
    """Compile un document PDF complet avec couverture, numérotation et figures."""
    print(f"Génération du PDF : {output_pdf_path.name}...")
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with open(md_file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # 1. Page de couverture
    create_cover_page(story, doc_title, subtitle, nature_doc)

    # 2. Corps de document
    content_flowables = markdown_to_platypus(md_text, styles)
    story.extend(content_flowables)

    # 3. Insertion de figures emblématiques si spécifiées
    if figures_to_embed:
        story.append(PageBreak())
        story.append(Paragraph("ANNEXE VISUELLE — SÉLECTION DE FIGURES CERTIFIÉES", ParagraphStyle("FigTitle", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#1E3A5F"), spaceBefore=10, spaceAfter=15)))
        for fig_path, caption in figures_to_embed:
            if fig_path.exists():
                story.append(Spacer(1, 0.4 * cm))
                img = Image(str(fig_path), width=15 * cm, height=9 * cm)
                story.append(img)
                story.append(Spacer(1, 0.2 * cm))
                story.append(Paragraph(f"<b>Figure :</b> {caption}", ParagraphStyle("CaptionP", fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=colors.HexColor("#475569"), alignment=TA_CENTER)))
                story.append(Spacer(1, 0.6 * cm))

    # Compilation avec NumberedCanvas
    def canvas_maker(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.doc_title = doc_title
        return c

    doc.build(story, canvasmaker=canvas_maker)
    print(f"✓ PDF compilé avec succès : {output_pdf_path}")


def main():
    print("================================================================================")
    print("AGADIR MAPPING — COMPILATION OFFICIELLE DES LIVRABLES PDF")
    print("Auteurs : Basma OUAARAB & Fatimaezzahrae ELHAMDIOUI")
    print("Encadrant : Mr BENHRA Jamal")
    print("================================================================================")

    # 1. Document 1 : Rapport Scientifique et Technique Complet
    fig_selection_rapport = [
        (ATLAS_DIR / "cartes" / "carte_tournee_optimisee.png", "Circuit ATSP Optimal Certifié d'Agadir (18 933,1 m, 42 arrêts)"),
        (ATLAS_DIR / "cartes" / "carte_comparative_phase4_phase5.png", "Comparaison Cartographique Phase 4 (21 014,3 m) vs Phase 5 (18 933,1 m)"),
        (ATLAS_DIR / "graphiques" / "phase8_algorithm_comparison_benchmark.png", "Benchmark Expérimental des 5 Algorithmes Évalués"),
        (ATLAS_DIR / "diagrammes" / "architecture_multi_agents.png", "Architecture de Gouvernance Tripartite Multi-Agents, Judge et Veto Python"),
    ]
    build_pdf_document(
        output_pdf_path=DOC_DIR / "rapport_general" / "AGADIR_MAPPING_Rapport_Complet.pdf",
        md_file_path=DOC_DIR / "rapport_general" / "AGADIR_MAPPING_Rapport_Complet.md",
        doc_title="AGADIR MAPPING — Rapport Scientifique et Technique Complet",
        subtitle="Conception et Développement d'un Système Intelligent de Cartographie Urbaine et d'Optimisation Logistique à Agadir",
        nature_doc="Rapport Scientifique et Technique Universitaire Exhaustif (Phases 1 à 8)",
        figures_to_embed=fig_selection_rapport,
    )

    # 2. Document 2 : Spécifications Fonctionnelles
    fig_selection_fonc = [
        (ATLAS_DIR / "diagrammes" / "uml_cas_utilisation.png", "Diagramme UML des Cas d'Utilisation Métier"),
        (ATLAS_DIR / "cartes" / "carte_40_points_agadir.png", "Semis Spatial des 40 Points de Livraison et du Dépôt Central"),
    ]
    build_pdf_document(
        output_pdf_path=DOC_DIR / "documentation_fonctionnelle" / "AGADIR_MAPPING_Specifications_Fonctionnelles.pdf",
        md_file_path=DOC_DIR / "documentation_fonctionnelle" / "AGADIR_MAPPING_Specifications_Fonctionnelles.md",
        doc_title="AGADIR MAPPING — Spécifications Fonctionnelles Détaillées",
        subtitle="Dossier d'Analyse des Besoins, Règles Métier, Cas d'Utilisation et Modélisation Fonctionnelle",
        nature_doc="Spécifications Fonctionnelles & Cahier des Charges Logiciel",
        figures_to_embed=fig_selection_fonc,
    )

    # 3. Document 3 : Documentation Technique
    fig_selection_tech = [
        (ATLAS_DIR / "diagrammes" / "uml_composants_systeme.png", "Diagramme UML des Composants Logiciels Python"),
        (ATLAS_DIR / "diagrammes" / "uml_deploiement_systeme.png", "Architecture de Déploiement Client / Serveur HTTP REST"),
        (ATLAS_DIR / "graphiques" / "distance_matrix_heatmap.png", "Heatmap Asymétrique de la Matrice OSRM 41x41"),
    ]
    build_pdf_document(
        output_pdf_path=DOC_DIR / "documentation_technique" / "AGADIR_MAPPING_Documentation_Technique.pdf",
        md_file_path=DOC_DIR / "documentation_technique" / "AGADIR_MAPPING_Documentation_Technique.md",
        doc_title="AGADIR MAPPING — Documentation Technique Complète",
        subtitle="Architecture Logicielle, Spécifications des Modules, API REST, Sécurité et Traçabilité",
        nature_doc="Dossier d'Architecture Technique, Guide Développeur et Assurance Qualité",
        figures_to_embed=fig_selection_tech,
    )

    # 4. Document 4 : Guide Utilisateur
    fig_selection_user = [
        (ATLAS_DIR / "captures_dashboard" / "cadran1_cartographie_agadir.jpg", "Capture Réelle de la Cartographie Leaflet d'Agadir (Cadran 1)"),
        (ATLAS_DIR / "graphiques" / "profil_etapes_tournee.png", "Profil des 41 Étapes et Arrêt Côtier #40"),
    ]
    build_pdf_document(
        output_pdf_path=DOC_DIR / "guide_utilisateur" / "AGADIR_MAPPING_Guide_Utilisateur.pdf",
        md_file_path=DOC_DIR / "guide_utilisateur" / "AGADIR_MAPPING_Guide_Utilisateur.md",
        doc_title="AGADIR MAPPING — Guide Utilisateur Officiel",
        subtitle="Manuel Pratique d'Installation, d'Exécution et d'Exploitation du Tableau de Bord à Quatre Cadrans",
        nature_doc="Guide Utilisateur et Manuel d'Exploitation Opérationnel",
        figures_to_embed=fig_selection_user,
    )

    # 5. Annexe 1 : Glossaire
    build_pdf_document(
        output_pdf_path=DOC_DIR / "annexes" / "glossaire.pdf",
        md_file_path=DOC_DIR / "annexes" / "glossaire.md",
        doc_title="AGADIR MAPPING — Glossaire Scientifique et Technique",
        subtitle="Définitions Terminologiques Bilingues Français / Anglais",
        nature_doc="Annexe Terminologique & Lexique",
    )

    # 6. Annexe 2 : Bibliographie
    build_pdf_document(
        output_pdf_path=DOC_DIR / "annexes" / "bibliographie.pdf",
        md_file_path=DOC_DIR / "annexes" / "bibliographie.md",
        doc_title="AGADIR MAPPING — Bibliographie et Webographie Officielles",
        subtitle="Publications Scientifiques, Ouvrages et Sources Documentaires (Format APA 7)",
        nature_doc="Annexe Bibliographique & Sources Officielles",
    )

    # 7. Annexe 3 : Inventaire des Modules
    build_pdf_document(
        output_pdf_path=DOC_DIR / "annexes" / "inventaire_modules.pdf",
        md_file_path=DOC_DIR / "annexes" / "inventaire_modules.md",
        doc_title="AGADIR MAPPING — Inventaire Technique des Modules",
        subtitle="Dictionnaire Exhaustif des Composants Logiciels, Classes, Fonctions et Tests",
        nature_doc="Annexe Technique d'Ingénierie Logicielle",
    )

    print("\n✓ Tous les 7 documents PDF ont été générés avec succès.")


if __name__ == "__main__":
    main()
