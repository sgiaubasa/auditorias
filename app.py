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

# ==========================================================
# REQUISITOS ISO 9001:2015 (4 a 10) + ISO 39001:2012 (4 a 10)
# ==========================================================

REQUISITOS_9001 = [
    # 4 Contexto
    {"codigo": "9001-4.1", "descripcion": "Comprensión de la organización y su contexto."},
    {"codigo": "9001-4.2", "descripcion": "Comprensión de las necesidades y expectativas de las partes interesadas."},
    {"codigo": "9001-4.3", "descripcion": "Determinación del alcance del sistema de gestión de la calidad."},
    {"codigo": "9001-4.4", "descripcion": "Sistema de gestión de la calidad y sus procesos."},

    # 5 Liderazgo
    {"codigo": "9001-5.1.1", "descripcion": "Liderazgo y compromiso - General."},
    {"codigo": "9001-5.1.2", "descripcion": "Liderazgo y compromiso - Enfoque al cliente."},
    {"codigo": "9001-5.2.1", "descripcion": "Política de la calidad - Establecimiento."},
    {"codigo": "9001-5.2.2", "descripcion": "Política de la calidad - Comunicación."},
    {"codigo": "9001-5.3", "descripcion": "Roles, responsabilidades y autoridades."},

    # 6 Planificación
    {"codigo": "9001-6.1", "descripcion": "Acciones para abordar riesgos y oportunidades."},
    {"codigo": "9001-6.2.1", "descripcion": "Objetivos de la calidad."},
    {"codigo": "9001-6.2.2", "descripcion": "Planificación para lograr los objetivos de la calidad."},
    {"codigo": "9001-6.3", "descripcion": "Planificación de los cambios."},

    # 7 Apoyo
    {"codigo": "9001-7.1.1", "descripcion": "Recursos - General."},
    {"codigo": "9001-7.1.2", "descripcion": "Personas."},
    {"codigo": "9001-7.1.3", "descripcion": "Infraestructura."},
    {"codigo": "9001-7.1.4", "descripcion": "Ambiente para la operación de los procesos."},
    {"codigo": "9001-7.1.5", "descripcion": "Recursos de seguimiento y medición."},
    {"codigo": "9001-7.1.6", "descripcion": "Conocimiento de la organización."},
    {"codigo": "9001-7.2", "descripcion": "Competencia."},
    {"codigo": "9001-7.3", "descripcion": "Toma de conciencia."},
    {"codigo": "9001-7.4", "descripcion": "Comunicación."},
    {"codigo": "9001-7.5.1", "descripcion": "Información documentada - General."},
    {"codigo": "9001-7.5.2", "descripcion": "Creación y actualización."},
    {"codigo": "9001-7.5.3", "descripcion": "Control de la información documentada."},

    # 8 Operación
    {"codigo": "9001-8.1", "descripcion": "Planificación y control operacional."},
    {"codigo": "9001-8.2.1", "descripcion": "Requisitos para los productos y servicios - Comunicación con el cliente."},
    {"codigo": "9001-8.2.2", "descripcion": "Determinación de los requisitos para los productos y servicios."},
    {"codigo": "9001-8.2.3", "descripcion": "Revisión de los requisitos para los productos y servicios."},
    {"codigo": "9001-8.2.4", "descripcion": "Cambios en los requisitos para los productos y servicios."},
    {"codigo": "9001-8.3", "descripcion": "Diseño y desarrollo de productos y servicios (si aplica)."},
    {"codigo": "9001-8.4.1", "descripcion": "Control de procesos, productos y servicios suministrados externamente - General."},
    {"codigo": "9001-8.4.2", "descripcion": "Tipo y alcance del control externo."},
    {"codigo": "9001-8.4.3", "descripcion": "Información para los proveedores externos."},
    {"codigo": "9001-8.5.1", "descripcion": "Producción y provisión del servicio - Control de la prestación."},
    {"codigo": "9001-8.5.2", "descripcion": "Identificación y trazabilidad (si aplica)."},
    {"codigo": "9001-8.5.3", "descripcion": "Propiedad perteneciente a los clientes o proveedores externos (si aplica)."},
    {"codigo": "9001-8.5.4", "descripcion": "Preservación."},
    {"codigo": "9001-8.5.5", "descripcion": "Actividades posteriores a la entrega (si aplica)."},
    {"codigo": "9001-8.5.6", "descripcion": "Control de los cambios."},
    {"codigo": "9001-8.6", "descripcion": "Liberación de los productos y servicios."},
    {"codigo": "9001-8.7", "descripcion": "Control de las salidas no conformes."},

    # 9 Evaluación del desempeño
    {"codigo": "9001-9.1.1", "descripcion": "Seguimiento, medición, análisis y evaluación - General."},
    {"codigo": "9001-9.1.2", "descripcion": "Satisfacción del cliente."},
    {"codigo": "9001-9.1.3", "descripcion": "Análisis y evaluación."},
    {"codigo": "9001-9.2.1", "descripcion": "Auditoría interna - General."},
    {"codigo": "9001-9.2.2", "descripcion": "Programa de auditoría interna."},
    {"codigo": "9001-9.3.1", "descripcion": "Revisión por la dirección - General."},
    {"codigo": "9001-9.3.2", "descripcion": "Entradas para la revisión por la dirección."},
    {"codigo": "9001-9.3.3", "descripcion": "Salidas para la revisión por la dirección."},

    # 10 Mejora
    {"codigo": "9001-10.1", "descripcion": "General (mejora)."},
    {"codigo": "9001-10.2.1", "descripcion": "No conformidad y acción correctiva - General."},
    {"codigo": "9001-10.2.2", "descripcion": "Acción correctiva - Revisión de la eficacia."},
    {"codigo": "9001-10.3", "descripcion": "Mejora continua."},
]

REQUISITOS_39001 = [
    # 4 Contexto
    {"codigo": "39001-4.1", "descripcion": "Comprensión de la organización y su contexto (Seguridad Vial)."},
    {"codigo": "39001-4.2", "descripcion": "Necesidades y expectativas de las partes interesadas (Seguridad Vial)."},
    {"codigo": "39001-4.3", "descripcion": "Determinación del alcance del sistema de gestión de seguridad vial."},
    {"codigo": "39001-4.4", "descripcion": "Sistema de gestión de seguridad vial y sus procesos."},

    # 5 Liderazgo
    {"codigo": "39001-5.1", "descripcion": "Liderazgo y compromiso (Seguridad Vial)."},
    {"codigo": "39001-5.2", "descripcion": "Política de seguridad vial."},
    {"codigo": "39001-5.3", "descripcion": "Roles, responsabilidades y autoridades (Seguridad Vial)."},

    # 6 Planificación
    {"codigo": "39001-6.1", "descripcion": "Acciones para abordar riesgos y oportunidades (Seguridad Vial)."},
    {"codigo": "39001-6.2", "descripcion": "Objetivos de seguridad vial y planificación para lograrlos."},

    # 7 Apoyo
    {"codigo": "39001-7.1", "descripcion": "Recursos (Seguridad Vial)."},
    {"codigo": "39001-7.2", "descripcion": "Competencia (Seguridad Vial)."},
    {"codigo": "39001-7.3", "descripcion": "Toma de conciencia (Seguridad Vial)."},
    {"codigo": "39001-7.4", "descripcion": "Comunicación (Seguridad Vial)."},
    {"codigo": "39001-7.5", "descripcion": "Información documentada (Seguridad Vial)."},

    # 8 Operación
    {"codigo": "39001-8.1", "descripcion": "Planificación y control operacional (Seguridad Vial)."},
    {"codigo": "39001-8.2", "descripcion": "Preparación y respuesta ante emergencias viales."},

    # 9 Evaluación del desempeño
    {"codigo": "39001-9.1", "descripcion": "Seguimiento, medición, análisis y evaluación (Seguridad Vial)."},
    {"codigo": "39001-9.2", "descripcion": "Investigación de incidentes y accidentes de tránsito."},
    {"codigo": "39001-9.3", "descripcion": "Auditoría interna (Seguridad Vial)."},
    {"codigo": "39001-9.4", "descripcion": "Revisión por la dirección (Seguridad Vial)."},

    # 10 Mejora
    {"codigo": "39001-10.1", "descripcion": "No conformidad y acción correctiva (Seguridad Vial)."},
    {"codigo": "39001-10.2", "descripcion": "Mejora continua (Seguridad Vial)."},
]

REQUISITOS = REQUISITOS_9001 + REQUISITOS_39001
REQ_DESC = {r["codigo"]: r["descripcion"] for r in REQUISITOS}

# ==========================================================
# INTEGRACIÓN "REAL": SOLO CLÁUSULAS EQUIVALENTES (HLS)
# ==========================================================

CLAUSULAS_INTEGRABLES = {
    "4.1", "4.2", "4.3", "4.4",
    "5.1", "5.2", "5.3",
    "6.1", "6.2",
    "7.1", "7.2", "7.3", "7.4", "7.5",
    "8.1",
    "9.1", "9.3", "9.4",
    "10.1", "10.2"
}

def _norma_label_from_codigo(codigo: str) -> str:
    pref = (codigo or "").split("-", 1)[0].strip()
    return f"ISO {pref}" if pref else "ISO"

def _clausula_from_codigo(codigo: str) -> str:
    parts = (codigo or "").split("-", 1)
    return parts[1].strip() if len(parts) > 1 else codigo

def _clausula_base(clausula: str) -> str:
    if not clausula:
        return clausula
    parts = clausula.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else clausula

def _build_normas_por_clausula_integrable(requisitos):
    m = {}
    for r in requisitos or []:
        cod = r.get("codigo", "")
        clausula = _clausula_from_codigo(cod)
        base = _clausula_base(clausula)
        if base not in CLAUSULAS_INTEGRABLES:
            continue
        norma = _norma_label_from_codigo(cod)
        m.setdefault(base, [])
        if norma not in m[base]:
            m[base].append(norma)

    def _sort_norma(n):
        return (0 if "9001" in n else 1, n)

    for k in m:
        m[k] = sorted(m[k], key=_sort_norma)
    return m

NORMAS_POR_CLAUSULA = _build_normas_por_clausula_integrable(REQUISITOS)

def etiqueta_requisito(codigo: str) -> str:
    clausula = _clausula_from_codigo(codigo)
    base = _clausula_base(clausula)

    normas = NORMAS_POR_CLAUSULA.get(base)
    if normas and len(normas) >= 2:
        return f"{' / '.join(normas)} – {base}"

    return f"{_norma_label_from_codigo(codigo)} – {clausula}"

# ==========================================================
# FORMULARIO UNIFICADO (GRUPOS)
# ==========================================================

GRUPOS_SGI = [
    {"id": "G-4.1", "codigos": ["9001-4.1", "39001-4.1"]},
    {"id": "G-4.2", "codigos": ["9001-4.2", "39001-4.2"]},
    {"id": "G-4.3", "codigos": ["9001-4.3", "39001-4.3"]},
    {"id": "G-4.4", "codigos": ["9001-4.4", "39001-4.4"]},

    {"id": "G-5.1", "codigos": ["9001-5.1.1", "9001-5.1.2", "39001-5.1"]},
    {"id": "G-5.2", "codigos": ["9001-5.2.1", "9001-5.2.2", "39001-5.2"]},
    {"id": "G-5.3", "codigos": ["9001-5.3", "39001-5.3"]},

    {"id": "G-6.1", "codigos": ["9001-6.1", "39001-6.1"]},
    {"id": "G-6.2", "codigos": ["9001-6.2.1", "9001-6.2.2", "39001-6.2"]},
    {"id": "G-6.3", "codigos": ["9001-6.3"]},

    {"id": "G-7.1", "codigos": ["9001-7.1.1", "9001-7.1.2", "9001-7.1.3", "9001-7.1.4", "9001-7.1.5", "9001-7.1.6", "39001-7.1"]},
    {"id": "G-7.2", "codigos": ["9001-7.2", "39001-7.2"]},
    {"id": "G-7.3", "codigos": ["9001-7.3", "39001-7.3"]},
    {"id": "G-7.4", "codigos": ["9001-7.4", "39001-7.4"]},
    {"id": "G-7.5", "codigos": ["9001-7.5.1", "9001-7.5.2", "9001-7.5.3", "39001-7.5"]},

    {"id": "G-8.1", "codigos": ["9001-8.1", "39001-8.1"]},

    # 8.2 NO se integra
    {"id": "G-9001-8.2", "codigos": ["9001-8.2.1", "9001-8.2.2", "9001-8.2.3", "9001-8.2.4"]},
    {"id": "G-39001-8.2", "codigos": ["39001-8.2"]},

    {"id": "G-9001-8.3", "codigos": ["9001-8.3"]},
    {"id": "G-9001-8.4", "codigos": ["9001-8.4.1", "9001-8.4.2", "9001-8.4.3"]},
    {"id": "G-9001-8.5", "codigos": ["9001-8.5.1", "9001-8.5.2", "9001-8.5.3", "9001-8.5.4", "9001-8.5.5", "9001-8.5.6"]},
    {"id": "G-9001-8.6", "codigos": ["9001-8.6"]},
    {"id": "G-9001-8.7", "codigos": ["9001-8.7"]},

    {"id": "G-9.1", "codigos": ["9001-9.1.1", "9001-9.1.2", "9001-9.1.3", "39001-9.1"]},
    {"id": "G-AUD", "codigos": ["9001-9.2.1", "9001-9.2.2", "39001-9.3"]},
    {"id": "G-RPD", "codigos": ["9001-9.3.1", "9001-9.3.2", "9001-9.3.3", "39001-9.4"]},
    {"id": "G-39001-9.2", "codigos": ["39001-9.2"]},

    {"id": "G-10.1", "codigos": ["9001-10.2.1", "9001-10.2.2", "39001-10.1"]},
    {"id": "G-10.2", "codigos": ["9001-10.1", "9001-10.3", "39001-10.2"]},
]

def _grupo_base_visible(grupo: dict) -> str:
    codigos = grupo.get("codigos") or []
    if not codigos:
        return ""
    cl = _clausula_from_codigo(codigos[0])
    return _clausula_base(cl)

def etiqueta_grupo(grupo: dict) -> str:
    codigos = grupo.get("codigos") or []
    tiene_9001 = any(str(c).startswith("9001-") for c in codigos)
    tiene_39001 = any(str(c).startswith("39001-") for c in codigos)
    base = _grupo_base_visible(grupo)

    if tiene_9001 and tiene_39001:
        return f"ISO 9001 / ISO 39001 – {base}"
    if tiene_9001:
        return f"ISO 9001 – {base}"
    if tiene_39001:
        return f"ISO 39001 – {base}"
    return grupo.get("id", "Requisito")

CHECKLIST_GRUPOS = {
    "G-4.1": "¿Se determinan y revisan factores internos/externos relevantes para el SGI (calidad y seguridad vial)?",
    "G-4.2": "¿Se identifican partes interesadas y requisitos relevantes (calidad y seguridad vial)?",
    "G-4.3": "¿El alcance del SGI está definido, disponible y actualizado?",
    "G-4.4": "¿Se gestionan los procesos del SGI (interacción, criterios, responsables, recursos y control)?",

    "G-5.1": "¿La Dirección evidencia liderazgo y compromiso (enfoque al cliente/seguridad vial, recursos, mejora)?",
    "G-5.2": "¿Existe política (integrada o coherente), comunicada y disponible?",
    "G-5.3": "¿Están asignados y comunicados roles, responsabilidades y autoridades del SGI?",

    "G-6.1": "¿Se determinan riesgos/oportunidades y se planifican acciones (calidad y seguridad vial)?",
    "G-6.2": "¿Se establecen objetivos con planes, responsables, recursos y seguimiento?",
    "G-6.3": "¿Los cambios del sistema se planifican y controlan para no afectar la integridad del SGC?",

    "G-7.1": "¿Se aseguran recursos suficientes (personas, infraestructura, medición, conocimiento) para el SGI?",
    "G-7.2": "¿El personal es competente y hay evidencias de competencia/capacitación?",
    "G-7.3": "¿Las personas toman conciencia de su contribución y consecuencias del incumplimiento?",
    "G-7.4": "¿Está definida la comunicación interna/externa del SGI (qué, quién, cuándo, cómo)?",
    "G-7.5": "¿La información documentada está controlada (creación, actualización, acceso, registros)?",

    "G-8.1": "¿Se planifica y controla la operación con criterios y controles definidos?",
    "G-9001-8.2": "¿Se determinan, revisan y controlan requisitos del servicio antes de comprometerse (incluye cambios)?",
    "G-39001-8.2": "¿Existe plan de respuesta a emergencias viales (roles, coordinación, simulacros y mejora)?",
    "G-9001-8.3": "Si aplica: ¿se controla el diseño y desarrollo (entradas/salidas/revisiones/verificación)?",
    "G-9001-8.4": "¿Se controlan proveedores externos según riesgos y criterios definidos?",
    "G-9001-8.5": "¿La prestación del servicio se controla y los cambios se gestionan con registros?",
    "G-9001-8.6": "¿Se libera el servicio solo con evidencia de conformidad?",
    "G-9001-8.7": "¿Se controlan salidas no conformes (identificación, acciones, registros)?",

    "G-9.1": "¿Se miden y analizan resultados/indicadores del SGI y se evalúa desempeño?",
    "G-AUD": "¿Se realizan auditorías internas con programa, criterios, informes y acciones?",
    "G-RPD": "¿La Dirección revisa el SGI con entradas/salidas registradas y decisiones claras?",
    "G-39001-9.2": "¿Se investigan siniestros/incidentes viales, se identifican causas y se definen acciones?",

    "G-10.1": "¿Se gestionan no conformidades y acciones correctivas verificando su eficacia?",
    "G-10.2": "¿Se impulsa la mejora continua con oportunidades, acciones y seguimiento?",
}

OUTPUT_DIR = os.path.join(app.root_path, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _safe_filename(text: str) -> str:
    text = text or "SIN_SECTOR"
    text = re.sub(r"[^A-Za-z0-9_\-]+", "_", text.strip())
    return text[:80] if len(text) > 80 else text

def _build_resumen_txt(doc: dict) -> str:
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
        etiqueta = etiqueta_requisito(codigo)
        lineas.append(f"- [{etiqueta}] {e.get('descripcion','')}")
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

        for grupo in GRUPOS_SGI:
            gid = grupo["id"]
            codigos = grupo.get("codigos") or []

            resultado = request.form.get(f"res_{gid}")
            evidencia = request.form.get(f"ev_{gid}")
            detalle = request.form.get(f"detalle_{gid}")
            oportunidad = request.form.get(f"op_{gid}")

            if not resultado:
                continue

            for codigo in codigos:
                desc = REQ_DESC.get(codigo, "")

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

                if resultado != "no requiere":
                    data["evaluaciones"].append({
                        "codigo": codigo,
                        "descripcion": desc,
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
            pass

        flash("✅ Auditoría guardada. Elegí qué informe descargar.")
        return redirect(url_for("post_guardado", id=audit_id))

    # ✅ lo que se ve en el formulario
    grupos_view = []
    for g in GRUPOS_SGI:
        gg = dict(g)
        gg["etiqueta"] = etiqueta_grupo(g)
        grupos_view.append(gg)

    return render_template(
        "auditoria_form.html",
        sectores=SECTORES,
        requisitos=grupos_view,
        checklist=CHECKLIST_GRUPOS
    )

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
            req_lbl = etiqueta_requisito(req) if req else ""
            txt = it.get(item_key, "") or ""
            ev = it.get("evidencia", "") or ""

            c.setFont("Helvetica-Bold", 9)
            c.drawString(left, y, f"• Requisito: {req_lbl or req}")
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








