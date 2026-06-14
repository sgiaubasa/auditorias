from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from datetime import date
from pymongo import MongoClient
from bson import ObjectId
import json
import os
import re

from data_models import REQUISITOS, CHECKLIST, SECTORES

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_para_flash")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["Auditorias"]
coleccion = db["Auditorias"]

OUTPUT_DIR = os.path.join(app.root_path, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("auditoria_form_iram.html", requisitos=REQUISITOS, checklist=CHECKLIST, sectores=SECTORES)

@app.route("/post_auditoria", methods=["POST"])
def post_auditoria():
    data = {
        "organizacion": request.form.get("organizacion"),
        "sector": request.form.get("sector"),
        "anio": request.form.get("anio"),
        "tipo_auditoria": request.form.get("tipo_auditoria"),
        "fechas_auditoria": request.form.get("fechas_auditoria"),
        "equipo": {
            "auditor_responsable": request.form.get("auditor_responsable"),
            "auditor_2": request.form.get("auditor_2"),
            "auditor_3": request.form.get("auditor_3"),
            "experto_tecnico": request.form.get("experto_tecnico"),
            "veedores": request.form.get("veedores"),
            "personas_auditadas": request.form.get("personas_auditadas"),
        },
        "evaluaciones": [],
        "fortalezas": [],
        "oportunidades": []
    }

    # Procesar evaluaciones
    for req in REQUISITOS:
        codigo = req["codigo"]
        resultado = request.form.get(f"res_{codigo}")
        evidencia = request.form.get(f"ev_{codigo}")
        detalle = request.form.get(f"detalle_{codigo}")
        
        if resultado and resultado != "no requiere":
            data["evaluaciones"].append({
                "codigo": codigo,
                "descripcion": req["descripcion"],
                "resultado": resultado.upper(),
                "evidencia": evidencia,
                "detalle": detalle
            })

    # Procesar fortalezas (arrays dinámicos)
    f_normas = request.form.getlist("fortalezas_norma[]")
    f_reqs = request.form.getlist("fortalezas_req[]")
    f_descs = request.form.getlist("fortalezas_desc[]")
    for n, r, d in zip(f_normas, f_reqs, f_descs):
        if d.strip():
            data["fortalezas"].append({"norma": n, "req": r, "desc": d})

    # Procesar oportunidades (arrays dinámicos)
    o_normas = request.form.getlist("oportunidades_norma[]")
    o_reqs = request.form.getlist("oportunidades_req[]")
    o_descs = request.form.getlist("oportunidades_desc[]")
    for n, r, d in zip(o_normas, o_reqs, o_descs):
        if d.strip():
            data["oportunidades"].append({"norma": n, "req": r, "desc": d})

    res = coleccion.insert_one(data)
    audit_id = str(res.inserted_id)

    flash("✅ Informe AUBASA guardado con éxito.")
    return redirect(url_for("post_guardado", id=audit_id))

@app.route("/post_guardado/<id>")
def post_guardado(id):
    return f"""
    <!DOCTYPE html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Auditoría guardada</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="{{ url_for('static', filename='estilos.css') }}">
        <style>
            .success-card {{ max-width: 600px; margin: 4rem auto; text-align: center; }}
            .btn-download {{ display: inline-block; padding: 1rem; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.5rem; color: #f8fafc; text-decoration: none; font-weight: 600; transition: all 0.3s ease; margin: 5px; }}
            .btn-download:hover {{ background: rgba(14, 165, 233, 0.2); border-color: rgba(14, 165, 233, 0.5); transform: translateY(-2px); }}
        </style>
      </head>
      <body>
        <div class="page-container">
            <div class="glass-panel success-card">
                <div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
                <h2 class="title" style="font-size: 2rem; margin-bottom: 1rem;">Informe AUBASA Generado</h2>
                <p style="color: #cbd5e1; margin-bottom: 2rem;">ID de registro: <strong style="color: #f8fafc;">{id}</strong></p>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <a href="/auditoria/{id}/pdf" class="btn-download">📄 Descargar Informe PDF (Estilo AUBASA)</a>
                </div>
                <a href="/" style="display: inline-block; margin-top: 1rem; color: #bae6fd;">← Volver al formulario</a>
            </div>
        </div>
      </body>
    </html>
    """

@app.route("/auditoria/<id>/pdf")
def descargar_pdf_desde_mongo(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return "ID inválido", 400

    doc = coleccion.find_one({"_id": oid})
    if not doc:
        return "No encontrado", 404

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    left = 2 * cm
    right = W - 2 * cm

    AUBASA_TEAL = colors.HexColor("#21b8c7")
    AUBASA_LIGHT = colors.HexColor("#e0f4f7")
    GRAY = colors.HexColor("#F2F2F2")
    TEXT_GRAY = colors.HexColor("#4A4A4A")

    def draw_header_footer(c, page_num):
        # Header
        c.setStrokeColor(AUBASA_TEAL)
        c.setLineWidth(2)
        c.line(2*cm, H - 2*cm, 13*cm, H - 2*cm)
        c.setFillColor(AUBASA_TEAL)
        c.setFont("Helvetica", 20)
        c.drawString(2*cm, H - 1.8*cm, "Sistema de Gestión Integrado")
        
        # Aubasa Logo
        logo_path = os.path.join(app.root_path, "static", "AUBASA_LOGO_web.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(app.root_path, "AUBASA_LOGO_web.png")
        if os.path.exists(logo_path):
            c.drawImage(logo_path, W - 6*cm, H - 2.8*cm, width=4.5*cm, height=1.8*cm, preserveAspectRatio=True, mask="auto")
        
        # Left bar
        c.setFillColor(AUBASA_TEAL)
        c.rect(1*cm, 2*cm, 0.4*cm, H - 4*cm, fill=1, stroke=0)
        
        # Footer
        c.setFillColor(TEXT_GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, 1*cm, f"Organización: {doc.get('organizacion', '')} - Año: {doc.get('anio', '')}")
        c.drawRightString(W - 2*cm, 1*cm, f"Página {page_num}")

    def new_page(c, p_num):
        c.showPage()
        p_num += 1
        draw_header_footer(c, p_num)
        return p_num, H - 3.5*cm

    def wrap_with_prefix(c, prefix, text, x, y, max_width, font_base="Helvetica", size=9):
        c.setFont(f"{font_base}-Bold", size)
        c.drawString(x, y, prefix)
        prefix_width = c.stringWidth(prefix + " ", f"{font_base}-Bold", size)
        c.setFont(font_base, size)
        words = text.split()
        line = ""
        for w in words:
            if c.stringWidth(line + w, font_base, size) < (max_width - prefix_width):
                line += w + " "
            else:
                c.drawString(x + prefix_width, y, line)
                y -= 0.5*cm
                line = w + " "
        if line:
            c.drawString(x + prefix_width, y, line)
            y -= 0.5*cm
        return y

    page_num = 1
    draw_header_footer(c, page_num)
    y = H - 3.5*cm

    # PORTADA
    c.setFillColor(AUBASA_TEAL)
    c.rect(left, y - 1.5*cm, W - 4*cm, 1.5*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left + 0.5*cm, y - 0.7*cm, "PLAN E INFORME DE")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left + 0.5*cm, y - 1.3*cm, "AUDITORÍA INTERNA DEL SISTEMA DE GESTIÓN INTEGRADO")
    
    # Caja AÑO
    c.setFillColor(AUBASA_LIGHT)
    c.rect(W - 5.5*cm, y - 1.5*cm, 3.5*cm, 1.5*cm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W - 3.75*cm, y - 0.5*cm, "AÑO")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W - 3.75*cm, y - 1.2*cm, doc.get("anio", ""))

    y -= 2*cm
    # Caja Organización y Sector
    c.setFillColor(AUBASA_LIGHT)
    c.rect(left, y - 0.7*cm, W - 4*cm, 0.7*cm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left + 0.2*cm, y - 0.5*cm, "ORGANIZACIÓN / SECTOR")
    y -= 0.7*cm
    c.rect(left, y - 1.2*cm, W - 4*cm, 1.2*cm, fill=0, stroke=1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left + 0.2*cm, y - 0.5*cm, f"{doc.get('organizacion', '')}")
    c.drawString(left + 0.2*cm, y - 0.95*cm, f"Sector: {doc.get('sector', '')}")
    
    y -= 2.5*cm
    
    # CONTENIDO
    c.setFillColor(AUBASA_TEAL)
    c.rect(left, y - 0.8*cm, W - 4*cm, 0.8*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left + 0.5*cm, y - 0.6*cm, "CONTENIDO")
    y -= 1.5*cm
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(left, y, "Este documento contiene la planificación y el resultado de la realización de la auditoría del")
    y -= 0.5*cm
    c.drawString(left, y, "Sistema de Gestión Integrado. El auditor responsable completa este documento.")
    
    y -= 2*cm
    
    # INFO AUDITORIA
    c.setFillColor(AUBASA_TEAL)
    c.rect(left, y - 0.8*cm, W - 4*cm, 0.8*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left + 0.5*cm, y - 0.6*cm, "INFORMACIÓN DE LA AUDITORÍA")
    y -= 1.5*cm
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(left, y, f"Tipo de Auditoría: {doc.get('tipo_auditoria', '')}")
    y -= 0.6*cm
    c.drawString(left, y, f"Fecha de Auditoría: {doc.get('fechas_auditoria', '')}")
    y -= 0.6*cm
    eq = doc.get("equipo", {})
    c.drawString(left, y, f"Auditor Responsable: {eq.get('auditor_responsable', '')}")
    y -= 0.6*cm
    c.drawString(left, y, f"Auditor 2: {eq.get('auditor_2', '')} | Auditor 3: {eq.get('auditor_3', '')}")
    y -= 0.6*cm
    c.drawString(left, y, f"Experto Técnico: {eq.get('experto_tecnico', '')} | Veedores: {eq.get('veedores', '')}")
    y -= 0.6*cm
    c.drawString(left, y, f"Personas Auditadas: {eq.get('personas_auditadas', '')}")
    
    y -= 2*cm

    # REQUISITOS EVALUADOS
    page_num, y = new_page(c, page_num)
    c.setFillColor(AUBASA_TEAL)
    c.rect(left, y - 0.8*cm, W - 4*cm, 0.8*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left + 0.5*cm, y - 0.6*cm, "RESULTADO DE EVALUACIÓN DE REQUISITOS")
    y -= 1.2*cm

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    evals = doc.get("evaluaciones", [])
    for ev in evals:
        if y < 3*cm:
            page_num, y = new_page(c, page_num)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left, y, f"Requisito: {ev.get('codigo', '')} - {ev.get('descripcion', '')}")
        y -= 0.5*cm
        c.setFont("Helvetica", 9)
        c.drawString(left + 0.5*cm, y, f"Resultado: {ev.get('resultado', '')}")
        y -= 0.5*cm
        
        det = ev.get('detalle', '')
        if det:
            y = wrap_with_prefix(c, "Detalle:", det, left + 0.5*cm, y, W - 4*cm, "Helvetica", 9)

        evi = ev.get('evidencia', '')
        if evi:
            y = wrap_with_prefix(c, "Evidencia:", evi, left + 0.5*cm, y, W - 4*cm, "Helvetica", 9)
            
        y -= 0.3*cm

    obs = [e for e in evals if "OBSERVACI" in e.get("resultado", "").upper()]
    ncs = [e for e in evals if "NO CONFORMIDAD" in e.get("resultado", "").upper()]

    # HALLAZGOS (Fortalezas y OM)
    if doc.get("fortalezas") or doc.get("oportunidades") or obs or ncs:
        page_num, y = new_page(c, page_num)
        c.setFillColor(AUBASA_TEAL)
        c.rect(left, y - 0.8*cm, W - 4*cm, 0.8*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left + 0.5*cm, y - 0.6*cm, "HALLAZGOS DE LA PRESENTE AUDITORÍA")
        y -= 1.5*cm

        c.setFillColor(colors.black)
        
        if doc.get("fortalezas"):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left, y, "Fortalezas")
            y -= 0.6*cm
            for f in doc.get("fortalezas"):
                if y < 3*cm: page_num, y = new_page(c, page_num)
                txt = f"Norma: {f.get('norma','')} | Req: {f.get('req','')} | Detalle: {f.get('desc','')}"
                y = wrap_with_prefix(c, "•", txt, left + 0.5*cm, y, W - 4*cm, "Helvetica", 10)
            y -= 0.5*cm

        if doc.get("oportunidades"):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left, y, "Oportunidades de Mejora")
            y -= 0.6*cm
            for o in doc.get("oportunidades"):
                if y < 3*cm: page_num, y = new_page(c, page_num)
                txt = f"Norma: {o.get('norma','')} | Req: {o.get('req','')} | Detalle: {o.get('desc','')}"
                y = wrap_with_prefix(c, "•", txt, left + 0.5*cm, y, W - 4*cm, "Helvetica", 10)
            y -= 0.5*cm
            
        if obs:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left, y, "Observaciones (OB)")
            y -= 0.6*cm
            for o in obs:
                if y < 3*cm: page_num, y = new_page(c, page_num)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(left + 0.5*cm, y, f"Req: {o.get('codigo','')} - {o.get('descripcion','')}")
                y -= 0.5*cm
                y = wrap_with_prefix(c, "Detalle:", o.get('detalle', ''), left + 0.5*cm, y, W - 4*cm, "Helvetica", 10)
                y -= 0.4*cm
            y -= 0.5*cm

        if ncs:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left, y, "No Conformidades (NC)")
            y -= 0.6*cm
            for n in ncs:
                if y < 3*cm: page_num, y = new_page(c, page_num)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(left + 0.5*cm, y, f"Req: {n.get('codigo','')} - {n.get('descripcion','')}")
                y -= 0.5*cm
                y = wrap_with_prefix(c, "Detalle:", n.get('detalle', ''), left + 0.5*cm, y, W - 4*cm, "Helvetica", 10)
                y -= 0.4*cm

    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename = f"Informe_AUBASA_{doc.get('anio', '')}_{id}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

if __name__ == "__main__":
    app.run(debug=True)
