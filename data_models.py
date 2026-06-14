# data_models.py

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

# Expandimos los requisitos para incluir 3810 según el IRAM
REQUISITOS = [
    {"codigo": "9001-39001-3810-4.1", "descripcion": "Comprensión de la organización y su contexto."},
    {"codigo": "9001-39001-3810-4.2", "descripcion": "Comprensión de las necesidades y expectativas de las partes interesadas."},
    {"codigo": "9001-39001-3810-4.3", "descripcion": "Determinación del alcance del SGI."},
    {"codigo": "9001-39001-3810-4.4", "descripcion": "Sistema de gestión de la calidad/sv y sus procesos."},
    {"codigo": "9001-39001-3810-5.1", "descripcion": "Liderazgo y compromiso del SGI."},
    {"codigo": "9001-39001-3810-5.2", "descripcion": "Política del SGI establecida y comunicada."},
    {"codigo": "9001-39001-3810-5.3", "descripcion": "Roles, responsabilidades y autoridades del SGI."},

    {"codigo": "9001-6.1-39001-6.2", "descripcion": "Acciones para abordar riesgos y oportunidades."},
    {"codigo": "9001-6.2-39001-6.4", "descripcion": "Objetivos del SGI y planificación para lograrlos."},

    {"codigo": "9001-6.3", "descripcion": "Gestión de los cambios relevantes."},
    {"codigo": "39001-6.3-3810-6.3", "descripcion": "Factores de desempeño de SV "},

    {"codigo": "9001-7.1-39001-7.2-3810-7.1", "descripcion": "Recursos adecuados para el SGI."},
    {"codigo": "9001-7.2-39001-7.3-3810-7.2", "descripcion": "Competencia y formación del personal."},
    {"codigo": "9001-7.3-39001-7.4-3810-7.3", "descripcion": "Conciencia sobre la política y objetivos del SGI."},
    {"codigo": "9001-7.4-39001-7.5-3810-7.4", "descripcion": "Comunicación interna y externa del SGI."},
    {"codigo": "9001-7.5-39001-7.6-3810-7.6", "descripcion": "Control de la información documentada."},

    {"codigo": "9001-8.1-39001-8.1-3810-8.1", "descripcion": "Planificación y control operacional."},
    {"codigo": "9001-8.2-3810-8.2", "descripcion": "Determinación de requisitos para productos y servicios."},
    {"codigo": "39001-8.2", "descripcion": "Preparación y respuesta ante emergencias."},
    {"codigo": "9001-8.4-3810-8.4", "descripcion": "Control de los procesos, productos y servicios suministrados externamente."},
    {"codigo": "9001-8.5-3810-8.5", "descripcion": "Producción y provisión del servicio."},
    {"codigo": "9001-8.7-3810-8.7", "descripcion": "Control de salidas no conformes."},

    {"codigo": "9001-39001-9.1-3810-9.1", "descripcion": "Seguimiento, medición, análisis y evaluación del SGI."},
    {"codigo": "39001-9.2-3810-9.2", "descripcion": "Investigación de siniestros e incidentes viales."},

    {"codigo": "9001-9.2-39001-9.3-3810-5.10", "descripcion": "Auditoría interna del SGI."},
    {"codigo": "9001-9.3-39001-9.4-3810-4.2", "descripcion": "Revisión por la dirección."},
    {"codigo": "9001-10.2-39001-10.1-3810-10.1", "descripcion": "Gestión de no conformidades y acciones correctivas."},
    {"codigo": "9001-10.3-39001-10.2-3810-10.2", "descripcion": "Mejora continua del SGI."},
]

CHECKLIST = {
    "9001-39001-3810-4.1": "¿Se identificaron las partes internas/externas relevantes y su contexto?",
    "9001-39001-3810-4.2": "¿Se identificaron partes interesadas y sus necesidades/expectativas?",
    "9001-39001-3810-4.3": "¿El alcance del SGI está definido y disponible como información documentada?",
    "9001-39001-3810-4.4": "¿Se determinan procesos del SGI y su interacción?",
    "9001-39001-3810-5.1": "¿La dirección demuestra liderazgo y compromiso con el SGI?",
    "9001-39001-3810-5.2": "¿La política SGI está disponible y comunicada?",
    "9001-39001-3810-5.3": "¿Se asignan roles, responsabilidades y autoridades del SGI?",

    "9001-6.1-39001-6.2": "¿Se abordan riesgos y oportunidades en el SGI?",
    "9001-6.2-39001-6.4": "¿Se establecen objetivos SGI medibles y se planifica su logro?",
    "9001-6.3": "¿Se planifican y controlan cambios relevantes?",
    "39001-6.3-3810-6.3": "¿Se determinan y gestionan factores de desempeño de seguridad vial?",

    "9001-7.1-39001-7.2-3810-7.1": "¿Se determinan y proporcionan recursos para el SGI?",
    "9001-7.2-39001-7.3-3810-7.2": "¿Se asegura competencia del personal y se conserva evidencia?",
    "9001-7.3-39001-7.4-3810-7.3": "¿El personal toma conciencia de política, objetivos y su contribución?",
    "9001-7.4-39001-7.5-3810-7.4": "¿Existe comunicación interna/externa del SGI definida?",
    "9001-7.5-39001-7.6-3810-7.6": "¿Se controla la información documentada?",

    "9001-8.1-39001-8.1-3810-8.1": "¿Se planifica y controla la operación (incluye criterios y controles)?",
    "9001-8.2-3810-8.2": "¿Se determinan requisitos del servicio antes de su provisión?",
    "39001-8.2": "¿Se implementan controles operacionales y respuesta ante emergencias viales?",
    "9001-8.4-3810-8.4": "¿Se controla a proveedores externos y servicios tercerizados?",
    "9001-8.5-3810-8.5": "¿Se controlan procesos de prestación del servicio?",
    "9001-8.7-3810-8.7": "¿Se controlan salidas no conformes?",

    "9001-39001-9.1-3810-9.1": "¿Se hace seguimiento, medición, análisis y evaluación?",
    "39001-9.2-3810-9.2": "¿Se investigan siniestros e incidentes viales?",
    "9001-9.2-39001-9.3-3810-5.10": "¿Se audita el SGI internamente según un programa establecido?",
    "9001-9.3-39001-9.4-3810-4.2": "¿Se hace revisión por la dirección con entradas/salidas claras?",
    "9001-10.2-39001-10.1-3810-10.1": "¿Se gestionan no conformidades y se implementan acciones correctivas?",
    "9001-10.3-39001-10.2-3810-10.2": "¿El SGI impulsa la mejora continua?",
}
