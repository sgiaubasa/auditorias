from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from datetime import date
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
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_para_flash")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

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

# =========================
# REQUISITOS (SE DEJAN COMO LOS TENÍAS)
# =========================
REQUISITOS = [
    {"codigo": "9001-39001-4.1", "descripcion": "Comprensión de la organización y su contexto."},
    {"codigo": "9001-39001-4.2", "descripcion": "Comprensión de las necesidades y expectativas de las partes interesadas."},
    {"codigo": "9001-39001-4.3", "descripcion": "Determinación del alcance del SGI."},
    {"codigo": "9001-39001-4.4", "descripcion": "Sistema de gestión de la calidad/sv y sus procesos."},
    {"codigo": "9001-39001-5.1", "descripcion": "Liderazgo y compromiso del SGI."},
    {"codigo": "9001-39001-5.2", "descripcion": "Política del SGI establecida y comunicada."},
    {"codigo": "9001-39001-5.3", "descripcion": "Roles, responsabilidades y autoridades del SGI."},

    {"codigo": "9001-6.1-39001-6.2", "descripcion": "Acciones para abordar riesgos y oportunidades."},
    {"codigo": "9001-6.2-39001-6.4", "descripcion": "Objetivos del SGI y planificación para lograrlos."},

    {"codigo": "9001-6.3", "descripcion": "Gestión de los cambios relevantes."},
    {"codigo": "39001-6.3", "descripcion": "Factores de desempeño de SV "},

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
    {"codigo": "39001-9.2", "descripcion": "Investigación de siniestros e incidentes viales."},

    {"codigo": "9001-9.2-39001-9.3", "descripcion": "Auditoría interna del SGI."},
    {"codigo": "9001-9.3-39001-9.4", "descripcion": "Revisión por la dirección."},
    {"codigo": "9001-10.2-39001-10.1", "descripcion": "Gestión de no conformidades y acciones correctivas."},
    {"codigo": "9001-10.3-39001-10.2", "descripcion": "Mejora continua del SGI."},
]

# =========================
# CHECKLIST (CLAVES IGUALES A REQUISITOS)
# =========================
CHECKLIST = {
    "9001-39001-4.1": "¿Se identificaron las partes internas/externas relevantes y su contexto?",
    "9001-39001-4.2": "¿Se identificaron partes interesadas y sus necesidades/expectativas?",
    "9001-39001-4.3": "¿El alcance del SGI está definido y disponible como información documentada?",
    "9001-39001-4.4": "¿Se determinan procesos del SGI y su interacción?",
    "9001-39001-5.1": "¿La dirección demuestra liderazgo y compromiso con el SGI?",
    "9001-39001-5.2": "¿La política SGI está disponible y comunicada?",
    "9001-39001-5.3": "¿Se asignan roles, responsabilidades y autoridades del SGI?",

    "9001-6.1-39001-6.2": "¿Se abordan riesgos y oportunidades en el SGI?",
    "9001-6.2-39001-6.4": "¿Se establecen objetivos SGI medibles y se planifica su logro?",
    "9001-6.3": "¿Se planifican y controlan cambios relevantes?",
    "39001-6.3": "¿Se determinan y gestionan factores de desempeño de seguridad vial?",

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
    "39001-9.2": "¿Se investigan siniestros e incidentes viales?",
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


# ✅ TXT (PROLIJO): incluye detalle hallazgo + evidencia y oportunidad + evidencia por requisito
def _build_resumen_txt(doc: dict) -> str:
    evaluaciones = doc.get("evaluaciones", []) or []
    observaciones = doc.get("observaciones", []) or []
    no_conformidades = doc.get("no_conformidades", []) or []
    oportunidades = doc.get("oportunidades", []) or []

    def norm(s):
        return re.sub(r"\s+", " ", (s or "")).strip()

    def join_list(x):
        if isinstance(x, list):
            return ", ".join([norm(i) for i in x if norm(i)])
        return norm(x)

    # Índices por requisito para no “perder” el detalle
    obs_by_req = {norm(o.get("requisito","")): o for o in observaciones if norm(o.get("requisito",""))}
    nc_by_req  = {norm(n.get("requisito","")): n for n in no_conformidades if norm(n.get("requisito",""))}
    op_by_req  = {norm(op.get("requisito","")): op for op in oportunidades if norm(op.get("requisito",""))}

    total = len(evaluaciones)
    cumplen = sum(1 for e in evaluaciones if norm(e.get("resultado", "")).lower() == "cumple")

    lineas = []
    lineas.append("AUBASA - AUDITORÍAS INTERNAS")
    lineas.append("=" * 90)
    lineas.append("OBJETIVO: Verificar la adecuada implementación y desempeño del SGI")
    lineas.append("conforme ISO 9001 e ISO 39001, con foco en la mejora continua.")
    lineas.append("")
    lineas.append(f"ID Auditoría: {str(doc.get('_id',''))}")
    lineas.append(f"Fecha: {norm(doc.get('fecha',''))}")
    lineas.append(f"Sector: {norm(doc.get('sector',''))}")
    lineas.append(f"Lugar: {norm(doc.get('lugar',''))}")
    lineas.append("")
    lineas.append(f"Auditores líder: {join_list(doc.get('auditores_lider', []))}")
    lineas.append(f"Auditores: {join_list(doc.get('auditores', []))}")
    lineas.append(f"Veedores: {join_list(doc.get('veedores', []))}")
    lineas.append(f"Presentes: {join_list(doc.get('presentes', []))}")
    lineas.append("")
    lineas.append("RESUMEN DE AUDITORÍA")
    lineas.append("-" * 90)
    lineas.append(
        f"Total puntos evaluados: {total} | Cumplen: {cumplen} | "
        f"Observaciones: {len(observaciones)} | No conformidades: {len(no_conformidades)} | "
        f"Oportunidades de mejora: {len(oportunidades)}"
    )
    lineas.append("")

    lineas.append("DETALLE POR REQUISITO (INCLUYE HALLAZGO/OM + EVIDENCIAS)")
    lineas.append("-" * 90)

    if not evaluaciones:
        lineas.append("Sin evaluaciones registradas.")
        lineas.append("")
    else:
        evaluaciones_sorted = sorted(evaluaciones, key=lambda x: norm(x.get("codigo","")))
        for i, e in enumerate(evaluaciones_sorted, start=1):
            codigo = norm(e.get("codigo",""))
            desc = norm(e.get("descripcion",""))
            resultado = norm(e.get("resultado",""))
            ev_eval = norm(e.get("evidencia",""))

            lineas.append(f"{i}) {codigo} — {desc}")
            lineas.append(f"   Resultado: {resultado if resultado else '-'}")
            lineas.append(f"   Evidencia (evaluación): {ev_eval if ev_eval else '-'}")

            if codigo in obs_by_req:
                o = obs_by_req[codigo]
                lineas.append("   >>> OBSERVACIÓN")
                lineas.append(f"       Detalle: {norm(o.get('observacion','')) or '-'}")
                lineas.append(f"       Evidencia: {norm(o.get('evidencia','')) or '-'}")

            if codigo in nc_by_req:
                n = nc_by_req[codigo]
                lineas.append("   >>> NO CONFORMIDAD")
                lineas.append(f"       Detalle: {norm(n.get('no_conformidad','')) or '-'}")
                lineas.append(f"       Evidencia: {norm(n.get('evidencia','')) or '-'}")

            if codigo in op_by_req:
                op = op_by_req[codigo]
                lineas.append("   >>> OPORTUNIDAD DE MEJORA")
                lineas.append(f"       Propuesta: {norm(op.get('oportunidad','')) or '-'}")
                lineas.append(f"       Evidencia/Referencia: {norm(op.get('evidencia','')) or '-'}")

            lineas.append("")

    lineas.append("")
    lineas.append("HALLAZGOS (RESUMEN POR SECCIÓN)")
    lineas.append("-" * 90)

    def add_section(title, items, key_text):
        lineas.append(title)
        lineas.append("-" * len(title))
        if not items:
            lineas.append("Sin registros.")
            lineas.append("")
            return
        for idx, it in enumerate(items, start=1):
            req = norm(it.get("requisito",""))
            detalle = norm(it.get(key_text,"")) or "-"
            ev = norm(it.get("evidencia","")) or "-"
            lineas.append(f"{idx}) Requisito: {req}")
            lineas.append(f"   Detalle: {detalle}")
            lineas.append(f"   Evidencia: {ev}")
            lineas.append("")
        lineas.append("")

    add_section("OBSERVACIONES", observaciones, "observacion")
    add_section("NO CONFORMIDADES", no_conformidades, "no_conformidad")
    add_section("OPORTUNIDADES DE MEJORA", oportunidades, "oportunidad")

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
            detalle = request.form.get(f"detalle_{codigo}")  # <- detalle hallazgo
            oportunidad = request.form.get(f"op_{codigo}")   # <- oportunidad de mejora

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

        res = coleccion.insert_one(data)
        audit_id = str(res.inserted_id)

        flash("✅ Auditoría guardada. Elegí qué informe descargar.")
        return redirect(url_for("post_guardado", id=audit_id))

    return render_template("auditoria_form.html", sectores=SECTORES, requisitos=REQUISITOS, checklist=CHECKLIST)


@app.route("/post_guardado/<id>")
def post_guardado(id):
    return f"""
    <html>
      <head><meta charset="utf-8" /><title>Auditoría guardada</title></head>
      <body style="font-family:Arial;padding:30px">
        <h2>✅ Auditoría guardada</h2>
        <p><b>ID:</b> {id}</p>
        <p>
          <a href="/auditoria/{id}/pdf">⬇️ Descargar PDF</a> |
          <a href="/auditoria/{id}/txt">⬇️ Descargar TXT</a> |
          <a href="/auditoria/{id}/json">⬇️ Descargar JSON</a> |
          <a href="/">↩️ Volver</a>
        </p>
      </body>
    </html>
    """


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


@app.route("/auditoria/<id>/txt")
def descargar_txt_desde_mongo(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return "ID inválido", 400

    doc = coleccion.find_one({"_id": oid})
    if not doc:
        return "No encontrado", 404

    contenido = _build_resumen_txt(doc)

    sector = _safe_filename(doc.get("sector") or "SIN_SECTOR")
    fecha = doc.get("fecha") or "SIN_FECHA"
    filename = f"resumen_{sector}_{fecha}_{id}.txt"

    return Response(
        contenido,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


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

    # Mapas para poder meter “detalle hallazgo” y “OM” dentro del detalle por requisito
    obs_by_req = {o.get("requisito",""): o for o in observaciones if o.get("requisito")}
    nc_by_req  = {n.get("requisito",""): n for n in no_conformidades if n.get("requisito")}
    op_by_req  = {op.get("requisito",""): op for op in oportunidades if op.get("requisito")}

    total = len(evaluaciones)
    cumplen = sum(1 for e in evaluaciones if (e.get("resultado") or "").strip().lower() == "cumple")
    obs_count = len(observaciones)
    nc_count = len(no_conformidades)
    op_count = len(oportunidades)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    # Paleta
    CELESTE = colors.HexColor("#BFE3FF")
    AZUL = colors.HexColor("#0B3D91")
    GRIS = colors.HexColor("#333333")
    AZUL_SUAVE = colors.HexColor("#4A6FA5")

    # Estados
    NARANJA_OBS = colors.HexColor("#D97904")
    ROJO_NC = colors.HexColor("#B00020")
    VERDE_OP = colors.HexColor("#1B7F3A")

    left = 2 * cm
    right = W - 2 * cm
    TOP_Y = H - 2.8 * cm
    BOTTOM_SAFE = 3.0 * cm

    y = TOP_Y

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
        c.rect(0, H - 2.2 * cm, W, 2.2 * cm, fill=1, stroke=0)

        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, H - 1.2 * cm, "INFORME DE AUDITORÍA INTERNA - SGI")

        possible_paths = [
            os.path.join(app.root_path, "AUBASA_LOGO_web.png"),
            os.path.join(app.root_path, "static", "AUBASA_LOGO_web.png"),
            os.path.join(app.root_path, "static", "img", "AUBASA_LOGO_web.png"),
        ]
        logo_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if logo_path:
            c.drawImage(logo_path, W - 5.5 * cm, H - 2.0 * cm, width=3.8 * cm, height=1.6 * cm, mask="auto")

    def footer():
        c.setFillColor(colors.HexColor("#777777"))
        c.setFont("Helvetica", 8)
        c.drawString(2 * cm, 1.2 * cm, "AUBASA - Sistema de Gestión Integrado (ISO 9001 / ISO 39001)")
        c.drawRightString(W - 2 * cm, 1.2 * cm, f"Página {c.getPageNumber()}")

    def new_page():
        nonlocal y
        footer()
        c.showPage()
        header()
        y = TOP_Y

    def ensure_space(min_space_cm=0.0):
        nonlocal y
        if (y - (min_space_cm * cm)) <= BOTTOM_SAFE:
            new_page()

    def section_title(txt):
        ensure_space(3.6)
        nonlocal y
        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, txt)
        y -= 0.5 * cm
        c.setStrokeColor(CELESTE)
        c.setLineWidth(1)
        c.line(left, y, right, y)
        y -= 0.6 * cm

    def key_value(k, v):
        nonlocal y
        ensure_space(1.2)

        label_w = 3.2 * cm
        x_label = left
        x_value = left + label_w
        max_w = right - x_value

        c.setFillColor(GRIS)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_label, y, f"{k}:")

        c.setFont("Helvetica", 9)
        lines = wrap_text_by_width(v if v else "-", "Helvetica", 9, max_w)

        c.drawString(x_value, y, lines[0])
        y -= 0.5 * cm

        for extra in lines[1:]:
            ensure_space(0.8)
            c.drawString(x_value, y, extra)
            y -= 0.5 * cm

    def color_by_section(title: str):
        t = (title or "").lower()
        if "observ" in t:
            return NARANJA_OBS
        if "no conform" in t:
            return ROJO_NC
        if "oportun" in t:
            return VERDE_OP
        return AZUL

    def color_by_result(result: str):
        r = (result or "").strip().lower()
        if "observ" in r:
            return NARANJA_OBS
        if "no conform" in r:
            return ROJO_NC
        if "oportun" in r:
            return VERDE_OP
        return AZUL

    def estimated_height_cm_for_item(main_lines: int, ev_lines: int) -> float:
        base = 0.45 + 0.25
        main = main_lines * 0.5
        ev = (0.35 + ev_lines * 0.4) if ev_lines > 0 else 0
        tail = 0.6
        return base + main + ev + tail

    def items_section(title, items, item_key):
        nonlocal y

        if items:
            first = items[0]
            f_txt = first.get(item_key, "") or ""
            f_ev = first.get("evidencia", "") or ""
            f_main_lines = wrap_text_by_width(f_txt, "Helvetica", 11, right - (left + 0.6 * cm))
            f_ev_lines = wrap_text_by_width(f"Evidencia: {f_ev}", "Helvetica-Oblique", 9, right - (left + 0.6 * cm)) if f_ev.strip() else []
            first_needed = 3.6 + estimated_height_cm_for_item(len(f_main_lines), len(f_ev_lines))
            if (y - (first_needed * cm)) <= BOTTOM_SAFE:
                new_page()
        else:
            ensure_space(4.2)

        section_title(title)

        if not items:
            ensure_space(1.0)
            c.setFont("Helvetica", 9)
            c.setFillColor(GRIS)
            c.drawString(left, y, "Sin registros.")
            y -= 0.7 * cm
            return

        principal_color = color_by_section(title)

        for it in items:
            req = it.get("requisito", "")
            txt = it.get(item_key, "") or ""
            ev = it.get("evidencia", "") or ""

            main_lines = wrap_text_by_width(txt, "Helvetica", 11, right - (left + 0.6 * cm))
            ev_lines = wrap_text_by_width(f"Evidencia: {ev}", "Helvetica-Oblique", 9, right - (left + 0.6 * cm)) if ev.strip() else []

            needed_cm = estimated_height_cm_for_item(len(main_lines), len(ev_lines))
            if (y - (needed_cm * cm)) <= BOTTOM_SAFE:
                new_page()

            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(GRIS)
            c.drawString(left, y, f"• Requisito: {req}")
            y -= 0.45 * cm

            c.setFont("Helvetica", 11)
            c.setFillColor(principal_color)
            for line in main_lines:
                ensure_space(0.8)
                c.drawString(left + 0.6 * cm, y, line)
                y -= 0.5 * cm

            if ev_lines:
                c.setFont("Helvetica-Oblique", 9)
                c.setFillColor(AZUL_SUAVE)
                for line in ev_lines:
                    ensure_space(0.8)
                    c.drawString(left + 0.6 * cm, y, line)
                    y -= 0.4 * cm

            y -= 0.5 * cm

    # ===== PDF Construcción =====
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
    ensure_space(1.2)
    c.drawString(left, y, f"Total puntos evaluados: {total}")
    y -= 0.5 * cm
    ensure_space(1.2)
    c.drawString(left, y, f"Cumplen: {cumplen}    Observaciones: {obs_count}    No conformidades: {nc_count}    Oportunidades: {op_count}")
    y -= 0.9 * cm

    items_section("Observaciones", observaciones, "observacion")
    items_section("No conformidades", no_conformidades, "no_conformidad")
    items_section("Oportunidades de mejora", oportunidades, "oportunidad")

    # ✅ AHORA: Detalle por requisito con HALLAZGO + OM
    section_title("Detalle de evaluación por requisito")

    if not evaluaciones:
        ensure_space(1.0)
        c.setFont("Helvetica", 9)
        c.setFillColor(GRIS)
        c.drawString(left, y, "Sin evaluaciones registradas.")
        y -= 0.7 * cm
    else:
        for e in evaluaciones:
            codigo = e.get("codigo", "")
            desc = e.get("descripcion", "")
            resu = e.get("resultado", "")
            ev = (e.get("evidencia", "") or "").strip()

            # Buscar detalle hallazgo y OM para ese requisito
            obs = obs_by_req.get(codigo)
            nc = nc_by_req.get(codigo)
            op = op_by_req.get(codigo)

            det_hallazgo = ""
            ev_hallazgo = ""
            if obs:
                det_hallazgo = (obs.get("observacion", "") or "").strip()
                ev_hallazgo = (obs.get("evidencia", "") or "").strip()
            elif nc:
                det_hallazgo = (nc.get("no_conformidad", "") or "").strip()
                ev_hallazgo = (nc.get("evidencia", "") or "").strip()

            det_op = (op.get("oportunidad", "") or "").strip() if op else ""
            ev_op = (op.get("evidencia", "") or "").strip() if op else ""

            # Estimar espacio (para que no se corte feo)
            title_lines = wrap_text_by_width(f"[{codigo}] {desc}", "Helvetica-Bold", 10, right - left)
            ev_lines = wrap_text_by_width(f"Evidencia: {ev}", "Helvetica", 10, right - left) if ev else []

            hallazgo_lines = []
            hallazgo_ev_lines = []
            if det_hallazgo:
                hallazgo_lines = wrap_text_by_width(f"Detalle hallazgo: {det_hallazgo}", "Helvetica", 10, right - left)
            if ev_hallazgo:
                hallazgo_ev_lines = wrap_text_by_width(f"Evidencia hallazgo: {ev_hallazgo}", "Helvetica-Oblique", 9, right - left)

            op_lines = []
            op_ev_lines = []
            if det_op:
                op_lines = wrap_text_by_width(f"Oportunidad de mejora: {det_op}", "Helvetica", 10, right - left)
            if ev_op:
                op_ev_lines = wrap_text_by_width(f"Evidencia/Referencia: {ev_op}", "Helvetica-Oblique", 9, right - left)

            needed_cm = (
                len(title_lines) * 0.5 +
                0.5 +
                (len(ev_lines) * 0.5) +
                (len(hallazgo_lines) * 0.5) +
                (len(hallazgo_ev_lines) * 0.45) +
                (len(op_lines) * 0.5) +
                (len(op_ev_lines) * 0.45) +
                0.9
            )
            if (y - (needed_cm * cm)) <= BOTTOM_SAFE:
                new_page()

            # Título requisito
            c.setFillColor(AZUL)
            c.setFont("Helvetica-Bold", 10)
            for line in title_lines:
                ensure_space(0.8)
                c.drawString(left, y, line)
                y -= 0.5 * cm

            # Resultado
            c.setFillColor(color_by_result(resu))
            c.setFont("Helvetica-Bold", 9)
            ensure_space(0.8)
            c.drawString(left, y, f"Resultado: {resu}")
            y -= 0.45 * cm

            # Evidencia evaluación
            if ev_lines:
                c.setFillColor(GRIS)
                c.setFont("Helvetica", 10)
                for line in ev_lines:
                    ensure_space(0.8)
                    c.drawString(left, y, line)
                    y -= 0.5 * cm

            # Detalle hallazgo
            if hallazgo_lines:
                c.setFillColor(GRIS)
                c.setFont("Helvetica", 10)
                for line in hallazgo_lines:
                    ensure_space(0.8)
                    c.drawString(left, y, line)
                    y -= 0.5 * cm

            if hallazgo_ev_lines:
                c.setFillColor(AZUL_SUAVE)
                c.setFont("Helvetica-Oblique", 9)
                for line in hallazgo_ev_lines:
                    ensure_space(0.8)
                    c.drawString(left, y, line)
                    y -= 0.45 * cm

            # Oportunidad de mejora
            if op_lines:
                c.setFillColor(GRIS)
                c.setFont("Helvetica", 10)
                for line in op_lines:
                    ensure_space(0.8)
                    c.drawString(left, y, line)
                    y -= 0.5 * cm

            if op_ev_lines:
                c.setFillColor(AZUL_SUAVE)
                c.setFont("Helvetica-Oblique", 9)
                for line in op_ev_lines:
                    ensure_space(0.8)
                    c.drawString(left, y, line)
                    y -= 0.45 * cm

            y -= 0.6 * cm

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


# (Tus rutas viejas de descarga desde output; en Render pueden no servir, pero las dejo por compatibilidad)
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














