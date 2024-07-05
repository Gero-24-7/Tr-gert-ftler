if are_fields_different:
                # Berechnung für unterschiedliche Spannweiten durch Zerlegung in statische Systeme

                # Feldmomente berechnen

                # Berechnung der effektiven Spannweiten li
                def calculate_li(span_lengths):
                    li_values = []
                    num_spans = len(span_lengths)
                    
                    # Ersten und letzten Index berücksichtigen
                    if num_spans < 2:
                        raise ValueError("Es müssen mindestens zwei Spannweiten eingegeben werden.")
                    
                    # Spezielle Behandlung für 2-Feld-Träger
                    if num_spans == 2:
                        l1, l2 = span_lengths
                        if l1 == l2:
                            li1 = 0.8 * l1
                            li2 = 0.8 * l2
                        else:
                            if l1 > l2:
                                li1 = 0.8 * l1
                                li2 = 2 / 3 * l2
                            else:
                                li1 = 2 / 3 * l1
                                li2 = 0.8 * l2
                        li_values.extend([li1, li2])
                        return li_values

                    # Berechne die li-Werte für Träger mit mehr als 2 Feldern
                    for i in range(num_spans):
                        if i == 0:  # Erstes Feld
                            if span_lengths[i] < span_lengths[i + 1]:
                                li = 2 / 3 * span_lengths[i]
                            else:
                                li = 3 / 4 * span_lengths[i]
                        elif i == num_spans - 1:  # Letztes Feld
                            if span_lengths[i] < span_lengths[i - 1]:
                                li = 2 / 3 * span_lengths[i]
                            else:
                                li = 3 / 4 * span_lengths[i]
                        else:  # Mittlere Felder
                            li = 0.6 * span_lengths[i]
                        
                        li_values.append(li)

                    return li_values

                # Konvertiere die beam_fields in Floats
                span_lengths = [float(field) for field in beam_fields]

                # Berechne die li-Werte
                li_values = calculate_li(span_lengths)

                # Berechnung der Momente für jedes Feld
                moments = []
                q_values = []  # Liste zum Speichern der q-Werte für jedes Feld

                for i, li in enumerate(li_values):
                    # Initialisiere die Gesamtlast q für das aktuelle Feld
                    q = 0.0
                    
                    # Füge Dachlasten hinzu
                    if roofForce > 0:
                        q += roofForce * load_field_value

                    # Füge Wind- und Schneelasten hinzu
                    if total_wind_snow_force > 0:
                        q += total_wind_snow_force * load_field_value

                    # Füge benutzerdefinierte Lasten hinzu
                    for custom_load in custom_loads:
                        custom_fields = custom_load["Belastete Felder"]
                        if f"Feld {i + 1}" in custom_fields:
                            q += custom_load["Last"] * load_field_value

                    # Speichere den q-Wert
                    q_values.append(q)

                    # Berechne die Feldmomente
                    M = (q * (li ** 2)) / 8
                    moments.append(M)

                # Gesamtausgabe der Momente
                for i, M in enumerate(moments):
                    st.write(f"Feldmoment L{i + 1} = {M:.2f} kNm")

                M_max_feld = max(moments)
                # st.write(f"Das größte Feldmoment beträgt {M_max_feld:.2f} kNm") # Kontrollausgabe

                # Berechnung der Auflagerkräfte und Stützmomente

                # Initialisierung der Liste für Auflagerkräfte und Gelenkkräfte
                support_reactions = []
                joint_forces = []

                # Berechne die Auflagerkraft A und die Gelenkkraft G für das erste Auflager
                li1 = li_values[0]
                q1 = q_values[0]

                # Gleichgewichtsgleichung: q * li * (li/2) - A * li = 0
                # Umgestellt: A = q * (li/2)
                A = q1 * (li1 / 2)
                G1 = A

                # Speichern der Auflagerkraft
                support_reactions.append(A)
                joint_forces.append(G1)

                # Weiterführende Berechnungen für den Zweifeldträger
                if len(span_lengths) == 2:
                    l1 = span_lengths[0]
                    l2 = span_lengths[1]
                    li1 = li_values[0]
                    li2 = li_values[1]

                    q1 = q_values[0]
                    q2 = q_values[1]

                    # Berechne G2
                    G2 = q2 * (li2 / 2)
                    
                    # Berechne Moment B
                    Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite

                    # Ausgabe des berechneten Stützmoments
                    st.write(f"Stützmoment bei B = {Moment_B:.2f} kNm") # linke Seite
                    moments2.append(Moment_B)


                # Weiterführende Berechnungen für den Dreifeldträger
                if len(span_lengths) == 3:
                    l1 = span_lengths[0]
                    l2 = span_lengths[1]
                    l3 = span_lengths[2]
                    li1 = li_values[0]
                    li2 = li_values[1]
                    li3 = li_values[2]

                    q1 = q_values[0]
                    q2 = q_values[1]
                    q3 = q_values[2]

                    # Berechnung Gelenkkräfte
                    G2 = q2 * (li2 / 2)
                    G3 = G2
                    G4 = q3 * (li3 / 2)
                    
                    # Berechne Moment B
                    Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite

                    # Berechne Moment C
                    Moment_C = -q3 * ((l3 - li3) ** 2) / 2 - G4 * (l3 - li3) # Momentberechnung rechte Seite
                    
                    # Ausgabe der berechneten Stützmomente
                    st.write(f"Stützmoment bei B = {Moment_B:.2f} kNm") # linke Seite
                    st.write(f"Stützmoment bei C = {Moment_C:.2f} kNm") # rechte Seite

                    moments2.append(Moment_B)
                    moments2.append(Moment_C)

                # Weiterführende Berechnungen für den Vierfeldträger
                if len(span_lengths) == 4:
                    l1 = span_lengths[0]
                    l2 = span_lengths[1]
                    l3 = span_lengths[2]
                    l4 = span_lengths[3]
                    li1 = li_values[0]
                    li2 = li_values[1]
                    li3 = li_values[2]
                    li4 = li_values[3]

                    q1 = q_values[0]
                    q2 = q_values[1]
                    q3 = q_values[2]
                    q4 = q_values[3]

                    # Berechnung Gelenkkräfte
                    G2 = q2 * (li2 / 2)
                    G3 = G2
                    G4 = q3 * (li3 / 2)
                    G5 = G4
                    G6 = q4 * (li4 / 2)

                    # Berechne Moment B
                    Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite

                    # Berechne Moment C
                    Moment_C = -q3 * ((l3/2 - li3/2) ** 2) / 2 - G4 * (l3/2 - li3/2) # Momentberechnung rechte Seite, beachte mittleres Feld (/2)

                    # Berechne Moment D
                    Moment_D = -q4 * ((l4 - li4) ** 2) / 2 - G6 * (l4 - li4) # Momentberechnung rechte Seite

                    # Ausgabe der berechneten Stützmomente
                    st.write(f"Stützmoment bei B = {Moment_B:.2f} kNm") # linke Seite
                    st.write(f"Stützmoment bei C = {Moment_C:.2f} kNm") # rechte Seite
                    st.write(f"Stützmoment bei D = {Moment_D:.2f} kNm") # rechte Seite

                    moments2.append(Moment_B)
                    moments2.append(Moment_C)
                    moments2.append(Moment_D)

                
                # Weiterführende Berechnungen für den Vierfeldträger
                if len(span_lengths) == 5:
                    l1 = span_lengths[0]
                    l2 = span_lengths[1]
                    l3 = span_lengths[2]
                    l4 = span_lengths[3]
                    l5 = span_lengths[4]
                    li1 = li_values[0]
                    li2 = li_values[1]
                    li3 = li_values[2]
                    li4 = li_values[3]
                    li5 = li_values[4]

                    q1 = q_values[0]
                    q2 = q_values[1]
                    q3 = q_values[2]
                    q4 = q_values[3]
                    q5 = q_values[4]

                    # Berechnung Gelenkkräfte
                    G2 = q2 * (li2 / 2)
                    G3 = G2
                    G4 = q3 * (li3 / 2)
                    G5 = G4
                    G6 = q4 * (li4 / 2)
                    G7 = G6
                    G8 = q5 * (li5 / 2)

                    # Berechne Moment B
                    Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite

                    # Berechne Moment C
                    Moment_C = -q3 * ((l3/2 - li3/2) ** 2) / 2 - G4 * (l3/2 - li3/2) # Momentberechnung rechte Seite, beachte mittleres Feld (/2)

                    # Berechne Moment D
                    Moment_D = -q4 * ((l4/2 - li4/2) ** 2) / 2 - G6 * (l4/2 - li4/2) # Momentberechnung rechte Seite, beachte mittleres Feld (/2)

                    # Berechne Moment E
                    Moment_E = -q5 * ((l5 - li5) ** 2) / 2 - G8 * (l5 - li5) # Momentberechnung rechte Seite, beachte mittleres Feld (/2)

                    # Ausgabe der berechneten Stützmomente
                    st.write(f"Stützmoment bei B = {Moment_B:.2f} kNm") # linke Seite
                    st.write(f"Stützmoment bei C = {Moment_C:.2f} kNm") # rechte Seite
                    st.write(f"Stützmoment bei D = {Moment_D:.2f} kNm") # rechte Seite
                    st.write(f"Stützmoment bei E = {Moment_E:.2f} kNm") # rechte Seite

                    moments2.append(Moment_B)
                    moments2.append(Moment_C)
                    moments2.append(Moment_D)
                    moments2.append(Moment_E)

                M_max_Stütze = max(moments2, key=abs)
                # key=abs, aber M_max_Stütze ist negativ
                M_k_max = max(M_max_feld, abs(M_max_Stütze))

                # Ausgabe des größten Moments
                st.write(f":blue[Das Wert für M_k_max beträgt {M_k_max:.2f} kNm]")
                

                @st.experimental_dialog("Momentenverlauf", width="large")
                def show_popup(li1, li2, q1, A, G1, li_values, q_values, moments, span_lengths):
                    st.markdown(":blue[Berechne ideelle Spannweiten li]")
                    # Ausgabe der berechneten li-Werte
                    if len(span_lengths) == 2:
                        l1, l2 = span_lengths
                        if l1 == l2:
                            li1 = 0.8 * l1
                            li2 = 0.8 * l2
                            st.write(f"li für Feld L1: 0.8 * l1 = 0.8 * {l1:.2f} m = {li1:.2f} m")
                            st.write(f"li für Feld L2: 0.8 * l2 = 0.8 * {l2:.2f} m = {li2:.2f} m")
                        else:
                            if l1 > l2:
                                li1 = 0.8 * l1
                                li2 = 2 / 3 * l2
                            else:
                                li1 = 2 / 3 * l1
                                li2 = 0.8 * l2
                            st.write(f"li für Feld L1: {0.8 if l1 > l2 else '2/3'} * l1 = {0.8 if l1 > l2 else '2/3'} * {l1:.2f} m = {li1:.2f} m")
                            st.write(f"li für Feld L2: {0.8 if l2 > l1 else '2/3'} * l2 = {0.8 if l2 > l1 else '2/3'} * {l2:.2f} m = {li2:.2f} m")
                    else:
                        for i, li in enumerate(li_values):
                            span_length = span_lengths[i]
                            if i == 0:
                                if span_length < span_lengths[i + 1]:
                                    st.write(f"li für Feld L{i + 1}: 2/3 * l{i + 1} = 2/3 * {span_length:.2f} m = {li:.2f} m")
                                else:
                                    st.write(f"li für Feld L{i + 1}: 3/4 * l{i + 1} = 3/4 * {span_length:.2f} m = {li:.2f} m")
                            elif i == len(li_values) - 1:
                                if span_length < span_lengths[i - 1]:
                                    st.write(f"li für Feld L{i + 1}: 2/3 * l{i + 1} = 2/3 * {span_length:.2f} m = {li:.2f} m")
                                else:
                                    st.write(f"li für Feld L{i + 1}: 3/4 * l{i + 1} = 3/4 * {span_length:.2f} m = {li:.2f} m")
                            else:
                                st.write(f"li für Feld L{i + 1}: 0.6 * l{i + 1} = 0.6 * {span_length:.2f} m = {li:.2f} m")

                    st.markdown(":blue[Berechne Feldmomente]")
                    # Berechne den Rechenweg für das Moment und gebe ihn aus
                    for i, M in enumerate(moments):
                        q = q_values[i]
                        li = li_values[i]
                        M = (q * (li ** 2)) / 8  # Stelle sicher, dass hier die genaue Berechnung wiederholt wird
                        st.write(f"Feldmoment für L{i + 1}: M = (q{i + 1} * (li{i + 1})²) / 8 = ({q:.2f} kN/m * ({li:.2f} m)²) / 8 = {M:.2f} kNm")

                    st.markdown(":blue[Berechne Auflager A und Gelenkkraft G]")
                    # Zeige den Rechenweg für A und G
                    st.write(f"Auflagerkraft A = q1 * (li1 / 2) = {q1:.2f} kN/m * ({li1:.2f} m / 2) = {A:.2f} kN")
                    st.write(f"Gelenkkraft G1 = A = {G1:.2f} kN")

                    if len(span_lengths) == 2:
                        st.markdown(":blue[Berechne Stützmoment]")
                        
                        # Berechne Moment B
                        Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite
                        l_B = l1 - li1 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei B = -q1 * (l1 - li1)² / 2 - G1 * (l1 - li1) = -{q1:.2f} kN/m * ({l_B:.2f} m)² / 2 - ({G1:.2f} kN * {l_B:.2f} m) = {Moment_B:.2f} kNm")

                        
                    if len(span_lengths) == 3:
                        l1 = span_lengths[0]
                        l2 = span_lengths[1]
                        l3 = span_lengths[2]
                        st.markdown(":blue[Berechne Gelenkkraft G2 und Stützmomente]")
                        # Zeige Berechnung G2
                        G2 = q3 * (li3 / 2)
                        st.write(f"Gelenkkraft G2: q3 * (li3 / 2) = {q2:.2f} kN/m * ({li3:.2f} m / 2) = {G2:.2f} kN")

                        # Berechne Moment B
                        Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite
                        l_B = l1 - li1 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei B = -q1 * (l1 - li1)² / 2 - G1 * (l1 - li1) = -{q1:.2f} kN/m * ({l_B:.2f} m)² / 2 - ({G1:.2f} kN * {l_B:.2f} m) = {Moment_B:.2f} kNm")

                        # Berechne Moment C
                        G4 = q3 * (li3 / 2)
                        Moment_C = -q3 * ((l3 - li3) ** 2) / 2 - G4 * (l3 - li3) # Momentberechnung rechte Seite
                        l_C = l3 - li3 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei C = -q3 * (l3 - li3)² / 2 - G4 * (l3 - li3) = -{q3:.2f} kN/m * ({l_C:.2f} m)² / 2 - ({G4:.2f} kN * ({l_C:.2f} m) = {Moment_C:.2f} kNm")
                    

                    if len(span_lengths) == 4:
                        l1 = span_lengths[0]
                        l2 = span_lengths[1]
                        l3 = span_lengths[2]
                        l4 = span_lengths[3]
                        st.markdown(":blue[Berechne Gelenkkräfte und Stützmomente]")

                        # Berechnung Gelenkkräfte
                        G2 = q2 * (li2 / 2)
                        G3 = G2
                        st.write(f"Gelenkkraft G2 = G3 = q2 * (li2 / 2) = {q2:.2f} kN/m * ({li2:.2f} m / 2) = {G2:.2f} kN")
                        G4 = q3 * (li3 / 2)
                        G5 = G4
                        st.write(f"Gelenkkraft G4 = G5 = q3 * (li3 / 2) = {q3:.2f} kN/m * ({li3:.2f} m / 2) = {G4:.2f} kN")
                        G6 = q4 * (li4 / 2)
                        st.write(f"Gelenkkraft G6 = q4 * (li4 / 2) = {q4:.2f} kN/m * ({li4:.2f} m / 2) = {G6:.2f} kN")

                        # Berechne Moment B
                        Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite
                        l_B = l1 - li1 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei B = -q1 * (l1 - li1)² / 2 - G1 * (l1 - li1) = -{q1:.2f} kN/m * ({l_B:.2f} m)² / 2 - ({G1:.2f} kN * {l_B:.2f} m) = {Moment_B:.2f} kNm")

                        # Berechne Moment C
                        Moment_C = -q3 * ((l3/2 - li3/2) ** 2) / 2 - G4 * (l3/2 - li3/2) # Momentberechnung rechte Seite
                        l_C = (l3 - li3) / 2 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei C = -q3 * (l3/2 - li3/2)² / 2 - G4 * (l3/2 - li3/2) = -{q3:.2f} kN/m * ({l_C:.2f} m/2)² / 2 - ({G4:.2f} kN * ({l_C:.2f} m) = {Moment_C:.2f} kNm")

                        # Berechne Moment D
                        Moment_D = -q4 * ((l4 - li4) ** 2) / 2 - G6 * (l4 - li4) # Momentberechnung rechte Seite
                        l_D = l4 - li4 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei D = -q4 * (l4 - li4)² / 2 - G6 * (l4 - li4) = -{q4:.2f} kN/m * ({l_D:.2f} m)² / 2 - ({G6:.2f} kN * {l_D:.2f} m) = {Moment_D:.2f} kNm")

                    if len(span_lengths) == 5:
                        l1 = span_lengths[0]
                        l2 = span_lengths[1]
                        l3 = span_lengths[2]
                        l4 = span_lengths[3]
                        l5 = span_lengths[4]
                        st.markdown(":blue[Berechne Gelenkkräfte und Stützmomente]")

                        # Berechnung Gelenkkräfte
                        G2 = q2 * (li2 / 2)
                        G3 = G2
                        st.write(f"Gelenkkraft G2 = G3 = q2 * (li2 / 2) = {q2:.2f} kN/m * ({li2:.2f} m / 2) = {G2:.2f} kN")
                        G4 = q3 * (li3 / 2)
                        G5 = G4
                        st.write(f"Gelenkkraft G4 = G5 = q3 * (li3 / 2) = {q3:.2f} kN/m * ({li3:.2f} m / 2) = {G4:.2f} kN")
                        G6 = q4 * (li4 / 2)
                        G7 = G6
                        st.write(f"Gelenkkraft G6 = G7 = q4 * (li4 / 2) = {q4:.2f} kN/m * ({li4:.2f} m / 2) = {G6:.2f} kN")
                        G8 = q5 * (li5 / 2)
                        st.write(f"Gelenkkraft G8 = q5 * (li5 / 2) = {q5:.2f} kN/m * ({li5:.2f} m / 2) = {G8:.2f} kN")

                        # Berechne Moment B
                        Moment_B = -q1 * ((l1 - li1) ** 2) / 2 - G1 * (l1 - li1) # Momentberechnung linke Seite
                        l_B = l1 - li1 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei B = -q1 * (l1 - li1)² / 2 - G1 * (l1 - li1) = -{q1:.2f} kN/m * ({l_B:.2f} m)² / 2 - ({G1:.2f} kN * {l_B:.2f} m) = {Moment_B:.2f} kNm")

                        # Berechne Moment C
                        Moment_C = -q3 * ((l3/2 - li3/2) ** 2) / 2 - G4 * (l3/2 - li3/2) # Momentberechnung rechte Seite
                        l_C = (l3 - li3) / 2 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei C = -q3 * (l3/2 - li3/2)² / 2 - G4 * (l3/2 - li3/2) = -{q3:.2f} kN/m * ({l_C:.2f} m)² / 2 - ({G4:.2f} kN * ({l_C:.2f} m) = {Moment_C:.2f} kNm")

                        # Berechne Moment D
                        Moment_D = -q3 * ((l3/2 - li3/2) ** 2) / 2 - G5 * (l3/2 - li3/2) # Momentberechnung linke Seite
                        l_D = (l3 - li3) / 2 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei D = -q4 * (l4/2 - li4/2)² / 2 - G6 * (l4/2 - li4/2) = -{q4:.2f} kN/m * ({l_D:.2f} m)² / 2 - ({G6:.2f} kN * {l_D:.2f} m) = {Moment_D:.2f} kNm")

                        # Berechne Moment E
                        Moment_E = -q5 * ((l5 - li5) ** 2) / 2 - G8 * (l5 - li5) # Momentberechnung rechte Seite
                        l_E = l5 - li5 # für bessere Lesbarkeit
                        st.write(f"Stützmoment bei E = -q5 * (l5 - li5)² / 2 - G6 * (l5 - li5) = -{q5:.2f} kN/m * ({l_E:.2f} m)² / 2 - ({G8:.2f} kN * {l_E:.2f} m) = {Moment_E:.2f} kNm")


                if st.button("Rechenweg Momentenverlauf"):
                    show_popup(li1, li2, q1, A, G1, li_values, q_values, moments, span_lengths)