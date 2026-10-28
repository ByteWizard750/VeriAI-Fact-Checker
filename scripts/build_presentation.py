"""
VeriAI Final PowerPoint Presentation Generator
Creates submission/VeriAI_Final_Presentation.pptx
16:9 Widescreen, 16 academic review slides with embedded figures, tables, and metric callouts.
"""

import os
import sys

# Ensure project root is in sys.path and set as current working directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

import json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def load_results():
    with open('submission/experiment_results.json', 'r') as f:
        return json.load(f)

def create_presentation():
    results = load_results()
    prs = Presentation()
    
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide
    
    # Theme Palette
    c_navy = RGBColor(15, 42, 74)       # #0F2A4A - Primary Deep Navy
    c_dark = RGBColor(15, 23, 42)       # #0F172A - Title text
    c_blue = RGBColor(37, 99, 235)      # #2563EB - Royal Blue accent
    c_slate = RGBColor(71, 85, 105)     # #475569 - Secondary body text
    c_light_bg = RGBColor(248, 250, 252)# #F8FAFC - Card background
    c_border = RGBColor(203, 213, 225)  # #CBD5E1 - Border
    c_white = RGBColor(255, 255, 255)
    c_green = RGBColor(5, 150, 105)     # #059669 - Positive
    c_red = RGBColor(220, 38, 38)       # #DC2626 - Alert/Fake

    def add_header(slide, title_text, category_text="VERIAI | DECISION ANALYTICS FINAL REVIEW"):
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.9))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_cat = tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = 'Calibri'
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = c_blue
        
        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.name = 'Calibri'
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = c_navy
        
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.73), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = c_border
        line.line.color.rgb = c_border

    def add_card(slide, left, top, width, height, bg_color=c_light_bg, border_color=c_border):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    def add_bullet_run(paragraph, bold_text, desc_text, bold_color=c_blue, desc_color=c_slate, bold_size=Pt(11.5), desc_size=Pt(11)):
        r_b = paragraph.add_run()
        r_b.text = bold_text
        r_b.font.bold = True
        r_b.font.size = bold_size
        r_b.font.color.rgb = bold_color
        
        r_d = paragraph.add_run()
        r_d.text = desc_text
        r_d.font.bold = False
        r_d.font.size = desc_size
        r_d.font.color.rgb = desc_color

    # ==========================================
    # SLIDE 1: TITLE SLIDE
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = c_navy
    bg1.line.color.rgb = c_navy
    
    tb1 = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(4.2), Inches(0.4))
    tb1.fill.solid()
    tb1.fill.fore_color.rgb = RGBColor(30, 58, 95)
    tb1.line.color.rgb = c_blue
    tf_b = tb1.text_frame
    tf_b.paragraphs[0].text = "ACADEMIC FINAL PROJECT REVIEW | 2026"
    tf_b.paragraphs[0].font.size = Pt(11)
    tf_b.paragraphs[0].font.bold = True
    tf_b.paragraphs[0].font.color.rgb = RGBColor(147, 197, 253)
    tf_b.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    title_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(2.5))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    
    p1 = tf1.paragraphs[0]
    p1.text = "VeriAI: Real-Time Fact Verification & Explainable AI"
    p1.font.name = 'Calibri'
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = c_white
    
    p2 = tf1.add_paragraph()
    p2.text = "Dual-Stream Semantic Grounding, Atomic Decomposition, and SHAP Feature Attribution"
    p2.font.name = 'Calibri'
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(191, 219, 254)
    p2.space_before = Pt(8)

    c_auth = add_card(slide1, Inches(1.0), Inches(4.5), Inches(11.3), Inches(1.9), bg_color=RGBColor(24, 52, 88), border_color=RGBColor(59, 130, 246))
    tf_a = c_auth.text_frame
    tf_a.word_wrap = True
    tf_a.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    pa1 = tf_a.paragraphs[0]
    pa1.text = "Project Team & Institutional Details"
    pa1.font.size = Pt(12)
    pa1.font.bold = True
    pa1.font.color.rgb = RGBColor(147, 197, 253)
    
    pa2 = tf_a.add_paragraph()
    pa2.text = "Student Researchers:  Rohan (rayavarapurohan2006@gmail.com)  |  Lakshya Kumar Singh (lakshyakumarsingh1@gmail.com)\nDepartment:               School of Computer Science & Engineering (SCOPE)\nInstitution:                  Vellore Institute of Technology (VIT), Chennai\nCourse / Focus:            Decision Analytics & Applied Machine Learning | Explainable AI (XAI) Track"
    pa2.font.size = Pt(11)
    pa2.font.color.rgb = c_white
    pa2.space_before = Pt(6)

    # ==========================================
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Problem Statement & The Disinformation Dilemma")
    
    add_card(slide2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    tb_l = slide2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    
    p = tf_l.paragraphs[0]
    p.text = "The Threat of Digital Disinformation"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = c_navy
    
    bullets_l = [
        ("• Exponential Spread: ", "False narratives diffuse 6x faster than truthful reporting on social networks, exacerbating societal polarization and public risk."),
        ("• Synthetic Content: ", "Generative AI tools enable bad actors to mass-produce structurally convincing propaganda at near-zero marginal cost."),
        ("• High-Stakes Decisions: ", "In financial markets, health crises, and elections, stakeholders require instant verification before acting on unverified reports."),
        ("• Regulatory Mandates: ", "Global compliance frameworks (e.g., EU AI Act) mandate explainable, auditable reasoning rather than unverified binary predictions.")
    ]
    for b_title, b_desc in bullets_l:
        p = tf_l.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_blue, desc_color=c_slate)

    add_card(slide2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=RGBColor(254, 242, 242), border_color=RGBColor(254, 202, 202))
    tb_r = slide2.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    
    p = tf_r.paragraphs[0]
    p.text = "The 'Black Box' & False Confidence Trap"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = c_red
    
    bullets_r = [
        ("• Opaque Outputs: ", "Traditional deep learning classifiers output solitary binary labels (e.g., 'Fake 87%') with zero provenance or factual justification."),
        ("• User Distrust: ", "When users cannot see why an article is flagged, adoption drops and skepticism towards automated fact-checkers increases."),
        ("• Zero Error Recovery: ", "If an authentic breaking story uses unusual vocabulary, an isolated NLP model rejects it without recourse to live corroboration."),
        ("• Need for Dual Assurance: ", "Users need linguistic style evaluation AND authoritative real-world evidence presented in an interactive dashboard.")
    ]
    for b_title, b_desc in bullets_r:
        p = tf_r.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_red, desc_color=c_slate)

    # ==========================================
    # SLIDE 3: RESEARCH GAP & OBJECTIVES
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Research Gaps & Project Objectives")
    
    col_w = Inches(3.7)
    gap = Inches(0.3)
    
    cards_s3 = [
        ("GAP 1: Linguistic Shortcutting", "Models learn publisher metadata ('Reuters', 'said') instead of verifying claims.", "Objective 1: Expose Bias via SHAP", "Compute exact Shapley attributions to quantify stylistic shortcuts and establish an auditable Journalistic Style Index.", c_blue),
        ("GAP 2: Static Knowledge Limits", "Corpus-trained models cannot verify fresh breaking events or contemporary claims.", "Objective 2: Live Multi-Feed Retrieval", "Deploy asynchronous web retrieval across Google News RSS and DuckDuckGo to extract contemporary evidence dynamically.", c_green),
        ("GAP 3: Coarse Unstructured Labels", "Paragraph-level labels fail to identify nuanced half-truths and mixed assertions.", "Objective 3: Atomic NLI Decomposition", "Decompose statements into atomic propositions and compute cross-encoder NLI (Entailment / Contradiction) with calibrated confidence.", c_navy)
    ]
    
    for idx, (g_title, g_desc, o_title, o_desc, color) in enumerate(cards_s3):
        left_pos = Inches(0.8) + idx * (col_w + gap)
        add_card(slide3, left_pos, Inches(1.6), col_w, Inches(5.3))
        
        tb = slide3.shapes.add_textbox(left_pos + Inches(0.2), Inches(1.8), col_w - Inches(0.4), Inches(4.9))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = g_title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = c_red
        
        p_gd = tf.add_paragraph()
        p_gd.text = g_desc
        p_gd.font.size = Pt(11)
        p_gd.font.color.rgb = c_slate
        p_gd.space_before = Pt(4)
        
        p_div = tf.add_paragraph()
        p_div.text = "--------------------------------------"
        p_div.font.size = Pt(8)
        p_div.font.color.rgb = c_border
        p_div.space_before = Pt(12)
        
        p_oh = tf.add_paragraph()
        p_oh.text = o_title
        p_oh.font.size = Pt(14)
        p_oh.font.bold = True
        p_oh.font.color.rgb = color
        p_oh.space_before = Pt(8)
        
        p_od = tf.add_paragraph()
        p_od.text = o_desc
        p_od.font.size = Pt(11.5)
        p_od.font.color.rgb = c_dark
        p_od.space_before = Pt(6)

    # ==========================================
    # SLIDE 4: EXISTING APPROACHES & LIMITATIONS
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Comparative Analysis of Existing Approaches")
    
    t_shape = slide4.shapes.add_table(6, 6, Inches(0.8), Inches(1.6), Inches(11.73), Inches(3.6))
    table = t_shape.table
    
    headers = ["Approach / Framework", "Benchmark Dataset", "Core Architecture", "Explainability", "Live Retrieval", "Verification Scope"]
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = c_navy
        p = cell.text_frame.paragraphs[0]
        p.font.name = 'Calibri'
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = c_white
        p.alignment = PP_ALIGN.CENTER
        
    rows_data = [
        ["FakeNewsNet (Shu et al., 2017)", "PolitiFact / GossipCop", "GNN + Social Context", "Attention Heatmaps", "No (Static)", "Graph Topology"],
        ["LIAR Benchmark (Wang, 2017)", "PolitiFact (12.8k)", "CNN / BiLSTM", "None (Black Box)", "No (Static)", "Short Statements"],
        ["FEVER (Thorne et al., 2018)", "Wikipedia (185k)", "MLP / DeBERTa", "Sentence Selection", "No (Pre-indexed)", "Wikipedia Scope"],
        ["LIME Text (Ribeiro et al., 2016)", "General Corpora", "Sparse Linear Surrogate", "Perturbation Weights", "No", "Local Surrogates"],
        ["VeriAI (Proposed)", "ISOT + LIAR (57.7k)", "TF-IDF + Calibrated LR", "SHAP Linear Explainer", "Yes (RSS + DDG)", "Dual-Stream Grounding"]
    ]
    for r_idx, r_vals in enumerate(rows_data):
        for c_idx, val in enumerate(r_vals):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            if r_idx == 4:
                cell.fill.fore_color.rgb = RGBColor(239, 246, 255)
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(248, 250, 252)
            else:
                cell.fill.fore_color.rgb = c_white
                
            p = cell.text_frame.paragraphs[0]
            p.font.name = 'Calibri'
            p.font.size = Pt(10)
            if r_idx == 4:
                p.font.bold = True
                p.font.color.rgb = c_blue
            else:
                p.font.color.rgb = c_dark
            if c_idx >= 3:
                p.alignment = PP_ALIGN.CENTER
                
    add_card(slide4, Inches(0.8), Inches(5.4), Inches(11.73), Inches(1.5), bg_color=RGBColor(240, 253, 244), border_color=RGBColor(187, 247, 208))
    tb_bot = slide4.shapes.add_textbox(Inches(1.0), Inches(5.5), Inches(11.33), Inches(1.3))
    tf_b = tb_bot.text_frame
    tf_b.word_wrap = True
    
    pb = tf_b.paragraphs[0]
    pb.text = "Key Takeaway: The Critical Research Gap"
    pb.font.size = Pt(13)
    pb.font.bold = True
    pb.font.color.rgb = c_green
    
    pb2 = tf_b.add_paragraph()
    pb2.text = "No prior system provides end-to-end integration of (1) closed-form Shapley game-theoretic word attribution, (2) microsecond inference latency, and (3) live multi-source web evidence retrieval with atomic NLI decomposition. VeriAI is engineered specifically to close this multi-dimensional gap."
    pb2.font.size = Pt(11)
    pb2.font.color.rgb = c_dark
    pb2.space_before = Pt(3)

    # ==========================================
    # SLIDE 5: PROPOSED ARCHITECTURE & WORKFLOW
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Proposed Architecture: Dual-Stream Verification Pipeline")
    
    if os.path.exists('submission/figures/fig1_architecture.png'):
        slide5.shapes.add_picture('submission/figures/fig1_architecture.png', Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.3))
        
    add_card(slide5, Inches(8.5), Inches(1.6), Inches(4.0), Inches(5.3))
    tb_steps = slide5.shapes.add_textbox(Inches(8.7), Inches(1.8), Inches(3.6), Inches(4.9))
    tf_s = tb_steps.text_frame
    tf_s.word_wrap = True
    
    ps = tf_s.paragraphs[0]
    ps.text = "5-Stage Verification Workflow"
    ps.font.size = Pt(15)
    ps.font.bold = True
    ps.font.color.rgb = c_navy
    
    steps = [
        ("1. Preprocessing: ", "RegEx cleaning, stopword removal, lemmatization, 10k TF-IDF projection."),
        ("2. Stream 1 (NLP + SHAP): ", "Calibrated Logistic Regression & LinearExplainer compute exact word Shapley values."),
        ("3. Stream 2 (Evidence): ", "Dynamic Boolean queries search Google RSS & DuckDuckGo for live reporting."),
        ("4. NLI Reasoning: ", "Atomic decomposition evaluated via DeBERTa-v3 & Gemini 3.5."),
        ("5. Hybrid Synthesis: ", "Reconciles style with ground truth to produce final calibrated verdict.")
    ]
    for s_title, s_desc in steps:
        p = tf_s.add_paragraph()
        p.space_before = Pt(8)
        add_bullet_run(p, s_title, s_desc, bold_color=c_blue, desc_color=c_slate, bold_size=Pt(11), desc_size=Pt(10.5))

    # ==========================================
    # SLIDE 6: DATASET & EXPERIMENTAL SETUP
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Dataset Composition & Experimental Protocol")
    
    dp = results['dataset_profile']
    add_card(slide6, Inches(0.8), Inches(1.6), Inches(3.7), Inches(1.4), bg_color=RGBColor(239, 246, 255), border_color=RGBColor(191, 219, 254))
    tb_s1 = slide6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(3.3), Inches(1.2))
    tb_s1.text_frame.paragraphs[0].text = "57,689 Total Articles"
    tb_s1.text_frame.paragraphs[0].font.size = Pt(22)
    tb_s1.text_frame.paragraphs[0].font.bold = True
    tb_s1.text_frame.paragraphs[0].font.color.rgb = c_blue
    p = tb_s1.text_frame.add_paragraph()
    p.text = "ISOT (44.9k) + LIAR (12.8k) Multi-Source Pool"
    p.font.size = Pt(10)
    p.font.color.rgb = c_slate
    
    add_card(slide6, Inches(4.8), Inches(1.6), Inches(3.7), Inches(1.4), bg_color=RGBColor(240, 253, 244), border_color=RGBColor(187, 247, 208))
    tb_s2 = slide6.shapes.add_textbox(Inches(5.0), Inches(1.7), Inches(3.3), Inches(1.2))
    tb_s2.text_frame.paragraphs[0].text = "15,000 Stratified"
    tb_s2.text_frame.paragraphs[0].font.size = Pt(22)
    tb_s2.text_frame.paragraphs[0].font.bold = True
    tb_s2.text_frame.paragraphs[0].font.color.rgb = c_green
    p = tb_s2.text_frame.add_paragraph()
    p.text = "12,000 Train (80%) | 3,000 Holdout Test (20%)"
    p.font.size = Pt(10)
    p.font.color.rgb = c_slate

    add_card(slide6, Inches(8.8), Inches(1.6), Inches(3.73), Inches(1.4), bg_color=RGBColor(254, 243, 199), border_color=RGBColor(253, 230, 138))
    tb_s3 = slide6.shapes.add_textbox(Inches(9.0), Inches(1.7), Inches(3.3), Inches(1.2))
    tb_s3.text_frame.paragraphs[0].text = "10,000 N-Grams"
    tb_s3.text_frame.paragraphs[0].font.size = Pt(22)
    tb_s3.text_frame.paragraphs[0].font.bold = True
    tb_s3.text_frame.paragraphs[0].font.color.rgb = RGBColor(180, 83, 9)
    p = tb_s3.text_frame.add_paragraph()
    p.text = "Sublinear TF-IDF (Unigrams & Bigrams)"
    p.font.size = Pt(10)
    p.font.color.rgb = c_slate

    add_card(slide6, Inches(0.8), Inches(3.2), Inches(11.73), Inches(3.7))
    tb_det = slide6.shapes.add_textbox(Inches(1.0), Inches(3.4), Inches(11.33), Inches(3.3))
    tf_d = tb_det.text_frame
    tf_d.word_wrap = True
    
    p = tf_d.paragraphs[0]
    p.text = "Experimental Rigor & Methodology"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = c_navy
    
    exp_bullets = [
        ("• Stratified Holdout Protocol: ", f"Training split: {dp['train_class_distribution']['fake']} Fake, {dp['train_class_distribution']['true']} True. Testing split: {dp['test_class_distribution']['fake']} Fake, {dp['test_class_distribution']['true']} True (Exact 50/50 balance, random seed 42)."),
        ("• Models Evaluated: ", "Logistic Regression (L2 regularized), Multinomial Naive Bayes (alpha=1.0), Random Forest (100 trees), XGBoost (100 estimators), and LightGBM (100 estimators)."),
        ("• Comprehensive Metrics: ", "Accuracy, Precision, Recall, Macro F1, ROC-AUC, Brier Score (probability loss), Expected Calibration Error (ECE across 10 bins), and Inference Latency per sample."),
        ("• Hardware Environment: ", "Benchmarked on Apple Silicon (M-series, ARM64) running Python 3.13, Scikit-Learn 1.7.0, XGBoost 3.1.1, and LightGBM 4.6.0.")
    ]
    for b_title, b_desc in exp_bullets:
        p = tf_d.add_paragraph()
        p.space_before = Pt(8)
        add_bullet_run(p, b_title, b_desc, bold_color=c_blue, desc_color=c_dark, bold_size=Pt(11.5), desc_size=Pt(11))

    # ==========================================
    # SLIDE 7: BASELINE MODEL RESULTS
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Baseline Model Results & Deployment Selection")
    
    t_shape7 = slide7.shapes.add_table(6, 6, Inches(0.8), Inches(1.6), Inches(6.8), Inches(3.5))
    t7 = t_shape7.table
    
    headers7 = ["Classifier", "Accuracy", "F1-Score", "ROC-AUC", "ECE", "Latency"]
    for c_idx, h in enumerate(headers7):
        cell = t7.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = c_navy
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = c_white
        p.alignment = PP_ALIGN.CENTER
        
    for r_idx, (m_name, m_res) in enumerate(results['baseline_evaluations'].items()):
        row_vals = [
            m_name.replace(" (Deployed)", ""),
            f"{m_res['accuracy']*100:.2f}%",
            f"{m_res['f1_score']:.4f}",
            f"{m_res['roc_auc']:.4f}",
            f"{m_res['ece']:.4f}",
            f"{m_res['inference_latency_ms']*1000:.1f} µs"
        ]
        for c_idx, val in enumerate(row_vals):
            cell = t7.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = RGBColor(236, 253, 245)
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(248, 250, 252)
            else:
                cell.fill.fore_color.rgb = c_white
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            if r_idx == 0:
                p.font.bold = True
                p.font.color.rgb = c_green
            else:
                p.font.color.rgb = c_dark
            if c_idx >= 1:
                p.alignment = PP_ALIGN.CENTER

    add_card(slide7, Inches(0.8), Inches(5.3), Inches(6.8), Inches(1.6), bg_color=c_light_bg)
    tb_cm = slide7.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(6.4), Inches(1.4))
    tf_cm = tb_cm.text_frame
    tf_cm.word_wrap = True
    pcm = tf_cm.paragraphs[0]
    pcm.text = "Deployed Logistic Regression Confusion Matrix (n=3,000)"
    pcm.font.size = Pt(11)
    pcm.font.bold = True
    pcm.font.color.rgb = c_navy
    pcm2 = tf_cm.add_paragraph()
    pcm2.text = "• True Negatives (Correctly Fake): 1,259 (86.11%)\n• True Positives (Correctly True): 1,409 (91.61%)\n• False Positives: 203 | False Negatives: 129 | Overall Accuracy: 88.93%"
    pcm2.font.size = Pt(10)
    pcm2.font.color.rgb = c_dark
    pcm2.space_before = Pt(2)

    if os.path.exists('submission/figures/fig3_confusion_matrix.png'):
        slide7.shapes.add_picture('submission/figures/fig3_confusion_matrix.png', Inches(7.8), Inches(1.6), Inches(4.7), Inches(3.6))
        
    add_card(slide7, Inches(7.8), Inches(5.3), Inches(4.73), Inches(1.6), bg_color=RGBColor(239, 246, 255), border_color=RGBColor(191, 219, 254))
    tb_rat = slide7.shapes.add_textbox(Inches(8.0), Inches(5.4), Inches(4.33), Inches(1.4))
    tf_rat = tb_rat.text_frame
    tf_rat.word_wrap = True
    prat = tf_rat.paragraphs[0]
    prat.text = "Why Deployed Logistic Regression Wins:"
    prat.font.size = Pt(11)
    prat.font.bold = True
    prat.font.color.rgb = c_blue
    prat2 = tf_rat.add_paragraph()
    prat2.text = "1. 8x Faster Latency: 0.4 µs vs. 3.3 µs (XGBoost).\n2. Closed-Form SHAP: Exact linear attribution in O(M) time.\n3. Calibrated Probabilities: Low ECE (0.0403) vs. Random Forest (0.1708)."
    prat2.font.size = Pt(10)
    prat2.font.color.rgb = c_dark
    prat2.space_before = Pt(2)

    # ==========================================
    # SLIDE 8: IMPLEMENTED XAI TECHNIQUES
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Implemented Explainable AI (XAI) Architecture")
    
    add_card(slide8, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_x1 = slide8.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf_x1 = tb_x1.text_frame
    tf_x1.word_wrap = True
    
    px1 = tf_x1.paragraphs[0]
    px1.text = "1. SHAP Linear Explainer Formulation"
    px1.font.size = Pt(15)
    px1.font.bold = True
    px1.font.color.rgb = c_navy
    
    x1_bullets = [
        ("• Axiomatic Foundation: ", "Grounded in cooperative game theory (Lundberg & Lee, 2017). Uniquely satisfies Efficiency, Symmetry, Dummy, and Additivity axioms."),
        ("• Closed-Form Solution: ", "phi_i(x) = beta_i * (x_i - E[x_i]). Computes exact token attributions without Monte Carlo sampling approximations."),
        ("• Microsecond Efficiency: ", "Explanation generation takes < 0.05 ms, allowing real-time word highlighting in the browser."),
        ("• Local Word Highlighting: ", "Positive terms highlighted in green (credibility boosters); negative terms highlighted in red (promotional risk).")
    ]
    for b_title, b_desc in x1_bullets:
        p = tf_x1.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_blue, desc_color=c_slate)

    add_card(slide8, Inches(6.8), Inches(1.6), Inches(5.73), Inches(5.3))
    tb_x2 = slide8.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf_x2 = tb_x2.text_frame
    tf_x2.word_wrap = True
    
    px2 = tf_x2.paragraphs[0]
    px2.text = "2. Journalistic Style Index & Risk Flags"
    px2.font.size = Pt(15)
    px2.font.bold = True
    px2.font.color.rgb = c_navy
    
    x2_bullets = [
        ("• Journalistic Style Index: ", "Quantifies formal objective reporting density vs sensational conversational phrasing on a 0-100 scale."),
        ("• Credibility-Boosting Terms: ", "Extracts attribution clauses (e.g., 'spokesman', 'statement', 'official') that ground professional news reports."),
        ("• Promotional & Emotional Risk: ", "Detects clickbait click-drivers (e.g., 'watch', 'video', 'shocking', 'breaking') that inflate sensationalism."),
        ("• UI Transparency: ", "Renders feature impact waterfall charts and style indices directly on the VeriAI frontend.")
    ]
    for b_title, b_desc in x2_bullets:
        p = tf_x2.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_green, desc_color=c_slate)

    # ==========================================
    # SLIDE 9: XAI EVALUATION METRICS & METHODOLOGY
    # ==========================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Formal XAI Evaluation Metrics & Formulas")
    
    w_card = Inches(5.7)
    h_card = Inches(2.55)
    
    grid = [
        ("1. Faithfulness (Comprehensiveness)", "Delta P = P(y|x) - P(y|x \\ S_k)", "Measures confidence drop when removing the top-k SHAP explanatory features. A faithful explanation must cause significantly greater degradation than random removal.", Inches(0.8), Inches(1.6), c_blue),
        ("2. Sufficiency", "Ratio = P(y|S_k) / P(y|x)", "Measures prediction retention when the model is presented ONLY with the top-k explanatory tokens. High sufficiency confirms explanations isolate the true core signal.", Inches(6.8), Inches(1.6), c_green),
        ("3. Stability & Robustness", "Jaccard = |E(x) cap E(x')| / |E(x) cup E(x')|", "Measures explanation consistency when input undergoes localized perturbation (e.g. minor typos or punctuation noise). High Jaccard confirms robustness against manipulation.", Inches(0.8), Inches(4.35), RGBColor(180, 83, 9)),
        ("4. Confidence Calibration", "ECE = sum_m (|B_m|/N) * |acc(B_m) - conf(B_m)|", "Evaluates whether predicted probabilities match empirical observation frequencies across 10 probability bins. Critical for trustworthy decision support.", Inches(6.8), Inches(4.35), c_navy)
    ]
    
    for title, formula, desc, l, t, color in grid:
        add_card(slide9, l, t, w_card, h_card)
        tb = slide9.shapes.add_textbox(l + Inches(0.2), t + Inches(0.15), w_card - Inches(0.4), h_card - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = color
        
        pf = tf.add_paragraph()
        pf.text = formula
        pf.font.size = Pt(11)
        pf.font.bold = True
        pf.font.color.rgb = c_navy
        pf.space_before = Pt(4)
        
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = c_slate
        pd.space_before = Pt(4)

    # ==========================================
    # SLIDE 10: QUANTITATIVE XAI BENCHMARK RESULTS
    # ==========================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "Empirical XAI Benchmark Results")
    
    xm = results['xai_metrics']
    t_shape10 = slide10.shapes.add_table(8, 3, Inches(0.8), Inches(1.6), Inches(6.2), Inches(5.3))
    t10 = t_shape10.table
    
    headers10 = ["XAI Metric", "Empirical Value", "Significance"]
    for c_idx, h in enumerate(headers10):
        cell = t10.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = c_navy
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = c_white
        p.alignment = PP_ALIGN.CENTER
        
    xai_rows = [
        ["Comprehensiveness (Top-10)", "0.1275", "2.7x higher than random (0.0465)"],
        ["Sufficiency (Top-10)", "0.8890 (88.9%)", "10 tokens retain 89% prediction"],
        ["Fidelity (Surrogate Corr.)", "r = 0.9984", "Near-perfect decision mimicry"],
        ["Stability (Jaccard Top-5)", "1.0000", "Zero explanation flip under noise"],
        ["Explanation Sparsity", "Gini = 0.4954", "Concentrated in compact tokens"],
        ["Actionability", "148.3 tokens", "High barrier against manipulation"],
        ["Confidence Calibration", "ECE = 0.0403", "Brier Score = 0.0778 (Well-calibrated)"]
    ]
    for r_idx, r_vals in enumerate(xai_rows):
        for c_idx, val in enumerate(r_vals):
            cell = t10.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r_idx % 2 == 1 else c_white
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            p.font.color.rgb = c_dark
            if c_idx == 1:
                p.font.bold = True
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = c_blue

    if os.path.exists('submission/figures/fig5_xai_faithfulness_ablation.png'):
        slide10.shapes.add_picture('submission/figures/fig5_xai_faithfulness_ablation.png', Inches(7.2), Inches(1.6), Inches(5.33), Inches(5.3))

    # ==========================================
    # SLIDE 11: EXPLANATION-GUIDED EVALUATION & INTERVENTIONS
    # ==========================================
    slide11 = prs.slides.add_slide(blank_layout)
    add_header(slide11, "Explanation-Guided Interventions: Neutralizing Bias")
    
    if os.path.exists('submission/figures/fig4_shap_global_importance.png'):
        slide11.shapes.add_picture('submission/figures/fig4_shap_global_importance.png', Inches(0.8), Inches(1.6), Inches(6.8), Inches(5.3))
        
    add_card(slide11, Inches(7.8), Inches(1.6), Inches(4.73), Inches(5.3), bg_color=RGBColor(240, 253, 244), border_color=RGBColor(187, 247, 208))
    tb_int = slide11.shapes.add_textbox(Inches(8.0), Inches(1.8), Inches(4.33), Inches(4.9))
    tf_int = tb_int.text_frame
    tf_int.word_wrap = True
    
    pint = tf_int.paragraphs[0]
    pint.text = "How the Evidence Stream Intervenes"
    pint.font.size = Pt(15)
    pint.font.bold = True
    pint.font.color.rgb = c_green
    
    interventions = [
        ("• The Discovery: ", "SHAP exposes that top 'True' words are wire markers ('said', 'reuter', 'wednesday'), while top 'Fake' words are media tags ('video', 'via')."),
        ("• The Vulnerability: ", "A fabricated rumor written in Reuters wire style fools pure NLP classifiers into high-confidence 'True' predictions."),
        ("• The Dual-Stream Fix: ", "VeriAI's Web Evidence Engine queries contemporary feeds. If no corroboration exists, the NLI module flags Contradiction."),
        ("• Automated Intervention: ", "Evidence grounding overrides the misleading linguistic prior, preventing disastrous false positives on propaganda.")
    ]
    for b_title, b_desc in interventions:
        p = tf_int.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_navy, desc_color=c_dark)

    # ==========================================
    # SLIDE 12: SENSITIVITY ANALYSIS
    # ==========================================
    slide12 = prs.slides.add_slide(blank_layout)
    add_header(slide12, "Hyperparameter Sensitivity Analysis")
    
    if os.path.exists('submission/figures/fig6_sensitivity_analysis.png'):
        slide12.shapes.add_picture('submission/figures/fig6_sensitivity_analysis.png', Inches(0.8), Inches(1.6), Inches(7.2), Inches(5.3))
        
    sa = results['sensitivity_analysis']
    add_card(slide12, Inches(8.2), Inches(1.6), Inches(4.33), Inches(5.3))
    tb_sa = slide12.shapes.add_textbox(Inches(8.4), Inches(1.8), Inches(3.93), Inches(4.9))
    tf_sa = tb_sa.text_frame
    tf_sa.word_wrap = True
    
    psa = tf_sa.paragraphs[0]
    psa.text = "Parameter Robustness Insights"
    psa.font.size = Pt(15)
    psa.font.bold = True
    psa.font.color.rgb = c_navy
    
    sa_bullets = [
        ("• Vocabulary Capacity: ", f"Expanding max features from 1k to 10k lifts F1 from {sa['vocab_f1_scores'][0]:.4f} to {sa['vocab_f1_scores'][3]:.4f}. Beyond 10k, gains plateau (+0.0001 at 15k) while doubling memory."),
        ("• Optimal Envelope: ", "10,000 features balances discriminatory power with < 15 MB model footprint."),
        ("• Regularization C: ", f"Optimal F1 achieved between C=1.0 ({sa['c_f1_scores'][3]:.4f}) and C=2.0 ({sa['c_f1_scores'][4]:.4f})."),
        ("• Over/Under Fitting: ", f"C=0.01 over-penalizes informative terms (F1={sa['c_f1_scores'][0]:.4f}); C=10.0 overfits on noisy bigrams (F1={sa['c_f1_scores'][6]:.4f}).")
    ]
    for b_title, b_desc in sa_bullets:
        p = tf_sa.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_blue, desc_color=c_slate, bold_size=Pt(11), desc_size=Pt(10.5))

    # ==========================================
    # SLIDE 13: FAILURE-CASE ANALYSIS
    # ==========================================
    slide13 = prs.slides.add_slide(blank_layout)
    add_header(slide13, "Failure-Case Analysis & Operational Diagnostics")
    
    w_fc = Inches(3.7)
    gap_fc = Inches(0.3)
    
    fail_cases = [
        ("Case 1: Breaking Local News", "Authentic breaking emergency reports (e.g., student fatalities) lack Reuters datelines and contain words like 'dead' or 'police'.", "NLP Failure Mode: ", "Linguistic model flags sensationalism risk and predicts Fake.", "VeriAI Mitigation: ", "Evidence Engine retrieves local police bulletins and regional reporting to rescue the claim as True.", c_blue),
        ("Case 2: Stylized Satirical News", "The Onion articles mimic Reuters editorial syntax ('said on Thursday'), using formal attribution verbs.", "NLP Failure Mode: ", "Linguistic model misclassifies satire as credible real news.", "VeriAI Mitigation: ", "Evidence Engine checks domain provenance and NLI detects absence of real-world event corroboration.", c_red),
        ("Case 3: Nuanced Half-Truths", "Statements that contain 90% truthful background facts wrapped around a single deceptive statistic.", "NLP Failure Mode: ", "Coarse paragraph classifiers assign high truth probability.", "VeriAI Mitigation: ", "Atomic Claim Decomposition isolates each sub-clause, flagging the lone contradicted statistic.", c_green)
    ]
    for idx, (f_title, f_desc, m_lbl, m_desc, mit_lbl, mit_desc, col) in enumerate(fail_cases):
        l_pos = Inches(0.8) + idx * (w_fc + gap_fc)
        add_card(slide13, l_pos, Inches(1.6), w_fc, Inches(5.3))
        
        tb = slide13.shapes.add_textbox(l_pos + Inches(0.15), Inches(1.8), w_fc - Inches(0.3), Inches(4.9))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f_title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        
        pd = tf.add_paragraph()
        pd.text = f_desc
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = c_slate
        pd.space_before = Pt(4)
        
        pm = tf.add_paragraph()
        pm.space_before = Pt(8)
        add_bullet_run(pm, m_lbl, m_desc, bold_color=c_red, desc_color=c_dark, bold_size=Pt(10.5), desc_size=Pt(10))
        
        pmit = tf.add_paragraph()
        pmit.space_before = Pt(8)
        add_bullet_run(pmit, mit_lbl, mit_desc, bold_color=c_green, desc_color=c_dark, bold_size=Pt(10.5), desc_size=Pt(10))

    # ==========================================
    # SLIDE 14: NOVEL CONTRIBUTIONS
    # ==========================================
    slide14 = prs.slides.add_slide(blank_layout)
    add_header(slide14, "Summary of Novel Contributions")
    
    add_card(slide14, Inches(0.8), Inches(1.6), Inches(11.73), Inches(5.3))
    tb_nc = slide14.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.13), Inches(4.9))
    tf_nc = tb_nc.text_frame
    tf_nc.word_wrap = True
    
    pnc = tf_nc.paragraphs[0]
    pnc.text = "Key Research & Engineering Breakthroughs"
    pnc.font.size = Pt(16)
    pnc.font.bold = True
    pnc.font.color.rgb = c_navy
    
    contribs = [
        ("• Dual-Stream Verification Paradigm: ", "First architecture to decouple stylistic credibility modeling (SHAP attribution) from real-world empirical ground truth (live multi-feed web retrieval and cross-encoder NLI)."),
        ("• Empirical Discovery of Publisher Bias: ", "Uncovered through global SHAP analysis that static text models overfit to news agency structure ('said', 'reuter') rather than factual validity, explaining real-world classifier breakdowns."),
        ("• Comprehensive Quantitative XAI Benchmarking: ", "Established formal empirical benchmarks across Faithfulness, Sufficiency, Stability (Jaccard = 1.000), Fidelity (r = 0.9984), and Expected Calibration Error (ECE = 0.0403)."),
        ("• Microsecond Inference Latency: ", "Demonstrated that a regularized linear model achieves ensemble-level F1 (0.8946 vs 0.9015) while executing in 0.4 µs and enabling closed-form Shapley computations."),
        ("• Interactive Deployed Fact-Checker: ", "Delivered an open-source, full-stack application featuring client-side word attribution, atomic claim inspection, and dynamic search re-querying.")
    ]
    for b_title, b_desc in contribs:
        p = tf_nc.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_blue, desc_color=c_dark, bold_size=Pt(12), desc_size=Pt(11.5))

    # ==========================================
    # SLIDE 15: CONCLUSION & FUTURE WORK
    # ==========================================
    slide15 = prs.slides.add_slide(blank_layout)
    add_header(slide15, "Conclusion & Future Research Roadmap")
    
    add_card(slide15, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3), bg_color=RGBColor(240, 253, 244), border_color=RGBColor(187, 247, 208))
    tb_c1 = slide15.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    
    pc1 = tf_c1.paragraphs[0]
    pc1.text = "Project Conclusions"
    pc1.font.size = Pt(16)
    pc1.font.bold = True
    pc1.font.color.rgb = c_green
    
    conc_bullets = [
        ("• High Predictive Accuracy: ", "88.93% Accuracy, 0.8946 F1-Score, and 0.9625 ROC-AUC across 57,689 multi-source benchmark records."),
        ("• Transparent Explanations: ", "SHAP feature attribution delivers auditable word-level transparency, eliminating the opaque black-box problem."),
        ("• Bias Elimination: ", "Dual-stream retrieval successfully neutralizes stylistic publisher shortcuts, grounding verdicts in contemporary reporting."),
        ("• Production Readiness: ", "0.4 µs inference latency enables real-time deployment without expensive GPU clusters.")
    ]
    for b_title, b_desc in conc_bullets:
        p = tf_c1.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_navy, desc_color=c_dark, bold_size=Pt(12), desc_size=Pt(11.5))

    add_card(slide15, Inches(6.8), Inches(1.6), Inches(5.73), Inches(5.3))
    tb_c2 = slide15.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    
    pc2 = tf_c2.paragraphs[0]
    pc2.text = "Future Research Directions"
    pc2.font.size = Pt(16)
    pc2.font.bold = True
    pc2.font.color.rgb = c_navy
    
    fut_bullets = [
        ("• Multimodal Forensics: ", "Extend verification to deepfake video detection and reverse-image metadata forensic analysis."),
        ("• Cross-Lingual Fact Verification: ", "Incorporate multilingual transformer cross-encoders to verify non-English and regional Indian language claims."),
        ("• Newsroom Human-in-the-Loop Trial: ", "Conduct double-blind usability trials with professional journalists to evaluate decision speed and cognitive load."),
        ("• Social Propagation Modeling: ", "Integrate graph neural networks to analyze coordinated inauthentic behavior on social media platforms.")
    ]
    for b_title, b_desc in fut_bullets:
        p = tf_c2.add_paragraph()
        p.space_before = Pt(10)
        add_bullet_run(p, b_title, b_desc, bold_color=c_blue, desc_color=c_slate, bold_size=Pt(12), desc_size=Pt(11.5))

    # ==========================================
    # SLIDE 16: REFERENCES & VIVA Q&A
    # ==========================================
    slide16 = prs.slides.add_slide(blank_layout)
    add_header(slide16, "Key References & Technical Viva Defense")
    
    add_card(slide16, Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.3))
    tb_ref = slide16.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(7.1), Inches(4.9))
    tf_ref = tb_ref.text_frame
    tf_ref.word_wrap = True
    
    pref = tf_ref.paragraphs[0]
    pref.text = "Selected Academic References"
    pref.font.size = Pt(14)
    pref.font.bold = True
    pref.font.color.rgb = c_navy
    
    refs_ppt = [
        "[1] S. M. Lundberg and S.-I. Lee, 'A unified approach to interpreting model predictions,' NeurIPS, 2017.",
        "[2] M. T. Ribeiro et al., '\"Why should I trust you?\": Explaining predictions,' ACM SIGKDD, 2016.",
        "[3] W. Y. Wang, '\"Liar, liar pants on fire\": A new benchmark dataset,' ACL, 2017.",
        "[4] J. Thorne et al., 'FEVER: a large-scale dataset for fact extraction,' NAACL-HLT, 2018.",
        "[5] K. Shu et al., 'Fake news detection on social media: A data mining perspective,' ACM SIGKDD, 2017.",
        "[6] C. Guo et al., 'On calibration of modern neural networks,' ICML, 2017.",
        "[7] P. He et al., 'DeBERTa: Decoding-enhanced BERT with disentangled attention,' ICLR, 2021."
    ]
    for r in refs_ppt:
        p = tf_ref.add_paragraph()
        p.text = r
        p.font.size = Pt(9.5)
        p.font.color.rgb = c_slate
        p.space_before = Pt(4)

    add_card(slide16, Inches(8.5), Inches(1.6), Inches(4.03), Inches(5.3), bg_color=c_navy, border_color=c_blue)
    tb_qa = slide16.shapes.add_textbox(Inches(8.7), Inches(2.2), Inches(3.63), Inches(4.1))
    tf_qa = tb_qa.text_frame
    tf_qa.word_wrap = True
    
    pqa = tf_qa.paragraphs[0]
    pqa.text = "Thank You!"
    pqa.font.size = Pt(28)
    pqa.font.bold = True
    pqa.font.color.rgb = c_white
    pqa.alignment = PP_ALIGN.CENTER
    
    pqa2 = tf_qa.add_paragraph()
    pqa2.text = "Questions & Discussion"
    pqa2.font.size = Pt(18)
    pqa2.font.color.rgb = RGBColor(147, 197, 253)
    pqa2.alignment = PP_ALIGN.CENTER
    pqa2.space_before = Pt(8)
    
    pqa3 = tf_qa.add_paragraph()
    pqa3.text = "VeriAI Deliverables:\n• Final Academic Report (DOCX & PDF)\n• Deployed Full-Stack Web Application\n• Open-Source GitHub Repository\n\nRohan & Lakshya Kumar Singh\nVIT Chennai"
    pqa3.font.size = Pt(11)
    pqa3.font.color.rgb = RGBColor(226, 232, 240)
    pqa3.alignment = PP_ALIGN.CENTER
    pqa3.space_before = Pt(20)

    prs.save('submission/VeriAI_Final_Presentation.pptx')
    print("Successfully built submission/VeriAI_Final_Presentation.pptx!")

if __name__ == '__main__':
    create_presentation()
