from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from datetime import date, datetime
from pymongo import MongoClient
from bson import ObjectId
import json
import os
import re

# ✅ PDF (ReportLab)
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

app = Flask(__name__)

# ✅ Mejor práctica: SECRET_KEY por entorno (en local cae a tu valor actual)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_para_flash")

# ✅ Mongo: usa Atlas si seteás MONGO_URI, si no cae a localhost como antes
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

# ✅ Usar la DB/colección que creaste en Atlas
db = client["Auditorias"]
coleccion = db["Auditorias"]

SECTORES = {
    1: "Gerencia de Recursos Humanos",
    2: "Gerencia de Compras",
    3: "Gerencia de Operaciones",
    4: "Subgerencia de Relaciones Institucionales",
    5: "Subgerencia de Seguridad Patrimonial",
    6: "Taller Mecánico (Gerencia de Mantenimiento)",
    7: "Gerencia de Comercial",
    8: "Centro de Control y Monitoreo",
    9: "Asistencia Vial",
    10: "Gerencia de Sistemas",
    11: "Gerencia de Asuntos Legales",
    12: "Gerencia General",
    13: "Sistema de Gestión Integrado"
}

REQUISITOS = [
    {"codigo": "9001-39001-4.1", "descripcion": "Comprensión de la organización y su contexto."},
    {"codigo": "9001-39001-4.2", "descripcion": "Comprensión de las necesidades y expectativas de las partes interesadas."},
    {"codigo": "9001-39001-4.3", "descripcion": "Determinación del alcance del SGI."},
    {"codigo": "9001-39001-4.4", "descripcion": "Sistema de gestión de la calidad/sv y sus procesos."},
    {"codigo": "9001-39001-5.1", "descripcion": "Liderazgo y compromiso del SGI."},
    {"codigo": "9001-39001-5.2", "descripcion": "Política del SGI establecida y comunicada."},
    {"codigo": "9001-39001-5.3", "descripcion": "Roles, responsabilidades y autoridades del SGI."},

    # 👇 Se deja TU criterio (39001 “corrida” un punto arriba)
    {"codigo": "9001-6.1-39001-6.2", "descripcion": "Acciones para abordar riesgos y oportunidades."},
    {"codigo": "9001-6.2-39001-6.4", "descripcion": "Objetivos del SGI y planificación para lograrlos."},

    {"codigo": "9001-6.3", "descripcion": "Gestión de los cambios relevantes."},
    {"codigo": "39001-6.3", "descripcion": "Factores de desempeño de SV"},

    # 👇 Se deja TU criterio (39001 corrida)
    {"codigo": "9001-7.1-39001-7.2", "descripcion": "Recursos adecuados para el SGI."},
    {"codigo": "9001-7.2-39001-7.3", "descripcion": "Competencia y formación del personal."},
    {"codigo": "9001-7.3-39001-7.4", "descripcion": "Conciencia sobre la política y objetivos del SGI."},
    {"codigo": "9001-7.4-39001-7.5", "descripcion": "Comunicación interna y externa del SGI."},
    {"codigo": "9001-7.5-39001-7.6", "descripcion": "Control de la información documentada."},

    {"codigo": "9001-8.1-39001-8.1", "descripcion": "Planificación y control operacional."},
    {"codigo": "9001-8.2", "descripcion": "Determinación de requisitos para productos y servicios."},
    {"codigo": "39001-8.2", "descripcion": "Preparación y respuesta ante emergencias."},
    {"codigo": "9001-8.4", "descripcion": "Control de los procesos, productos y servicios suministrados externamente."},
    {"codigo": "9001-8.5", "descripcion": "Producción y provisión del servicio."},
    {"codigo": "9001-8.7", "descripcion": "Control de salidas no conformes."},

    {"codigo": "9001-39001-9.1", "descripcion": "Seguimiento, medición, análisis y evaluación del SGI."},

    # ✅ FIX: antes estaba mal armado (sin 'descripcion')
    {"codigo": "39001-9.2", "descripcion": "Investigación de siniestros e incidentes viales."},

    # 👇 Se deja TU criterio (39001 corrida)
    {"codigo": "9001-9.2-39001-9.3", "descripcion": "Auditoría interna del SGI."},
    {"codigo": "9001-9.3-39001-9.4", "descripcion": "Revisión por la dirección."},
    {"codigo": "9001-10.2-39001-10.1", "descripcion": "Gestión de no conformidades y acciones correctivas."},
    {"codigo": "9001-10.3-39001-10.2", "descripcion": "Mejora continua del SGI."},
]

# ✅ CHECKLIST readecuado para que coincida EXACTO con REQUISITOS (misma clave/código)
CHECKLIST = {
    "9001-39001-4.1": "¿Se identificaron las partes internas/externas relevantes y su contexto?",
    "9001-39001-4.2": "¿Se identificaron partes interesadas y sus necesidades/expectativas?",
    "9001-39001-4.3": "¿El alcance del SGI está definido y disponible como información documentada?",
    "9001-39001-4.4": "¿Se determinan procesos del SGI y su interacción?",

    "9001-39001-5.1": "¿La dirección demuestra liderazgo y compromiso con el SGI?",
    "9001-39001-5.2": "¿La política SGI está disponible y comunicada?",
    "9001-39001-5.3": "¿Se asignan roles, responsabilidades y autoridades del SGI?",

    # 👇 claves EXACTAS a tu REQUISITOS (39001 “corrida”)
    "9001-6.1-39001-6.2": "¿Se abordan riesgos y oportunidades en el SGI (incluye SV cuando aplique)?",
    "9001-6.2-39001-6.4": "¿Se establecen objetivos SGI medibles y se planifica su logro?",
    "9001-6.3": "¿Se planifican y controlan cambios relevantes?",
    "39001-6.3": "¿Se determinan y gestionan factores de desempeño de seguridad vial?",

    # 👇 claves EXACTAS a tu REQUISITOS
    "9001-7.1-39001-7.2": "¿Se determinan y proporcionan recursos para el SGI?",
    "9001-7.2-39001-7.3": "¿Se asegura competencia del personal y se conserva evidencia?",
    "9001-7.3-39001-7.4": "¿El personal toma conciencia de política, objetivos y su contribución?",
    "9001-7.4-39001-7.5": "¿Existe comunicación interna/externa del SGI definida?",
    "9001-7.5-39001-7.6": "¿Se controla la información documentada?",

    "9001-8.1-39001-8.1": "¿Se planifica y controla la operación (incluye criterios y controles)?",
    "9001-8.2": "¿Se determinan requisitos del servicio antes de su provisión?",
    "39001-8.2": "¿Se implementan controles operacionales y respuesta ante emergencias viales?",
    "9001-8.4": "¿Se controla a proveedores externos y servicios tercerizados?",
    "9001-8.5": "¿Se controlan procesos de prestación del servicio?",
    "9001-8.7": "¿Se controlan salidas no conformes?",

    "9001-39001-9.1": "¿Se hace seguimiento, medición, análisis y evaluación?",
    "39001-9.2": "¿Se investigan siniestros e incidentes viales y se registran conclusiones?",
    "9001-9.2-39001-9.3": "¿Se audita el SGI internamente según un programa establecido?",
    "9001-9.3-39001-9.4": "¿Se hace revisión por la dirección con entradas/salidas claras?",

    "9001-10.2-39001-10.1": "¿Se gestionan no conformidades y se implementan acciones correctivas?",
    "9001-10.3-39001-10.2": "¿El SGI impulsa la mejora continua?",
}

# ✅ Carpeta de salida (solo útil en local; en Render es temporal)
OUTPUT_DIR = os.path.join(app.root_path, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _safe_filename(text: str) -> str:
    text = text or "SIN_SECTOR"
    text = re.sub(r"[^A-Za-z0-9_\-]+", "_", text.strip())
    return text[:80] if len(text) > 80 else text


def _build_resumen_txt(doc: dict) -> str:
    """
    Genera el TXT 'presentable' a partir del documento de MongoDB.
    No guarda nada en disco ni en la base.
    """
    evaluaciones = doc.get("evaluaciones", []) or []
    observaciones = doc.get("observaciones", []) or []
    no_conformidades = doc.get("no_conformidades", []) or []
    oportunidades = doc.get("oportunidades", []) or []

    total = len(evaluaciones)
    cumplen = sum(1 for e in evaluaciones if (e.get("resultado") or "").strip().lower() == "cumple")
    obs_count = len(observaciones)
    nc_count = len(no_conformidades)
    op_count = len(oportunidades)

    def find_obs(codigo):
        return next((o for o in observaciones if o.get("requisito") == codigo), None)

    def find_nc(codigo):
        return next((n for n in no_conformidades if n.get("requisito") == codigo), None)

    def find_op(codigo):
        return next((o for o in oportunidades if o.get("requisito") == codigo), None)

    lineas = []
    lineas.append("AUBASA - AUDITORÍAS INTERNAS")
    lineas.append("=" * 80)
    lineas.append("OBJETIVO: Verificar la adecuada implementación y desempeño del SGI")
    lineas.append("conforme ISO 9001 e ISO 39001, con foco en la mejora continua.")
    lineas.append("")
    lineas.append(f"ID Auditoría: {str(doc.get('_id',''))}")
    lineas.append(f"Fecha: {doc.get('fecha','')}")
    lineas.append(f"Sector: {doc.get('sector','')}")
    lineas.append(f"Lugar: {doc.get('lugar','')}")
    lineas.append("")
    lineas.append(f"Auditores líder: {', '.join(doc.get('auditores_lider', []) or [])}")
    lineas.append(f"Auditores: {', '.join(doc.get('auditores', []) or [])}")
    lineas.append(f"Veedores: {', '.join(doc.get('veedores', []) or [])}")
    lineas.append(f"Presentes: {', '.join(doc.get('presentes', []) or [])}")
    lineas.append("")
    lineas.append("RESUMEN DE AUDITORÍA")
    lineas.append(
        f"Total puntos: {total}   Cumplen: {cumplen}   Observaciones: {obs_count}   "
        f"No conformidades: {nc_count}   Oportunidades de mejora: {op_count}"
    )
    lineas.append("")
    lineas.append("RESULTADOS:")
    lineas.append("")

    for e in evaluaciones:
        codigo = e.get("codigo", "")
        lineas.append(f"- [{codigo}] {e.get('descripcion','')}")
        lineas.append(f"    Resultado: {e.get('resultado','')}")
        if (e.get("evidencia") or "").strip():
            lineas.append(f"    Evidencia: {e.get('evidencia','')}")

        if (e.get("tipo") or "").lower() == "observación":
            obs = find_obs(codigo)
            if obs and (obs.get("observacion") or "").strip():
                lineas.append(f"    Observación: {obs.get('observacion','')}")

        if (e.get("tipo") or "").lower() == "no conformidad":
            nc = find_nc(codigo)
            if nc and (nc.get("no_conformidad") or "").strip():
                lineas.append(f"    No conformidad: {nc.get('no_conformidad','')}")

        op = find_op(codigo)
        if op and (op.get("oportunidad") or "").strip():
            lineas.append(f"    Oportunidad de mejora: {op.get('oportunidad','')}")

        lineas.append("")

    lineas.append("CONCLUSIÓN:")
    if nc_count > 0:
        lineas.append("Se han identificado no conformidades que requieren atención inmediata.")
    elif obs_count > 0 or op_count > 0:
        lineas.append("Se han registrado observaciones y oportunidades de mejora.")
    else:
        lineas.append("Todos los puntos cumplen.")
    lineas.append("")

    return "\n".join(lineas)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = {
            "fecha": date.today().isoformat(),
            "sector": request.form.get("sector"),
            "lugar": request.form.get("lugar"),
            "auditores_lider": [x.strip() for x in (request.form.get("aud_lider") or "").split(",") if x.strip()],
            "auditores": [x.strip() for x in (request.form.get("auditores") or "").split(",") if x.strip()],
            "veedores": [x.strip() for x in (request.form.get("veedores") or "").split(",") if x.strip()],
            "presentes": [x.strip() for x in (request.form.get("presentes") or "").split(",") if x.strip()],
            "evaluaciones": [],
            "observaciones": [],
            "no_conformidades": [],
            "oportunidades": []
        }

        for req in REQUISITOS:
            codigo = req["codigo"]
            resultado = request.form.get(f"res_{codigo}")
            evidencia = request.form.get(f"ev_{codigo}")
            detalle = request.form.get(f"detalle_{codigo}")
            oportunidad = request.form.get(f"op_{codigo}")

            tipo = None
            if resultado == "observación":
                tipo = "observación"
                data["observaciones"].append({
                    "requisito": codigo,
                    "observacion": detalle,
                    "evidencia": evidencia
                })
            elif resultado == "no conformidad":
                tipo = "no conformidad"
                data["no_conformidades"].append({
                    "requisito": codigo,
                    "no_conformidad": detalle,
                    "evidencia": evidencia
                })

            if resultado and resultado != "no requiere":
                data["evaluaciones"].append({
                    "codigo": codigo,
                    "descripcion": req["descripcion"],
                    "resultado": resultado.title(),
                    "evidencia": evidencia,
                    "tipo": tipo
                })

            if oportunidad and oportunidad.strip():
                data["oportunidades"].append({
                    "requisito": codigo,
                    "oportunidad": oportunidad,
                    "evidencia": evidencia
                })

        # ✅ Guardar en MongoDB
        res = coleccion.insert_one(data)
        audit_id = str(res.inserted_id)

        # (Dejamos tu funcionalidad de export local; en Render puede no servir, pero no rompe)
        try:
            export_data = dict(data)
            export_data["_id"] = audit_id

            timestamp = datetime.now().strftime("%H%M%S")
            safe_sector = _safe_filename(export_data.get("sector", "SIN_SECTOR"))

            fname = os.path.join(OUTPUT_DIR, f"informe_{safe_sector}_{export_data['fecha']}_{timestamp}.json")
            resumen_txt = os.path.join(OUTPUT_DIR, f"resumen_{safe_sector}_{export_data['fecha']}_{timestamp}.txt")

            with open(fname, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            with open(resumen_txt, "w", encoding="utf-8") as f:
                f.write(_build_resumen_txt({"_id": audit_id, **export_data}))
        except Exception:
            # En Render puede fallar por filesystem; no cortamos el flujo.
            pass

        flash("✅ Auditoría guardada. Elegí qué informe descargar.")
        return redirect(url_for("post_guardado", id=audit_id))

    return render_template("auditoria_form.html", sectores=SECTORES, requisitos=REQUISITOS, checklist=CHECKLIST)


# ✅ Pantalla simple post-guardado: TXT + JSON + PDF
@app.route("/post_guardado/<id>")
def post_guardado(id):
    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Auditoría guardada</title>
        <style>
          body {{ font-family: Arial, sans-serif; padding: 30px; }}
          .box {{ max-width: 720px; border: 1px solid #ddd; padding: 20px; border-radius: 12px; }}
          a.btn {{
            display: inline-block; margin: 8px 10px 0 0; padding: 12px 16px;
            text-decoration: none; border-radius: 10px; border: 1px solid #0aa;
          }}
          a.btn:hover {{ opacity: .85; }}
          .muted {{ color: #666; font-size: 13px; margin-top: 12px; }}
        </style>
      </head>
      <body>
        <div class="box">
          <h2>✅ Auditoría guardada</h2>
          <p><b>ID:</b> {id}</p>

          <a class="btn" href="/auditoria/{id}/pdf">⬇️ Descargar PDF (Empresa)</a>
          <a class="btn" href="/auditoria/{id}/txt">⬇️ Descargar TXT</a>
          <a class="btn" href="/auditoria/{id}/json">⬇️ Descargar JSON</a>
          <a class="btn" href="/">↩️ Volver al formulario</a>

          <p class="muted">
            Nota: en Render no conviene guardar archivos en disco. Estos informes se generan desde Mongo en el momento.
          </p>
        </div>
      </body>
    </html>
    """


# ✅ Descargar TXT generado desde Mongo (NO guarda archivo)
@app.route("/auditoria/<id>/txt")
def descargar_txt_desde_mongo(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return "ID inválido", 400

    doc = coleccion.find_one({"_id": oid})
    if not doc:
        return "No encontrado", 404

    resumen = _build_resumen_txt(doc)

    sector = _safe_filename(doc.get("sector") or "SIN_SECTOR")
    fecha = doc.get("fecha") or "SIN_FECHA"
    filename = f"resumen_{sector}_{fecha}_{id}.txt"

    return Response(
        resumen,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ✅ Descargar JSON generado desde Mongo (NO guarda archivo)
@app.route("/auditoria/<id>/json")
def descargar_json_desde_mongo(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return "ID inválido", 400

    doc = coleccion.find_one({"_id": oid})
    if not doc:
        return "No encontrado", 404

    doc["_id"] = str(doc["_id"])
    contenido = json.dumps(doc, indent=2, ensure_ascii=False)

    sector = _safe_filename(doc.get("sector") or "SIN_SECTOR")
    fecha = doc.get("fecha") or "SIN_FECHA"
    filename = f"informe_{sector}_{fecha}_{id}.json"

    return Response(
        contenido,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ✅ Descargar PDF “lindo” generado desde Mongo (NO guarda archivo)
@app.route("/auditoria/<id>/pdf")
def descargar_pdf_desde_mongo(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return "ID inválido", 400

    doc = coleccion.find_one({"_id": oid})
    if not doc:
        return "No encontrado", 404

    fecha = doc.get("fecha", "")
    sector = doc.get("sector", "")
    lugar = doc.get("lugar", "")
    aud_lider = ", ".join(doc.get("auditores_lider", []) or [])
    auditores = ", ".join(doc.get("auditores", []) or [])
    veedores = ", ".join(doc.get("veedores", []) or [])
    presentes = ", ".join(doc.get("presentes", []) or [])

    evaluaciones = doc.get("evaluaciones", []) or []
    observaciones = doc.get("observaciones", []) or []
    no_conformidades = doc.get("no_conformidades", []) or []
    oportunidades = doc.get("oportunidades", []) or []

    total = len(evaluaciones)
    cumplen = sum(1 for e in evaluaciones if (e.get("resultado") or "").strip().lower() == "cumple")
    obs_count = len(observaciones)
    nc_count = len(no_conformidades)
    op_count = len(oportunidades)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    CELESTE = colors.HexColor("#BFE3FF")
    AZUL = colors.HexColor("#0B3D91")
    GRIS = colors.HexColor("#333333")

    def wrap_text_by_width(text, font_name="Helvetica", font_size=9, max_width=400):
        text = (text or "").strip()
        if not text:
            return ["-"]

        def split_long_token(token: str):
            parts = []
            current = ""
            for ch in token:
                trial = current + ch
                if c.stringWidth(trial, font_name, font_size) <= max_width:
                    current = trial
                else:
                    if current:
                        parts.append(current)
                    current = ch
            if current:
                parts.append(current)
            return parts

        words = text.split(" ")
        lines = []
        current = ""

        for w in words:
            if c.stringWidth(w, font_name, font_size) > max_width:
                if current:
                    lines.append(current.strip())
                    current = ""
                for piece in split_long_token(w):
                    lines.append(piece)
                continue

            trial = (current + " " + w).strip()
            if c.stringWidth(trial, font_name, font_size) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current.strip())
                current = w

        if current:
            lines.append(current.strip())

        return lines

    def header():
        c.setFillColor(CELESTE)
        c.rect(0, H - 2.2*cm, W, 2.2*cm, fill=1, stroke=0)

        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, H - 1.2*cm, "INFORME DE AUDITORÍA INTERNA - SGI")

        possible_paths = [
            os.path.join(app.root_path, "AUBASA_LOGO_web.png"),
            os.path.join(app.root_path, "static", "AUBASA_LOGO_web.png"),
            os.path.join(app.root_path, "static", "img", "AUBASA_LOGO_web.png"),
        ]
        logo_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if logo_path:
            c.drawImage(logo_path, W - 5.5*cm, H - 2.0*cm, width=3.8*cm, height=1.6*cm, mask="auto")

    def footer():
        c.setFillColor(colors.HexColor("#777777"))
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, 1.2*cm, "AUBASA - Sistema de Gestión Integrado (ISO 9001 / ISO 39001)")
        c.drawRightString(W - 2*cm, 1.2*cm, f"Página {c.getPageNumber()}")

    y = H - 2.8*cm
    left = 2*cm
    right = W - 2*cm

    def ensure_space(min_space=3*cm):
        nonlocal y
        if y < min_space:
            footer()
            c.showPage()
            header()
            y = H - 2.8*cm

    def section_title(txt):
        nonlocal y
        ensure_space()
        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, txt)
        y -= 0.5*cm
        c.setStrokeColor(CELESTE)
        c.setLineWidth(1)
        c.line(left, y, right, y)
        y -= 0.6*cm

    def key_value(k, v):
        nonlocal y
        ensure_space()

        label_w = 3.2*cm
        x_label = left
        x_value = left + label_w
        max_w = right - x_value

        c.setFillColor(GRIS)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_label, y, f"{k}:")

        c.setFont("Helvetica", 9)
        lines = wrap_text_by_width(v if v else "-", "Helvetica", 9, max_w)

        c.drawString(x_value, y, lines[0])
        y -= 0.5*cm

        for extra in lines[1:]:
            ensure_space()
            c.drawString(x_value, y, extra)
            y -= 0.5*cm

    def items_section(title, items, item_key):
        nonlocal y
        section_title(title)
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 9)

        if not items:
            c.drawString(left, y, "Sin registros.")
            y -= 0.7*cm
            return

        for it in items:
            ensure_space()
            req = it.get("requisito", "")
            txt = it.get(item_key, "") or ""
            ev = it.get("evidencia", "") or ""

            c.setFont("Helvetica-Bold", 9)
            c.drawString(left, y, f"• Requisito: {req}")
            y -= 0.45*cm

            c.setFont("Helvetica", 9)
            for line in wrap_text_by_width(txt, "Helvetica", 9, right - (left + 0.6*cm)):
                c.drawString(left + 0.6*cm, y, line)
                y -= 0.4*cm

            if ev.strip():
                c.setFillColor(colors.HexColor("#555555"))
                for line in wrap_text_by_width(f"Evidencia: {ev}", "Helvetica", 9, right - (left + 0.6*cm)):
                    c.drawString(left + 0.6*cm, y, line)
                    y -= 0.4*cm
                c.setFillColor(GRIS)

            y -= 0.3*cm

    header()

    section_title("Datos generales")
    key_value("Fecha", fecha)
    key_value("Sector", sector)
    key_value("Lugar", lugar)
    key_value("Auditor líder", aud_lider)
    key_value("Auditores", auditores)
    key_value("Veedores", veedores)
    key_value("Presentes", presentes)

    section_title("Resumen ejecutivo")
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 10)
    c.drawString(left, y, f"Total puntos evaluados: {total}")
    y -= 0.5*cm
    c.drawString(left, y, f"Cumplen: {cumplen}    Observaciones: {obs_count}    No conformidades: {nc_count}    Oportunidades: {op_count}")
    y -= 0.9*cm

    items_section("Observaciones", observaciones, "observacion")
    items_section("No conformidades", no_conformidades, "no_conformidad")
    items_section("Oportunidades de mejora", oportunidades, "oportunidad")

    section_title("Detalle de evaluación por requisito")
    if not evaluaciones:
        c.setFont("Helvetica", 9)
        c.setFillColor(GRIS)
        c.drawString(left, y, "Sin evaluaciones registradas.")
        y -= 0.7*cm
    else:
        for e in evaluaciones:
            ensure_space()
            codigo = e.get("codigo", "")
            desc = e.get("descripcion", "")
            resu = e.get("resultado", "")
            ev = e.get("evidencia", "") or ""

            c.setFillColor(AZUL)
            c.setFont("Helvetica-Bold", 9)
            for line in wrap_text_by_width(f"[{codigo}] {desc}", "Helvetica-Bold", 9, right - left):
                c.drawString(left, y, line)
                y -= 0.45*cm

            c.setFillColor(GRIS)
            c.setFont("Helvetica", 9)
            c.drawString(left, y, f"Resultado: {resu}")
            y -= 0.4*cm

            if ev.strip():
                for line in wrap_text_by_width(f"Evidencia: {ev}", "Helvetica", 9, right - left):
                    c.drawString(left, y, line)
                    y -= 0.4*cm

            y -= 0.3*cm

    footer()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    safe_sector = _safe_filename(sector)
    filename = f"Informe_Auditoria_{safe_sector}_{fecha}_{id}.pdf"

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.route("/descargar/<nombre_archivo>")
def descargar(nombre_archivo):
    path = os.path.join(OUTPUT_DIR, nombre_archivo)
    return send_file(path, as_attachment=True)


@app.route("/descargar_txt/<nombre>")
def descargar_txt(nombre):
    path = os.path.join(OUTPUT_DIR, nombre)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)









