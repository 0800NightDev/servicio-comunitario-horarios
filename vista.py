"""
===========================================================================
UPEL – Sistema de Oferta Academica  |  Prototipo Interactivo v1.0
Framework: Flet  |  Nucleo: Palo Verde  |  Periodo: 2026-2
===========================================================================
"""
import flet as ft
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════
#  HELPERS para border / padding / margin
# ═══════════════════════════════════════════════════════

def _ba(w: float, c: str) -> ft.Border:
    s = ft.BorderSide(w, c)
    return ft.Border(top=s, right=s, bottom=s, left=s)

def _br(w: float, c: str) -> ft.Border:
    return ft.Border(right=ft.BorderSide(w, c))

def _bb(w: float, c: str) -> ft.Border:
    return ft.Border(bottom=ft.BorderSide(w, c))

def _pa(v: float) -> ft.Padding:
    return ft.Padding(left=v, top=v, right=v, bottom=v)

def _ps(h: float = 0, v: float = 0) -> ft.Padding:
    return ft.Padding(left=h, top=v, right=h, bottom=v)

def _po(left=0, top=0, right=0, bottom=0) -> ft.Padding:
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)

def _ma(v: float) -> ft.Margin:
    return ft.Margin(left=v, top=v, right=v, bottom=v)

def _ms(h: float = 0, v: float = 0) -> ft.Margin:
    return ft.Margin(left=h, top=v, right=h, bottom=v)

def _mo(left=0, top=0, right=0, bottom=0) -> ft.Margin:
    return ft.Margin(left=left, top=top, right=right, bottom=bottom)

# ═══════════════════════════════════════════════════════
#  PALETA Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════

BG_P  = "#0D1B2A"   # primario
BG_C  = "#152235"   # cards
BG_SB = "#0A1628"   # sidebar
BG_IN = "#1A2F45"   # inputs
BG_RA = "#12203A"   # filas alternas

BLUE  = "#2196F3"
PURP  = "#7C4DFF"
GRN   = "#00E676"
ORG   = "#FF9800"
RED   = "#FF5252"
CYAN  = "#00BCD4"

TW    = "#FFFFFF"
TG    = "#78909C"
TL    = "#B0BEC5"
BOR   = "#1E3A52"

MAX_EST = 45
MAX_AMB = 30

DIAS    = ["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES","SABADO"]
FRANJAS = [
    "07:40-09:20","09:20-10:50","10:50-12:10",
    "12:30-01:50","02:10-03:30","03:40-05:00","05:00-06:20",
]

AMBIENTES: List[str] = (
    [f"P{p}-{n:02d}" for p in range(1,5) for n in range(1,8)]
    + ["VIRTUAL-01","VIRTUAL-02"]
)

PERIODOS = ["2026-2","2026-1","2025-2","2025-1"]

CARRERAS: Dict[str,Dict] = {
    "EDUC_INIC":   {"nombre":"Educacion Inicial",        "mencion":"Sin Mencion",              "color":"#FF6B6B"},
    "EDUC_INTEG":  {"nombre":"Educacion Integral",       "mencion":"Sin Mencion",              "color":"#4ECDC4"},
    "EDUC_MATEM":  {"nombre":"Educ. Mencion Matematica", "mencion":"Docencia en Matematica",   "color":"#45B7D1"},
    "EDUC_INGLES": {"nombre":"Educ. Mencion Ingles",     "mencion":"Docencia en Ingles",       "color":"#96CEB4"},
    "ORGAN_SIS":   {"nombre":"Organizacion y Sistemas",  "mencion":"Sin Mencion",              "color":"#FFEAA7"},
    "RRHH":        {"nombre":"Recursos Humanos",         "mencion":"Sin Mencion",              "color":"#DDA0DD"},
}

DOCENTES = [
    "ADA URSULINA BRITO CARDENAS","MARYELIN ALEJANDRA GONZALEZ",
    "REYNA DEL CARMEN HURTADO DE VILLARROEL","FELIPA ECHEZURIA",
    "LILIANA MERCEDES MONASTERIO BLANCO","INGRID JOSEFINA BORGES OROPEZA",
    "EMMA JOSEFINA MANEIRO","LOURDES ELENA MANRIQUE RIOS",
    "JOSE FRANCISCO LUZONDO RIVAS","ANIBAL JOSE GARCIA ESCORIHUELA",
    "GABRIEL SEGUNDO LEAL PENALOZA","EVA CRISTINA REVERAND PEREZ",
    "JORGE LUIS DE MOYA PUERTA","CARLOS JESUS PACHECO ISAVA",
    "CELMIS COROMOTO GUERRERO MANCILLA","THAIS DEL CARMEN GALEA",
    "ANTONIO DE JESUS DELGADO","NELLY MEDINA DE PRADO",
    "JUSETH FELIX GONZALEZ LAREZ","JOSE DE JESUS GONZALEZ RODRIGUEZ",
    "LAURA PATRICIA SOSA HERNANDEZ","CARLOS ALBERTO FIGUEROA RAMOS",
]

MATERIAS: Dict[str,List[Dict]] = {
    "EDUC_INIC":[
        {"nombre":"ESTRATEGIAS COGNITIVAS",        "horas":3,"ciclo":"INTRODUCTORIO"},
        {"nombre":"INICIACION UNIVERSITARIA",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"USO DE LAS TIC",                "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"LENGUAJE Y COMUNICACION",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"ETICA VALORES AUTOBIOGRAFIA",   "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"PENSAMIENTO ROBINSONIANO",      "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"DIDACTICA I",                   "horas":3,"ciclo":"BASICO"},
        {"nombre":"PSICOLOGIA DEL DESARROLLO",     "horas":3,"ciclo":"BASICO"},
        {"nombre":"PRACTICA DOCENTE I",            "horas":4,"ciclo":"PROFESIONAL"},
    ],
    "EDUC_INTEG":[
        {"nombre":"SEMINARIO DE INICIACION",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"MATEMATICA I",                  "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"LENGUAJE Y COMUNICACION",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"ETICA VALORES AUTOBIOGRAFIA",   "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"PENSAMIENTO ROBINSONIANO",      "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"PENSAMIENTO ANDRAGOGICO",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"GEOGRAFIA DE VENEZUELA",        "horas":3,"ciclo":"BASICO"},
        {"nombre":"DIDACTICA GENERAL",             "horas":3,"ciclo":"BASICO"},
    ],
    "EDUC_MATEM":[
        {"nombre":"CALCULO IV",                    "horas":3,"ciclo":"PROFESIONAL"},
        {"nombre":"GEOMETRIA II",                  "horas":4,"ciclo":"PROFESIONAL"},
        {"nombre":"ALGEBRA III",                   "horas":3,"ciclo":"PROFESIONAL"},
        {"nombre":"PROYECTO I",                    "horas":6,"ciclo":"PROFESIONAL"},
        {"nombre":"PROYECTO II",                   "horas":6,"ciclo":"PROFESIONAL"},
        {"nombre":"SEMINARIO ESPECIAL DE GRADO",   "horas":4,"ciclo":"PROFESIONAL"},
        {"nombre":"PRECALCULO",                    "horas":3,"ciclo":"INTRODUCTORIO"},
        {"nombre":"ALGEBRA LINEAL",                "horas":3,"ciclo":"BASICO"},
    ],
    "EDUC_INGLES":[
        {"nombre":"INICIACION UNIVERSITARIA",      "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"LENGUAJE Y COMUNICACION",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"METODOS Y TECNICAS DE ESTUDIO", "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"PRECALCULO",                    "horas":3,"ciclo":"INTRODUCTORIO"},
        {"nombre":"ETICA VALORES AUTOBIOGRAFIA",   "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"ENGLISH I",                     "horas":4,"ciclo":"BASICO"},
        {"nombre":"ENGLISH II",                    "horas":4,"ciclo":"BASICO"},
        {"nombre":"PHONETICS AND PHONOLOGY",       "horas":3,"ciclo":"PROFESIONAL"},
    ],
    "ORGAN_SIS":[
        {"nombre":"INICIACION UNIVERSITARIA",      "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"LENGUAJE Y COMUNICACION",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"METODOS Y TECNICAS DE ESTUDIO", "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"PRECALCULO",                    "horas":3,"ciclo":"INTRODUCTORIO"},
        {"nombre":"ETICA VALORES AUTOBIOGRAFIA",   "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"PENSAMIENTO ROBINSONIANO",      "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"SISTEMAS DE INFORMACION",       "horas":3,"ciclo":"BASICO"},
        {"nombre":"ADMINISTRACION I",              "horas":3,"ciclo":"BASICO"},
    ],
    "RRHH":[
        {"nombre":"INICIACION UNIVERSITARIA",      "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"LENGUAJE Y COMUNICACION",       "horas":2,"ciclo":"INTRODUCTORIO"},
        {"nombre":"RELACIONES INDUSTRIALES",       "horas":3,"ciclo":"BASICO"},
        {"nombre":"PSICOLOGIA ORGANIZACIONAL",     "horas":3,"ciclo":"BASICO"},
        {"nombre":"GESTION DEL TALENTO HUMANO",    "horas":3,"ciclo":"PROFESIONAL"},
        {"nombre":"DERECHO LABORAL",               "horas":3,"ciclo":"PROFESIONAL"},
        {"nombre":"PROYECTO COMUNITARIO",          "horas":6,"ciclo":"PROFESIONAL"},
    ],
}

# ═══════════════════════════════════════════════════════
#  MOTOR DE HORARIOS SIN CONFLICTOS
# ═══════════════════════════════════════════════════════

class Motor:
    def __init__(self):
        self._sa: Dict[Tuple,dict] = {}   
        self._sd: Dict[Tuple,bool] = {}   
        self._u:  set              = set()

    def _slot(self, doc: str) -> Optional[Dict]:
        for d in DIAS:
            for f in FRANJAS:
                if (d,f,doc) in self._sd:
                    continue
                for a in AMBIENTES:
                    if (d,f,a) not in self._sa:
                        return {"dia":d,"franja":f,"ambiente":a}
        return None

    def registrar(self, datos: Dict) -> Dict:
        sl = self._slot(datos["docente"])
        if sl is None:
            return {**datos,"_error":"Sin slots disponibles"}
        am = "AM" if int(sl["franja"][:2]) < 12 else "PM"
        e  = {**datos,"dia":sl["dia"],"franja":sl["franja"],
              "ambiente":sl["ambiente"],"am_pm":am,"cupo":MAX_EST,"_error":None}
        self._sa[(sl["dia"],sl["franja"],sl["ambiente"])] = e
        self._sd[(sl["dia"],sl["franja"],datos["docente"])] = True
        self._u.add(sl["ambiente"])
        return e

    def entradas(self) -> List[Dict]:
        return list(self._sa.values())

    def usados(self) -> set:
        return set(self._u)

    def stats(self) -> Dict:
        t = self.entradas()
        return {
            "cursos":  len(t),
            "amb_uso": len(self._u),
            "amb_lib": MAX_AMB - len(self._u),
            "docs":    len({e["docente"] for e in t}),
        }

def _seed_data() -> Tuple[Motor, List[Dict]]:
    m = Motor()
    rows = [
        ("EDUC_INIC",  "ADA URSULINA BRITO CARDENAS",            "ESTRATEGIAS COGNITIVAS",       3,"INTRODUCTORIO",10100),
        ("EDUC_INIC",  "ADA URSULINA BRITO CARDENAS",            "INICIACION UNIVERSITARIA",      2,"INTRODUCTORIO",10100),
        ("EDUC_INIC",  "MARYELIN ALEJANDRA GONZALEZ",            "USO DE LAS TIC",               2,"INTRODUCTORIO",10100),
        ("EDUC_INIC",  "REYNA DEL CARMEN HURTADO DE VILLARROEL", "LENGUAJE Y COMUNICACION",      2,"INTRODUCTORIO",10100),
        ("EDUC_INIC",  "FELIPA ECHEZURIA",                       "ETICA VALORES AUTOBIOGRAFIA",  2,"INTRODUCTORIO",10100),
        ("EDUC_INIC",  "FELIPA ECHEZURIA",                       "PENSAMIENTO ROBINSONIANO",     2,"INTRODUCTORIO",10100),
        ("EDUC_INTEG", "LILIANA MERCEDES MONASTERIO BLANCO",     "SEMINARIO DE INICIACION",      2,"INTRODUCTORIO",10100),
        ("EDUC_INTEG", "INGRID JOSEFINA BORGES OROPEZA",         "MATEMATICA I",                 2,"INTRODUCTORIO",10100),
        ("EDUC_INTEG", "EMMA JOSEFINA MANEIRO",                  "LENGUAJE Y COMUNICACION",      2,"INTRODUCTORIO",10100),
        ("EDUC_INTEG", "LOURDES ELENA MANRIQUE RIOS",            "ETICA VALORES AUTOBIOGRAFIA",  2,"INTRODUCTORIO",10100),
        ("EDUC_INTEG", "JOSE FRANCISCO LUZONDO RIVAS",           "PENSAMIENTO ROBINSONIANO",     2,"INTRODUCTORIO",10100),
        ("EDUC_INTEG", "JOSE FRANCISCO LUZONDO RIVAS",           "PENSAMIENTO ANDRAGOGICO",      2,"INTRODUCTORIO",10100),
        ("EDUC_MATEM", "ANIBAL JOSE GARCIA ESCORIHUELA",         "CALCULO IV",                   3,"PROFESIONAL",  20112),
        ("EDUC_MATEM", "GABRIEL SEGUNDO LEAL PENALOZA",          "GEOMETRIA II",                 4,"PROFESIONAL",  20102),
        ("EDUC_MATEM", "ANIBAL JOSE GARCIA ESCORIHUELA",         "ALGEBRA III",                  3,"PROFESIONAL",  20203),
        ("EDUC_MATEM", "EVA CRISTINA REVERAND PEREZ",            "PROYECTO I",                   6,"PROFESIONAL",  20203),
        ("EDUC_MATEM", "EVA CRISTINA REVERAND PEREZ",            "PROYECTO II",                  6,"PROFESIONAL",  20111),
        ("EDUC_MATEM", "EVA CRISTINA REVERAND PEREZ",            "SEMINARIO ESPECIAL DE GRADO",  4,"PROFESIONAL",  20212),
        ("EDUC_INGLES","JORGE LUIS DE MOYA PUERTA",              "INICIACION UNIVERSITARIA",      2,"INTRODUCTORIO",10200),
        ("EDUC_INGLES","CARLOS JESUS PACHECO ISAVA",             "LENGUAJE Y COMUNICACION",      2,"INTRODUCTORIO",10200),
        ("EDUC_INGLES","ADA URSULINA BRITO CARDENAS",            "METODOS Y TECNICAS DE ESTUDIO",2,"INTRODUCTORIO",10200),
        ("EDUC_INGLES","CELMIS COROMOTO GUERRERO MANCILLA",      "PRECALCULO",                   3,"INTRODUCTORIO",10200),
        ("EDUC_INGLES","LOURDES ELENA MANRIQUE RIOS",            "ETICA VALORES AUTOBIOGRAFIA",  2,"INTRODUCTORIO",10200),
        ("EDUC_INGLES","THAIS DEL CARMEN GALEA",                 "PENSAMIENTO ROBINSONIANO",     2,"INTRODUCTORIO",10200),
        ("ORGAN_SIS",  "ANTONIO DE JESUS DELGADO",               "INICIACION UNIVERSITARIA",      2,"INTRODUCTORIO",20100),
        ("ORGAN_SIS",  "CARLOS JESUS PACHECO ISAVA",             "LENGUAJE Y COMUNICACION",      2,"INTRODUCTORIO",20100),
        ("ORGAN_SIS",  "NELLY MEDINA DE PRADO",                  "METODOS Y TECNICAS DE ESTUDIO",2,"INTRODUCTORIO",20100),
        ("ORGAN_SIS",  "JUSETH FELIX GONZALEZ LAREZ",            "PRECALCULO",                   3,"INTRODUCTORIO",20100),
        ("ORGAN_SIS",  "ANTONIO DE JESUS DELGADO",               "ETICA VALORES AUTOBIOGRAFIA",  2,"INTRODUCTORIO",20100),
        ("ORGAN_SIS",  "JOSE DE JESUS GONZALEZ RODRIGUEZ",       "PENSAMIENTO ROBINSONIANO",     2,"INTRODUCTORIO",20100),
        ("RRHH",       "LAURA PATRICIA SOSA HERNANDEZ",          "INICIACION UNIVERSITARIA",      2,"INTRODUCTORIO",30100),
        ("RRHH",       "CARLOS ALBERTO FIGUEROA RAMOS",          "LENGUAJE Y COMUNICACION",      2,"INTRODUCTORIO",30100),
        ("RRHH",       "GABRIEL SEGUNDO LEAL PENALOZA",          "RELACIONES INDUSTRIALES",      3,"BASICO",        30201),
    ]
    datos = [
        {"carrera_id":r[0],"docente":r[1],"materia":r[2],"horas":r[3], "ciclo":r[4],"seccion":r[5],"periodo":"2026-2"}
        for r in rows
    ]
    entries = [m.registrar(d) for d in datos]
    return m, entries

# ═══════════════════════════════════════════════════════
#  WIDGET HELPERS
# ═══════════════════════════════════════════════════════

def badge(txt: str, col: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(txt, color=col, size=10, weight=ft.FontWeight.W_700),
        bgcolor=f"{col}22", border_radius=6, padding=_ps(8,3),
    )

def divl() -> ft.Container:
    return ft.Container(height=1, bgcolor=BOR)

def titulo(txt: str, sub: str = "") -> ft.Column:
    c: List[ft.Control] = [ft.Text(txt, color=TW, size=26, weight=ft.FontWeight.BOLD)]
    if sub:
        c.append(ft.Text(sub, color=TG, size=13))
    return ft.Column(c, spacing=4)

def stat_card(tit: str, val: str, ico, col: str, nota: str) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Icon(ico, color=col, size=20),
                bgcolor=f"{col}20", border_radius=10,
                padding=10, width=42, height=42,
            ),
            ft.Container(height=14),
            ft.Text(val,  color=TW, size=30, weight=ft.FontWeight.BOLD),
            ft.Text(tit,  color=TL, size=12),
            ft.Container(height=4),
            ft.Text(nota, color=col, size=11),
        ], spacing=0),
        bgcolor=BG_C, border_radius=14,
        padding=_pa(18), border=_ba(1,BOR), expand=True,
    )

def campo(lbl: str, **kw) -> ft.TextField:
    return ft.TextField(
        label=lbl, bgcolor=BG_IN, border_color=BOR,
        focused_border_color=BLUE, color=TW,
        label_style=ft.TextStyle(color=TG),
        border_radius=10, **kw,
    )

def ddrop(lbl: str, opts, **kw) -> ft.Dropdown:
    return ft.Dropdown(
        label=lbl, options=opts, bgcolor=BG_IN,
        border_color=BOR, focused_border_color=BLUE,
        color=TW, label_style=ft.TextStyle(color=TG),
        border_radius=10, **kw,
    )

# ═══════════════════════════════════════════════════════
#  APP
# ═══════════════════════════════════════════════════════

class App:
    NAV = [
        ("dashboard",   ft.Icons.DASHBOARD_ROUNDED,    "Dashboard"),
        ("nueva_carga", ft.Icons.ADD_CIRCLE_ROUNDED,   "Nueva Carga"),
        ("horarios",    ft.Icons.CALENDAR_MONTH,        "Horarios"),
        ("ambientes",   ft.Icons.MEETING_ROOM_ROUNDED,  "Ambientes"),
        ("docentes",    ft.Icons.PEOPLE_ROUNDED,        "Docentes"),
        ("carreras",    ft.Icons.SCHOOL_ROUNDED,        "Carreras"),
    ]

    def __init__(self, page: ft.Page):
        self.page    = page
        self.motor, self._all = _seed_data()
        self.vista   = "dashboard"
        self._setup()
        self._build()
        self._nav("dashboard")

    def _setup(self):
        p = self.page
        p.title      = "UPEL - Oferta Academica 2026-2"
        p.theme_mode = ft.ThemeMode.DARK
        p.bgcolor    = BG_P
        p.padding    = 0
        p.spacing    = 0
        p.width      = 1360
        p.height     = 860

    def _build(self):
        self.sb_col = ft.Column(spacing=0, expand=True)
        self.sb     = ft.Container(
            content=self.sb_col, width=235, bgcolor=BG_SB,
            border=_br(1, BOR),
        )
        self.mc_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
        self.mc     = ft.Container(
            content=self.mc_col, expand=True, bgcolor=BG_P,
            padding=_pa(28),
        )
        self.page.add(ft.Row([self.sb, self.mc], spacing=0, expand=True))

    def _nav(self, v: str):
        self.vista = v
        self._sb_refresh()
        self._mc_refresh()
        self.page.update()

    def _sb_refresh(self):
        st = self.motor.stats()

        logo = ft.Container(content=ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, color=TW, size=22),
                    bgcolor=BLUE, border_radius=10, padding=9, width=42, height=42,
                ),
                ft.Column([
                    ft.Text("USR", color=TW, size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Palo Verde", color=TG, size=10),
                ], spacing=0),
            ], spacing=10),
            ft.Container(height=6),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, color=GRN, size=8),
                    ft.Text("Periodo 2026-2", color=GRN, size=11),
                ], spacing=6),
                bgcolor=f"{GRN}15", border_radius=20,
                padding=_ps(10, 5), border=_ba(1, f"{GRN}40"),
            ),
        ], spacing=10), padding=_pa(18))

        btns = []
        for vid, ico, lbl in self.NAV:
            act = self.vista == vid
            btns.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ico, color=BLUE if act else TG, size=18),
                    ft.Text(lbl, color=TW if act else TG, size=13,
                            weight=ft.FontWeight.W_600 if act else ft.FontWeight.W_400),
                ], spacing=12),
                bgcolor=f"{BLUE}20" if act else None,
                border=_ba(1, f"{BLUE}60") if act else None,
                border_radius=10,
                padding=_ps(14, 10),
                margin=_ms(10, 0),
                on_click=lambda e, v=vid: self._nav(v),
                ink=True,
            ))

        def mrow(lbl, val, col):
            return ft.Row([
                ft.Text(lbl, color=TG, size=11, expand=True),
                ft.Container(
                    content=ft.Text(val, color=col, size=11, weight=ft.FontWeight.W_700),
                    bgcolor=f"{col}18", border_radius=6,
                    padding=_ps(7, 2),
                ),
            ])

        bot = ft.Container(content=ft.Column([
            divl(),
            ft.Container(content=ft.Column([
                ft.Text("RESUMEN RAPIDO", color=TG, size=10, weight=ft.FontWeight.W_700),
                ft.Container(height=8),
                mrow("Cursos activos",   str(st["cursos"]),  BLUE),
                mrow("Ambientes en uso", f"{st['amb_uso']}/{MAX_AMB}", ORG),
                mrow("Conflictos",       "0",                 GRN),
                mrow("Docentes",         str(st["docs"]),    CYAN),
            ], spacing=6), padding=_pa(16)),
        ]))

        self.sb_col.controls = [
            logo, divl(), ft.Container(height=8),
            ft.Column(btns, spacing=3),
            ft.Container(expand=True), bot,
        ]

    def _mc_refresh(self):
        fn = {
            "dashboard":   self._vd,
            "nueva_carga": self._vnc,
            "horarios":    self._vh,
            "ambientes":   self._va,
            "docentes":    self._vdoc,
            "carreras":    self._vc,
        }.get(self.vista, self._vd)
        self.mc_col.controls = [fn()]

    # ══════════════════════════════════════════════════
    #  VISTA DASHBOARD
    # ══════════════════════════════════════════════════
    def _vd(self) -> ft.Control:
        st = self.motor.stats()

        cards = ft.Row([
            stat_card("Total Cursos",     str(st["cursos"]),  ft.Icons.BOOK_ROUNDED,          BLUE, "Periodo 2026-2"),
            stat_card("Ambientes en Uso", str(st["amb_uso"]), ft.Icons.MEETING_ROOM_ROUNDED,  ORG,  f"de {MAX_AMB} totales"),
            stat_card("Docentes Activos", str(st["docs"]),    ft.Icons.PEOPLE_ROUNDED,        PURP, "Periodo 2026-2"),
            stat_card("Conflictos",       "0",                ft.Icons.VERIFIED_ROUNDED,      GRN,  "Cero colisiones!"),
        ], spacing=16)

        enc = ft.Container(
            content=ft.Row([
                ft.Container(width=4),
                ft.Text("CARRERA",  color=TG, size=10, weight=ft.FontWeight.W_700, width=140),
                ft.Text("DOCENTE",  color=TG, size=10, weight=ft.FontWeight.W_700, width=195),
                ft.Text("MATERIA",  color=TG, size=10, weight=ft.FontWeight.W_700, width=195),
                ft.Text("DIA",      color=TG, size=10, weight=ft.FontWeight.W_700, width=85),
                ft.Text("HORARIO",  color=TG, size=10, weight=ft.FontWeight.W_700, width=120),
                ft.Text("AMBIENTE", color=TG, size=10, weight=ft.FontWeight.W_700),
            ], spacing=8),
            bgcolor="#1A2F45", border_radius=8,
            padding=_ps(12, 10), margin=_mo(bottom=4),
        )

        filas = []
        for i, e in enumerate(reversed(self._all[-10:])):
            ci  = CARRERAS.get(e["carrera_id"], {})
            col = ci.get("color", BLUE)
            bg  = BG_C if i % 2 == 0 else BG_RA
            filas.append(ft.Container(
                content=ft.Row([
                    ft.Container(width=4, height=32, bgcolor=col, border_radius=2),
                    ft.Container(ft.Text(ci.get("nombre","")[:15], color=col, size=11, weight=ft.FontWeight.W_600), width=140),
                    ft.Container(ft.Text(e["docente"][:23],         color=TL, size=11), width=195),
                    ft.Container(ft.Text(e["materia"][:24],          color=TL, size=11), width=195),
                    ft.Container(ft.Text(e["dia"],                   color=TG, size=11), width=85),
                    ft.Container(ft.Text(e["franja"],                color=TG, size=11), width=120),
                    badge(e["ambiente"], BLUE),
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=GRN, size=15),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=bg, border_radius=8,
                padding=_ps(12, 7), margin=_mo(bottom=2),
            ))

        tabla = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Carga Academica Reciente", color=TW, size=15, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.TextButton("Ver todo ->",style=ft.ButtonStyle(color=BLUE),on_click=lambda _: self._nav("horarios")),
                ]),
                ft.Container(height=8),
                enc,
                ft.Column(filas, spacing=0),
            ], spacing=0),
            bgcolor=BG_C, border_radius=14, padding=_pa(20), border=_ba(1,BOR),
        )

        mini_car = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Container(width=8, height=8, bgcolor=c["color"], border_radius=4),
                    ft.Container(height=6),
                    ft.Text(str(len([e for e in self._all if e["carrera_id"]==k])),
                            color=TW, size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(c["nombre"], color=TG, size=10, max_lines=2),
                ], spacing=2),
                bgcolor=BG_C, border_radius=12, padding=_pa(14),
                border=_ba(1, f"{c['color']}35"), width=152,
                on_click=lambda _,kk=k: self._nav("horarios"), ink=True,
            )
            for k, c in CARRERAS.items()
        ], spacing=12, wrap=True)

        # REEMPLAZO 1: ElevatedButton eliminado, ahora es un ft.Container interactivo
        btn_nueva_carga = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_ROUNDED, color=TW, size=18),
                ft.Text("Nueva Carga  +", color=TW, size=14, weight=ft.FontWeight.W_600)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=BLUE, border_radius=10, padding=_ps(18, 14),
            on_click=lambda _: self._nav("nueva_carga"), ink=True,
        )

        return ft.Column([
            ft.Row([
                titulo("Dashboard","Sistema de Gestion de Oferta Academica - UPEL Palo Verde"),
                ft.Container(expand=True),
                btn_nueva_carga
            ]),
            ft.Container(height=22),
            cards,
            ft.Container(height=20),
            tabla,
            ft.Container(height=20),
            ft.Text("Distribucion por Carrera", color=TW, size=15, weight=ft.FontWeight.W_600),
            ft.Container(height=10),
            mini_car,
            ft.Container(height=10),
        ], spacing=0)

    # ══════════════════════════════════════════════════
    #  VISTA NUEVA CARGA
    # ══════════════════════════════════════════════════
    def _vnc(self) -> ft.Control:
        dd_per = ddrop("Periodo", [ft.dropdown.Option(p) for p in PERIODOS], value="2026-2")
        dd_car = ddrop("Carrera",  [ft.dropdown.Option(k, c["nombre"]) for k,c in CARRERAS.items()])
        dd_doc = ddrop("Docente",  [ft.dropdown.Option(d) for d in DOCENTES])
        dd_mat = ddrop("Materia",  [])
        tf_hrs = campo("Horas Semanales", keyboard_type=ft.KeyboardType.NUMBER, value="2")
        dd_cic = ddrop("Ciclo", [ft.dropdown.Option(c) for c in ["INTRODUCTORIO","BASICO","PROFESIONAL"]])
        tf_sec = campo("Seccion", hint_text="Ej: 10100", keyboard_type=ft.KeyboardType.NUMBER)

        res = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=BLUE, size=18),
                ft.Text("El sistema asignara horario y ambiente automaticamente.",
                        color=TG, size=13, italic=True),
            ], spacing=10),
            bgcolor=f"{BLUE}10", border_radius=12,
            padding=_pa(16), border=_ba(1,BOR),
        )

        def on_car(e):
            k = dd_car.value
            if k in MATERIAS:
                dd_mat.options = [ft.dropdown.Option(m["nombre"]) for m in MATERIAS[k]]
                dd_mat.value   = None
                dd_mat.update()

        def on_mat(e):
            k, n = dd_car.value, dd_mat.value
            if k and n:
                for m in MATERIAS.get(k,[]):
                    if m["nombre"] == n:
                        tf_hrs.value = str(m["horas"])
                        dd_cic.value = m["ciclo"]
                        tf_hrs.update(); dd_cic.update()
                        break

        dd_car.on_change = on_car
        dd_mat.on_change = on_mat

        def generar(e):
            vacios = [n for n,w in [("Carrera",dd_car.value),("Docente",dd_doc.value),("Materia",dd_mat.value),("Horas",tf_hrs.value)] if not w]
            if vacios:
                res.content = ft.Row([
                    ft.Icon(ft.Icons.ERROR_ROUNDED, color=RED, size=18),
                    ft.Text(f"Completa: {', '.join(vacios)}", color=RED, size=13),
                ], spacing=10)
                res.bgcolor = f"{RED}12"; res.border = _ba(1,f"{RED}50")
                res.update(); return

            res.content = ft.Row([
                ft.ProgressRing(width=22, height=22, stroke_width=3, color=BLUE),
                ft.Text("Generando horario sin conflictos...", color=TG, size=13),
            ], spacing=12)
            res.bgcolor = f"{BLUE}10"; res.border = _ba(1,BOR); res.update()

            datos = {
                "carrera_id": dd_car.value, "docente": dd_doc.value,
                "materia": dd_mat.value, "horas": int(tf_hrs.value or 2),
                "ciclo": dd_cic.value or "INTRODUCTORIO",
                "seccion": int(tf_sec.value or 10100), "periodo": dd_per.value or "2026-2",
            }
            entrada = self.motor.registrar(datos)
            self._all.append(entrada)

            if entrada.get("_error"):
                res.content = ft.Column([
                    ft.Row([ft.Icon(ft.Icons.ERROR_ROUNDED,color=RED,size=18),
                            ft.Text("Sin disponibilidad",color=RED,size=13,weight=ft.FontWeight.W_600)],spacing=8),
                    ft.Text(entrada["_error"], color=TG, size=12),
                ], spacing=6)
                res.bgcolor = f"{RED}10"; res.border = _ba(1,f"{RED}50")
            else:
                ci  = CARRERAS.get(entrada["carrera_id"],{})
                col = ci.get("color", BLUE)

                def fr(lbl, val, vc=TW):
                    return ft.Row([
                        ft.Text(lbl, color=TG, size=12, width=160),
                        ft.Text(val, color=vc, size=12, weight=ft.FontWeight.W_500, expand=True),
                    ])

                res.content = ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=GRN, size=20),
                        ft.Text("Horario generado exitosamente!", color=GRN, size=14, weight=ft.FontWeight.W_700),
                    ], spacing=8),
                    ft.Container(height=14),
                    ft.Container(content=ft.Column([
                        fr("Carrera:",       ci.get("nombre",""),  col),
                        fr("Docente:",       entrada["docente"]),
                        fr("Materia:",       entrada["materia"]),
                        fr("Ciclo:",         entrada["ciclo"]),
                        divl(),
                        fr("Dia asignado:",  entrada["dia"],        BLUE),
                        fr("Horario:",       entrada["franja"],     BLUE),
                        fr("Ambiente:",      entrada["ambiente"],   ORG),
                        fr("Cap. maxima:",   f"{MAX_EST} estudiantes", GRN),
                        fr("Conflictos:",    "Ninguno detectado",   GRN),
                    ], spacing=8), bgcolor=BG_P, border_radius=10, padding=_pa(14)),
                ], spacing=0)
                res.bgcolor = f"{GRN}10"; res.border = _ba(1,f"{GRN}50")
                self._sb_refresh(); self.page.update()

            res.update()

        def paso(n, txt):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(n,color=TW,size=10,weight=ft.FontWeight.BOLD),
                        bgcolor=BLUE, border_radius=12, width=22, height=22,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(txt, color=TG, size=12, expand=True),
                ], spacing=10),
                margin=_mo(bottom=8),
            )

        # REEMPLAZO 2: ElevatedButton eliminado, ahora es un ft.Container interactivo
        btn_generar = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=TW, size=18),
                ft.Text("Generar Horario Automatico", color=TW, size=14, weight=ft.FontWeight.W_600)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=BLUE, border_radius=10, padding=_ps(20, 16),
            on_click=generar, width=float("inf"), ink=True,
        )

        pf = ft.Container(content=ft.Column([
            ft.Text("Datos de la Carga", color=TW, size=15, weight=ft.FontWeight.W_600),
            divl(), ft.Container(height=12),
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.INFO_ROUNDED,color=BLUE,size=15),
                        ft.Text("Restricciones del Sistema",color=TW,size=12,weight=ft.FontWeight.W_600)],spacing=8),
                ft.Container(height=4),
                ft.Text(f"- Maximo {MAX_EST} estudiantes por ambiente", color=TG, size=11),
                ft.Text(f"- {MAX_AMB} ambientes disponibles en total",  color=TG, size=11),
                ft.Text("- El sistema garantiza 0 conflictos",           color=GRN, size=11),
            ], spacing=3), bgcolor=f"{BLUE}12", border_radius=10,padding=_pa(12), border=_ba(1,f"{BLUE}40")),
            ft.Container(height=14),
            dd_per, ft.Container(height=8),
            dd_car, ft.Container(height=8),
            dd_doc, ft.Container(height=8),
            dd_mat, ft.Container(height=8),
            ft.Row([tf_hrs, dd_cic], spacing=10), ft.Container(height=8),
            tf_sec, ft.Container(height=20),
            btn_generar
        ], spacing=0), bgcolor=BG_C, border_radius=14, padding=_pa(22), border=_ba(1,BOR), expand=True)

        pr = ft.Container(content=ft.Column([
            ft.Text("Resultado del Sistema", color=TW, size=15, weight=ft.FontWeight.W_600),
            divl(), ft.Container(height=12),
            res,
            ft.Container(height=20),
            ft.Text("Como funciona el motor?", color=TW, size=13, weight=ft.FontWeight.W_600),
            ft.Container(height=10),
            paso("1","Recibes solo los datos esenciales del docente y la materia."),
            paso("2","El motor verifica la disponibilidad del docente en cada franja."),
            paso("3","Busca un ambiente libre en esa misma franja horaria."),
            paso("4","Confirma que no existen superposiciones en ninguna carrera."),
            paso("5","Registra la asignacion con todos los datos generados."),
        ], spacing=0), bgcolor=BG_C, border_radius=14, padding=_pa(22), border=_ba(1,BOR), expand=True)

        return ft.Column([
            titulo("Nueva Carga Academica","Ingresa los datos; el sistema asigna horario y ambiente sin conflictos."),
            ft.Container(height=22),
            ft.Row([pf, pr], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START, expand=True),
        ], spacing=0, expand=True)

    # ══════════════════════════════════════════════════
    #  VISTA HORARIOS
    # ══════════════════════════════════════════════════
    def _vh(self) -> ft.Control:
        dd_fc = ddrop("Filtrar Carrera",
            [ft.dropdown.Option("TODAS","Todas las Carreras")]
            +[ft.dropdown.Option(k,c["nombre"]) for k,c in CARRERAS.items()],
            value="TODAS", width=220)
        dd_fd = ddrop("Filtrar Dia",
            [ft.dropdown.Option("TODOS","Todos los Dias")]
            +[ft.dropdown.Option(d) for d in DIAS],
            value="TODOS", width=180)

        col_t = ft.Column(spacing=0)

        def build(e=None):
            fc, fd = dd_fc.value, dd_fd.value
            datos  = self._all
            if fc and fc != "TODAS": datos = [x for x in datos if x["carrera_id"]==fc]
            if fd and fd != "TODOS": datos = [x for x in datos if x["dia"]==fd]

            enc = ft.Container(
                content=ft.Row([
                    ft.Container(width=4),
                    ft.Text("CARRERA",  color=TG,size=10,weight=ft.FontWeight.W_700,width=140),
                    ft.Text("DOCENTE",  color=TG,size=10,weight=ft.FontWeight.W_700,width=195),
                    ft.Text("MATERIA",  color=TG,size=10,weight=ft.FontWeight.W_700,width=195),
                    ft.Text("CICLO",    color=TG,size=10,weight=ft.FontWeight.W_700,width=100),
                    ft.Text("DIA",      color=TG,size=10,weight=ft.FontWeight.W_700,width=85),
                    ft.Text("HORARIO",  color=TG,size=10,weight=ft.FontWeight.W_700,width=120),
                    ft.Text("AMBIENTE", color=TG,size=10,weight=ft.FontWeight.W_700,width=90),
                    ft.Text("OK",       color=TG,size=10,weight=ft.FontWeight.W_700),
                ], spacing=8),
                bgcolor="#1A2F45", border_radius=8,
                padding=_ps(12,10), margin=_mo(bottom=4),
            )
            filas = []
            for i, entry in enumerate(datos):
                ci  = CARRERAS.get(entry["carrera_id"],{})
                col = ci.get("color", BLUE)
                bg  = BG_C if i%2==0 else BG_RA
                filas.append(ft.Container(
                    content=ft.Row([
                        ft.Container(width=4,height=32,bgcolor=col,border_radius=2),
                        ft.Container(ft.Text(ci.get("nombre","")[:15],color=col,size=11,weight=ft.FontWeight.W_600),width=140),
                        ft.Container(ft.Text(entry["docente"][:24],color=TL,size=11),width=195),
                        ft.Container(ft.Text(entry["materia"][:24], color=TL,size=11),width=195),
                        ft.Container(badge(entry["ciclo"][:5],PURP),width=100),
                        ft.Container(ft.Text(entry["dia"],  color=TG,size=11),width=85),
                        ft.Container(ft.Text(entry["franja"],color=TG,size=11),width=120),
                        badge(entry["ambiente"],BLUE),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED,color=GRN,size=15),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=bg, border_radius=8,
                    padding=_ps(12,7), margin=_mo(bottom=2),
                ))
            col_t.controls = [
                enc, ft.Column(filas,spacing=0),
                ft.Container(
                    content=ft.Text(f"Total: {len(datos)} registros",color=TG,size=11),
                    padding=_ps(12,8),
                ),
            ]
            col_t.update()

        dd_fc.on_change = build
        dd_fd.on_change = build
        build()

        banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.VERIFIED_ROUNDED, color=GRN, size=22),
                ft.Column([
                    ft.Text("Sistema Sin Conflictos de Horario",color=GRN,size=13,weight=ft.FontWeight.W_700),
                    ft.Text("Todos los ambientes y docentes asignados sin superposicion.",color=TG,size=11),
                ], spacing=2),
                ft.Container(expand=True),
                badge("0 CONFLICTOS", GRN),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=f"{GRN}12", border_radius=12,
            padding=_pa(16), border=_ba(1,f"{GRN}40"),
        )

        return ft.Column([
            titulo("Horarios Asignados","Vista completa de la oferta academica generada automaticamente."),
            ft.Container(height=18),
            banner,
            ft.Container(height=14),
            ft.Row([dd_fc, dd_fd], spacing=12),
            ft.Container(height=12),
            ft.Container(
                content=ft.Column([col_t], scroll=ft.ScrollMode.AUTO),
                bgcolor=BG_C, border_radius=14, padding=_pa(16),
                border=_ba(1,BOR), expand=True,
            ),
        ], expand=True, spacing=0)

    # ══════════════════════════════════════════════════
    #  VISTA AMBIENTES
    # ══════════════════════════════════════════════════
    def _va(self) -> ft.Control:
        usados = self.motor.usados()
        st     = self.motor.stats()

        cards = []
        for amb in AMBIENTES:
            en_uso = amb in usados
            clases = [e for e in self._all if e.get("ambiente") == amb]
            col    = ORG if en_uso else GRN
            cards.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.MEETING_ROOM_ROUNDED, color=col, size=16),
                        ft.Container(expand=True),
                        badge("OCUP" if en_uso else "LIBRE", col),
                    ]),
                    ft.Container(height=8),
                    ft.Text(amb, color=TW, size=13, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{len(clases)} clase(s)", color=TG, size=10),
                    ft.Container(height=4),
                    ft.Text(f"Cap: {MAX_EST}", color=TG, size=10),
                ], spacing=3),
                bgcolor=BG_C, border_radius=12, padding=_pa(12),
                border=_ba(1,f"{col}40"), width=135, height=115,
            ))

        return ft.Column([
            titulo("Gestion de Ambientes", f"Distribucion de los {MAX_AMB} ambientes academicos."),
            ft.Container(height=20),
            ft.Row([
                stat_card("Total Ambientes", str(MAX_AMB),         ft.Icons.MEETING_ROOM_ROUNDED, BLUE, "Capacidad total"),
                stat_card("En Uso",           str(st["amb_uso"]),   ft.Icons.LOCK_ROUNDED,          ORG,  "Asignados"),
                stat_card("Disponibles",      str(st["amb_lib"]),   ft.Icons.CHECK_ROUNDED,         GRN,  "Libres"),
                stat_card("Cap. por Aula",    str(MAX_EST),         ft.Icons.PERSON_ROUNDED,        PURP, "Estudiantes max."),
            ], spacing=16),
            ft.Container(height=20),
            ft.Text("Estado de cada Ambiente", color=TW, size=15, weight=ft.FontWeight.W_600),
            ft.Container(height=12),
            ft.Container(
                content=ft.GridView(
                    controls=cards, max_extent=145,
                    child_aspect_ratio=145/115,
                    spacing=12, run_spacing=12, expand=True,
                ),
                bgcolor=BG_C, border_radius=14,
                padding=_pa(18), border=_ba(1,BOR), height=430,
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    # ══════════════════════════════════════════════════
    #  VISTA DOCENTES
    # ══════════════════════════════════════════════════
    def _vdoc(self) -> ft.Control:
        cards = []
        for doc in DOCENTES:
            asig    = [e for e in self._all if e.get("docente") == doc]
            nombres = doc.title().split()
            ini     = nombres[0][0] if nombres else "?"
            filas_m = [
                ft.Row([
                    ft.Container(width=6, height=6,bgcolor=CARRERAS.get(e["carrera_id"],{}).get("color",BLUE),border_radius=3),
                    ft.Text(e["materia"][:22], color=TG, size=10, expand=True),
                    ft.Text(e["dia"][:3],      color=BLUE, size=10),
                ], spacing=6)
                for e in asig[:3]
            ]
            if len(asig) > 3:
                filas_m.append(ft.Text(f"+{len(asig)-3} mas", color=TG, size=10, italic=True))

            cards.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(ini, color=TW, size=15, weight=ft.FontWeight.BOLD),
                            bgcolor=BLUE, width=38, height=38, border_radius=19,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column([
                            ft.Text(" ".join(nombres[:2]), color=TW, size=12, weight=ft.FontWeight.W_600),
                            ft.Text(f"{len(asig)} materia(s)", color=TG, size=10),
                        ], spacing=2, expand=True),
                    ], spacing=10),
                    ft.Container(height=8),
                    divl(),
                    ft.Container(height=8),
                    *filas_m,
                ], spacing=0),
                bgcolor=BG_C, border_radius=12, padding=_pa(14),
                border=_ba(1,BOR), width=265,
            ))

        return ft.Column([
            titulo("Gestion de Docentes","Panel de docentes activos para el periodo 2026-2."),
            ft.Container(height=22),
            ft.Row(cards, wrap=True, spacing=14, run_spacing=14),
        ], scroll=ft.ScrollMode.AUTO, spacing=0)

    # ══════════════════════════════════════════════════
    #  VISTA CARRERAS
    # ══════════════════════════════════════════════════
    def _vc(self) -> ft.Control:
        paneles = []
        for kid, c in CARRERAS.items():
            col    = c["color"]
            asig   = [e for e in self._all if e["carrera_id"]==kid]
            pensum = MATERIAS.get(kid,[])
            mat_r  = [
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=7, height=7, bgcolor=col, border_radius=4),
                        ft.Text(m["nombre"], color=TW, size=11, expand=True),
                        ft.Text(f"{m['horas']}h", color=TG, size=10),
                        badge(m["ciclo"][:5], col),
                    ], spacing=8),
                    padding=_ps(0,5),
                    border=_bb(1,BOR),
                )
                for m in pensum
            ]
            paneles.append(ft.Container(
                content=ft.Column([
                    ft.Container(content=ft.Row([
                        ft.Container(width=4, height=48, bgcolor=col, border_radius=2),
                        ft.Column([
                            ft.Text(c["nombre"],  color=TW, size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(c["mencion"], color=TG, size=11),
                        ], spacing=3, expand=True),
                        badge(f"{len(asig)} cursos", col),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER), height=52),
                    divl(),
                    ft.Container(height=8),
                    ft.Text("Pensum de Materias", color=TG, size=11, weight=ft.FontWeight.W_600),
                    ft.Container(height=4),
                    *mat_r,
                ], spacing=4),
                bgcolor=BG_C, border_radius=14, padding=_pa(18),
                border=_ba(1,f"{col}35"), width=375,
            ))

        return ft.Column([
            titulo("Gestion de Carreras","Carreras registradas y su pensum academico en el sistema."),
            ft.Container(height=22),
            ft.Row(paneles, wrap=True, spacing=18, run_spacing=18),
        ], scroll=ft.ScrollMode.AUTO, spacing=0)

# ═══════════════════════════════════════════════════════
#  ENTRY POINT / ARRANQUE INFALIBLE
# ═══════════════════════════════════════════════════════
def main(page: ft.Page) -> None:
    App(page)

if __name__ == "__main__":
    ft.run(main)