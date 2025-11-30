"""
src/services/pdf_service.py
Generates Bilingual PDF Reports.
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from loguru import logger
from utils.paths import get_resource_path

class PDFService:
    def __init__(self):
        self.fonts = {}
        self._register_fonts()

    def _register_fonts(self):
        """
        Registers bundled fonts. Falls back to Helvetica if missing.
        """
        self.fonts = {'Hindi': 'Helvetica', 'Latin': 'Helvetica'}
        
        try:
            font_dir = get_resource_path("src/resources/fonts")
            
            # Register Hindi
            hindi_path = font_dir / "NotoSansDevanagari-Regular.ttf"
            if hindi_path.exists():
                pdfmetrics.registerFont(TTFont('Hindi', str(hindi_path)))
                self.fonts['Hindi'] = 'Hindi'
                
            # Register Latin
            latin_path = font_dir / "NotoSans-Regular.ttf"
            if latin_path.exists():
                pdfmetrics.registerFont(TTFont('Latin', str(latin_path)))
                self.fonts['Latin'] = 'Latin'
                
        except Exception as e:
            logger.error(f"Font Reg Error: {e} - Using Helvetica default.")

    def generate_report(self, filepath, original_text, translated_text, insights, doc_type, lang):
        try:
            self._build_pdf(filepath, original_text, translated_text, insights, doc_type, lang)
        except Exception as e:
            logger.error(f"PDF Build Failed: {e}")
            raise e

    def _build_pdf(self, filepath, original_text, translated_text, insights, doc_type, lang):
        doc = SimpleDocTemplate(filepath, pagesize=LETTER)
        elements = []
        styles = getSampleStyleSheet()
        
        # Ensure we always have a valid font name
        target_font = self.fonts.get('Hindi', 'Helvetica') if lang == "Hindi" else self.fonts.get('Latin', 'Helvetica')
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName=self.fonts['Latin'])
        meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontName=self.fonts['Latin'])
        normal_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName=self.fonts['Latin'])
        trans_style = ParagraphStyle('Trans', parent=styles['BodyText'], fontName=target_font)

        elements.append(Paragraph("MediTranslate Report", title_style))
        type_str = str(doc_type) if doc_type else "Unknown"
        lang_str = str(lang) if lang else "English"
        elements.append(Paragraph(f"Type: {type_str} | Language: {lang_str}", meta_style))
        elements.append(Spacer(1, 20))

        orig_str = str(original_text) if original_text else ""
        trans_str = str(translated_text) if translated_text else ""
        
        orig_paragraphs = orig_str.split('\n')
        trans_paragraphs = trans_str.split('\n')
        
        data = [[
            Paragraph("<b>ORIGINAL TEXT</b>", normal_style), 
            Paragraph(f"<b>{lang_str.upper()}</b>", trans_style)
        ]]
        
        max_len = max(len(orig_paragraphs), len(trans_paragraphs))
        for i in range(max_len):
            o_txt = orig_paragraphs[i] if i < len(orig_paragraphs) else ""
            t_txt = trans_paragraphs[i] if i < len(trans_paragraphs) else ""
            
            if not o_txt.strip() and not t_txt.strip(): continue
                
            data.append([
                Paragraph(o_txt, normal_style),
                Paragraph(t_txt, trans_style)
            ])
        
        t = Table(data, colWidths=[230, 230])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 30))
        
        if insights:
            elements.append(Paragraph("Medical Insights", title_style))
            elements.append(Spacer(1, 10))

            for item in insights:
                # Safe Access with defaults
                title = str(item.get('title', 'Unknown'))
                desc = str(item.get('desc', ''))
                
                trans_title = str(item.get('trans_title', title))
                trans_desc = str(item.get('trans_desc', desc))
                
                # Rows: Title (Eng/Target), Desc (Eng/Target)
                card_data = [
                    [Paragraph(f"<b>{title}</b>", normal_style), Paragraph(f"<b>{trans_title}</b>", trans_style)],
                    [Paragraph(desc, normal_style), Paragraph(trans_desc, trans_style)]
                ]
                
                c_table = Table(card_data, colWidths=[230, 230])
                c_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.aliceblue),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('LINEAFTER', (0, 0), (0, -1), 1, colors.lightgrey)
                ]))
                
                elements.append(c_table)
                elements.append(Spacer(1, 10))

        doc.build(elements)
        logger.success(f"PDF Report saved to {filepath}")