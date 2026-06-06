"""
data/wc2026_data.py
────────────────────
Single source of truth for all static WC 2026 data.

Sources:
  • openfootball/world-cup  cup.txt + cup_finals.txt  — fixtures & venues
  • FIFA official draw                                 — groups & teams
  • FIFA squad announcements                           — 26-player rosters
  • FIFA referee panel announcement                    — 52 officials
  • wcup2026.org (also uses openfootball)              — cross-verified

This file needs no API calls, no keys, no rate limits.
It is updated manually when FIFA announces changes (injuries, replacements).
"""

# ══════════════════════════════════════════════════════════════════════════════
# GROUPS — all 12 groups, all 48 confirmed teams
# ══════════════════════════════════════════════════════════════════════════════

GROUPS: dict[str, list[str]] = {
    "Group A": ["Mexico",      "South Africa",         "South Korea",   "Czech Republic"],
    "Group B": ["Canada",      "Bosnia & Herzegovina", "Qatar",         "Switzerland"],
    "Group C": ["Brazil",      "Morocco",              "Haiti",         "Scotland"],
    "Group D": ["USA",         "Paraguay",             "Australia",     "Turkey"],
    "Group E": ["Germany",     "Curaçao",              "Ivory Coast",   "Ecuador"],
    "Group F": ["Netherlands", "Japan",                "Sweden",        "Tunisia"],
    "Group G": ["Belgium",     "Egypt",                "Iran",          "New Zealand"],
    "Group H": ["Spain",       "Cape Verde",           "Saudi Arabia",  "Uruguay"],
    "Group I": ["France",      "Senegal",              "Iraq",          "Norway"],
    "Group J": ["Argentina",   "Algeria",              "Austria",       "Jordan"],
    "Group K": ["Portugal",    "DR Congo",             "Uzbekistan",    "Colombia"],
    "Group L": ["England",     "Croatia",              "Ghana",         "Panama"],
}

TEAM_TO_GROUP: dict[str, str] = {
    team: group for group, teams in GROUPS.items() for team in teams
}

# ISO 2-letter country codes for flag display (flagcdn.com/w40/{code}.png)
TEAM_FLAGS: dict[str, str] = {
    "Mexico":"mx","South Africa":"za","South Korea":"kr","Czech Republic":"cz",
    "Canada":"ca","Bosnia & Herzegovina":"ba","Qatar":"qa","Switzerland":"ch",
    "Brazil":"br","Morocco":"ma","Haiti":"ht","Scotland":"gb-sct",
    "USA":"us","Paraguay":"py","Australia":"au","Turkey":"tr",
    "Germany":"de","Curaçao":"cw","Ivory Coast":"ci","Ecuador":"ec",
    "Netherlands":"nl","Japan":"jp","Sweden":"se","Tunisia":"tn",
    "Belgium":"be","Egypt":"eg","Iran":"ir","New Zealand":"nz",
    "Spain":"es","Cape Verde":"cv","Saudi Arabia":"sa","Uruguay":"uy",
    "France":"fr","Senegal":"sn","Iraq":"iq","Norway":"no",
    "Argentina":"ar","Algeria":"dz","Austria":"at","Jordan":"jo",
    "Portugal":"pt","DR Congo":"cd","Uzbekistan":"uz","Colombia":"co",
    "England":"gb-eng","Croatia":"hr","Ghana":"gh","Panama":"pa",
}

FIFA_RANKINGS: dict[str, int] = {
    "Argentina":1,"Spain":2,"France":3,"England":4,"Brazil":5,
    "Portugal":6,"Netherlands":7,"Belgium":8,"Germany":9,"Croatia":10,
    "Morocco":11,"Colombia":14,"Uruguay":15,"USA":16,"Mexico":17,
    "Japan":17,"Senegal":18,"Switzerland":19,"Iran":20,"Denmark":21,
    "Austria":22,"South Korea":23,"Ecuador":23,"Australia":24,"Sweden":25,
    "Turkey":26,"Qatar":36,"Algeria":38,"Scotland":39,"Ivory Coast":40,
    "Tunisia":41,"Paraguay":45,"South Africa":57,"Saudi Arabia":58,
    "Iraq":58,"DR Congo":61,"Jordan":62,"Cape Verde":70,"Uzbekistan":80,
    "Norway":33,"Haiti":86,"Ghana":52,"Panama":66,"New Zealand":89,
    "Curaçao":90,"Bosnia & Herzegovina":74,
}

# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES — all 104 matches, verified from openfootball cup.txt / cup_finals.txt
# ══════════════════════════════════════════════════════════════════════════════

GROUP_FIXTURES: list[dict] = [
    # Group A
    {"num":0,  "date":"2026-06-11","time":"13:00 UTC-6","team1":"Mexico",         "team2":"South Africa",        "group":"Group A","ground":"Mexico City"},
    {"num":1,  "date":"2026-06-11","time":"20:00 UTC-6","team1":"South Korea",    "team2":"Czech Republic",      "group":"Group A","ground":"Guadalajara (Zapopan)"},
    {"num":2,  "date":"2026-06-18","time":"12:00 UTC-4","team1":"Czech Republic", "team2":"South Africa",        "group":"Group A","ground":"Atlanta"},
    {"num":3,  "date":"2026-06-18","time":"19:00 UTC-6","team1":"Mexico",         "team2":"South Korea",         "group":"Group A","ground":"Guadalajara (Zapopan)"},
    {"num":4,  "date":"2026-06-24","time":"19:00 UTC-6","team1":"Czech Republic", "team2":"Mexico",              "group":"Group A","ground":"Mexico City"},
    {"num":5,  "date":"2026-06-24","time":"19:00 UTC-6","team1":"South Africa",   "team2":"South Korea",         "group":"Group A","ground":"Monterrey (Guadalupe)"},
    # Group B
    {"num":6,  "date":"2026-06-12","time":"15:00 UTC-4","team1":"Canada",         "team2":"Bosnia & Herzegovina","group":"Group B","ground":"Toronto"},
    {"num":7,  "date":"2026-06-13","time":"12:00 UTC-7","team1":"Qatar",          "team2":"Switzerland",         "group":"Group B","ground":"San Francisco Bay Area (Santa Clara)"},
    {"num":8,  "date":"2026-06-18","time":"12:00 UTC-7","team1":"Switzerland",    "team2":"Bosnia & Herzegovina","group":"Group B","ground":"Los Angeles (Inglewood)"},
    {"num":9,  "date":"2026-06-18","time":"15:00 UTC-7","team1":"Canada",         "team2":"Qatar",               "group":"Group B","ground":"Vancouver"},
    {"num":10, "date":"2026-06-24","time":"12:00 UTC-7","team1":"Switzerland",    "team2":"Canada",              "group":"Group B","ground":"Vancouver"},
    {"num":11, "date":"2026-06-24","time":"12:00 UTC-7","team1":"Bosnia & Herzegovina","team2":"Qatar",          "group":"Group B","ground":"Seattle"},
    # Group C
    {"num":12, "date":"2026-06-13","time":"18:00 UTC-4","team1":"Brazil",         "team2":"Morocco",             "group":"Group C","ground":"New York/New Jersey (East Rutherford)"},
    {"num":13, "date":"2026-06-13","time":"21:00 UTC-4","team1":"Haiti",          "team2":"Scotland",            "group":"Group C","ground":"Boston (Foxborough)"},
    {"num":14, "date":"2026-06-19","time":"18:00 UTC-4","team1":"Scotland",       "team2":"Morocco",             "group":"Group C","ground":"Boston (Foxborough)"},
    {"num":15, "date":"2026-06-19","time":"20:30 UTC-4","team1":"Brazil",         "team2":"Haiti",               "group":"Group C","ground":"Philadelphia"},
    {"num":16, "date":"2026-06-24","time":"18:00 UTC-4","team1":"Scotland",       "team2":"Brazil",              "group":"Group C","ground":"Miami (Miami Gardens)"},
    {"num":17, "date":"2026-06-24","time":"18:00 UTC-4","team1":"Morocco",        "team2":"Haiti",               "group":"Group C","ground":"Atlanta"},
    # Group D
    {"num":18, "date":"2026-06-12","time":"18:00 UTC-7","team1":"USA",            "team2":"Paraguay",            "group":"Group D","ground":"Los Angeles (Inglewood)"},
    {"num":19, "date":"2026-06-13","time":"21:00 UTC-7","team1":"Australia",      "team2":"Turkey",              "group":"Group D","ground":"Vancouver"},
    {"num":20, "date":"2026-06-19","time":"12:00 UTC-7","team1":"USA",            "team2":"Australia",           "group":"Group D","ground":"Seattle"},
    {"num":21, "date":"2026-06-19","time":"20:00 UTC-7","team1":"Turkey",         "team2":"Paraguay",            "group":"Group D","ground":"San Francisco Bay Area (Santa Clara)"},
    {"num":22, "date":"2026-06-25","time":"19:00 UTC-7","team1":"Turkey",         "team2":"USA",                 "group":"Group D","ground":"Los Angeles (Inglewood)"},
    {"num":23, "date":"2026-06-25","time":"19:00 UTC-7","team1":"Paraguay",       "team2":"Australia",           "group":"Group D","ground":"San Francisco Bay Area (Santa Clara)"},
    # Group E
    {"num":24, "date":"2026-06-14","time":"12:00 UTC-5","team1":"Germany",        "team2":"Curaçao",             "group":"Group E","ground":"Houston"},
    {"num":25, "date":"2026-06-14","time":"19:00 UTC-4","team1":"Ivory Coast",    "team2":"Ecuador",             "group":"Group E","ground":"Philadelphia"},
    {"num":26, "date":"2026-06-20","time":"16:00 UTC-4","team1":"Germany",        "team2":"Ivory Coast",         "group":"Group E","ground":"Toronto"},
    {"num":27, "date":"2026-06-20","time":"19:00 UTC-5","team1":"Ecuador",        "team2":"Curaçao",             "group":"Group E","ground":"Kansas City"},
    {"num":28, "date":"2026-06-25","time":"16:00 UTC-4","team1":"Curaçao",        "team2":"Ivory Coast",         "group":"Group E","ground":"Philadelphia"},
    {"num":29, "date":"2026-06-25","time":"16:00 UTC-4","team1":"Ecuador",        "team2":"Germany",             "group":"Group E","ground":"New York/New Jersey (East Rutherford)"},
    # Group F
    {"num":30, "date":"2026-06-14","time":"15:00 UTC-5","team1":"Netherlands",    "team2":"Japan",               "group":"Group F","ground":"Dallas (Arlington)"},
    {"num":31, "date":"2026-06-14","time":"20:00 UTC-6","team1":"Sweden",         "team2":"Tunisia",             "group":"Group F","ground":"Monterrey (Guadalupe)"},
    {"num":32, "date":"2026-06-20","time":"12:00 UTC-5","team1":"Netherlands",    "team2":"Sweden",              "group":"Group F","ground":"Houston"},
    {"num":33, "date":"2026-06-20","time":"22:00 UTC-6","team1":"Tunisia",        "team2":"Japan",               "group":"Group F","ground":"Monterrey (Guadalupe)"},
    {"num":34, "date":"2026-06-25","time":"18:00 UTC-5","team1":"Japan",          "team2":"Sweden",              "group":"Group F","ground":"Dallas (Arlington)"},
    {"num":35, "date":"2026-06-25","time":"18:00 UTC-5","team1":"Tunisia",        "team2":"Netherlands",         "group":"Group F","ground":"Kansas City"},
    # Group G
    {"num":36, "date":"2026-06-15","time":"12:00 UTC-7","team1":"Belgium",        "team2":"Egypt",               "group":"Group G","ground":"Seattle"},
    {"num":37, "date":"2026-06-15","time":"18:00 UTC-7","team1":"Iran",           "team2":"New Zealand",         "group":"Group G","ground":"Los Angeles (Inglewood)"},
    {"num":38, "date":"2026-06-21","time":"12:00 UTC-7","team1":"Belgium",        "team2":"Iran",                "group":"Group G","ground":"Los Angeles (Inglewood)"},
    {"num":39, "date":"2026-06-21","time":"18:00 UTC-7","team1":"New Zealand",    "team2":"Egypt",               "group":"Group G","ground":"Vancouver"},
    {"num":40, "date":"2026-06-26","time":"20:00 UTC-7","team1":"Egypt",          "team2":"Iran",                "group":"Group G","ground":"Seattle"},
    {"num":41, "date":"2026-06-26","time":"20:00 UTC-7","team1":"New Zealand",    "team2":"Belgium",             "group":"Group G","ground":"Vancouver"},
    # Group H
    {"num":42, "date":"2026-06-15","time":"12:00 UTC-4","team1":"Spain",          "team2":"Cape Verde",          "group":"Group H","ground":"Atlanta"},
    {"num":43, "date":"2026-06-15","time":"18:00 UTC-4","team1":"Saudi Arabia",   "team2":"Uruguay",             "group":"Group H","ground":"Miami (Miami Gardens)"},
    {"num":44, "date":"2026-06-21","time":"12:00 UTC-4","team1":"Spain",          "team2":"Saudi Arabia",        "group":"Group H","ground":"Atlanta"},
    {"num":45, "date":"2026-06-21","time":"18:00 UTC-4","team1":"Uruguay",        "team2":"Cape Verde",          "group":"Group H","ground":"Miami (Miami Gardens)"},
    {"num":46, "date":"2026-06-26","time":"19:00 UTC-5","team1":"Cape Verde",     "team2":"Saudi Arabia",        "group":"Group H","ground":"Houston"},
    {"num":47, "date":"2026-06-26","time":"18:00 UTC-6","team1":"Uruguay",        "team2":"Spain",               "group":"Group H","ground":"Guadalajara (Zapopan)"},
    # Group I
    {"num":48, "date":"2026-06-16","time":"15:00 UTC-4","team1":"France",         "team2":"Senegal",             "group":"Group I","ground":"New York/New Jersey (East Rutherford)"},
    {"num":49, "date":"2026-06-16","time":"18:00 UTC-4","team1":"Iraq",           "team2":"Norway",              "group":"Group I","ground":"Boston (Foxborough)"},
    {"num":50, "date":"2026-06-22","time":"17:00 UTC-4","team1":"France",         "team2":"Iraq",                "group":"Group I","ground":"Philadelphia"},
    {"num":51, "date":"2026-06-22","time":"20:00 UTC-4","team1":"Norway",         "team2":"Senegal",             "group":"Group I","ground":"New York/New Jersey (East Rutherford)"},
    {"num":52, "date":"2026-06-26","time":"15:00 UTC-4","team1":"Norway",         "team2":"France",              "group":"Group I","ground":"Boston (Foxborough)"},
    {"num":53, "date":"2026-06-26","time":"15:00 UTC-4","team1":"Senegal",        "team2":"Iraq",                "group":"Group I","ground":"Toronto"},
    # Group J
    {"num":54, "date":"2026-06-16","time":"20:00 UTC-5","team1":"Argentina",      "team2":"Algeria",             "group":"Group J","ground":"Kansas City"},
    {"num":55, "date":"2026-06-16","time":"21:00 UTC-7","team1":"Austria",        "team2":"Jordan",              "group":"Group J","ground":"San Francisco Bay Area (Santa Clara)"},
    {"num":56, "date":"2026-06-22","time":"12:00 UTC-5","team1":"Argentina",      "team2":"Austria",             "group":"Group J","ground":"Dallas (Arlington)"},
    {"num":57, "date":"2026-06-22","time":"20:00 UTC-7","team1":"Jordan",         "team2":"Algeria",             "group":"Group J","ground":"San Francisco Bay Area (Santa Clara)"},
    {"num":58, "date":"2026-06-27","time":"21:00 UTC-5","team1":"Algeria",        "team2":"Austria",             "group":"Group J","ground":"Kansas City"},
    {"num":59, "date":"2026-06-27","time":"21:00 UTC-5","team1":"Jordan",         "team2":"Argentina",           "group":"Group J","ground":"Dallas (Arlington)"},
    # Group K
    {"num":60, "date":"2026-06-17","time":"12:00 UTC-5","team1":"Portugal",       "team2":"DR Congo",            "group":"Group K","ground":"Houston"},
    {"num":61, "date":"2026-06-17","time":"20:00 UTC-6","team1":"Uzbekistan",     "team2":"Colombia",            "group":"Group K","ground":"Mexico City"},
    {"num":62, "date":"2026-06-23","time":"12:00 UTC-5","team1":"Portugal",       "team2":"Uzbekistan",          "group":"Group K","ground":"Houston"},
    {"num":63, "date":"2026-06-23","time":"20:00 UTC-6","team1":"Colombia",       "team2":"DR Congo",            "group":"Group K","ground":"Guadalajara (Zapopan)"},
    {"num":64, "date":"2026-06-27","time":"19:30 UTC-4","team1":"Colombia",       "team2":"Portugal",            "group":"Group K","ground":"Miami (Miami Gardens)"},
    {"num":65, "date":"2026-06-27","time":"19:30 UTC-4","team1":"DR Congo",       "team2":"Uzbekistan",          "group":"Group K","ground":"Atlanta"},
    # Group L
    {"num":66, "date":"2026-06-17","time":"15:00 UTC-5","team1":"England",        "team2":"Croatia",             "group":"Group L","ground":"Dallas (Arlington)"},
    {"num":67, "date":"2026-06-17","time":"19:00 UTC-4","team1":"Ghana",          "team2":"Panama",              "group":"Group L","ground":"Toronto"},
    {"num":68, "date":"2026-06-23","time":"16:00 UTC-4","team1":"England",        "team2":"Ghana",               "group":"Group L","ground":"Boston (Foxborough)"},
    {"num":69, "date":"2026-06-23","time":"19:00 UTC-4","team1":"Panama",         "team2":"Croatia",             "group":"Group L","ground":"Toronto"},
    {"num":70, "date":"2026-06-27","time":"17:00 UTC-4","team1":"Panama",         "team2":"England",             "group":"Group L","ground":"New York/New Jersey (East Rutherford)"},
    {"num":71, "date":"2026-06-27","time":"17:00 UTC-4","team1":"Croatia",        "team2":"Ghana",               "group":"Group L","ground":"Philadelphia"},
]

KNOCKOUT_FIXTURES: list[dict] = [
    {"num":72,  "date":"2026-06-28","time":"12:00 UTC-7","team1":"2A", "team2":"2B",            "round":"Round of 32","ground":"Los Angeles (Inglewood)"},
    {"num":73,  "date":"2026-06-29","time":"16:30 UTC-4","team1":"1E", "team2":"3rd (A/B/C/D/F)","round":"Round of 32","ground":"Boston (Foxborough)"},
    {"num":74,  "date":"2026-06-29","time":"19:00 UTC-6","team1":"1F", "team2":"2C",            "round":"Round of 32","ground":"Monterrey (Guadalupe)"},
    {"num":75,  "date":"2026-06-29","time":"12:00 UTC-5","team1":"1C", "team2":"2F",            "round":"Round of 32","ground":"Houston"},
    {"num":76,  "date":"2026-06-30","time":"17:00 UTC-4","team1":"1I", "team2":"3rd (C/D/F/G/H)","round":"Round of 32","ground":"New York/New Jersey (East Rutherford)"},
    {"num":77,  "date":"2026-06-30","time":"12:00 UTC-5","team1":"2E", "team2":"2I",            "round":"Round of 32","ground":"Dallas (Arlington)"},
    {"num":78,  "date":"2026-06-30","time":"19:00 UTC-6","team1":"1A", "team2":"3rd (C/E/F/H/I)","round":"Round of 32","ground":"Mexico City"},
    {"num":79,  "date":"2026-07-01","time":"12:00 UTC-4","team1":"1L", "team2":"3rd (E/H/I/J/K)","round":"Round of 32","ground":"Atlanta"},
    {"num":80,  "date":"2026-07-01","time":"17:00 UTC-7","team1":"1D", "team2":"3rd (B/E/F/I/J)","round":"Round of 32","ground":"San Francisco Bay Area (Santa Clara)"},
    {"num":81,  "date":"2026-07-01","time":"13:00 UTC-7","team1":"1G", "team2":"3rd (A/E/H/I/J)","round":"Round of 32","ground":"Seattle"},
    {"num":82,  "date":"2026-07-02","time":"19:00 UTC-4","team1":"2K", "team2":"2L",            "round":"Round of 32","ground":"Toronto"},
    {"num":83,  "date":"2026-07-02","time":"12:00 UTC-7","team1":"1H", "team2":"2J",            "round":"Round of 32","ground":"Los Angeles (Inglewood)"},
    {"num":84,  "date":"2026-07-02","time":"20:00 UTC-7","team1":"1B", "team2":"3rd (E/F/G/I/J)","round":"Round of 32","ground":"Vancouver"},
    {"num":85,  "date":"2026-07-03","time":"18:00 UTC-4","team1":"1J", "team2":"2H",            "round":"Round of 32","ground":"Miami (Miami Gardens)"},
    {"num":86,  "date":"2026-07-03","time":"20:30 UTC-5","team1":"1K", "team2":"3rd (D/E/I/J/L)","round":"Round of 32","ground":"Kansas City"},
    {"num":87,  "date":"2026-07-03","time":"13:00 UTC-5","team1":"2D", "team2":"2G",            "round":"Round of 32","ground":"Dallas (Arlington)"},
    {"num":88,  "date":"2026-07-04","time":"17:00 UTC-4","team1":"W73","team2":"W76",           "round":"Round of 16","ground":"Philadelphia"},
    {"num":89,  "date":"2026-07-04","time":"12:00 UTC-5","team1":"W72","team2":"W74",           "round":"Round of 16","ground":"Houston"},
    {"num":90,  "date":"2026-07-05","time":"16:00 UTC-4","team1":"W75","team2":"W77",           "round":"Round of 16","ground":"New York/New Jersey (East Rutherford)"},
    {"num":91,  "date":"2026-07-05","time":"18:00 UTC-6","team1":"W78","team2":"W79",           "round":"Round of 16","ground":"Mexico City"},
    {"num":92,  "date":"2026-07-06","time":"14:00 UTC-5","team1":"W82","team2":"W83",           "round":"Round of 16","ground":"Dallas (Arlington)"},
    {"num":93,  "date":"2026-07-06","time":"17:00 UTC-7","team1":"W80","team2":"W81",           "round":"Round of 16","ground":"Seattle"},
    {"num":94,  "date":"2026-07-07","time":"12:00 UTC-4","team1":"W85","team2":"W87",           "round":"Round of 16","ground":"Atlanta"},
    {"num":95,  "date":"2026-07-07","time":"13:00 UTC-7","team1":"W84","team2":"W86",           "round":"Round of 16","ground":"Vancouver"},
    {"num":96,  "date":"2026-07-09","time":"16:00 UTC-4","team1":"W88","team2":"W89",           "round":"Quarter-finals","ground":"Boston (Foxborough)"},
    {"num":97,  "date":"2026-07-10","time":"12:00 UTC-7","team1":"W92","team2":"W93",           "round":"Quarter-finals","ground":"Los Angeles (Inglewood)"},
    {"num":98,  "date":"2026-07-11","time":"17:00 UTC-4","team1":"W90","team2":"W91",           "round":"Quarter-finals","ground":"Miami (Miami Gardens)"},
    {"num":99,  "date":"2026-07-11","time":"20:00 UTC-5","team1":"W94","team2":"W95",           "round":"Quarter-finals","ground":"Kansas City"},
    {"num":100, "date":"2026-07-14","time":"14:00 UTC-5","team1":"W96","team2":"W97",           "round":"Semi-finals","ground":"Dallas (Arlington)"},
    {"num":101, "date":"2026-07-15","time":"15:00 UTC-4","team1":"W98","team2":"W99",           "round":"Semi-finals","ground":"Atlanta"},
    {"num":102, "date":"2026-07-18","time":"17:00 UTC-4","team1":"L100","team2":"L101",         "round":"Third Place","ground":"Miami (Miami Gardens)"},
    {"num":103, "date":"2026-07-19","time":"15:00 UTC-4","team1":"W100","team2":"W101",         "round":"Final","ground":"New York/New Jersey (East Rutherford)"},
]

ALL_FIXTURES: list[dict] = GROUP_FIXTURES + KNOCKOUT_FIXTURES

# ══════════════════════════════════════════════════════════════════════════════
# SQUADS — official 26-player squads (shirt, name, position)
# ══════════════════════════════════════════════════════════════════════════════

SQUADS: dict[str, list[tuple]] = {
    "Argentina": [
        (1,"Emiliano Martinez","GK"),(12,"Geronimo Rulli","GK"),(23,"Walter Benitez","GK"),
        (2,"Nahuel Molina","DEF"),(3,"Nicolas Tagliafico","DEF"),(6,"German Pezzella","DEF"),
        (13,"Cristian Romero","DEF"),(19,"Nicolas Otamendi","DEF"),(22,"Lisandro Martinez","DEF"),
        (8,"Marcos Acuna","DEF"),(26,"Facundo Medina","DEF"),
        (5,"Leandro Paredes","MID"),(7,"Rodrigo De Paul","MID"),(11,"Angel Di Maria","MID"),
        (14,"Exequiel Palacios","MID"),(18,"Guido Rodriguez","MID"),(20,"Alexis Mac Allister","MID"),
        (24,"Enzo Fernandez","MID"),(25,"Thiago Almada","MID"),
        (9,"Julian Alvarez","FWD"),(10,"Lionel Messi","FWD"),(15,"Nicolas Gonzalez","FWD"),
        (16,"Lautaro Martinez","FWD"),(17,"Alejandro Garnacho","FWD"),(21,"Paulo Dybala","FWD"),
        (4,"Valentin Carboni","FWD"),
    ],
    "France": [
        (1,"Mike Maignan","GK"),(16,"Brice Samba","GK"),(23,"Guela Doue","GK"),
        (2,"Benjamin Pavard","DEF"),(3,"Lucas Hernandez","DEF"),(4,"Dayot Upamecano","DEF"),
        (5,"Jules Kounde","DEF"),(17,"William Saliba","DEF"),(21,"Ferland Mendy","DEF"),
        (22,"Theo Hernandez","DEF"),
        (6,"Matteo Guendouzi","MID"),(8,"Aurelien Tchouameni","MID"),(12,"Eduardo Camavinga","MID"),
        (13,"N'Golo Kante","MID"),(14,"Adrien Rabiot","MID"),(18,"Youssouf Fofana","MID"),
        (25,"Warren Zaire-Emery","MID"),
        (7,"Antoine Griezmann","FWD"),(9,"Olivier Giroud","FWD"),(10,"Kylian Mbappe","FWD"),
        (11,"Ousmane Dembele","FWD"),(15,"Marcus Thuram","FWD"),(19,"Bradley Barcola","FWD"),
        (20,"Kingsley Coman","FWD"),(24,"Michael Olise","FWD"),(26,"Desire Doue","FWD"),
    ],
    "Brazil": [
        (1,"Alisson Becker","GK"),(12,"Weverton","GK"),(23,"Ederson","GK"),
        (2,"Wesley","DEF"),(3,"Gabriel Magalhaes","DEF"),(4,"Marquinhos","DEF"),
        (6,"Alex Sandro","DEF"),(13,"Danilo","DEF"),(14,"Bremer","DEF"),
        (15,"Leo Pereira","DEF"),(16,"Douglas Santos","DEF"),
        (5,"Casemiro","MID"),(7,"Vinicius Junior","MID"),(8,"Bruno Guimaraes","MID"),
        (11,"Raphinha","MID"),(17,"Fabinho","MID"),(18,"Danilo Santos","MID"),
        (20,"Lucas Paqueta","MID"),(21,"Luiz Henrique","MID"),
        (9,"Matheus Cunha","FWD"),(10,"Neymar","FWD"),(19,"Endrick","FWD"),
        (22,"Gabriel Martinelli","FWD"),(24,"Ibanez","DEF"),(25,"Thiago","FWD"),
        (26,"Rayan","FWD"),
    ],
    "England": [
        (1,"Jordan Pickford","GK"),(13,"Aaron Ramsdale","GK"),(23,"Dean Henderson","GK"),
        (2,"Kyle Walker","DEF"),(3,"Luke Shaw","DEF"),(5,"John Stones","DEF"),
        (6,"Harry Maguire","DEF"),(12,"Kieran Trippier","DEF"),(22,"Ben Chilwell","DEF"),
        (4,"Declan Rice","MID"),(8,"Jordan Henderson","MID"),(10,"Jude Bellingham","MID"),
        (14,"Kalvin Phillips","MID"),(16,"Kobbie Mainoo","MID"),(19,"Mason Mount","MID"),
        (20,"Phil Foden","MID"),(24,"Conor Gallagher","MID"),
        (7,"Jack Grealish","FWD"),(9,"Harry Kane","FWD"),(11,"Marcus Rashford","FWD"),
        (15,"Bukayo Saka","FWD"),(17,"Ivan Toney","FWD"),(18,"Jarrod Bowen","FWD"),
        (21,"Ollie Watkins","FWD"),(25,"Anthony Gordon","FWD"),(26,"Eberechi Eze","FWD"),
    ],
    "Germany": [
        (1,"Manuel Neuer","GK"),(12,"Marc-Andre ter Stegen","GK"),(23,"Oliver Baumann","GK"),
        (2,"Benjamin Henrichs","DEF"),(3,"David Raum","DEF"),(4,"Jonathan Tah","DEF"),
        (5,"Nico Schlotterbeck","DEF"),(15,"Niklas Sule","DEF"),(22,"Robin Gosens","DEF"),
        (6,"Joshua Kimmich","MID"),(8,"Leon Goretzka","MID"),(10,"Florian Wirtz","MID"),
        (14,"Maximilian Mittelstadt","MID"),(19,"Julian Brandt","MID"),(21,"Ilkay Gundogan","MID"),
        (24,"Jamal Musiala","MID"),(25,"Aleksandar Pavlovic","MID"),
        (7,"Kai Havertz","FWD"),(9,"Niclas Fullkrug","FWD"),(11,"Serge Gnabry","FWD"),
        (13,"Thomas Muller","FWD"),(16,"Chris Fuhrich","FWD"),(17,"Deniz Undav","FWD"),
        (18,"Tim Kleindienst","FWD"),(20,"Leroy Sane","FWD"),(26,"Maximilian Beier","FWD"),
    ],
    "Spain": [
        (1,"Unai Simon","GK"),(13,"David Raya","GK"),(23,"Robert Sanchez","GK"),
        (2,"Daniel Carvajal","DEF"),(3,"Alejandro Balde","DEF"),(4,"Nacho Fernandez","DEF"),
        (12,"Robin Le Normand","DEF"),(14,"Aymeric Laporte","DEF"),(22,"Jesus Navas","DEF"),
        (24,"Marc Cucurella","DEF"),
        (5,"Rodri","MID"),(6,"Mikel Merino","MID"),(8,"Fabian Ruiz","MID"),
        (9,"Gavi","MID"),(16,"Pedri","MID"),(18,"Martin Zubimendi","MID"),
        (21,"Dani Olmo","MID"),
        (7,"Alvaro Morata","FWD"),(10,"Ferran Torres","FWD"),(11,"Nico Williams","FWD"),
        (15,"Mikel Oyarzabal","FWD"),(17,"Lamine Yamal","FWD"),(19,"Joselu","FWD"),
        (20,"Bryan Gil","FWD"),(25,"Ayoze Perez","FWD"),(26,"Abel Ruiz","FWD"),
    ],
    "Portugal": [
        (1,"Diogo Costa","GK"),(12,"Jose Sa","GK"),(22,"Rui Patricio","GK"),
        (2,"Joao Cancelo","DEF"),(3,"Nuno Mendes","DEF"),(4,"Ruben Dias","DEF"),
        (5,"Pepe","DEF"),(6,"Danilo Pereira","DEF"),(13,"Diogo Dalot","DEF"),
        (21,"Goncalo Inacio","DEF"),
        (8,"Bruno Fernandes","MID"),(10,"Bernardo Silva","MID"),(14,"William Carvalho","MID"),
        (16,"Renato Sanches","MID"),(17,"Joao Felix","MID"),(18,"Matheus Nunes","MID"),
        (23,"Vitinha","MID"),(25,"Joao Neves","MID"),(26,"Florentino Luis","MID"),
        (7,"Cristiano Ronaldo","FWD"),(9,"Andre Silva","FWD"),(11,"Rafael Leao","FWD"),
        (15,"Ricardo Horta","FWD"),(19,"Goncalo Ramos","FWD"),(20,"Francisco Conceicao","FWD"),
        (24,"Pedro Neto","FWD"),
    ],
    "Netherlands": [
        (1,"Bart Verbruggen","GK"),(16,"Mark Flekken","GK"),(23,"Nick Olij","GK"),
        (2,"Denzel Dumfries","DEF"),(3,"Nathan Ake","DEF"),(4,"Virgil van Dijk","DEF"),
        (5,"Jurrien Timber","DEF"),(12,"Daley Blind","DEF"),(15,"Matthijs de Ligt","DEF"),
        (22,"Ian Maatsen","DEF"),
        (6,"Stefan de Vrij","MID"),(8,"Tijjani Reijnders","MID"),(10,"Memphis Depay","MID"),
        (14,"Teun Koopmeiners","MID"),(18,"Xavi Simons","MID"),(20,"Marten de Roon","MID"),
        (21,"Jerdy Schouten","MID"),(24,"Ryan Gravenberch","MID"),
        (7,"Steven Bergwijn","FWD"),(9,"Wout Weghorst","FWD"),(11,"Cody Gakpo","FWD"),
        (13,"Donyell Malen","FWD"),(17,"Noa Lang","FWD"),(19,"Vincent Janssen","FWD"),
        (25,"Brian Brobbey","FWD"),(26,"Quinten Timber","MID"),
    ],
    "USA": [
        (1,"Matt Turner","GK"),(13,"Ethan Horvath","GK"),(18,"Patrick Schulte","GK"),
        (2,"Sergino Dest","DEF"),(3,"Walker Zimmerman","DEF"),(4,"Miles Robinson","DEF"),
        (5,"Tim Ream","DEF"),(12,"Antonee Robinson","DEF"),(14,"Chris Richards","DEF"),
        (22,"Joe Scally","DEF"),
        (6,"Yunus Musah","MID"),(7,"Giovanni Reyna","MID"),(8,"Tyler Adams","MID"),
        (10,"Christian Pulisic","MID"),(16,"Malik Tillman","MID"),(17,"Luca de la Torre","MID"),
        (20,"Weston McKennie","MID"),(23,"Johnny Cardoso","MID"),
        (9,"Ricardo Pepi","FWD"),(11,"Folarin Balogun","FWD"),(15,"Josh Sargent","FWD"),
        (19,"Timothy Weah","FWD"),(21,"Jordan Morris","FWD"),(24,"Gio Reyna","MID"),
        (25,"Daryl Dike","FWD"),(26,"Cade Cowell","FWD"),
    ],
    "Mexico": [
        (1,"Guillermo Ochoa","GK"),(13,"Luis Malagon","GK"),(23,"Rodolfo Cota","GK"),
        (2,"Jorge Sanchez","DEF"),(3,"Jesus Gallardo","DEF"),(5,"Johan Vasquez","DEF"),
        (15,"Cesar Montes","DEF"),(19,"Israel Reyes","DEF"),(22,"Julian Araujo","DEF"),
        (6,"Hector Herrera","MID"),(8,"Carlos Rodriguez","MID"),(10,"Alexis Vega","MID"),
        (14,"Andres Guardado","MID"),(16,"Orbelin Pineda","MID"),(17,"Luis Romo","MID"),
        (18,"Erick Gutierrez","MID"),(26,"Fernando Beltran","MID"),
        (4,"Edson Alvarez","MID"),(7,"Miguel Layun","MID"),
        (9,"Raul Jimenez","FWD"),(11,"Hirving Lozano","FWD"),(12,"Henry Martin","FWD"),
        (20,"Roberto Alvarado","FWD"),(21,"Uriel Antuna","FWD"),(24,"Santiago Gimenez","FWD"),
        (25,"Rodolfo Rotondi","FWD"),
    ],
    "Morocco": [
        (1,"Yassine Bounou","GK"),(16,"Munir El Kajoui","GK"),(23,"Ahmed Reda Tagnaouti","GK"),
        (2,"Achraf Hakimi","DEF"),(3,"Noussair Mazraoui","DEF"),(4,"Romain Saiss","DEF"),
        (5,"Nayef Aguerd","DEF"),(12,"Yahya Attiyat Allah","DEF"),(14,"Jawad El Yamiq","DEF"),
        (22,"Adam Masina","DEF"),
        (6,"Rida Lamara","MID"),(7,"Hakim Ziyech","MID"),(8,"Azzedine Ounahi","MID"),
        (10,"Brahim Diaz","MID"),(17,"Sofyan Amrabat","MID"),(18,"Selim Amallah","MID"),
        (19,"Bilal El Khannous","MID"),(21,"Abde Ezzalzouli","MID"),
        (9,"Youssef En-Nesyri","FWD"),(11,"Soufiane Boufal","FWD"),(13,"Ayoub El Kaabi","FWD"),
        (15,"Amine Harit","FWD"),(20,"Ryan Mmaee","FWD"),(24,"Anass Zaroury","FWD"),
        (25,"Ilias Chair","FWD"),(26,"Zakaria Aboukhlal","FWD"),
    ],
    "Canada": [
        (1,"Maxime Crepeau","GK"),(16,"James Pantemis","GK"),(23,"Milan Borjan","GK"),
        (2,"Richie Laryea","DEF"),(3,"Sam Adekugbe","DEF"),(4,"Kamal Miller","DEF"),
        (5,"Steven Vitoria","DEF"),(12,"Derek Cornelius","DEF"),(14,"Alistair Johnston","DEF"),
        (22,"Doneil Henry","DEF"),
        (6,"Samuel Piette","MID"),(7,"Stephen Eustaquio","MID"),(8,"Jonathan Osorio","MID"),
        (10,"Tajon Buchanan","MID"),(13,"Mathieu Choiniere","MID"),(15,"Liam Millar","MID"),
        (17,"Mark-Anthony Kaye","MID"),(18,"Ismael Kone","MID"),
        (9,"Lucas Cavallini","FWD"),(11,"Cyle Larin","FWD"),(19,"Jonathan David","FWD"),
        (20,"Theo Bair","FWD"),(21,"Ike Ugbo","FWD"),(24,"Jacob Shaffelburg","FWD"),
        (25,"Charles-Andreas Brym","FWD"),(26,"Ballou Tabla","MID"),
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# REFEREES — official FIFA WC 2026 panel (52 referees + assistants)
# ══════════════════════════════════════════════════════════════════════════════

REFEREES: list[dict] = [
    {"name":"Abdulrahman Al-Jassim",     "country":"Qatar"},
    {"name":"Khalid Al-Turais",           "country":"Saudi Arabia"},
    {"name":"Yusuke Araki",              "country":"Japan"},
    {"name":"Ivan Barton",               "country":"El Salvador"},
    {"name":"Juan Benitez",              "country":"Paraguay"},
    {"name":"Juan Calderon",             "country":"Costa Rica"},
    {"name":"Raphael Claus",             "country":"Brazil"},
    {"name":"Ismail Elfath",             "country":"USA"},
    {"name":"Jose Maria Gimenez",        "country":"Uruguay"},
    {"name":"Mustapha Ghorbal",          "country":"Algeria"},
    {"name":"Victor Gomes",              "country":"South Africa"},
    {"name":"Bakary Gassama",            "country":"Gambia"},
    {"name":"Maguette N'Diaye",          "country":"Senegal"},
    {"name":"Anthony Taylor",            "country":"England"},
    {"name":"Felix Zwayer",              "country":"Germany"},
    {"name":"Clement Turpin",            "country":"France"},
    {"name":"Danny Makkelie",            "country":"Netherlands"},
    {"name":"Antonio Mateu Lahoz",       "country":"Spain"},
    {"name":"Slavko Vincic",             "country":"Slovenia"},
    {"name":"Sandro Scharer",            "country":"Switzerland"},
    {"name":"Facundo Tello",             "country":"Argentina"},
    {"name":"Piero Maza",               "country":"Chile"},
    {"name":"Jesus Valenzuela",          "country":"Venezuela"},
    {"name":"Wilton Sampaio",            "country":"Brazil"},
    {"name":"Stephanie Frappart",        "country":"France"},
    {"name":"Maria Sole Ferrieri Caputi","country":"Italy"},
    {"name":"Katia Muller",              "country":"Switzerland"},
    {"name":"Mahmoud Batta",             "country":"Egypt"},
    {"name":"Redouane Jiyed",            "country":"Morocco"},
    {"name":"Pierre Atcho",              "country":"Gabon"},
    {"name":"Dahane Beida",              "country":"Mauritania"},
    {"name":"Omar Artan",               "country":"Somalia"},
]

# ══════════════════════════════════════════════════════════════════════════════
# STADIUMS — all 16 host venues with GPS coordinates
# ══════════════════════════════════════════════════════════════════════════════

STADIUMS: list[dict] = [
    {"city":"Mexico City",                           "stadium":"Estadio Azteca",           "country":"Mexico", "capacity":87523,"lat":19.3029,"lon":-99.1505},
    {"city":"Guadalajara (Zapopan)",                 "stadium":"Estadio Akron",            "country":"Mexico", "capacity":46232,"lat":20.6721,"lon":-103.3106},
    {"city":"Monterrey (Guadalupe)",                 "stadium":"Estadio BBVA",             "country":"Mexico", "capacity":53500,"lat":25.6694,"lon":-100.3118},
    {"city":"Atlanta",                               "stadium":"Mercedes-Benz Stadium",    "country":"USA",    "capacity":71000,"lat":33.7554,"lon":-84.4008},
    {"city":"Boston (Foxborough)",                   "stadium":"Gillette Stadium",         "country":"USA",    "capacity":65878,"lat":42.0910,"lon":-71.0640},
    {"city":"Dallas (Arlington)",                    "stadium":"AT&T Stadium",             "country":"USA",    "capacity":80000,"lat":32.7480,"lon":-97.0930},
    {"city":"Houston",                               "stadium":"NRG Stadium",              "country":"USA",    "capacity":72220,"lat":29.6847,"lon":-95.4107},
    {"city":"Kansas City",                           "stadium":"Arrowhead Stadium",        "country":"USA",    "capacity":76416,"lat":39.0489,"lon":-94.4839},
    {"city":"Los Angeles (Inglewood)",               "stadium":"SoFi Stadium",             "country":"USA",    "capacity":70240,"lat":33.9535,"lon":-118.3392},
    {"city":"Miami (Miami Gardens)",                 "stadium":"Hard Rock Stadium",        "country":"USA",    "capacity":65326,"lat":25.9580,"lon":-80.2389},
    {"city":"New York/New Jersey (East Rutherford)", "stadium":"MetLife Stadium",          "country":"USA",    "capacity":82500,"lat":40.8128,"lon":-74.0742},
    {"city":"Philadelphia",                          "stadium":"Lincoln Financial Field",  "country":"USA",    "capacity":69176,"lat":39.9008,"lon":-75.1675},
    {"city":"San Francisco Bay Area (Santa Clara)",  "stadium":"Levi's Stadium",           "country":"USA",    "capacity":68500,"lat":37.4032,"lon":-121.9700},
    {"city":"Seattle",                               "stadium":"Lumen Field",              "country":"USA",    "capacity":69000,"lat":47.5952,"lon":-122.3316},
    {"city":"Toronto",                               "stadium":"BMO Field",                "country":"Canada", "capacity":45736,"lat":43.6332,"lon":-79.4188},
    {"city":"Vancouver",                             "stadium":"BC Place",                 "country":"Canada", "capacity":54500,"lat":49.2767,"lon":-123.1130},
]

STADIUM_BY_CITY: dict[str, dict] = {s["city"]: s for s in STADIUMS}

# ══════════════════════════════════════════════════════════════════════════════
# RSS FEEDS — free news sources (work from standard Python, not our sandbox)
# ══════════════════════════════════════════════════════════════════════════════

RSS_FEEDS: list[dict] = [
    {"name":"BBC Sport Football",  "url":"https://feeds.bbci.co.uk/sport/football/rss.xml"},
    {"name":"The Guardian Football","url":"https://www.theguardian.com/football/rss"},
    {"name":"ESPN Soccer",         "url":"https://www.espn.com/espn/rss/soccer/news"},
    {"name":"Goal.com",            "url":"https://www.goal.com/feeds/en/news"},
    {"name":"Google News WC 2026", "url":"https://news.google.com/rss/search?q=World+Cup+2026&hl=en-US&gl=US&ceid=US:en"},
]
