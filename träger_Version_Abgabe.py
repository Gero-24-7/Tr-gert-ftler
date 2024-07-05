import streamlit as st
import matplotlib
import matplotlib.pyplot as plt # für grafische Darstellung
import numpy as np # zur Berechnung der Biegemomente, Querkraft und Durchbiegung
import pandas as pd # für behandeln von Datasets aus Tabellen
import json # für material import
import secrets # für random Hex Farbe
import copy # um st.session_state werte zu kopieren ohne diese weiter zu referenzieren
import requests # um material.json auf github abzufragen

#Seitenkonfiguration
st.set_page_config(
    page_title ="TrägerTüftler",
    layout ="wide",
    #page_icon = 
)

colTitel_1, colTitel_2 = st.columns([1,2], gap="large")
with colTitel_1:
    st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/Logo_with_background.png")
#with colTitel_2:
    #("")

st.header ("Dein Berechnungstool für Durchlaufträger")
# st.markdown("Für Einfeldträgerberechnung und weitere Tragwerktools besuche: www.Trako-Tools.de")
# Änderung sobald eine ähnliche Seite besteht, bis dahin:

# Popup-Funktion zur Anzeige weiterer Programme
@st.experimental_dialog("Weitere Programme für Architekturstudierende", width="large")
def show_popup_tools():
    st.markdown("Bei Einfeldträgerberechnung: https://log-run.streamlit.app/")
    st.markdown("Bei Fachwerkberechnung: https://fragwerk.streamlit.app/")
    st.markdown("Bei Stützenberechnung: https://stuetzen-stuetze.streamlit.app/")
    st.markdown("Weitere Programme folgen...")

# Button zum Anzeigen weiterer Programme
if st.button("Weitere Programme für Architekturstudierende"):
    show_popup_tools()


#Nun folgen nützliche Voreinstellungen (Listen, Dictionaries, Definitionen)

#Initiiere Dachvoreinstellungen
roofOptions = ["Schwer", "Mittelschwer", "Leicht", "Benutzerdefinierter Aufbau oder Deaktivierung"]

#Schichten der verschiedenen Dächer
roofLayers = {
    "Schwer" : {
        1 : ("Kies 5cm", 1),
        2 : ("zweilagige Dachabdichtung", 0.04),
        3 : ("Dämmstoff 20cm", 0.2),
        4 : ("2 ⋅ KVH 10/20", 0.24),
        5 : ("Dampfsperre", 0.01),
        6 : ("Deckenbekleidung 2cm", 0.07)
    },
    "Mittelschwer" : {
        1 : ("zweilagige Dachabdichtung", 0.04),
        2 : ("Dämmstoff 16cm", 0.16),
        3 : ("2 ⋅ KVH 8/16", 0.24),
        4 : ("Dampfsperre", 0.01),
        5 : ("Deckenbekleidung 2cm", 0.07)
    },
    "Leicht" : {
        1 : ("zweilagige Dachabdichtung", 0.04),
        2 : ("Dämmstoff 5cm", 0.05),
        3 : ("Dampfsperre", 0.01),
        4 : ("Trapezblech", 0.125)
    },
    "Benutzerdefinierter Aufbau oder Deaktivierung" : {
        1 : ("Schicht 1", 0.0),
        2 : ("Schicht 2", 0.0),
        3 : ("Schicht 3", 0.0),
        4 : ("Schicht 4", 0.0),
        5 : ("Schicht 5", 0.0),
        6 : ("Schicht 6", 0.0)
    }
}

#Dachdiagramm in Abhängigkeit zu Auswahl
roofImage = {
    "Schwer" : "https://raw.githubusercontent.com/Gero-24-7/images/main/Dach_Schwer.png",
    "Mittelschwer" : "https://raw.githubusercontent.com/Gero-24-7/images/main/Dach_Mittel.png",
    "Leicht" : "https://raw.githubusercontent.com/Gero-24-7/images/main/Dach_Leicht.png",
    "Benutzerdefinierter Aufbau oder Deaktivierung" : "https://raw.githubusercontent.com/Gero-24-7/images/main/Dach_Eigen.png"
}

#Voreingestellte Dachauflasten. "Bezeichnung" : [Last in kN/m²]
roofAdditives = {
    "Intensive Dachbegrünung" : 2.8,
    "Extensive Dachbegrünung" : 1.5,
    "Photovoltaik" : 0.15,
    "Deaktivierung": 0.0
}

#Tabelle für eventuelle Gewichtsberechnung. "Material" : [Dichte in kg/m³]
materialDensity = {
    "Holz" : 500,
    "Stahl" : 7850
}

#Funktion um die Eingabe Kommata und Buchstaben zu ermöglichen
def correctify_input(value):
    try:
        #Variable initialisieren
        numberString = ""
        #Iteriere durch alle Ziffern um Zahlen, Punkte und Kommata zu extrahieren,
        #Falls jemand einen Buchstaben eintippt.
        for character in str(value):
            if character.isdigit() or character == "." or character == ",":
                numberString += character
        valueChanged = str(numberString).replace(",", ".")
        #Mache Wert positiv falls jemand negative Werte einträgt und runde die Zahl
        valuePositive = abs(float(valueChanged))
        valuePositive = round (valuePositive, 2)
        return valuePositive
    #Falls kein sinnvoller Wert gebildet werden kann:
    except ValueError:
        return None

#Funktion, um Errormeldung zu schreiben, falls correctify_input ein None returned
def print_error_and_set_default(default):
    st.markdown(":red[Bitte gültigen Wert eingeben!]")
    st.markdown(f"Es wird mit {default}m weitergerechnet.")
    return default

#Initialisiere Windlasttabelle S.47
wind_mapping = {
    1: (0.50, 0.65, 0.75),
    2: (0.70, 0.90, 1.00),
    3: (0.90, 1.10, 1.20),
    4: (1.20, 1.30, 1.40)
}

#Initialisiere Schneelasttabelle S.45
snow_mapping = {
    200 : (0.65, 0.81, 0.85, 1.06, 1.10),
    300 : (0.65, 0.81, 0.89, 1.11, 1.29),
    400 : (0.65, 0.81, 1.21, 1.52, 1.78),
    500 : (0.84, 1.04, 1.60, 2.01, 2.37),
    600 : (1.05, 1.32, 2.06, 2.58, 3.07),
    700 : (1.30, 1.63, 2.58, 3.23, 3.87),
    800 : (1.58, 1.98, 3.17, 3.96, 4.76),
    900 : (None, None, 3.83, 4.78, 5.76),
    1000 : (None, None, 4.55, 5.68, 6.86),
    1100 : (None, None, 5.33, 6.67, 8.06),
    1200 : (None, None, 6.19, 7.73, 9.36),
    1300 : (None, None, None, None, 10.76),
    1400 : (None, None, None, None, 12.26),
    1500 : (None, None, None, None, 13.86)
}

#Initialisiere Durchlaufträgertablle S.55
beam_n_values = {
    1 : (8.0, 8.0, 8.0, 8.0, 8.0),
    2 : (12.0, 11.4, 10.7, 9.6, 8.0),
    3 : (11.5, 11.7, 12.1, 12.8, 14.2),
    4 : (9.0, 9.1, 9.2, 9.5, 10.0),
    5 : (18.0, 16.7, 15.0, 12.9, 10.0),
    6 : (15.0, 14.3, 13.3, 12.0, 10.0),
    7 : (10.7, 10.8, 11.1, 11.5, 12.5),
    8 : (15.0, 14.3, 13.3, 12.0, 10.0),
    9 : (17.1, 18.2, 20.0, 24.0, 40.0),
    10 : (8.6, 8.7, 8.8, 9.0, 9.3),
    11 : (10.5, 10.8, 11.2, 12.0, 9.3),
    12 : (10.9, 11.1, 11.4, 11.9, 12.9),
    13 : (15.2, 15.9, 17.1, 19.6, 27.3),
    14 : (8.7, 8.8, 8.9, 9.1, 9.5),
    15 : (10.0, 10.2, 10.5, 11.1, 12.7),
    16 : (10.9, 11.0, 11.3, 11.8, 12.8),
    17 : (13.8, 14.3, 15.2, 16.9, 21.7),
    18 : (15.7, 16.5, 17.9, 20.7, 30.4)
}    

#Initialisiere Durchlaufträgertabllen - Bautabellen S.4.17
table_value_2field_bothfields = {
    "1:1,1" : (-0.139, 0.065, 0.090, 0.361, -0.639, 0.676, 0.424),
    "1:1,2" : (-0.155, 0.060, 0.111, 0.345 , -0.655, 0.729, 0.471),
    "1:1,3" : (-0.174, 0.053, 0.133, 0.326, -0.674, 0.784, 0.516),
    "1:1,4" : (-0.195, 0.047, 0.157, 0.305, -0.695, 0.839, 0.561),
    "1:1,5" : (-0.219, 0.049, 0.183, 0.281, -0.719, 0.896, 0.604),
    "1:1,6" : (-0.245, 0.033, 0.209, 0.255, -0.745, 0.953, 0.646),
    "1:1,7" : (-0.274, 0.026, 0.237, 0.226, -0.774, 1.011, 0.689),
    "1:1,8" : (-0.305, 0.019, 0.267, 0.195, -0.805, 1.069, 0.731),
    "1:1,9" : (-0.339, 0.013, 0.298, 0.161, -0.839, 1.128, 0.772),
    "1:2,0" : (-0.375, 0.008, 0.330, 0.125, -0.875, 1.188, 0.813),
    "1:2,1" : (-0.414, 0.004, 0.364, 0.086, -0.914, 1.247, 0.853),
    "1:2,2" : (-0.455, 0.001, 0.399, 0.045, -0.955, 1.307, 0.893),
    "1:2,3" : (-0.499, 0.000, 0.435, 0.001, -0.999, 1.367, 0.933),
    "1:2,4" : (-0.545, 0.000, 0.473, -0.045, -1.045, 1.427, 0.973),
    "1:2,5" : (-0.594, 0.000, 0.513, -0.094, -1.094, 1.488, 1.013)
}

table_value_2field_firstfield = {
    "1:1,1" : (-0.060, 0.097, 0.441, -0.560, 0.054),
    "1:1,2" : (-0.057, 0.098, 0.443, -0.557, 0.047),
    "1:1,3" : (-0.054, 0.099, 0.446, -0.554, 0.042),
    "1:1,4" : (-0.052, 0.100, 0.448, -0.552, 0.037),
    "1:1,5" : (-0.050, 0.101, 0.450, -0.550, 0.033),
    "1:1,6" : (-0.048, 0.102, 0.452, -0.548, 0.030),
    "1:1,7" : (-0.046, 0.103, 0.454, -0.546, 0.027),
    "1:1,8" : (-0.045, 0.104, 0.455, -0.545, 0.025),
    "1:1,9" : (-0.043, 0.104, 0.457, -0.543, 0.023),
    "1:2,0" : (-0.042, 0.105, 0.458, -0.542, 0.021),
    "1:2,1" : (-0.040, 0.106, 0.460, -0.540, 0.019),
    "1:2,2" : (-0.039, 0.106, 0.461, -0.539, 0.018),
    "1:2,3" : (-0.038, 0.107, 0.462, -0.538, 0.017),
    "1:2,4" : (-0.037, 0.107, 0.463, -0.537, 0.015),
    "1:2,5" : (-0.036, 0.108, 0.464, -0.536, 0.014)
}

table_value_2field_secondfield = {
    "1:1,1" : (-0.079, 0.114, -0.079, 0.622, 0.478),
    "1:1,2" : (-0.098, 0.134, -0.098, 0.682, 0.518),
    "1:1,3" : (-0.119, 0.156, -0.119, 0.742, 0.558),
    "1:1,4" : (-0.143, 0.179, -0.143, 0.802, 0.598),
    "1:1,5" : (-0.169, 0.203, -0.169, 0.863, 0.638),
    "1:1,6" : (-0.197, 0.229, -0.197, 0.923, 0.677),
    "1:1,7" : (-0.228, 0.257, -0.228, 0.984, 0.716),
    "1:1,8" : (-0.260, 0.285, -0.260, 1.045, 0.755),
    "1:1,9" : (-0.296, 0.316, -0.296, 1.106, 0.794),
    "1:2,0" : (-0.333, 0.347, -0.333, 1.167, 0.833),
    "1:2,1" : (-0.373, 0.380, -0.373, 1.228, 0.872),
    "1:2,2" : (-0.416, 0.415, -0.416, 1.289, 0.911),
    "1:2,3" : (-0.461, 0.451, -0.461, 1.350, 0.950),
    "1:2,4" : (-0.508, 0.488, -0.508, 1.412, 0.988),
    "1:2,5" : (-0.558, 0.527, -0.558, 1.473, 1.027)
}

# Initialisiere IPE Stahltabelle S.100 / I- und W-Werte
ipe_values = {
    "IPE 80": (80, 20.0),
    "IPE 100": (171, 34.2),
    "IPE 120": (318, 53.0),
    "IPE 140": (541, 77.3),
    "IPE 160": (869, 109),
    "IPE 180": (1320, 146),
    "IPE 200": (1940, 194),
    "IPE 220": (2770, 252),
    "IPE 240": (3890, 324),
    "IPE 270": (5790, 429),
    "IPE 300": (8360, 557),
}

# Initialisiere Kantholztabelle / I- und W-Werte
kantholz_values = {
    "KVH 10/10":(833, 167),
    "KVH 10/12":(1440, 240),
    "KVH 10/14":(2290, 327),
    "KVH 10/16":(3410, 427),
    "KVH 10/18":(4860, 540),
    "KVH 10/20":(6670, 667),
    "KVH 10/22":(8870, 807),
    "KVH 12/12":(1730, 288),
    "KVH 12/14":(2740, 392),
    "KVH 12/16":(4100, 512),
    "KVH 12/18":(5830, 648),
    "KVH 12/20":(8000, 800),
    "KVH 12/22":(10650, 968),
    "KVH 12/24":(13820, 1150),
    "KVH 12/26":(17570, 1350),
    "KVH 14/14":(3200, 457),
    "KVH 14/16":(4780, 597),
    "KVH 14/18":(6800, 756),
    "KVH 14/20":(9333, 933),
    "KVH 14/24":(16130, 1340),
    "KVH 14/28":(25610, 1830),
    "KVH 16/16":(5460, 683),
    "KVH 16/20":(10670, 1067),
    "KVH 16/22":(14200, 1290),
    "KVH 16/24":(18430, 1536),
    "KVH 16/28":(29270, 2090),
    "KVH 16/30":(36000, 2400),
    "KVH 18/18":(8750, 972),
    "KVH 18/20":(12000, 1200),
    "KVH 18/22":(15970, 1450),
    "KVH 18/24":(20740, 1730),
    "KVH 18/28":(32930, 2350),
    "KVH 18/30":(40500, 2700),
    "KVH 20/20":(13330, 1330),
    "KVH 20/24":(23040, 1920),
    "KVH 20/26":(29290, 2250),
    "KVH 20/30":(45000, 3000),
    "KVH 22/22":(19520, 1770),
    "KVH 24/24":(27650, 2300),
    "KVH 28/28":(51220, 3660),
    "KVH 30/30":(67500, 4500),
}



#Nun folgt der Aufbau der Webseite / Tab1

tab1, tab2, tab3, tab4 = st.tabs([":red-background[Eingabe/System]", ":red-background[Ergebnisse/Kräfte]", ":red-background[Dimensionierung/Querschnitte]", ":red-background[Hinweise / Erläuterungen]"])

with tab4:

    with st.container(border=True):
        st.subheader("Hinweise", divider="red")

        st.write("Als Berechnungsverfahren werden Tabellenwerte genutzt, damit die Berechnungen für Architekturstudierende auch in jüngeren Semestern nachvollziehbar sind.")
        st.write("Je nach Aufbau des Durchlaufträgers werden dabei unterschiedliche Tabellen genutzt. Es folgt eine allgemeine Erklärung der Kraftberechnungen.")

        st.write("### :blue[Berechnung Durchlaufträger mit einheitlichen Feldbreiten (Verfahren 1)]")
        st.write(":blue[**(Bekannt aus TWL 1b)**]")
        st.write("Berechne das Verhältnis von p/g")
        st.write("Suche aus der Tabelle den passenden n-Wert")
        st.write("**Verwendete Tabelle:** Tabellen zur Tragwerklehre (Krauss, Führer, Weimar, Mähl) S.55 (12. Auflage), S. 39 (13. Auflage)")
        st.write("Berechne Stütz- und Feldmomente mit: q * l² / n")
        st.write("Berechne die Querkräfte mit: Faktor * q * l (s. verwendete Tabelle)")
        st.write(":red[Beachte: Bei der Querkraftberechnung wird hier nicht zwischen g und p unterschieden]")
        st.write(":red[Möglichkeit bei Dreifeldträger: Ändere eine Feldbreite minimal ab, um Berechnungsverfahren 3 für genauere Werte auszuführen]")

        st.write("### :blue[Berechnung Zweifeldträger mit unterschiedlichen Feldbreiten (Verfahren 2)]")
        st.write("Berechne das Verhältnis von l1/l2 (l1 immer kleinere Stützweite)")
        st.write("Suche aus der Tabelle den passenden Tafelwert")
        st.write("**Verwendete Tabelle:** Bautabellen für Ingenieure (Schneider) S.4.17 (20. Auflage)")
        st.write("Berechne Momente mit: Tafelwert * q * (l1)²")
        st.write("Berechne Kräfte mit: Tafelwert * q * l1")

        st.write("### :blue[Berechnung Dreifeldträger mit unterschiedlichen Feldbreiten (Verfahren 3)]")
        st.write("Berechne den Wert K = 4 * (l1+l2) * (l2+l3) - (l2)²")
        st.write("Berechne die Stützmomente für g für Lastfall 1 - 3 (s. Bautabellen für Ingenieure (Schneider) S.4.18)")
        st.write("Berechne den Fakor p/g")
        st.write("Berechne die Stützmomente für p für Lastfall 1 - 3 mit: M(von p) = M(von g) * (p/g)")
        st.write("Berechne die Stützmomente für die Lastfälle 4 - 8 durch Addition der entsprechenden Lastfälle 1 - 3")
        st.write("**Verwendete Tabelle:** Bautabellen für Ingenieure (Schneider) S.4.19 (20. Auflage)")
        st.write("Berechne Momente und Kräfte nach entsprechenden Formeln (s. verwendete Tabelle)")

with tab1:

    with st.container(border=True):
    
        colSystem_1, colSystem_2 = st.columns (2, gap="large")

    with colSystem_1:
        st.subheader("Eingabe statisches System", divider="red")

        # Anzahl der Auflager auswählen
        supportnumbers = st.selectbox("Anzahl der Auflager", (3, 4, 5, 6), index=1)
        st.write(":blue[Erstes und letztes Auflager befinden sich an den Balkenenden / Angaben in Metern]")

        # Erstellen der Liste der Optionen basierend auf der Anzahl der Supportnummern, wichtig für Benutzerdefinierte Eingabe
        field_options = [f"Feld {i+1}" for i in range(supportnumbers - 1)]

        beam_field_default_value = "4.00"

        # Initialisierung der Variablen für die Feldbreiten
        beam_fields = []

        # Eingabe der Feldbreiten basierend auf der Anzahl der Auflager
        if supportnumbers == 3:
            colsupport_1, colsupport_2 = st.columns(2, gap="large")
            with colsupport_1:
                beam_field1_input = st.text_input("Feldbreite L1:", value=beam_field_default_value)
                beam_field1 = correctify_input(beam_field1_input)
            with colsupport_2:
                beam_field2_input = st.text_input("Feldbreite L2:", value=beam_field_default_value)
                beam_field2 = correctify_input(beam_field2_input)
            st.write (":blue[Info: L1 ist immer die kleinere Stützweite]")
                
            # Konvertiere die Eingaben in Zahlen und überprüfe die Feldbreiten
            try:
                beam_field1_value = float(beam_field1)
                beam_field2_value = float(beam_field2)

                if beam_field1_value > beam_field2_value:
                    # Tausche die Werte, wenn beam_field1 größer als beam_field2 ist
                    beam_field1_value, beam_field2_value = beam_field2_value, beam_field1_value

                    # Aktualisiere die Anzeige der Feldbreiten nach dem Tausch
                    beam_field1 = str(beam_field1_value)
                    beam_field2 = str(beam_field2_value)

                    st.write(f":red[Feldbreiten getauscht: L1 = {beam_field1} m und L2 = {beam_field2} m]")

            except ValueError:
                st.write(":red[Bitte geben Sie gültige Zahlenwerte für die Feldbreiten ein.]")

            beam_fields.extend([beam_field1, beam_field2])

        if supportnumbers == 4:
            colsupport_1, colsupport_2, colsupport_3 = st.columns(3, gap="large")
            with colsupport_1:
                beam_field1_input = st.text_input("Feldbreite L1:", value=beam_field_default_value)
                beam_field1 = correctify_input(beam_field1_input)
            with colsupport_2:
                beam_field2_input = st.text_input("Feldbreite L2:", value=beam_field_default_value)
                beam_field2 = correctify_input(beam_field2_input)
            with colsupport_3:
                beam_field3_input = st.text_input("Feldbreite L3:", value=beam_field_default_value)
                beam_field3 = correctify_input(beam_field3_input)
            beam_fields.extend([beam_field1, beam_field2, beam_field3])

        if supportnumbers == 5:
            colsupport_1, colsupport_2, colsupport_3, colsupport_4 = st.columns(4, gap="large")
            with colsupport_1:
                beam_field1_input = st.text_input("Feldbreite L1:", value=beam_field_default_value)
                beam_field1 = correctify_input(beam_field1_input)
            with colsupport_2:
                beam_field2_input = st.text_input("Feldbreite L2:", value=beam_field_default_value)
                beam_field2 = correctify_input(beam_field2_input)
            with colsupport_3:
                beam_field3_input = st.text_input("Feldbreite L3:", value=beam_field_default_value)
                beam_field3 = correctify_input(beam_field3_input)
            with colsupport_4:
                beam_field4_input = st.text_input("Feldbreite L4:", value=beam_field_default_value)
                beam_field4 = correctify_input(beam_field4_input)
            beam_fields.extend([beam_field1, beam_field2, beam_field3, beam_field4])

        if supportnumbers == 6:
            colsupport_1, colsupport_2, colsupport_3, colsupport_4, colsupport_5 = st.columns(5, gap="small")
            with colsupport_1:
                beam_field1_input = st.text_input("Feldbreite L1:", value=beam_field_default_value)
                beam_field1 = correctify_input(beam_field1_input)
            with colsupport_2:
                beam_field2_input = st.text_input("Feldbreite L2:", value=beam_field_default_value)
                beam_field2 = correctify_input(beam_field2_input)
            with colsupport_3:
                beam_field3_input = st.text_input("Feldbreite L3:", value=beam_field_default_value)
                beam_field3 = correctify_input(beam_field3_input)
            with colsupport_4:
                beam_field4_input = st.text_input("Feldbreite L4:", value=beam_field_default_value)
                beam_field4 = correctify_input(beam_field4_input)
            with colsupport_5:
                beam_field5_input = st.text_input("Feldbreite L5:", value=beam_field_default_value)
                beam_field5 = correctify_input(beam_field5_input)
            beam_fields.extend([beam_field1, beam_field2, beam_field3, beam_field4, beam_field5])

        # Berechnung der Gesamtlänge des Trägers
        beamLength = sum(float(field) for field in beam_fields if field)

        # Definition des breitesten Feldes
        beam_field_max = max(float(field) for field in beam_fields if field)

        # Anzeige der Gesamtlänge des Trägers
        st.write(f"Gesamtlänge des Trägers: {beamLength:.2f} m")

        # Eingabe für Lasteinzugsfeld
        load_field_input = st.text_input("Lasteinzugsfeld (in m):", value="3.00")
        load_field_value = correctify_input(load_field_input)
        if load_field_value == None:
            load_field_value= print_error_and_set_default(3.00)


        #Nun folgen die Expander

        #Ausklappbare Dachaufbauten
        roofTypeExpander = st.expander("Benutzerdefinierte Lasten / Dachaufbau (g)")
        with roofTypeExpander:
            
            # Toggle für die Aktivierung/Deaktivierung von individueller Eingabe
            roofCostum_toggle = st.toggle("Eigenen Wert für benutzerdefinierte Last (g) eintragen", value=False)
            
            if roofCostum_toggle:
                st.markdown (":red[Um direkt Streckenlasten einzutragen, deaktiviere Flächenlast]")
                colroof_1, colroof_2, colroof_3 = st.columns([0.25, 0.3, 0.45], gap="small")
                with colroof_1:
                    is_flächenlast_roof = st.checkbox("Flächenlast", value=True)
                with colroof_2:    
                    roofCostum_Input = st.text_input("Last in kN/m²" if is_flächenlast_roof else "Last in kN/m", label_visibility="visible", placeholder="Last", value="1.5", key="roofCostum_Input_text")
                    roofCostum = correctify_input(roofCostum_Input)

            # Initialisiere Input für zusätzliche Dachlasten
            roofAdditive1 = st.selectbox("zusätzliche Dachlasten", options=roofAdditives.keys(), index=2)

            roofType = st.selectbox("Dachaufbau Eigengewicht / g benutzerdefiniert", options= roofOptions, index=1)
            #Anzeige des Diagramms in Abhängigkeit zu Auswahl
            st.image(roofImage[roofType], use_column_width=True)

            #Initialisiere Variablen
            roofLayerSum = 0
            flat_data = []
                
            #Anfängliche Bearbeitbarkeit in Abhängigkeit von Einstellung des Dachaufbaus
            if roofType == "Benutzerdefinierter Aufbau oder Deaktivierung":
                #Tabelle lässt sich bearbeiten
                roofEditValue = True
            else:
                #Tabelle bleibt statisch
                roofEditValue = False
                    
            roofEdit = st.toggle("Dachlagen bearbeiten", value=roofEditValue)

            #roofLayers JSON struktur in Pandas struktur umwandeln
            for layer, (layer_name, value) in roofLayers[roofType].items():
                flat_data.append({
                    "Lage": str(layer),
                    "Bezeichnung": layer_name,
                    "Last [kN/m²]": value
                })
            #Erzeuge DataFrame
            df = pd.DataFrame(flat_data)

            if roofEdit == True:
                #Erstelle bearbeitbaren DataFrame als Widget
                edited_df = st.data_editor(df, hide_index=True, num_rows="fixed", use_container_width=True,
                disabled=["Lage"])
            else:
                #Erstelle statischen DataFrame für bessere Darstellung
                st.dataframe(df, hide_index=True, use_container_width=True)
                edited_df = df
                
            #Aufsummieren aller Werte der Spalte "Last [kN/m²]"
            #abs() damit Negative eingaben trotzdem richtig addiert werden
            roofLayerSum = abs(edited_df["Last [kN/m²]"]).sum()

            # Berechne benutzerdefinierte Last als Streckenlast
            if roofCostum_toggle:            
                if is_flächenlast_roof:
                    roofCostum_field = roofCostum * load_field_value
                else:
                    roofCostum_field = roofCostum
            else:
                roofCostum_field = 0.0

            # Dachlasten als Streckenlast berechnen
            roofForce_field = (roofLayerSum + roofAdditives[roofAdditive1]) * load_field_value + roofCostum_field

            # Auf 2 Nachkommastellen runden
            roofLayerSum = round(roofLayerSum, 2)
            roofForce_field = round(roofForce_field, 2)

            st.markdown(f"Das Eigengewicht (Dachaufbau) beträgt **{roofLayerSum} kN/m²**.")
        
        # Verwende roofForce_field in der Ausgabe
        if roofForce_field == 0:
            st.write (":red[Fehler: Die ständige Last (g) darf nicht null sein, Wert wurde auf g = 1 kN/m gesetzt.]")
            roofForce_field = 1.0
        
        st.markdown("**Berechnung der Streckenlasten: Flächenlast * Lasteinzugsfeld**")
        st. markdown(f":blue[Die resultierende Streckenlast (g) beträgt somit **{roofForce_field} kN/m**.]")

        # Beispielhafte Liste, die die benutzerdefinierten Lasten speichert
        custom_loads = []


        with st.expander("Benutzerdefinierte Lasten (p)"):
            st.markdown (":red[Um direkt Streckenlasten einzutragen, deaktiviere Flächenlast]")

            # Eingabe der ersten benutzerdefinierten Last
            colcustom_1, colcustom_2, colcustom_3, colcustom_4, colcustom_5 = st.columns([0.25, 0.3, 0.3, 0.05, 0.1], gap="small")
            with colcustom_1:
                is_flächenlast1 = st.checkbox("Flächenlast", value=True, key="flächenlast_1")
            with colcustom_2:
                customAdditive1 = st.text_input("Name Last 1", label_visibility="visible", placeholder="Bezeichnung", value="Beispiellast 1")
            with colcustom_3:
                customValueInput1 = st.text_input("Last in kN/m²" if is_flächenlast1 else "Last in kN/m", label_visibility="visible", placeholder="Last", value="1")
                customValue1 = correctify_input(customValueInput1)
            with colcustom_4:
                customLoadfields1 = field_options
                # customLoadfields1 = st.multiselect("Belastete Felder", label_visibility="visible", placeholder="Wähle Felder", options=field_options, default=field_options[0])
                # Diese Funktion macht die Belastung einzelner Felder möglich
                # aktuell wird diese Funktion aber nicht verwendet
            with colcustom_5:
                customColor1 = st.color_picker("Farbe", label_visibility="visible", value="#D23939")
                customLoadUnit1 = "kN/m²" if is_flächenlast1 else "kN/m"

            # Überprüfe, ob der Wert sinnvoll ist und alle Felder ausgefüllt sind
            if customValue1 is not None and customAdditive1 and customLoadfields1:
                # Sortiere die benutzerdefinierten Felder
                sorted_customLoadfields1 = sorted(customLoadfields1, key=lambda x: int(x.split()[1]))
                custom_loads.append({
                    "Lasttyp": "Flächenlast" if is_flächenlast1 else "Streckenlast",
                    "Name": customAdditive1,
                    "Last": customValue1,
                    "Belastete Felder": sorted_customLoadfields1,
                    "Farbe": customColor1
                })

            # Eingabe der zweiten benutzerdefinierten Last
            colcustom_6, colcustom_7, colcustom_8, colcustom_9, colcustom_10 = st.columns([0.25, 0.3, 0.3, 0.05, 0.1], gap="small")
            with colcustom_6:
                is_flächenlast2 = st.checkbox("Flächenlast", value=False, key="flächenlast_2")
            with colcustom_7:
                customAdditive2 = st.text_input("Name Last 2", label_visibility="visible", placeholder="Bezeichnung")
            with colcustom_8:
                customValueInput2 = st.text_input("Last in kN/m²" if is_flächenlast2 else "Last in kN/m", label_visibility="visible", placeholder="Last")
                customValue2 = correctify_input(customValueInput2)
            with colcustom_9:
                customLoadfields2 = field_options
                # customLoadfields2 = st.multiselect("Belastete Felder", label_visibility="visible", placeholder="Wähle Felder", options=field_options)
            with colcustom_10:
                customColor2 = st.color_picker("Farbe", label_visibility="visible", value="#D8D318")
                customLoadUnit2 = "kN/m²" if is_flächenlast2 else "kN/m"

            # Überprüfe, ob der Wert sinnvoll ist und alle Felder ausgefüllt sind
            if customValue2 is not None and customAdditive2 and customLoadfields2:
                # Sortiere die benutzerdefinierten Felder
                sorted_customLoadfields2 = sorted(customLoadfields2, key=lambda x: int(x.split()[1]))
                custom_loads.append({
                    "Lasttyp": "Flächenlast" if is_flächenlast2 else "Streckenlast",
                    "Name": customAdditive2,
                    "Last": customValue2,
                    "Belastete Felder": sorted_customLoadfields2,
                    "Farbe": customColor2
                })

        # Überprüfe, ob die Feldbreiten unterschiedlich sind
        field_widths = [float(field) for field in beam_fields]
        are_fields_different = len(set(field_widths)) > 1

        # st.markdown(f":red[In der aktuellen Version wird die Last über alle Felder gelegt]")

        # Ausgabe der benutzerdefinierten Last basierend auf den ausgewählten Feldern
        for custom_load in custom_loads:
            custom_name = custom_load["Name"]
            custom_value = custom_load["Last"]
            custom_load_fields_str = ", ".join(custom_load["Belastete Felder"])
            custom_lasttyp = custom_load["Lasttyp"]
            custom_unit = "kN/m²" if custom_lasttyp == "Flächenlast" else "kN/m"

            if are_fields_different:
                    custom_load["Belastete Felder"] = field_options  # Alle Felder auswählen
                    custom_load_fields_str = ", ".join(field_options)
            else:
                    custom_load["Belastete Felder"] = field_options  # Alle Felder auswählen / Struktur für andere Entwickler erhalten
                    custom_load_fields_str = ", ".join(field_options) # if-else Funktion hier eigentlich nicht notwendig

            # Berechne benutzerdefinierte Last als Streckenlast
            if custom_lasttyp == "Flächenlast":
                custom_value_field = custom_value * load_field_value
            else:
                custom_value_field = custom_value

            custom_value_field = round(custom_value_field, 2)    
            
            st. markdown(f":blue[Die resultierende Streckenlast **{custom_name}** beträgt somit **{custom_value_field} kN/m**.]")

            # st.markdown(f":blue[Die **{custom_lasttyp}** **{custom_name}** beträgt **{custom_value} {custom_unit}** über {custom_load_fields_str}.]")
            # if custom_lasttyp == "Flächenlast":
                # st.markdown(f":blue[Resultierende Streckenlast beträgt somit **{custom_value_field} kN/m**.]")


        with st.expander("Wind- und Schneelast (p)"):
            # Toggle für die Aktivierung/Deaktivierung von Wind- und Schneelasten
            load_toggle = st.toggle("Wind- und Schneelasten aktivieren", value=True)

            if load_toggle:
            # Initialisiere Input für Geländehöhe über NN
                heightZoneInput = st.text_input("Geländehöhe über NN [m]", value=400 )
                heightZone = correctify_input(heightZoneInput)
                if heightZone == None:
                    heightZone = print_error_and_set_default(400)
                #Falls Höhe über 1500m, wird mit 1500 gerechnet
                if int(heightZone) > 1500:
                    heightZone = 1500
                #Iteriere durch snow_mapping bis Höhe einem Key entspricht
                for height in snow_mapping.keys():
                    if int(height) >= int(heightZone):
                        snowHeight = height
                        break

                #Anpassen der maximal/mininmalwerte für Schneezonen in Bezug auf Geländehöhe
                if snow_mapping[snowHeight][0] == None:
                    snowMinValue = 3
                    snowMinToMax = "[3-5]"
                    if snow_mapping[snowHeight][2] == None:
                        snowMinValue = 5
                        snowMinToMax = "[5]"
                else:
                    snowMinValue = 1
                    snowMinToMax = "[1-5]"

                #Initialisiere Input
                buildingHeightInput = st.text_input("Gebäudehöhe [m]", value=10)
                buildingHeight = correctify_input(buildingHeightInput)

                if buildingHeight == None:
                    buildingHeight = print_error_and_set_default(8.50)

                #Indexwahl von wind_mapping je nach Gebäudehöhe
                if buildingHeight <= 10:
                    windIndex = 0
                elif 10 < buildingHeight <= 18:
                    windIndex = 1
                else:
                    windIndex = 2

                colwindsnow_1, colwindsnow_2 = st.columns([0.5, 0.5], gap="small")
                with colwindsnow_1:
                    windZone = st.number_input("Windlastzone [1-4]", help="Wähle Anhand der Lage auf der Karte eine der 4 Windlastzonen", 
                                            step=1, value=2, min_value=1, max_value=4)
                    st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/windlasten.png", caption="Windlastzonen in DE")
                    #Berechnung der Windlast wie in Tabellenbuch S.47 (0.2 wegen Flachdach)
                    windForce = wind_mapping[windZone][windIndex] * 0.2
                    # Auf 2 Nachkommastellen runden
                    windForce = round(windForce, 2)
                    st.markdown(f"Die Windlast beträgt **{windForce} kN/m²**.")

                with colwindsnow_2:
                    snowZone = st.number_input(f"Schneelastzone {snowMinToMax}", help="Wähle Anhand der Lage auf der Karte eine der 5 Schneelastzonen", 
                                            step=1, value=snowMinValue, min_value=snowMinValue, max_value=5)
                    st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/schneelasten.png", caption="Schneelastzonen in DE")
                    #Berechnung der Schneelast wie in Tabellenbuch S.45 (0.8 wegen Flachdach)
                    snowForce = snow_mapping[snowHeight][snowZone - 1] * 0.8
                    # Auf 2 Nachkommastellen runden
                    snowForce = round(snowForce, 2)
                    st.markdown(f"Die Schneelast beträgt **{snowForce} kN/m²**.")

                total_wind_snow_force = windForce + snowForce
                total_wind_snow_force = round(total_wind_snow_force, 2)
                st.markdown(f":blue[Die Last (Wind+Schnee) beträgt **{total_wind_snow_force} kN/m²**.]")

            else:
                total_wind_snow_force = 0.0    

        # Ausgabe der resultierenden Streckenlast
        total_wind_snow_force_field = total_wind_snow_force * load_field_value
        total_wind_snow_force_field = round(total_wind_snow_force_field, 2)
        st. markdown(f":blue[Die resultierende Streckenlast (Wind+Schnee) beträgt somit **{total_wind_snow_force_field} kN/m**.]")


        # Streckenlast auf dem Träger berechnen
        combinedForceField = total_wind_snow_force_field + custom_value_field + roofForce_field
        
        # Auf 2 Nachkommastellen runden
        combinedForceField = round(combinedForceField, 2)
        
        # Ergebnis anzeigen
        # st.markdown(f":black[Die Streckenlast beträgt somit **{combinedForceField} kN/m**. (provisorische Anzeige)]") # Kontrollanzeige während des Programmierens


    with colSystem_2:
        st.subheader("Darstellung statisches System", divider="red")

        # Zeichne das statische System

        # Funktion zum Setzen der Plot-Einstellungen
        def set_ax_settings(ax, min_x, max_x):
            # Entferne Achsenbeschriftungen
            ax.set_xticks([])
            ax.set_yticks([])

            # Setze Limits des Plots
            ax.set_xlim([min_x - 1, max_x + 1])
            ax.set_ylim([-6, 6])

            # Setze X- und Y-Achsen Maßstabsverhältnis
            ax.set_aspect(1.5, adjustable='datalim')

            # Entferne Ränder um die Zeichenfläche
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)

        # Funktion zum Zeichnen der Maßbänder
        def draw_mass_band(beam_fields, ax):
            # Berechne die Knotenpositionen
            node_positions = [0]
            for i in range(len(beam_fields)):
                node_positions.append(node_positions[-1] + float(beam_fields[i]))

            # Definiere Offsets für die Positionierung der Maßbänder (proportional zur total_length)
            total_length = sum(float(field) for field in beam_fields)
            offset_individualchains = total_length/-10 #für Maßband der Einzelfelder
            offset_overallchain = total_length/-7 #für Maßband gesamt 

            # Zeichne Maßbänder entlang dem Träger
            for i in range(len(node_positions)):
                ax.plot(node_positions[i], offset_individualchains, "k+", markersize=10)
                if i < len(node_positions) - 1:
                    ax.plot([node_positions[i], node_positions[i + 1]], [offset_individualchains, offset_individualchains], "k-", linewidth=1)
                    mid_point = (node_positions[i] + node_positions[i + 1]) / 2
                    if total_length >= 6:
                        # Zeichne die Länge unter der Maßkette
                        ax.annotate(f"{float(beam_fields[i]):.2f}m", (mid_point, offset_individualchains * 1.23), xytext=(0, 0), textcoords='offset points', ha='center', va='center', fontsize=8, annotation_clip=False)
                        # Zeichne die Feldnummer über der Maßkette
                        ax.annotate(f"L{i+1}", (mid_point, offset_individualchains * 0.85), xytext=(0, 0), textcoords='offset points', ha='center', va='center', fontsize=8, annotation_clip=False)
                    else:
                        # Zeichne die Länge unter der Maßkette
                        ax.annotate(f"{float(beam_fields[i]):.2f}m", (mid_point, offset_individualchains * 1.3), xytext=(0, 0), textcoords='offset points', ha='center', va='center', fontsize=8, annotation_clip=False)
                        # Zeichne die Feldnummer über der Maßkette
                        ax.annotate(f"L{i+1}", (mid_point, offset_individualchains * 0.7), xytext=(0, 0), textcoords='offset points', ha='center', va='center', fontsize=8, annotation_clip=False)

            # Zeichne Maßband für Gesamtlänge
            ax.plot(node_positions[0], offset_overallchain, "k+", markersize=10)
            ax.plot(node_positions[-1], offset_overallchain, "k+", markersize=10)
            ax.plot([node_positions[0], node_positions[-1]], [offset_overallchain, offset_overallchain], "k-", linewidth=1)
            if total_length >= 6:
                ax.annotate(f"{total_length:.2f}m", ((node_positions[0] + node_positions[-1]) / 2, offset_overallchain * 1.15), xytext=(0, 0), textcoords='offset points', ha='center', va='center', fontsize=8, annotation_clip=False)
            else:
                ax.annotate(f"{total_length:.2f}m", ((node_positions[0] + node_positions[-1]) / 2, offset_overallchain * 1.25), xytext=(0, 0), textcoords='offset points', ha='center', va='center', fontsize=8, annotation_clip=False)

        # Funktion zum Zeichnen der Lasten
        def draw_loads(node_positions, total_wind_snow_force, roofForce_field, custom_loads, ax):
            current_offset = beamLength / 20  # Initialer Abstand über dem Träger
            min_spacing = beamLength / 70  # Mindestabstand zwischen den Lasten

            # Dachlasten zeichnen
            if roofForce_field > 0:
                for i in range(len(node_positions) - 1):
                    start_pos = node_positions[i]
                    end_pos = node_positions[i + 1]
                    # Berechne Dachlasten als Streckenlast
                    roof_force_field = roofForce_field
                    # Höhe der Last proportional zum Durchlaufträger
                    last_height_roof = roof_force_field / combinedForceField * beamLength / 12
                    # Zeichne das Rechteck
                    rect_roof = plt.Rectangle((start_pos, current_offset), end_pos - start_pos, last_height_roof, color='grey', alpha=0.5)
                    ax.add_patch(rect_roof)
                    # burlywood

                # Berechne die Position für den Text in der Mitte des gesamten Trägers
                mid_x_roof = (node_positions[0] + node_positions[-1]) / 2
                mid_y_roof = current_offset + last_height_roof / 2
                # Zeichne den Wert der Dachlast
                ax.text(mid_x_roof, mid_y_roof, f"{roof_force_field:.2f} kN/m", ha='center', va='center', fontsize=8, color='black')
                # Zeichne den Schriftzug "Dachaufbau" neben dem Rechteck
                ax.text(end_pos + beamLength / 60, current_offset + last_height_roof / 2, "g / Dachaufbau", ha='left', va='center', fontsize=8, color='black')

                # Update current_offset to avoid overlap
                current_offset += last_height_roof + min_spacing

            # Wind- und Schneelasten zeichnen
            if total_wind_snow_force > 0:
                for i in range(len(node_positions) - 1):
                    start_pos = node_positions[i]
                    end_pos = node_positions[i + 1]
                    # Berechne veränderliche Lasten als Streckenlast
                    total_wind_snow_force_field = total_wind_snow_force * load_field_value
                    # Höhe der Last proportional zum Durchlaufträger
                    last_height_wind_snow = total_wind_snow_force_field / combinedForceField * beamLength / 12
                    # Zeichne das Rechteck
                    rect = plt.Rectangle((start_pos, current_offset), end_pos - start_pos, last_height_wind_snow, color='cadetblue', alpha=0.5)
                    ax.add_patch(rect)

                # Berechne die Position für den Text in der Mitte des gesamten Trägers
                mid_x = (node_positions[0] + node_positions[-1]) / 2
                mid_y = current_offset + last_height_wind_snow / 2
                # Zeichne den Wert von Wind- und Schneelast
                ax.text(mid_x, mid_y, f"{total_wind_snow_force_field:.2f} kN/m", ha='center', va='center', fontsize=8, color='black')
                # Zeichne den Schriftzug "Wind- und Schneelast" neben dem Rechteck
                ax.text(end_pos + beamLength / 60, current_offset + last_height_wind_snow / 2, "p / Wind- und Schneelast", ha='left', va='center', fontsize=8, color='black')

                # Update current_offset to avoid overlap
                current_offset += last_height_wind_snow + min_spacing


            # Benutzerdefinierte Lasten zeichnen
            for custom_load in custom_loads:
                custom_value = custom_load["Last"]
                custom_fields = custom_load["Belastete Felder"]
                custom_color = custom_load["Farbe"]

                for field in custom_fields:
                    # Wandelt die Feldbezeichnung in einen Index um (angenommen "Feld 1" entspricht Index 0)
                    field_index = int(field.split()[-1]) - 1
                    # Ermittel Start- und Endposition des belasteten Feldes
                    start_pos = node_positions[field_index]
                    end_pos = node_positions[field_index + 1]
                    # Höhe der Last proportional zum Durchlaufträger
                    custom_value_field = custom_value * load_field_value if custom_load["Lasttyp"] == "Flächenlast" else custom_value
                    last_height_custom = custom_value_field / combinedForceField * beamLength / 12
                    # Zeichne das Rechteck
                    rect_custom = plt.Rectangle((start_pos, current_offset), end_pos - start_pos, last_height_custom, color=custom_color, alpha=0.5)
                    ax.add_patch(rect_custom)

                # Berechne die Position für den Text in der Mitte der benutzerdefinierten Lasten
                mid_x_custom = (node_positions[int(custom_fields[0].split()[-1]) - 1] + node_positions[int(custom_fields[-1].split()[-1])]) / 2
                mid_y_custom = current_offset + last_height_custom / 2
                # Zeichne den Wert der benutzerdefinierten Last
                ax.text(mid_x_custom, mid_y_custom, f"{custom_value_field:.2f} kN/m", ha='center', va='center', fontsize=8, color='black')
                # Zeichne die Bezeichnung der benutzerdefinierten Last neben dem Rechteck
                ax.text(end_pos + beamLength / 60, current_offset + last_height_custom / 2, "p / " + custom_load["Name"], ha='left', va='center', fontsize=8, color='black')

                # Update current_offset to avoid overlap
                current_offset += last_height_custom + min_spacing

            
        # Funktion zum Zeichnen des Durchlaufträgers
        def draw_beam(beam_fields):
            # Initialisiere Knotenkoordinaten
            node_positions = [0]  # Startknoten bei x=0
            for i in range(len(beam_fields)):
                node_positions.append(node_positions[-1] + float(beam_fields[i]))

            # Initialisiere matplotlib Zeichenfläche
            fig, ax = plt.subplots()

            # Berechne Trägerlänge
            total_length = sum(float(field) for field in beam_fields)

            # Zeichne den Durchlaufträger als rote Linie
            for i in range(len(node_positions) - 1):
                ax.plot([node_positions[i], node_positions[i+1]], [total_length/70, total_length/70], 'r-', linewidth=2)

            # Setze Festlager
            first_pos = node_positions[0]

            # Buchstaben für die Auflager
            support_labels = ['A', 'B', 'C', 'D', 'E', 'F']
            
            if total_length >= 6:

                # Festlager darstellen
                ax.plot(first_pos, 0, "k^", markersize=10)
                ax.plot([first_pos - 0.3, first_pos + 0.3], [total_length / -100, total_length / -100], 'k-', linewidth=1)
                ax.plot([first_pos - 0.3, first_pos - 0.1 ], [total_length / -60, total_length / -100], 'k-', linewidth=1)
                ax.plot([first_pos - 0.1, first_pos + 0.1], [total_length / -60, total_length / -100], 'k-', linewidth=1)
                ax.plot([first_pos + 0.1, first_pos + 0.3], [total_length / -60, total_length / -100], 'k-', linewidth=1)
                ax.text(first_pos, total_length / -25, support_labels[0], ha='center')

                # Zeichne schwarze Dreiecke und Linien an den restlichen Auflagern
                for idx, pos in enumerate(node_positions[1:]):
                    ax.plot(pos, 0, "k^", markersize=10)
                    # Zeichne die schwarze Linie unter dem Dreieck, proportional zum total_length
                    ax.plot([pos - 0.3, pos + 0.3], [total_length / -60, total_length / -60], 'k-', linewidth=1)
                    ax.text(pos, total_length / -25, support_labels[idx + 1], ha='center')

            elif total_length < 6 and total_length >= 2:
                # Festlager darstellen
                ax.plot(first_pos, 0, "k^", markersize=10)
                ax.plot([first_pos - 0.1, first_pos + 0.1], [total_length / -65, total_length / -65], 'k-', linewidth=1)
                ax.plot([first_pos - 0.2, first_pos - 0.1 ], [total_length / -35, total_length / -65], 'k-', linewidth=1)
                ax.plot([first_pos - 0.1, first_pos], [total_length / -35, total_length / -65], 'k-', linewidth=1)
                ax.plot([first_pos, first_pos + 0.1], [total_length / -35, total_length / -65], 'k-', linewidth=1)
                ax.text(first_pos, total_length / -15, support_labels[0], ha='center')

                # Zeichne schwarze Dreiecke und Linien an den restlichen Auflagern
                for idx, pos in enumerate(node_positions[1:]):
                    ax.plot(pos, 0, "k^", markersize=10)
                    # Zeichne die schwarze Linie unter dem Dreieck, proportional zum total_length
                    ax.plot([pos - 0.1, pos + 0.1], [total_length / -40, total_length / -40], 'k-', linewidth=1)
                    ax.text(pos, total_length / -15, support_labels[idx + 1], ha='center')

            else:
                # Festlager darstellen (Dreieck mit diagonale Linien)
                ax.plot(first_pos, 0, "k^", markersize=10)
                ax.plot([first_pos - 0.1, first_pos + 0.1], [total_length / -40, total_length / -40], 'k-', linewidth=1)
                ax.plot([first_pos - 0.2, first_pos - 0.1 ], [total_length / -30, total_length / -40], 'k-', linewidth=1)
                ax.plot([first_pos - 0.1, first_pos], [total_length / -30, total_length / -40], 'k-', linewidth=1)
                ax.plot([first_pos, first_pos + 0.1], [total_length / -30, total_length / -40], 'k-', linewidth=1)
                ax.text(first_pos, total_length / -13, support_labels[0], ha='center')

                # Zeichne schwarze Dreiecke und Linien an den restlichen Auflagern (Loslager)
                for idx, pos in enumerate(node_positions[1:]):
                    ax.plot(pos, 0, "k^", markersize=10)
                    # Zeichne die schwarze Linie unter dem Dreieck, proportional zum total_length
                    ax.plot([pos - 0.1, pos + 0.1], [total_length / -30, total_length / -30], 'k-', linewidth=1)
                    ax.text(pos, total_length / -13, support_labels[idx + 1], ha='center')

            # Setze Plot-Einstellungen
            set_ax_settings(ax, min(node_positions), max(node_positions))

            # Zeichne Maßbänder
            draw_mass_band(beam_fields, ax)

            # Zeichne Lastenfeld
            draw_loads(node_positions, total_wind_snow_force, roofForce_field, custom_loads, ax)

            # Zeige den Plot
            st.pyplot(fig, use_container_width=True)

        # Zeichne den Durchlaufträger
        draw_beam(beam_fields)
            

    st.markdown(":red[Für Ergebnisse siehe weitere Tabs]")




# Nun folgt der Aufbau der Webseite Tab2
# Liste für Momente (nur Stützmomente, wenn man statt mit Tafelwerten mit der "Zerlegung in statische Systeme" rechnet.)
# In jenem Verfahren wurden die Feldmomente in der Liste moments gespeichert. Im aktuellen Code gibt es diesen Abschnitt aber nicht mehr
# "Zerlegung in statische Systeme" ist im meinem github-Verzeichnis für Interessierte hinterlegt
moments2 = []
moments3 = [] # neue Liste nur für Stützmomente

with tab2:

    with st.container(border=True):
    
        st.subheader("Ergebnisse statisches System", divider="red")

        colKräfte_1, colKräfte_2 = st.columns ([1, 1], gap="large")

        with colKräfte_1:
            
            st.subheader("Momente")

            if are_fields_different:
                # Berechnung für unterschiedliche Spannweiten mit Tafelwerten (Bautabellen S. 4.17)
                # st.write("Berechnung mit Tafelwerten über l1/l2 Verhältnis")
                
                # Berechnung der veränderlichen Lasten (p)
                p = sum(custom_load["Last"] * load_field_value if custom_load["Lasttyp"] == "Flächenlast" else custom_load["Last"] for custom_load in custom_loads) + total_wind_snow_force_field
                
                # Berechnung der ständigen Last (g)
                g = roofForce_field
                
                # Berechnung der gesamten Last q
                q = p + g

                # Konvertiere die beam_fields in Floats
                span_lengths = [float(field) for field in beam_fields]
                # Definierung von Variable l
                l1 = span_lengths[0]  # Nehme die erste Feldbreite
                l2 = span_lengths[1] # Nehme die zweite Feldbreite

                # Weiterführende Berechnungen für den Zweifeldträger
                if len(span_lengths) == 2:

                    # Verhältnis l1:l2 berechnen
                    ratio_l2_l1 = l2 / l1

                    # Auswahl der passenden Spalte basierend auf dem Verhältnis
                    if ratio_l2_l1 <= 1.15:
                        selected_row = "1:1,1"
                    elif ratio_l2_l1 <= 1.25:
                        selected_row = "1:1,2"
                    elif ratio_l2_l1 <= 1.35:
                        selected_row = "1:1,3"
                    elif ratio_l2_l1 <= 1.45:
                        selected_row = "1:1,4"
                    elif ratio_l2_l1 <= 1.55:
                        selected_row = "1:1,5"
                    elif ratio_l2_l1 <= 1.65:
                        selected_row = "1:1,6"
                    elif ratio_l2_l1 <= 1.75:
                        selected_row = "1:1,7"
                    elif ratio_l2_l1 <= 1.85:
                        selected_row = "1:1,8"
                    elif ratio_l2_l1 <= 1.95:
                        selected_row = "1:1,9"
                    elif ratio_l2_l1 <= 2.05:
                        selected_row = "1:2,0"
                    elif ratio_l2_l1 <= 2.15:
                        selected_row = "1:2,1"
                    elif ratio_l2_l1 <= 2.25:
                        selected_row = "1:2,2"
                    elif ratio_l2_l1 <= 2.35:
                        selected_row = "1:2,3"
                    elif ratio_l2_l1 <= 2.45:
                        selected_row = "1:2,4"
                    elif ratio_l2_l1 <= 2.55:
                        selected_row = "1:2,5" 
                    else:
                        st.error("Das Verhältnis l1/l2 ist zu klein für die Tafelwerte. Das kleinste Verhältnis sollte um 1:2,5 liegen.")
                        st.stop()

                    # Lastfall 1
                    
                    max_M1_g = table_value_2field_bothfields[selected_row][1]  # Max. M1 Tafelwert für g
                    max_M1_p = table_value_2field_firstfield[selected_row][1]  # Max. M1 Tafelwert für p
                    max_M1 = max_M1_g * g * l1**2 + max_M1_p * p * l1**2

                    max_A_g = table_value_2field_bothfields[selected_row][3]  # Max. A Tafelwert für g
                    max_A_p = table_value_2field_firstfield[selected_row][2]  # Max. A Tafelwert für p
                    max_A = (max_A_g * g + max_A_p * p) * l1

                    # Lastfall 2
                    
                    max_M2_g = table_value_2field_bothfields[selected_row][2]  # Max. M2 Tafelwert für g
                    max_M2_p = table_value_2field_secondfield[selected_row][1]  # Max. M2 Tafelwert für p
                    max_M2 = max_M2_g * g * l1**2 + max_M2_p * p * l1**2

                    max_C_g = table_value_2field_bothfields[selected_row][6]  # Max. C Tafelwert für g
                    max_C_p = table_value_2field_secondfield[selected_row][4]  # Max. C Tafelwert für p
                    max_C = (max_C_g * g + max_C_p * p) * l1

                    # Lastfall 3
                    
                    min_Mb_tablevalue = table_value_2field_bothfields[selected_row][0]  # Min. Mb Tafelwert
                    min_Mb = min_Mb_tablevalue * q * l1**2

                    min_Vbl_tablevalue = table_value_2field_bothfields[selected_row][4]  # Min. Vbl Tafelwert
                    min_Vbl = min_Vbl_tablevalue * q * l1

                    max_Vbr_tablevalue = table_value_2field_bothfields[selected_row][5]  # Max. Vbr Tafelwert
                    max_Vbr = max_Vbr_tablevalue * q * l1

                    max_B = abs(min_Vbl) + abs(max_Vbr)
                    abs_min_Vbl = abs(min_Vbl)

                    # Ausgabe der berechneten Momente
                    st.write(f"Das minimale Moment M (B) beträgt: {min_Mb:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 1 beträgt: {max_M1:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 2 beträgt: {max_M2:.2f} kNm")

                    moments2.append(min_Mb)
                    moments2.append(max_M1)
                    moments2.append(max_M2)

                    M_max_moments2 = max(moments2, key=abs)
                    M_k_max = max(abs(0), abs(M_max_moments2))
                    st.write(f":blue[Der Wert für M_k_max beträgt {M_k_max:.2f} kNm]")

                    moments3.append(min_Mb)
                    M_max_moments3 = max(moments3, key=abs)
                    M_max_supportingmoment = max(abs(0), abs(M_max_moments3))

                    # Popup-Funktion zur Anzeige des Rechenwegs
                    @st.experimental_dialog("Rechenweg für Momente (über L1/L2-Verhältnis)", width="large")
                    def show_popup_moments_l1l2():
                        st.markdown(":blue[Da unterschiedliche Feldbreiten vorliegen, berechne Momente nach Bautabellen Seite 4.17]")
                        st.markdown(f"**Veränderliche Lasten (p):** {p:.2f} kN")
                        st.markdown(f"**Ständige Lasten (g):** {g:.2f} kN")
                        st.markdown(f"**Gesamte Last (q):** {q:.2f} kN")
                        st.markdown(f"**Feldbreite (l1):** {l1:.2f} m")
                        st.markdown(f"**Feldbreite (l2):** {l2:.2f} m")
                        st.markdown(f"**Verwendete Reihe:** {selected_row}")
                        st.markdown("**Berechnung:** Momente = Tafelwert * q * (l1)²")

                        st.write("### :blue[Lastfall 1]")
                        st.write(f"Tafelwert max M1 g = {max_M1_g}")
                        st.write(f"Tafelwert max M1 p = {max_M1_p}")
                        st.write(f"**max M1** = {max_M1_g} * {g:.2f} * {l1}² + {max_M1_p} * {p:.2f} * {l1}² = {max_M1:.2f} kNm")

                        st.write("### :blue[Lastfall 2]")
                        st.write(f"Tafelwert max M2 g = {max_M2_g}")
                        st.write(f"Tafelwert max M2 p = {max_M2_p}")
                        st.write(f"**max M2** = {max_M2_g} * {g:.2f} * {l1}² + {max_M2_p} * {p:.2f} * {l1}² = {max_M2:.2f} kNm")

                        st.write("### :blue[Lastfall 3]")
                        st.write(f"Tafelwert min Mb = {min_Mb_tablevalue}")
                        st.write(f"**min Mb** = {min_Mb_tablevalue} * {q:.2f} * {l1}² = {min_Mb:.2f} kNm")

                    # Button zur Anzeige des Popups
                    if st.button("Rechenweg für Momente (über L1/L2-Verhältnis)"):
                        show_popup_moments_l1l2()


                if len(span_lengths) == 3:

                    l3 = span_lengths[2] # Nehme die dritte Feldbreite

                    # Sicherstellen, dass g nicht null ist, um Division durch null zu vermeiden
                    # Funktion wurde ergänzt, die dann g=1 setzt, aber falls sich der Code ändert, erzeuge Fehlermeldung
                    if g != 0:
                        ratio_pg = p / g
                    else:
                        st.error("Fehler: Die ständige Last (g) darf nicht null sein. Bitte gebe einen gültigen Wert für g ein.")
                        st.stop

                    K_value = 4 * (l1+l2) * (l2+l3) - l2**2

                    Mb_g_case1 = -((g * l1**2 * l1) / (2*K_value)) * (l2+l3)
                    Mb_p_case1 = Mb_g_case1 * ratio_pg
                    Mc_g_case1 = ((g * l1**2) / (4*K_value)) * l1 * l2
                    Mc_p_case1 = Mc_g_case1 * ratio_pg

                    Mb_g_case2 = -((g * l2**2 * l2) / (4*K_value)) * (l2+ 2*l3)
                    Mb_p_case2 = Mb_g_case2 * ratio_pg
                    Mc_g_case2 = -((g * l2**2 * l2) / (4*K_value)) * (l2 + 2*l1)
                    Mc_p_case2 = Mc_g_case2 * ratio_pg

                    Mb_g_case3 = ((g * l3**2) / (4*K_value)) * l3 * l2
                    Mb_p_case3 = Mb_g_case3 * ratio_pg
                    Mc_g_case3 = -((g * l3**2 * l3) / (2*K_value)) * (l1 + l2)
                    Mc_p_case3 = Mc_g_case3 * ratio_pg

                    Mb_g_case4 = Mb_g_case1 + Mb_g_case2 + Mb_g_case3
                    Mc_g_case4 = Mc_g_case1 + Mc_g_case2 + Mc_g_case3

                    Mb_q_case5 = Mb_g_case4 + Mb_p_case1 + Mb_p_case3
                    Mc_q_case5 = Mc_g_case4 + Mc_p_case1 + Mc_p_case3

                    Mb_q_case6 = Mb_g_case4 + Mb_p_case2
                    Mc_q_case6 = Mc_g_case4 + Mc_p_case2

                    Mb_q_case7 = Mb_g_case4 + Mb_p_case1 + Mb_p_case2
                    Mc_q_case7 = Mc_g_case4 + Mc_p_case1 + Mc_p_case2

                    Mb_q_case8 = Mb_g_case4 + Mb_p_case2 + Mb_p_case3
                    Mc_q_case8 = Mc_g_case4 + Mc_p_case2 + Mc_p_case3

                    # Lastfall 5
                    max_A = q * l1/2 + Mb_q_case5/l1
                    Va = max_A
                    max_M1 = max_A**2 / (2 * q)
                    max_D = q * l3/2 + Mc_q_case5/l3
                    max_M3 = max_D**2 / (2*q)

                    # Lastfall 6
                    V_br = q * l2/2 + (Mc_q_case6 - Mb_q_case6)/l2
                    max_M2 = V_br**2 / (2 * q) + Mb_q_case6

                    # Lastfall 7
                    min_Vbl = -q * l1/2 + Mb_q_case7/l1
                    max_Vbr = q * l2/2 + (Mc_q_case7 - Mb_q_case7)/l2
                    max_B = abs(min_Vbl) + abs(max_Vbr)

                    # Lastfall 8
                    min_Vcl = -q * l2/2 + (Mc_q_case8 - Mb_q_case8)/l2
                    max_Vcr = q * l3/2 - Mc_q_case8/l3
                    max_C = abs(min_Vcl) + abs(max_Vcr)

                    # Ausgabe der berechneten Momente
                    st.write(f"Das minimale Moment M (B) beträgt: {Mb_q_case7:.2f} kNm")
                    st.write(f"Das minimale Moment M (C) beträgt: {Mc_q_case8:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 1 beträgt: {max_M1:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 2 beträgt: {max_M2:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 3 beträgt: {max_M3:.2f} kNm")                    
                    

                    moments2.append(max_M1)
                    moments2.append(max_M2)
                    moments2.append(max_M3)
                    moments2.append(Mb_q_case7)
                    moments2.append(Mc_q_case8)

                    M_max_moments2 = max(moments2, key=abs)
                    M_k_max = max(abs(0), abs(M_max_moments2))
                    st.write(f":blue[Der Wert für M_k_max beträgt {M_k_max:.2f} kNm]")

                    moments3.append(Mb_q_case7)
                    moments3.append(Mc_q_case8)
                    M_max_moments3 = max(moments3, key=abs)
                    M_max_supportingmoment = max(abs(0), abs(M_max_moments3))

                    @st.experimental_dialog("Rechenweg für Momente und Querkräfte (über Formeln)", width="large")
                    def show_popup_moments_and_forces():
                        st.markdown(":blue[Da unterschiedlichhe Feldbreiten vorliegen, berechne Momente und Querkräfte nach Bautabellen Seite 4.18/19]")
                        st.markdown(f"**Veränderliche Lasten (p):** {p:.2f} kN")
                        st.markdown(f"**Ständige Lasten (g):** {g:.2f} kN")
                        st.markdown(f"**Gesamte Last (q):** {q:.2f} kN")
                        st.markdown(f"**Feldbreite (l1):** {l1:.2f} m")
                        st.markdown(f"**Feldbreite (l2):** {l2:.2f} m")
                        st.markdown(f"**Feldbreite (l3):** {l3:.2f} m")
                        st.markdown(f"**Verhältnis p/g:** {ratio_pg:.2f}")

                        st.write("## :blue[Berechnung der Stützmomente]")
                        st.write(f"K = 4 * (l1+l2) * (l2+l3) - (l2)² = {K_value:.2f}")

                        st.write(":blue[Lastfall 1]")
                        st.write(f"Mb(g) = -((g * l1² * l1) / (2*K)) * (l2+l3) = {Mb_g_case1:.2f} kNm")
                        st.write(f"Mb(p) = Mb(g) * (p/g) = {Mb_p_case1:.2f} kNm")
                        st.write(f"Mc(g) = ((g * l1²) / (4*K)) * l1 * l2 = {Mc_g_case1:.2f} kNm")
                        st.write(f"Mc(p) = Mc(g) * (p/g) = {Mc_p_case1:.2f} kNm")

                        st.write(":blue[Lastfall 2]")
                        st.write(f"Mb(g) = -((g * l2² * l2) / (4*K)) * (l2 + 2*l3) = {Mb_g_case2:.2f} kNm")
                        st.write(f"Mb(p) = Mb(g) * (p/g) = {Mb_p_case2:.2f} kNm")
                        st.write(f"Mc(g) = -((g * l2² * l2) / 4*K) * (l2 + 2*l1) = {Mc_g_case2:.2f} kNm")
                        st.write(f"Mc(p) = Mc(g) * (p/g) = {Mc_p_case2:.2f} kNm")

                        st.write(":blue[Lastfall 3]")
                        st.write(f"Mb(g) = ((g * l3²) / (4*K)) * l3 * l2 = {Mb_g_case3:.2f} kNm")
                        st.write(f"Mb(p) = Mb(g) * (p/g) = {Mb_p_case3:.2f} kNm")
                        st.write(f"Mc(g) = -((g * l3² * l3) / (2*K)) * (l1 + l2) = {Mc_g_case3:.2f} kNm")
                        st.write(f"Mc(p) = Mc(g) * (p/g) = {Mc_p_case3:.2f} kNm")

                        # Weitere Lastfälle können gleich über ein dataframe abgelesen werden
                        
                        # Falls gewünscht, die Ausgabe in Schriftform:
                        # st.write(":blue[Lastfall 4]")
                        # st.write(f"Mb (g) = {Mb_g_case4:.2f} kNm")
                        # st.write(f"Mc (g) = {Mc_g_case4:.2f} kNm")
                        # st.write(":blue[Lastfall 5]")
                        # st.write(f"Mb = {Mb_q_case5:.2f} kNm")
                        # st.write(f"Mc = {Mc_q_case5:.2f} kNm")
                        # st.write(":blue[Lastfall 6]")
                        # st.write(f"Mb = {Mb_q_case6:.2f} kNm")
                        # st.write(f"Mc = {Mc_q_case6:.2f} kNm")
                        # st.write(":blue[Lastfall 7]")
                        # st.write(f"**max Mb = {Mb_q_case7:.2f} kNm**")
                        # st.write(f"Mc = {Mc_q_case7:.2f} kNm")
                        # st.write(":blue[Lastfall8]")
                        # st.write(f"Mb = {Mb_q_case8:.2f} kNm")
                        # st.write(f"**max Mc = {Mc_q_case8:.2f} kNm**")


                        # Erzeugen wir nun das Dataframe / die Tabelle
                        # Erstelle zuerst ein Dictionary für die Stützmomente
                        table_cases = {
                            1: ("Last auf 1", Mb_g_case1, Mb_p_case1, None, Mc_g_case1, Mc_p_case1, None),
                            2: ("Last auf 2", Mb_g_case2, Mb_p_case2, None, Mc_g_case2, Mc_p_case2, None),
                            3: ("Last auf 3", Mb_g_case3, Mb_p_case3, None, Mc_g_case3, Mc_p_case3, None),
                            4: ("Last auf 1-3", Mb_g_case4, None, None, Mc_g_case4, None, None),
                            5: ("g (1-3) + p (1+3)", None, None, Mb_q_case5, None, None, Mc_q_case5),
                            6: ("g (1-3) + p (2)", None, None, Mb_q_case6, None, None, Mc_q_case6),
                            7: ("g (1-3) + p (1+2)", None, None, Mb_q_case7, None, None, Mc_q_case7),
                            8: ("g (1-3) + p (2+3)", None, None, Mb_q_case8, None, None, Mc_q_case8)
                        }

                        # Zeige den gerundeten DataFrame an
                        df_table_cases = pd.DataFrame.from_dict(table_cases, orient='index', columns=["Lastfall", "Mb(g)", "Mb(p)", "Mb(q)", "Mc(g)", "Mc(p)", "Mc(q)"])

                        df_table_cases = df_table_cases.round(2)

                        st.dataframe(df_table_cases)

                        # Ausgabe der weiteren Kräfte

                        st.write(":blue[Lastfall 7]")
                        st.write(f"**min Mb = {Mb_q_case7:.2f} kNm**")
                        st.write(":blue[Lastfall8]")
                        st.write(f"**min Mc = {Mc_q_case8:.2f} kNm**")

                        st.write("## :blue[Berechnung der weiteren Momente und Kräfte]")
                        st.write(":blue[Lastfall 5]")
                        st.write(f"**max A = V(a) = q * l1/2 + Mb/l1 = {max_A:.2f} kN**")
                        st.write(f"**max M1 = max A² / (2 * q)= {max_M1:.2f} kNm**")
                        st.write(f"**max D = q * l3/2 + Mc/l3= {max_D:.2f} kN**")
                        st.write(f"**max M3 = max D² / (2*q) = {max_M3:.2f} kNm**")

                        st.write(":blue[Lastfall 6]")
                        st.write(f"V(br) = q * l2/2 + (Mc - Mb)/l2 = {V_br:.2f} kN")
                        st.write(f"**max M2 = V(br)² /(2 * q) + Mb = {max_M2:.2f} kNm**")

                        st.write(":blue[Lastfall 7]")
                        st.write(f"min V(bl) = -q * l1/2 + Mb/l1= {min_Vbl:.2f} kN")
                        st.write(f"max V(br) = q * l2/2 + (Mc - Mb)/l2= {max_Vbr:.2f} kN")
                        st.write(f"**max B = {max_B:.2f} kN**")

                        st.write(":blue[Lastfall 8]")
                        st.write(f"min V(cl) = -q * l2/2 + (Mc - Mb)/l2 = {min_Vcl:.2f} kN")
                        st.write(f"max V(cr) = q * l3/2 - Mc/l3 = {max_Vcr:.2f} kN")
                        st.write(f"**max C = {max_C:.2f} kN**")

                    # Button zur Anzeige des Popups
                    if st.button("Rechenweg für Momente und Querkräfte (über Formeln)"):
                        show_popup_moments_and_forces()

                if len(span_lengths) == 4:
                    st.error("Für einen 4-Feldträger mit unterschiedlichen Feldbreiten können aktuell keine Kräfte berechnet werden. Betrachte den 3-Feldträger oder erzeuge identische Feldbreiten.")

                if len(span_lengths) == 5:
                    st.error("Für einen 5-Feldträger mit unterschiedlichen Feldbreiten können aktuell keine Kräfte berechnet werden. Betrachte den 3-Feldträger oder erzeuge identische Feldbreiten.")                        

            else:

                # Berechnung der maximalen Momente mit Tabellenbuch (s. Seite 55)

                # Berechnung der veränderlichen Lasten (p)
                p = sum(custom_load["Last"] * load_field_value if custom_load["Lasttyp"] == "Flächenlast" else custom_load["Last"] for custom_load in custom_loads) + total_wind_snow_force * load_field_value
                
                # Berechnung der ständigen Last (g)
                g = roofForce_field
                
                # Berechnung der gesamten Last q
                q = p + g

                # Sicherstellen, dass g nicht null ist, um Division durch null zu vermeiden
                if g != 0:
                    ratio_pg = p / g
                else:
                    ratio_pg = float('inf')  # Falls g null ist, setzen wir das Verhältnis auf unendlich

                # Auswahl der passenden Spalte basierend auf dem Verhältnis
                if ratio_pg >= 3.0:
                    st.error("Verhältnis p/g zu groß für die Tabellenwerte (s. verwendete Tabelle, max. Verhältnis sollte um 2,0 liegen)")
                    st.stop()
                elif ratio_pg >= 1.75:
                    selected_column = 0
                elif ratio_pg >= 1.25:
                    selected_column = 1
                elif ratio_pg >= 0.75:
                    selected_column = 2
                elif ratio_pg >= 0.25:
                    selected_column = 3
                else:
                    selected_column = 4
                
                # Konvertiere die beam_fields in Floats
                span_lengths = [float(field) for field in beam_fields]
                # Definierung von Variable l
                l = span_lengths[0]  # Nehme die erste Feldbreite (alle Feldbreiten sind gleich)


                # Weiterführende Berechnungen für den Zweifeldträger
                if len(span_lengths) == 2:
                    # Berechnung der n-Werte für 2-Feld-Träger
                    n_value_M_b = beam_n_values[1][selected_column]  # Max. Stützmoment M (B)
                    n_value_M_a_b = beam_n_values[3][selected_column]  # Max. Feldmoment M (A-B) und M (B-C)
                    # Berechnung der Momente
                    moment_M_b = q * l**2 / n_value_M_b
                    moment_M_a_b = q * l**2 / n_value_M_a_b

                    # Ausgabe der berechneten Momente
                    st.write(f"Das minimale Moment M (B) beträgt: -{moment_M_b:.2f} kNm")
                    st.write(f"Das größte Feldmoment M1 und M 2 beträgt: {moment_M_a_b:.2f} kNm")

                    moments2.append(moment_M_b)
                    moments2.append(moment_M_a_b)

                    moments3.append(moment_M_b)


                # Weiterführende Berechnungen für den Dreifeldträger
                if len(span_lengths) == 3:
                    # Berechnung der n-Werte für 3-Feld-Träger
                    n_value_M_b = beam_n_values[4][selected_column]  # Max. Stützmoment M (B) und M (C)
                    n_value_M_a_b = beam_n_values[7][selected_column]  # Max. Feldmoment M (A-B) und M (C-D)
                    n_value_M_b_c = beam_n_values[9][selected_column]  # Max. Feldmoment M (B-C)
                    # Berechnung der Momente
                    moment_M_b = q * l**2 / n_value_M_b
                    moment_M_a_b = q * l**2 / n_value_M_a_b
                    moment_M_b_c = q * l**2 / n_value_M_b_c

                    # Ausgabe der berechneten Momente
                    st.write(f"Das minimale Moment M (B) und M (C) beträgt: -{moment_M_b:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 1 und M 3 beträgt: {moment_M_a_b:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 2 beträgt: {moment_M_b_c:.2f} kNm")

                    moments2.append(moment_M_b)
                    moments2.append(moment_M_a_b)
                    moments2.append(moment_M_b_c)

                    moments3.append(moment_M_b)


                # Weiterführende Berechnungen für den Vierfeldträger
                if len(span_lengths) == 4:
                    # Berechnung der n-Werte für 4-Feld-Träger
                    n_value_M_b = beam_n_values[10][selected_column]  # Max. Stützmoment M (B) und M (D)
                    n_value_M_c = beam_n_values[11][selected_column]  # Max. Stützmoment M (C)
                    n_value_M_a_b = beam_n_values[12][selected_column]  # Max. Feldmoment M (A-B) und M (D-E)
                    n_value_M_c_d = beam_n_values[13][selected_column]  # Max. Feldmoment M (C-D) und M (B-C)
                    # Berechnung der Momente
                    moment_M_b = q * l**2 / n_value_M_b
                    moment_M_c = q * l**2 / n_value_M_c
                    moment_M_a_b = q * l**2 / n_value_M_a_b
                    moment_M_c_d = q * l**2 / n_value_M_c_d

                    # Ausgabe der berechneten Momente
                    st.write(f"Das minimale Moment M (B) und M (D) beträgt: -{moment_M_b:.2f} kNm")
                    st.write(f"Das minimale Moment M (C) beträgt: -{moment_M_c:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 1 und M 4 beträgt: {moment_M_a_b:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 3 und M 2 beträgt: {moment_M_c_d:.2f} kNm")

                    moments2.append(moment_M_b)
                    moments2.append(moment_M_c)
                    moments2.append(moment_M_a_b)
                    moments2.append(moment_M_c_d)

                    moments3.append(moment_M_b)
                    moments3.append(moment_M_c)


                # Weiterführende Berechnungen für den Fünffeldträger
                if len(span_lengths) == 5:
                    # Berechnung der n-Werte für 5-Feld-Träger
                    n_value_M_b = beam_n_values[14][selected_column]  # Max. Stützmoment M (B) und M (E)
                    n_value_M_c = beam_n_values[15][selected_column]  # Max. Stützmoment M (C) und M (D)
                    n_value_M_a_b = beam_n_values[16][selected_column]  # Max. Feldmoment M (A-B) und M (E-F)
                    n_value_M_c_d = beam_n_values[17][selected_column]  # Max. Feldmoment M (C-D)
                    n_value_M_b_c = beam_n_values[18][selected_column]  # Max. Feldmoment M (B-C) und M (D-E)
                    # Berechnung der Momente
                    moment_M_b = q * l**2 / n_value_M_b
                    moment_M_c = q * l**2 / n_value_M_c
                    moment_M_a_b = q * l**2 / n_value_M_a_b
                    moment_M_c_d = q * l**2 / n_value_M_c_d
                    moment_M_b_c = q * l**2 / n_value_M_b_c

                    # Ausgabe der berechneten Momente
                    st.write(f"Das minimale Moment M (B) und M (E) beträgt: -{moment_M_b:.2f} kNm")
                    st.write(f"Das minimale Moment M (C) und M (D) beträgt: -{moment_M_c:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 1 und M 5 beträgt: {moment_M_a_b:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 3 beträgt: {moment_M_c_d:.2f} kNm")
                    st.write(f"Das größte Feldmoment M 2 und M 4 beträgt: {moment_M_b_c:.2f} kNm")

                    moments2.append(moment_M_b)
                    moments2.append(moment_M_c)
                    moments2.append(moment_M_a_b)
                    moments2.append(moment_M_c_d)
                    moments2.append(moment_M_b_c)

                    moments3.append(moment_M_b)
                    moments3.append(moment_M_c)
                    

                M_max_moments2 = max(moments2, key=abs)
                M_k_max = max(abs(0), abs(M_max_moments2))
                st.write(f":blue[Der Wert für M_k_max beträgt {M_k_max:.2f} kNm]")

                M_max_moments3 = max(moments3, key=abs)
                M_max_supportingmoment = max(abs(0), abs(M_max_moments3))
                    

                # Popup-Funktion zur Anzeige des Rechenwegs
                @st.experimental_dialog("Rechenweg für Momente (über p/g-Verhältnis)", width="large")
                def show_popup_moments_pg_ratio():
                    st.markdown(":blue[Da einheitliche Feldbreiten vorliegen, berechne Momente nach Tabellenbuch Seite 55]")
                    st.markdown(f"**Veränderliche Lasten (p):** {p:.2f} kN")
                    st.markdown(f"**Ständige Lasten (g):** {g:.2f} kN")
                    st.markdown(f"**Gesamte Last (q):** {q:.2f} kN")
                    st.markdown(f"**Feldbreite (l):** {l:.2f} m")
                    st.markdown(f"**Verhältnis p/g:** {ratio_pg:.2f}")

                    # Zeige den Rechenweg für den Zweifeldträger
                    if len(span_lengths) == 2:
                        st.markdown(":blue[2-Feld-Träger Berechnung]")
                        st.markdown(f"**n-Wert für das minimale Moment M (B):** {n_value_M_b:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 1:** {n_value_M_a_b:.2f}")
                        st.markdown(f"**Minimales Moment M (B):** -{moment_M_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 1:** {moment_M_a_b:.2f} kNm (Berechnet als: q * l² / n)")

                    # Zeige den Rechenweg für den Dreifeldträger
                    if len(span_lengths) == 3:
                        st.markdown(":blue[3-Feld-Träger Berechnung]")
                        st.markdown(f"**n-Wert für das minimale Moment M (B) und M (C):** {n_value_M_b:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 1 und M 3:** {n_value_M_a_b:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 2:** {n_value_M_b_c:.2f}")
                        st.markdown(f"**Minimales Moment M (B) und M (C):** -{moment_M_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 1 und M 3:** {moment_M_a_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 2:** {moment_M_b_c:.2f} kNm (Berechnet als: q * l² / n)")

                    # Zeige den Rechenweg für den Vierfeldträger
                    if len(span_lengths) == 4:
                        st.markdown(":blue[4-Feld-Träger Berechnung]")
                        st.markdown(f"**n-Wert für das minimale Moment M (B) und M (D):** {n_value_M_b:.2f}")
                        st.markdown(f"**n-Wert für das minimale Moment M (C):** {n_value_M_c:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 1 und M 4:** {n_value_M_a_b:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 3 und M 2:** {n_value_M_c_d:.2f}")
                        st.markdown(f"**Minimales Moment M (B) und M (D):** -{moment_M_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Minimales Moment M (C):** -{moment_M_c:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 1 und M 4:** {moment_M_a_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 3 und M 2:** {moment_M_c_d:.2f} kNm (Berechnet als: q * l² / n)")

                    # Zeige den Rechenweg für den Fünffeldträger
                    if len(span_lengths) == 5:
                        st.markdown(":blue[5-Feld-Träger Berechnung]")
                        st.markdown(f"**n-Wert für das minimale Moment M (B) und M (E):** {n_value_M_b:.2f}")
                        st.markdown(f"**n-Wert für das minimale Moment M (C) und M (D):** {n_value_M_c:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 1 und M 5:** {n_value_M_a_b:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 3:** {n_value_M_c_d:.2f}")
                        st.markdown(f"**n-Wert für das größte Feldmoment M 2 und M 4:** {n_value_M_b_c:.2f}")
                        st.markdown(f"**Minimales Moment M (B) und M (E):** -{moment_M_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Minimales Moment M (C) und M (D):** -{moment_M_c:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 1 und M 5:** {moment_M_a_b:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 3:** {moment_M_c_d:.2f} kNm (Berechnet als: q * l² / n)")
                        st.markdown(f"**Größtes Feldmoment M 2 und M 4:** {moment_M_b_c:.2f} kNm (Berechnet als: q * l² / n)")

                # Button zur Anzeige des Popups
                if st.button("Rechenweg für Momente (über p/g-Verhältnis)"):
                    show_popup_moments_pg_ratio()

            # Skizze zeigen
            if len(span_lengths) == 2:
                st.write("Momentenverlauf :red[(Achtung: allgemeine Skizze)]")
                st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/Skizze-2-Feld.png")
            if len(span_lengths) == 3:
                st.write("Momentenverlauf :red[(Achtung: allgemeine Skizze)]")
                st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/Skizze-3-Feld.png")
            if len(span_lengths) == 4 and not are_fields_different:
                st.write("Momentenverlauf :red[(Achtung: allgemeine Skizze)]")
                st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/Skizze-4-Feld.png")
            if len(span_lengths) == 5 and not are_fields_different:
                st.write("Momentenverlauf :red[(Achtung: allgemeine Skizze)]")
                st.image("https://raw.githubusercontent.com/Gero-24-7/images/main/Skizze-5-Feld.png")
            

        with colKräfte_2:        

            colQuerkraft_1, colQuerkraft_2, colQuerkraft_3 = st.columns([1,6,1], gap="large")

            with colQuerkraft_2:
                st.subheader("Querkräfte")

                if are_fields_different:
                    if len(span_lengths) == 2:

                        st.write(f"Die Auflagerkraft V(A) beträgt: {max_A:.2f} kN")
                        st.write(f"Die Auflagerkraft V(B) beträgt: {max_B:.2f} kN")
                        st.write(f"Die Auflagerkraft V(C) beträgt: {max_C:.2f} kN")

                        # Popup-Funktion zur Anzeige des Rechenwegs
                        @st.experimental_dialog("Rechenweg für Querkräfte (über L1/L2-Verhältnis)")
                        def show_popup_forces_l1l2():
                            st.markdown(":blue[Unterschiedliche Feldbreiten: Berechne Querkräfte nach Bautabellen für Ingenieure Seite 4.17]")
                            st.markdown(f"**Veränderliche Lasten (p):** {p:.2f} kN")
                            st.markdown(f"**Ständige Lasten (g):** {g:.2f} kN")
                            st.markdown(f"**Gesamte Last (q):** {q:.2f} kN")
                            st.markdown(f"**Feldbreite (l1):** {l1:.2f} m")
                            st.markdown(f"**Feldbreite (l2):** {l2:.2f} m")
                            st.markdown(f"**Verwendete Reihe:** {selected_row}")
                            st.markdown("**Berechnung:** Kräfte = Tafelwert * q * l1")
                        
                            st.write("### :blue[Lastfall 1]")
                            st.write(f"Tafelwert max A g = {max_A_g}")
                            st.write(f"Tafelwert max A p = {max_A_p}")
                            st.write(f"**max A** = ({max_A_g} * {g:.2f} + {max_A_p} * {p:.2f}) * {l1} = {max_A:.2f} kN")

                            st.write("### :blue[Lastfall 2]")
                            st.write(f"Tafelwert max C g = {max_C_g}")
                            st.write(f"Tafelwert max C p = {max_C_p}")
                            st.write(f"**max C** = ({max_C_g} * {g:.2f} + {max_C_p} * {p:.2f}) * {l1} = {max_C:.2f} kN")

                            st.write("### :blue[Lastfall 3]")
                            st.write(f"Tafelwert min Vbl = {min_Vbl_tablevalue}")
                            st.write(f"**min Vbl** = {min_Vbl_tablevalue} * {q:.2f} * {l1} = {min_Vbl:.2f} kN")
                            st.write(f"Tafelwert max Vbr = {max_Vbr_tablevalue}")
                            st.write(f"**max Vbr** = {max_Vbr_tablevalue} * {q:.2f} * {l1} = {max_Vbr:.2f} kN")
                            st.write(f"**max B** = {abs_min_Vbl:.2f} + {max_Vbr:.2f} = {max_B:.2f} kN")

                        # Button zur Anzeige des Popups
                        if st.button("Rechenweg für Querkräfte (über L1/L2-Verhältnis)"):
                            show_popup_forces_l1l2()

                    if len(span_lengths) == 3:
                        
                        st.write(f"Die Auflagerkraft V(A) beträgt: {max_A:.2f} kN")
                        st.write(f"Die Auflagerkraft V(B) beträgt: {max_B:.2f} kN")
                        st.write(f"Die Auflagerkraft V(C) beträgt: {max_C:.2f} kN")
                        st.write(f"Die Auflagerkraft V(D) beträgt: {max_D:.2f} kN")

                    if len(span_lengths) == 2 or len(span_lengths) == 3:  

                        # Funktion zum Zeichnen des Querkraftverlaufs
                        def draw_beam_Querkraft(beam_fields):
                            # Initialisiere Knotenkoordinaten
                            node_positions = [0]  # Startknoten bei x=0
                            for i in range(len(beam_fields)):
                                node_positions.append(node_positions[-1] + float(beam_fields[i]))

                            # Initialisiere matplotlib Zeichenfläche
                            fig, ax = plt.subplots()

                            # Berechne Trägerlänge
                            total_length = sum(float(field) for field in beam_fields)

                            # Zeichne den Durchlaufträger als schwarze Linie
                            for i in range(len(node_positions) - 1):
                                ax.plot([node_positions[i], node_positions[i+1]], [total_length/70, total_length/70], 'k-', linewidth=1)

                            # Setze Festlager
                            first_pos = node_positions[0]

                            # Buchstaben für die Auflager
                            support_labels = ['A', 'B', 'C', 'D', 'E', 'F']
                            
                            # Auflager werden nicht gezeichnet, nur Buchstaben platziert
                            if total_length >= 6:
                                # Festlagerbuchstaben darstellen
                                ax.text(first_pos, total_length / -25, support_labels[0], ha='center')

                                # Zeichne weitere Auflagerbuchstaben
                                for idx, pos in enumerate(node_positions[1:]):
                                    ax.text(pos, total_length / -25, support_labels[idx + 1], ha='center')

                            elif total_length < 6 and total_length >= 2:
                                # Festlagerbuchstaben darstellen
                                ax.text(first_pos, total_length / -15, support_labels[0], ha='center')

                                # Zeichne weitere Auflagerbuchstaben
                                for idx, pos in enumerate(node_positions[1:]):
                                    ax.text(pos, total_length / -15, support_labels[idx + 1], ha='center')

                            else:
                                # Festlagerbuchstaben darstellen
                                ax.text(first_pos, total_length / -13, support_labels[0], ha='center')

                                # Zeichne weitere Auflagerbuchstaben
                                for idx, pos in enumerate(node_positions[1:]):
                                    ax.text(pos, total_length / -13, support_labels[idx + 1], ha='center')

                            # Zeichne die Linie des Querkraftverlaufs
                            if len(span_lengths) == 2:
                                force_positions = [
                                    (node_positions[0], total_length/70),  # Start auf Höhe des Trägers
                                    (node_positions[0], total_length/70 + max_A / (q * 1.6)),   # Aufsteigend zu V_a
                                    (node_positions[1], total_length/70 + min_Vbl / (q * 1.6)),  # Absteigend zu V_bl
                                    (node_positions[1], total_length/70 + max_Vbr / (q * 1.6)),  # Aufsteigend zu V_br
                                    (node_positions[2], total_length/70 - max_C / (q * 1.6)),   # Absteigend zu V_c
                                    (node_positions[-1], total_length/70)  # Ende auf Höhe des Trägers
                                ]
                                # Werte der Querkraftverlaufspunkte
                                force_values = [-max_A, -min_Vbl, -max_Vbr, max_C]

                                # Beschriftung der Querkraftverlaufspunkte
                                for i, (x, y) in enumerate(force_positions[1:-1]):  # Ohne Start- und Endpunkt
                                    if y > total_length/70:  # Punkt oberhalb des Trägers
                                        ax.text(x, y + total_length/10, f'{force_values[i]:.2f} kN', ha='center', color='black')
                                    else:  # Punkt unterhalb des Trägers
                                        ax.text(x, y - total_length/10, f'{force_values[i]:.2f} kN', ha='center', color='black')

                            if len(span_lengths) == 3:
                                force_positions = [
                                    (node_positions[0], total_length/70),  # Start auf Höhe des Trägers
                                    (node_positions[0], total_length/70 + max_A / (q * 1.4)),   # Aufsteigend zu V_a
                                    (node_positions[1], total_length/70 + min_Vbl / (q * 1.4)),  # Absteigend zu V_bl
                                    (node_positions[1], total_length/70 + max_Vbr / (q * 1.4)),  # Aufsteigend zu V_br
                                    (node_positions[2], total_length/70 + min_Vcl / (q * 1.4)),  # Absteigend zu V_cl
                                    (node_positions[2], total_length/70 + max_Vcr / (q * 1.4)),  # Aufsteigend zu V_cr
                                    (node_positions[3], total_length/70 - max_D / (q * 1.4)),   # Absteigend zu V_d
                                    (node_positions[-1], total_length/70)  # Ende auf Höhe des Trägers
                                ]
                                # Werte der Querkraftverlaufspunkte
                                force_values = [-max_A, -min_Vbl, -max_Vbr, -min_Vcl, -max_Vcr, max_D]

                                # Beschriftung der Querkraftverlaufspunkte
                                for i, (x, y) in enumerate(force_positions[1:-1]):  # Ohne Start- und Endpunkt
                                    if y > total_length/70:  # Punkt oberhalb des Trägers
                                        ax.text(x, y + total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')
                                    else:  # Punkt unterhalb des Trägers
                                        ax.text(x, y - total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')


                            force_point_x, force_point_y = zip(*force_positions)

                            ax.plot(force_point_x, force_point_y, 'k-', linewidth=2, label='Querkraftverlauf')

                            # Setze Plot-Einstellungen
                            set_ax_settings(ax, min(node_positions), max(node_positions))

                            # Maßbänder werden nicht gezeichnet

                            # Lastenfeld wird nicht gezeichnet

                            # Zeige den Plot
                            st.pyplot(fig, use_container_width=True)


                        # Zeichne den Durchlaufträger
                        draw_beam_Querkraft(beam_fields)
                
                else:

                    # Berechnung der Auflagerreaktionen (Querkräfte)
                    if len(span_lengths) == 2:
                        V_a_varia2= 0.375 * q * l
                        V_c_varia2 = V_a_varia2

                        V_a = 0.375 * g * l + 0.438 * p * l
                        V_c = V_a

                        V_bl = 0.625 * q * l
                        V_br = V_bl
                        V_b = V_bl + V_br

                        st.write(f"Die Auflagerkraft V(A) beträgt: {V_a_varia2:.2f} kN (Verfahren 1)")
                        st.write(f"**V(A) mit g/p Unterscheidung: {V_a:.2f} kN** (Verfahren 2)")
                        st.write(f"Die Auflagerkraft V(B) beträgt: {V_b:.2f} kN")
                        st.write(f"Die Auflagerkraft V(C) beträgt: {V_c_varia2:.2f} kN (Verfahren 1)")
                        st.write(f"**V(C) mit g/p Unterscheidung: {V_c:.2f} kN** (Verfahren 2)")

                    if len(span_lengths) == 3:
                        V_a = 0.4 * q * l
                        V_d = V_a
                        V_bl = 0.6 * q * l
                        V_cr = V_bl
                        V_br = 0.5 * q * l
                        V_cl = V_br
                        V_b = V_bl + V_br
                        V_c = V_cl + V_cr

                        st.write(f"Die Auflagerkraft V(A) beträgt: {V_a:.2f} kN")
                        st.write(f"Die Auflagerkraft V(B) beträgt: {V_b:.2f} kN")
                        st.write(f"Die Auflagerkraft V(C) beträgt: {V_c:.2f} kN")
                        st.write(f"Die Auflagerkraft V(D) beträgt: {V_d:.2f} kN")

                    if len(span_lengths) == 4:
                        V_a = 0.4 * q * l
                        V_bl = 0.6 * q * l
                        V_br = 0.5 * q * l
                        V_b = V_bl + V_br
                        V_cl = V_br
                        V_cr = V_br
                        V_c = V_cl + V_cr
                        V_dl = V_br
                        V_dr = V_bl
                        V_d = V_dl + V_dr
                        V_e = V_a

                        st.write(f"Die Auflagerkraft V(A) beträgt: {V_a:.2f} kN")
                        st.write(f"Die Auflagerkraft V(B) beträgt: {V_b:.2f} kN")
                        st.write(f"Die Auflagerkraft V(C) beträgt: {V_c:.2f} kN")
                        st.write(f"Die Auflagerkraft V(D) beträgt: {V_d:.2f} kN")
                        st.write(f"Die Auflagerkraft V(E) beträgt: {V_e:.2f} kN")

                    if len(span_lengths) == 5:
                        V_a = 0.4 * q * l
                        V_bl = 0.6 * q * l
                        V_br = 0.5 * q * l
                        V_b = V_bl + V_br
                        V_cl = V_br
                        V_cr = V_br
                        V_c = V_cl + V_cr
                        V_dl = V_br
                        V_dr = V_br
                        V_d = V_dl + V_dr
                        V_el = V_br
                        V_er = V_bl
                        V_e = V_el + V_er
                        V_f = V_a

                        st.write(f"Die Auflagerkraft V(A) beträgt: {V_a:.2f} kN")
                        st.write(f"Die Auflagerkraft V(B) beträgt: {V_b:.2f} kN")
                        st.write(f"Die Auflagerkraft V(C) beträgt: {V_c:.2f} kN")
                        st.write(f"Die Auflagerkraft V(D) beträgt: {V_d:.2f} kN")
                        st.write(f"Die Auflagerkraft V(E) beträgt: {V_e:.2f} kN")
                        st.write(f"Die Auflagerkraft V(F) beträgt: {V_f:.2f} kN")


                    if len(span_lengths) == 2:
                        st.write(":red[Querkraft wird hier nach Verfahren 1 und Verfahren 2 (genauer) berechnet, siehe Rechenweg/Hinweise]")
                    else:
                        # Hinweis, da hier Berechnung nicht p und g unterscheidet
                        st.write(":red[Achtung: Querkraftberechnung unterscheidet hier nicht g und p, siehe Hinweise]")

                    # Popup-Funktion zur Anzeige des Rechenwegs
                    @st.experimental_dialog("Querkraftverlauf", width="large")
                    def show_popup_forces_samefieldwidth():
                        st.markdown(":blue[Berechne Auflagerkräfte]")
                        st.markdown(f"**Gesamte Last q:** {q:.2f} kN/m")
                        st.markdown(f"**Feldbreite l:** {l:.2f} m")

                        if len(span_lengths) == 2:
                            st.markdown(":blue[2-Feld-Träger]")
                            st.markdown(f"**Auflagerkraft V(A) und V(C):** 0.375 * q * l = {V_a_varia2:.2f} kN")
                            st.markdown(f":red[**Nach Berechnungsverfahren 2 (s.Hinweise), V(A) und V(C):** 0.375 * g * l + 0.438 * p * l = {V_a:.2f} kN]")
                            st.markdown(f"**Auflagerkraft V(Bl) und V(Br):** 0.625 * q * l = {V_bl:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(B):** V(Bl) + V(Br) = {V_b:.2f} kN")

                        if len(span_lengths) == 3:
                            st.markdown(":blue[3-Feld-Träger]")
                            st.markdown(f"**Auflagerkraft V(A) und V(D):** 0.4 * q * l = {V_a:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(Bl) und V(Cr):** 0.6 * q * l = {V_bl:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(Br) und V(Cl):** 0.5 * q * l = {V_br:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(B):** V(Bl) + V(Br) = {V_b:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(C):** V(cl) + V(cr) = {V_c:.2f} kN")

                        if len(span_lengths) == 4:
                            st.markdown(":blue[4-Feld-Träger]")
                            st.markdown(f"**Auflagerkraft V(A) und V(E):** 0.4 * q * l = {V_a:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(Bl) und V(Dr):** 0.6 * q * l = {V_bl:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(Br), V(Cl), V(Cr) und V(Dl):** 0.5 * q * l = {V_br:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(B):** V(Bl) + V(Br) = {V_b:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(C):** V(Cl) + V(Cr) = {V_c:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(D):** V(Dl) + V(Dr) = {V_c:.2f} kN")

                        if len(span_lengths) == 5:
                            st.markdown(":blue[5-Feld-Träger]")
                            st.markdown(f"**Auflagerkraft V(A) und V(F):** 0.4 * q * l = {V_a:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(Bl) und V(Er):** 0.6 * q * l = {V_bl:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(Br), V(Cl), V(Cr), V(Dl), V(Dr) und V(El):** 0.5 * q * l = {V_br:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(B):** V(Bl) + V(Br) = {V_b:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(C):** V(Cl) + V(Cr) = {V_c:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(D):** V(Dl) + V(Dr) = {V_c:.2f} kN")
                            st.markdown(f"**Auflagerkraft V(E):** V(El) + V(Er) = {V_c:.2f} kN")

                    # Button zur Anzeige des Popups
                    if st.button("Rechenweg Querkraftverlauf"):
                        show_popup_forces_samefieldwidth()

                    # Funktion zum Zeichnen des Querkraftverlaufs
                    def draw_beam_Querkraft(beam_fields):
                        # Initialisiere Knotenkoordinaten
                        node_positions = [0]  # Startknoten bei x=0
                        for i in range(len(beam_fields)):
                            node_positions.append(node_positions[-1] + float(beam_fields[i]))

                        # Initialisiere matplotlib Zeichenfläche
                        fig, ax = plt.subplots()

                        # Berechne Trägerlänge
                        total_length = sum(float(field) for field in beam_fields)

                        # Zeichne den Durchlaufträger als schwarze Linie
                        for i in range(len(node_positions) - 1):
                            ax.plot([node_positions[i], node_positions[i+1]], [total_length/70, total_length/70], 'k-', linewidth=1)

                        # Setze Festlager
                        first_pos = node_positions[0]

                        # Buchstaben für die Auflager
                        support_labels = ['A', 'B', 'C', 'D', 'E', 'F']
                        
                        # Auflager werden nicht gezeichnet, nur Buchstaben platziert
                        if total_length >= 6:
                            # Festlagerbuchstaben darstellen
                            ax.text(first_pos, total_length / -25, support_labels[0], ha='center')

                            # Zeichne weitere Auflagerbuchstaben
                            for idx, pos in enumerate(node_positions[1:]):
                                ax.text(pos, total_length / -25, support_labels[idx + 1], ha='center')

                        elif total_length < 6 and total_length >= 2:
                            # Festlagerbuchstaben darstellen
                            ax.text(first_pos, total_length / -15, support_labels[0], ha='center')

                            # Zeichne weitere Auflagerbuchstaben
                            for idx, pos in enumerate(node_positions[1:]):
                                ax.text(pos, total_length / -15, support_labels[idx + 1], ha='center')

                        else:
                            # Festlagerbuchstaben darstellen
                            ax.text(first_pos, total_length / -13, support_labels[0], ha='center')

                            # Zeichne weitere Auflagerbuchstaben
                            for idx, pos in enumerate(node_positions[1:]):
                                ax.text(pos, total_length / -13, support_labels[idx + 1], ha='center')

                        # Zeichne die Linie des Querkraftverlaufs
                        if len(span_lengths) == 2:
                            force_positions = [
                                (node_positions[0], total_length/70),  # Start auf Höhe des Trägers
                                (node_positions[0], total_length/70 + V_a / (q * 1.6)),   # Aufsteigend zu V_a
                                (node_positions[1], total_length/70 - V_bl / (q * 1.6)),  # Absteigend zu V_bl
                                (node_positions[1], total_length/70 + V_br / (q * 1.6)),  # Aufsteigend zu V_br
                                (node_positions[2], total_length/70 - V_c / (q * 1.6)),   # Absteigend zu V_c
                                (node_positions[-1], total_length/70)  # Ende auf Höhe des Trägers
                            ]
                            # Werte der Querkraftverlaufspunkte
                            force_values = [-V_a, V_bl, -V_br, V_c]

                            # Beschriftung der Querkraftverlaufspunkte
                            for i, (x, y) in enumerate(force_positions[1:-1]):  # Ohne Start- und Endpunkt
                                if y > total_length/70:  # Punkt oberhalb des Trägers
                                    ax.text(x, y + total_length/10, f'{force_values[i]:.2f} kN', ha='center', color='black')
                                else:  # Punkt unterhalb des Trägers
                                    ax.text(x, y - total_length/10, f'{force_values[i]:.2f} kN', ha='center', color='black')

                        if len(span_lengths) == 3:
                            force_positions = [
                                (node_positions[0], total_length/70),  # Start auf Höhe des Trägers
                                (node_positions[0], total_length/70 + V_a / (q * 1.4)),   # Aufsteigend zu V_a
                                (node_positions[1], total_length/70 - V_bl / (q * 1.4)),  # Absteigend zu V_bl
                                (node_positions[1], total_length/70 + V_br / (q * 1.4)),  # Aufsteigend zu V_br
                                (node_positions[2], total_length/70 - V_cl / (q * 1.4)),  # Absteigend zu V_cl
                                (node_positions[2], total_length/70 + V_cr / (q * 1.4)),  # Aufsteigend zu V_cr
                                (node_positions[3], total_length/70 - V_d / (q * 1.4)),   # Absteigend zu V_d
                                (node_positions[-1], total_length/70)  # Ende auf Höhe des Trägers
                            ]
                            # Werte der Querkraftverlaufspunkte
                            force_values = [-V_a, V_bl, -V_br, V_cl, -V_cr, V_d]

                            # Beschriftung der Querkraftverlaufspunkte
                            for i, (x, y) in enumerate(force_positions[1:-1]):  # Ohne Start- und Endpunkt
                                if y > total_length/70:  # Punkt oberhalb des Trägers
                                    ax.text(x, y + total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')
                                else:  # Punkt unterhalb des Trägers
                                    ax.text(x, y - total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')

                        elif len(span_lengths) == 4:
                            force_positions = [
                                (node_positions[0], total_length/70),  # Start auf Höhe des Trägers
                                (node_positions[0], total_length/70 + V_a / (q * 1.3)),   # Aufsteigend zu V_a
                                (node_positions[1], total_length/70 - V_bl / (q * 1.3)),  # Absteigend zu V_bl
                                (node_positions[1], total_length/70 + V_br / (q * 1.3)),  # Aufsteigend zu V_br
                                (node_positions[2], total_length/70 - V_cl / (q * 1.3)),   # Absteigend zu V_cl
                                (node_positions[2], total_length/70 + V_cr / (q * 1.3)),   # Aufsteigend zu V_cr
                                (node_positions[3], total_length/70 - V_dl / (q * 1.3)),   # Absteigend zu V_dl
                                (node_positions[3], total_length/70 + V_dr / (q * 1.3)),   # Aufsteigend zu V_dr
                                (node_positions[4], total_length/70 - V_e / (q * 1.3)),   # Absteigend zu V_e
                                (node_positions[-1], total_length/70)  # Ende auf Höhe des Trägers
                            ]
                            # Werte der Querkraftverlaufspunkte
                            force_values = [-V_a, V_bl, -V_br, V_cl, -V_cr, V_dl, -V_dr, V_e]

                            # Beschriftung der Querkraftverlaufspunkte
                            for i, (x, y) in enumerate(force_positions[1:-1]):  # Ohne Start- und Endpunkt
                                if y > total_length/70:  # Punkt oberhalb des Trägers
                                    ax.text(x, y + total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')
                                else:  # Punkt unterhalb des Trägers
                                    ax.text(x, y - total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')

                        elif len(span_lengths) == 5:
                            force_positions = [
                                (node_positions[0], total_length/70),  # Start auf Höhe des Trägers
                                (node_positions[0], total_length/70 + V_a / (q * 1.1)),   # Aufsteigend zu V_a
                                (node_positions[1], total_length/70 - V_bl / (q * 1.1)),  # Absteigend zu V_bl
                                (node_positions[1], total_length/70 + V_br / (q * 1.1)),  # Aufsteigend zu V_br
                                (node_positions[2], total_length/70 - V_cl / (q * 1.1)),   # Absteigend zu V_cl
                                (node_positions[2], total_length/70 + V_cr / (q * 1.1)),   # Aufsteigend zu V_cr
                                (node_positions[3], total_length/70 - V_dl / (q * 1.1)),   # Absteigend zu V_dl
                                (node_positions[3], total_length/70 + V_dr / (q * 1.1)),   # Aufsteigend zu V_dr
                                (node_positions[4], total_length/70 - V_el / (q * 1.1)),   # Absteigend zu V_el
                                (node_positions[4], total_length/70 + V_er / (q * 1.1)),   # Aufsteigend zu V_er
                                (node_positions[5], total_length/70 - V_f / (q * 1.1)),   # Absteigend zu V_f
                                (node_positions[-1], total_length/70)  # Ende auf Höhe des Trägers
                            ]
                            # Werte der Querkraftverlaufspunkte
                            force_values = [-V_a, V_bl, -V_br, V_cl, -V_cr, V_dl, -V_dr, V_el, -V_er, V_f]

                            # Beschriftung der Querkraftverlaufspunkte
                            for i, (x, y) in enumerate(force_positions[1:-1]):  # Ohne Start- und Endpunkt
                                if y > total_length/70:  # Punkt oberhalb des Trägers
                                    ax.text(x, y + total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')
                                else:  # Punkt unterhalb des Trägers
                                    ax.text(x, y - total_length/30, f'{force_values[i]:.2f} kN', ha='center', color='black')

                        force_point_x, force_point_y = zip(*force_positions)

                        ax.plot(force_point_x, force_point_y, 'k-', linewidth=2, label='Querkraftverlauf')


                        # Setze Plot-Einstellungen
                        set_ax_settings(ax, min(node_positions), max(node_positions))

                        # Maßbänder werden nicht gezeichnet

                        # Lastenfeld wird nicht gezeichnet

                        # Zeige den Plot
                        st.pyplot(fig, use_container_width=True)


                    # Zeichne den Durchlaufträger
                    draw_beam_Querkraft(beam_fields)




with tab3:

    with st.container(border=True):
        st.subheader("Profilauswahl", divider="red")

        colProfilauswahl_1, colProfilauswahl_2, colProfilauswahl_3 = st.columns ([1, 1, 1], gap="large")

        with colProfilauswahl_1:
            # Auswahl des Materials
            material = st.selectbox(label="Material", options=["Baustahl S235 (St37)", "Baustahl S355 (St52)", "Vollholz S10 C24"], index=0)

            # Toggle für die Aktivierung/Deaktivierung von Profilauswahl
            profil_toggle = st.toggle("Individuelle Eingabe", value=False)

            if profil_toggle:
                W_ValueInput = st.text_input("W in cm³", label_visibility="visible", value="200")
                W_Value = correctify_input(W_ValueInput)

                I_vorh_ValueInput = st.text_input("I in cm⁴", label_visibility="visible", value="2000")
                I_vorh_Value = correctify_input(I_vorh_ValueInput)
        
            else:
                # Auswahl des Profils
                if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"]:
                    profil = st.selectbox(label="Profil", options=list(ipe_values.keys()))
                else:
                    profil = st.selectbox(label="Profil", options=list(kantholz_values.keys()))

            # Erstelle einen DataFrame aus dem Dictionary
            df_ipe = pd.DataFrame.from_dict(ipe_values, orient='index', columns=['I (cm⁴)', 'W (cm³)'])
            df_kantholz = pd.DataFrame.from_dict(kantholz_values, orient='index', columns=['I (cm⁴)', 'W (cm³)'])
    
            # Popup-Funktion zur Anzeige der Tabelle
            @st.experimental_dialog("verwendete Tabelle", width="large")
            def show_popup_table():
                if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"]:
                    # Zeige den DataFrame als Tabelle an
                    st.write("IPE Werte Tabelle")
                    st.dataframe(df_ipe)
                else:
                    st.write("Kantholz Werte Tabelle")
                    st.dataframe(df_kantholz)

            # Button zum Anzeigen der Tabelle
            if st.button("Verwendete Tabelle anzeigen"):
                show_popup_table()


    with st.container(border=True):

        colProfil_1, colProfil_2 = st.columns([1, 1], gap="large")

        with colProfil_1:
            st.subheader("Ergebnisse ausgewähltes Profil")

            if are_fields_different and len(span_lengths) == 4:
                st.error("Für einen 4-Feldträger mit unterschiedlichen Feldbreiten können aktuell keine Kräfte berechnet werden. Betrachte den 3-Feldträger oder erzeuge identische Feldbreiten.")
            elif are_fields_different and len(span_lengths) == 5:
                st.error("Für einen 5-Feldträger mit unterschiedlichen Feldbreiten können aktuell keine Kräfte berechnet werden. Betrachte den 3-Feldträger oder erzeuge identische Feldbreiten.")
            else:
                # Spannungsnachweis: sigma_ed <= sigma_Rd
                st.write(":blue[**Spannungsnachweis mit sigma_ed ≤ sigma_Rd und Sicherheitsfaktor 1,4:**]")
                
                # sigma_ed = M_k,max * YF / W, Variablen definieren
                if profil_toggle:
                    W = W_Value
                else:
                    if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"] and profil in ipe_values:
                        W = ipe_values[profil][1]  # Extrahiere den W-Wert aus der zweiten Spalte (Einheit W = cm³)
                    if material in ["Vollholz S10 C24"] and profil in kantholz_values:
                        W = kantholz_values[profil][1]  # Extrahiere den W-Wert aus der zweiten Spalte (Einheit W = cm³)
                YF = 1.4
                
                # Berechnung von sigma_ed
                sigma_ed = (M_k_max * 100 * YF) / W  # (kNm * 100 / cm³ = kN/cm²)
                st.write(f"sigma_ed = {sigma_ed:.2f} kN/cm²")

                if material == "Baustahl S235 (St37)":
                    sigma_Rd = 21.8
                if material == "Baustahl S355 (St52)":
                    sigma_Rd = 32.7
                if material == "Vollholz S10 C24":
                    sigma_Rd = 2.4
                st.write(f"sigma_Rd = {sigma_Rd:.2f} kN/cm²")

                if sigma_ed <= sigma_Rd:
                    st.write(":green[**Spannungsnachweis erfüllt**]")
                else:
                    st.write(":red[**Spannungsnachweis nicht erfüllt**]")

                # Nur Gebrauchstauglichkeitsnachweis durchführen, wenn die Feldbreiten gleich sind
                if not are_fields_different:
                    # Gebrauchstauglichkeitsnachweis: I(erf) <= I(vorh)
                    st.write(":blue[**Gebrauchstauglichkeitsnachweis mit I(erf) ≤ I(vorh) und zulässiger Durchbiegung von l/300**]")

                    # I(erf) = k0 * M0 * l - km * Mm * l, Variablen definieren
                    l = span_lengths[0]  # Nehme die erste Feldbreite (alle Feldbreiten sind gleich)
                    M0 = q * l**2 / 8
                    Mm = M_max_supportingmoment / 2
                    st.write(f"Betrag gemitteltes Stützmoment Mm = {Mm:.2f} kNm")
                    if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"]:
                        k0 = 15
                        km = 18
                    if material in ["Vollholz S10 C24"]:
                        k0 = 312
                        km = 375

                    # Berechnung von I(erf)
                    I_erf = k0 * M0 * l - km * Mm * l  # (Faktor * kNm * m = Faktor * kNm² = cm⁴)
                    st.write(f"I(erf) = {I_erf:.2f} cm⁴")
                        
                    if profil_toggle:
                        I_vorh = I_vorh_Value
                    else:
                        if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"] and profil in ipe_values:
                            I_vorh = ipe_values[profil][0]  # Extrahiere den I-Wert aus der ersten Spalte (Einheit I = cm⁴)
                        if material in ["Vollholz S10 C24"] and profil in kantholz_values:
                            I_vorh = kantholz_values[profil][0]  # Extrahiere den I-Wert aus der ersten Spalte (Einheit I = cm⁴)
                    st.write(f"I(vorh) = {I_vorh:.2f} cm⁴")

                    if abs(I_erf) <= abs(I_vorh):
                        st.write(":green[**Gebrauchstauglichkeitsnachweis erfüllt**]")
                    else:
                        st.write(":red[**Gebrauchstauglichkeitsnachweis nicht erfüllt**]")

                # Popup-Funktion zur Anzeige des Rechenwegs
                @st.experimental_dialog("Rechenweg Nachweise", width="large")
                def show_popup_verifications():
                    st.write("### :blue[Spannungsnachweis:]")
                    st.write(f"**Material:** {material}")
                    if not profil_toggle:
                        st.write(f"**Profil:** {profil}")
                    st.write(f"**Maximales Moment (M_k_max):** {M_k_max:.2f} kNm")
                    st.write(f"**Widerstandsmoment (W):** {W:.2f} cm³")
                    st.write(f"**Berechne Spannung (sigma_ed) mit:** (M_k_max * 100 * YF) / W")
                    st.write(f"**Berechnete Spannung (sigma_ed):** ({M_k_max:.2f} kNm * 100 * {YF}) / {W:.2f} cm³ = {sigma_ed:.2f} kN/cm²")
                    st.write(f"**Zulässige Spannung (sigma_Rd):** {sigma_Rd:.2f} kN/cm²")

                    if not are_fields_different:
                        st.write("### :blue[Gebrauchstauglichkeitsnachweis:]")
                        st.write(f"**Berechne Moment Einfeldträger (M0) mit:** q * l² / 8 ")
                        st.write(f"**Moment Einfeldträger (M0):** {q:.2f} kN/m * ({l:.2f} m)² / 8 = {M0:.2f} kNm")
                        st.write(f"**gemitteltes Stützmoment (Mm):** {M_max_supportingmoment:.2f} kNm / 2 = {Mm:.2f} kNm")
                        st.write(f"**Berechne I(erf) mit:** k0 * M0 * l - km * Mm * l")
                        st.write(f"**Erforderliches Trägheitsmoment (I_erf):** {k0} * {M0:.2f} kNm * {l:.2f} m - {km} * {Mm:.2f} kNm * {l:.2f} m = {I_erf:.2f} cm⁴")
                        st.write(f"**Vorhandenes Trägheitsmoment (I_vorh):** {I_vorh:.2f} cm⁴")

                # Button zur Anzeige des Popups
                if st.button("Rechenweg Nachweise"):
                    show_popup_verifications()
                    

                with colProfil_2:
                    st.subheader("Ergebnisse Alternativ-Profil")

                    # Spannungsnachweis: sigma_ed <= sigma_Rd
                    if material == "Baustahl S235 (St37)":
                        sigma_Rd = 21.8
                    elif material == "Baustahl S355 (St52)":
                        sigma_Rd = 32.7
                    elif material == "Vollholz S10 C24":
                        sigma_Rd = 2.4
                    st.write(f"sigma_Rd = {sigma_Rd:.2f} kN/cm²")

                    # Berechnung des erforderlichen Widerstandsmoments W_erf
                    W_erf = (M_k_max * 100 * YF) / sigma_Rd  # (kNm * 100 / kN/cm² = cm³)
                    st.write(f"W(erf) = {W_erf:.2f} cm³")

                    found_profile = None  # Variable, um das gefundene Profil zu speichern
                    I_vorh = 0  # Variable für das vorhandene Flächenträgheitsmoment
                    
                    if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"]:
                        # Iteriere durch die IPE-Profile, um ein passendes Profil zu finden
                        for profil_name, values in ipe_values.items():
                            W = values[1]  # Extrahiere den W-Wert aus der zweiten Spalte (cm³)
                            if W >= W_erf:
                                I_vorh = values[0]  # Extrahiere den I-Wert aus der ersten Spalte (cm⁴)
                                found_profile = profil_name
                                break  # Passendes Profil gefunden, Schleife verlassen

                    elif material == "Vollholz S10 C24":
                        # Iteriere durch die KVH-Profile, um ein passendes Profil zu finden
                        for profil_name, values in kantholz_values.items():
                            W = values[1]  # Extrahiere den W-Wert aus der zweiten Spalte (cm³)
                            if W >= W_erf:
                                I_vorh = values[0]  # Extrahiere den I-Wert aus der ersten Spalte (cm⁴)
                                found_profile = profil_name
                                break  # Passendes Profil gefunden, Schleife verlassen

                    if found_profile:
                        # Ausgabe des gefundenen Profils
                        st.write(f"##### Gefundenes Profil: **{found_profile}** mit W = {W:.2f} cm³ und I = {I_vorh:.2f} cm⁴")

                        # Berechnung von sigma_ed für das gefundene Profil
                        sigma_ed = (M_k_max * 100 * YF) / W  # (kNm * 100 / cm³ = kN/cm²)
                        st.write(f"sigma_ed für das gefundene Profil = {sigma_ed:.2f} kN/cm²")
                        
                        # Überprüfung des Spannungsnachweises
                        if sigma_ed <= sigma_Rd:
                            st.write(":green[**Spannungsnachweis erfüllt (sigma_ed ≤ sigma_Rd)**]")

                            # Überprüfung des Gebrauchstauglichkeitsnachweises, falls die Feldbreiten identisch sind
                            if not are_fields_different:
                                # Moment am Stützpunkt berechnen und anzeigen
                                l = span_lengths[0]  # Nehme die erste Feldbreite (alle Feldbreiten sind gleich)
                                Mm = abs(M_max_supportingmoment / 2)
                                st.write(f"Betrag gemitteltes Stützmoment Mm = {Mm:.2f} kNm")
                                
                                if material in ["Baustahl S235 (St37)", "Baustahl S355 (St52)"]:
                                    k0, km = 15, 18  # Werte für Baustahl
                                elif material == "Vollholz S10 C24":
                                    k0, km = 312, 375  # Werte für Vollholz

                                # Berechnung von I_erf
                                M0 = q * l**2 / 8
                                I_erf = k0 * M0 * l - km * Mm * l  # (Faktor * kNm * m = Faktor * kNm² = cm⁴)
                                st.write(f"I(erf) = {I_erf:.2f} cm⁴")
                                
                                if abs(I_erf) <= abs(I_vorh):
                                    st.write(":green[**Gebrauchstauglichkeitsnachweis erfüllt (I(erf) ≤ I(vorh))**]")
                                else:
                                    st.write(":red[**Gebrauchstauglichkeitsnachweis nicht erfüllt**]")
                        else:
                            st.write(":red[**Spannungsnachweis nicht erfüllt**]")
                    else:
                        st.write(":red[**Es gibt kein passendes Profil, das den Spannungsnachweis (und ggf. den Gebrauchstauglichkeitsnachweis) besteht.**]")
