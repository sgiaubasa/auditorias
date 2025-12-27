from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import date, datetime
from pymongo import MongoClient
import json
import os

app = Flask(__name__)

# ✅ Mejor práctica: SECRET_KEY por entorno (en local cae a tu valor actual)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_para_flash")

# ✅ Mongo: usa Atlas si seteás MONGO_URI, si no cae a localhost como antes
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# Server selection timeout para no "colgarse" si hay problema de conexión
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
    {"codigo": "9001-4.1", "descripcion": "Comprensión de la organización y su contexto."},
    {"codigo": "9001-4.2", "descripcion": "Comprensión de las necesidades y expectativas de las partes interesadas."},
    {"codigo": "9001-4.3", "descripcion": "Determinación del alcance del SGI."},
    {"codigo": "9001-4.4", "descripcion": "Sistema de gestión de la calidad y sus procesos."},
    {"codigo": "9001-5.1", "descripcion": "Liderazgo y compromiso del SGI."},
    {"codigo": "9001-5.2", "descripcion": "Política del SGI establecida y comunicada."},
    {"codigo": "9001-5.3", "descripcion": "Roles, responsabilidades y autoridades del SGI."},
    {"codigo": "9001-6.1", "descripcion": "Acciones para abordar riesgos y oportunidades."},
    {"codigo": "9001-6.2", "descripcion": "Objetivos del SGI y planificación para lograrlos."},
    {"codigo": "9001-6.3", "descripcion": "Gestión de los cambios relevantes."},
    {"codigo": "9001-7.1", "descripcion": "Recursos adecuados para el SGI."},
    {"codigo": "9001-7.2", "descripcion": "Competencia y formación del personal."},
    {"codigo": "9001-7.3", "descripcion": "Conciencia sobre la política y objetivos del SGI."},
    {"codigo": "9001-7.4", "descripcion": "Comunicación interna y externa del SGI."},
    {"codigo": "9001-7.5", "descripcion": "Control de la información documentada."},
    {"codigo": "9001-8.1", "descripcion": "Planificación y control operacional."},
    {"codigo": "9001-8.2", "descripcion": "Determinación de requisitos para productos y servicios."},
    {"codigo": "9001-8.4", "descripcion": "Control de productos y servicios externos."},
    {"codigo": "9001-8.5", "descripcion": "Prestación del servicio y control de procesos."},
    {"codigo": "9001-8.7", "descripcion": "Control de salidas no conformes."},
    {"codigo": "39001-8.2", "descripcion": "Control operacional de riesgos de seguridad vial."},
    {"codigo": "9001-9.1", "descripcion": "Seguimiento, medición, análisis y evaluación del SGI."},
    {"codigo": "9001-9.2", "descripcion": "Auditoría interna del SGI."},
    {"codigo": "9001-9.3", "descripcion": "Revisión por la dirección."},
    {"codigo": "9001-10.1", "descripcion": "Gestión de no conformidades y acciones correctivas."},
    {"codigo": "9001-10.2", "descripcion": "Mejora continua del SGI."},
    {"codigo": "9001-10.3", "descripcion": "Resultados de la mejora y su efectividad."}
]

CHECKLIST = {
    "9001-4.1": "¿Se han identificado los factores internos y externos relevantes para el propósito y dirección estratégica?",
    "9001-4.2": "¿Se han determinado las partes interesadas pertinentes y sus requisitos?",
    "9001-4.3": "¿Está claramente definido y documentado el alcance del SGI?",
    "9001-4.4": "¿Se han establecido, implementado, mantenido y mejorado los procesos necesarios del SGI?",
    "9001-5.1": "¿La alta dirección demuestra liderazgo y compromiso con el SGI?",
    "9001-5.2": "¿Existe una política de calidad documentada, comunicada y entendida?",
    "9001-5.3": "¿Están definidos y comunicados roles, responsabilidades y autoridades?",
    "9001-6.1": "¿Se identifican y tratan riesgos y oportunidades del sistema?",
    "9001-6.2": "¿Se han establecido objetivos de calidad medibles y coherentes?",
    "9001-6.3": "¿Existe planificación para implementar cambios necesarios?",
    "9001-7.1": "¿Hay recursos adecuados para mantener el SGI?",
    "9001-7.2": "¿El personal es competente y está adecuadamente formado?",
    "9001-7.3": "¿El personal conoce la política y sus aportes al SGI?",
    "9001-7.4": "¿Se gestiona eficazmente la comunicación interna y externa?",
    "9001-7.5": "¿La documentación está actualizada, accesible y controlada?",
    "9001-8.1": "¿Se planifican y controlan los procesos operativos clave?",
    "9001-8.2": "¿Se determinan y revisan los requisitos del cliente?",
    "9001-8.4": "¿Se controlan eficazmente productos y servicios externos?",
    "9001-8.5": "¿La prestación del servicio sigue los estándares planificados?",
    "9001-8.7": "¿Se controlan adecuadamente las salidas no conformes?",
    "39001-8.2": "¿Se implementan controles para riesgos de seguridad vial?",
    "9001-9.1": "¿Se realiza seguimiento, medición y análisis del SGI?",
    "9001-9.2": "¿Se audita el SGI internamente según un programa establecido?",
    "9001-9.3": "¿Se hace revisión por la dirección con entradas/salidas claras?",
    "9001-10.1": "¿Se gestionan no conformidades y se implementan acciones correctivas?",
    "9001-10.2": "¿El SGI impulsa la mejora continua?",
    "9001-10.3": "¿Se analizan y aprovechan los resultados de mejora?",
}

# ✅ Carpeta de salida portable (Windows/Render/Linux)
OUTPUT_DIR = os.path.join(app.root_path, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # (Opcional) forzar conexión rápida para detectar problemas de Atlas
        try:
            client.admin.command("ping")
        except Exception as e:
            flash(f"❌ Error conectando a MongoDB: {e}")
            return redirect(url_for("index"))

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

        # ✅ Guardar en MongoDB (Atlas o local según MONGO_URI)
        res = coleccion.insert_one(data)

        # Para exportar a JSON/TXT, convertimos _id a string
        data["_id"] = str(res.inserted_id)

        timestamp = datetime.now().strftime("%H%M%S")
        safe_sector = (data["sector"] or "SIN_SECTOR").replace(" ", "_")

        fname = os.path.join(OUTPUT_DIR, f"informe_{safe_sector}_{data['fecha']}_{timestamp}.json")
        resumen_txt = os.path.join(OUTPUT_DIR, f"resumen_{safe_sector}_{data['fecha']}_{timestamp}.txt")

        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Crear resumen .txt (igual que tu funcionalidad original)
        total = len(data["evaluaciones"])
        cumplen = sum(1 for e in data["evaluaciones"] if (e["resultado"] or "").lower() == "cumple")
        obs_count = len(data["observaciones"])
        nc_count = len(data["no_conformidades"])
        op_count = len(data["oportunidades"])

        with open(resumen_txt, "w", encoding="utf-8") as f:
            f.write("AUBASA - AUDITORÍAS INTERNAS\n" + "=" * 80 + "\n")
            f.write(
                "OBJETIVO: Verificar la adecuada implementación y desempeño del SGI\n"
                "de la empresa conforme las normas ISO 9001 e ISO 39001, con foco\n"
                "en la mejora continua y la preparación para la auditoría de recertificación.\n\n"
            )
            f.write(f"Fecha: {data['fecha']}\n")
            f.write(f"Sector: {data['sector']}\n")
            f.write(f"Lugar: {data['lugar']}\n\n")
            f.write(f"Auditores líder: {', '.join(data['auditores_lider'])}\n")
            f.write(f"Auditores: {', '.join(data['auditores'])}\n")
            f.write(f"Veedores: {', '.join(data['veedores'])}\n")
            f.write(f"Presentes: {', '.join(data['presentes'])}\n\n")

            f.write("RESUMEN DE AUDITORÍA\n")
            f.write(
                f"Total puntos: {total}   Cumplen: {cumplen}   Observaciones: {obs_count}   "
                f"No conformidades: {nc_count}   Oportunidades de mejora: {op_count}\n\n"
            )

            f.write("RESULTADOS:\n")
            for e in data["evaluaciones"]:
                f.write(f"- [{e['codigo']}] {e['descripcion']}\n")
                f.write(f"    Resultado: {e['resultado']}\n")
                f.write(f"    Evidencia: {e['evidencia']}\n")

                if e["tipo"] == "observación":
                    for o in data["observaciones"]:
                        if o["requisito"] == e["codigo"]:
                            f.write(f"    Observación: {o['observacion']}\n")
                            break

                if e["tipo"] == "no conformidad":
                    for nc in data["no_conformidades"]:
                        if nc["requisito"] == e["codigo"]:
                            f.write(f"    No conformidad: {nc['no_conformidad']}\n")
                            break

                for op in data["oportunidades"]:
                    if op["requisito"] == e["codigo"]:
                        f.write(f"    Oportunidad de mejora: {op['oportunidad']}\n")
                        break

            f.write("\nCONCLUSIÓN:\n")
            if nc_count > 0:
                f.write(
                    "Se han identificado no conformidades en nuestro SGI que requieren atención\n"
                    "inmediata. Confiamos en que su pronta resolución garantizará el cumplimiento\n"
                    "normativo y reforzará la efectividad del sistema.\n\n"
                )
            elif obs_count > 0 or op_count > 0:
                f.write(
                    "Se han registrado observaciones y oportunidades de mejora que apuntan a aspectos\n"
                    "que pueden optimizarse en nuestro SGI. Confiamos en que su revisión contribuirá a\n"
                    "mejorar la eficiencia y solidez del sistema.\n\n"
                )
            else:
                f.write("Todos los puntos cumplen.\n")

        flash("✅ Auditoría guardada correctamente.")
        return redirect(url_for("index"))

    return render_template("auditoria_form.html", sectores=SECTORES, requisitos=REQUISITOS, checklist=CHECKLIST)

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




