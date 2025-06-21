
import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="Gestione Lavori", layout="wide")
st.title("📊 Gestione Lavori Settimanali")

# Upload dei file
persone_file = st.file_uploader("Carica il file persone.csv", type=["csv"])
lavori_file = st.file_uploader("Carica il file lavori.csv", type=["csv"])

if persone_file and lavori_file:
    st.success("✅ File caricati correttamente.")

    # Lettura file
    persone_df = pd.read_csv(persone_file, sep=";")
    lavori_df = pd.read_csv(lavori_file, sep=";")

    # Normalizza colonne
    settimane = persone_df.columns[1:].astype(int).tolist()
    ore_settimanali_long = persone_df.melt(
        id_vars="Persona", var_name="Settimana", value_name="OreDisponibili"
    )
    ore_settimanali_long["Settimana"] = ore_settimanali_long["Settimana"].astype(int)
    ore_settimanali_long["OreDisponibili"] = ore_settimanali_long["OreDisponibili"].astype(int)
    persone = ore_settimanali_long["Persona"].unique()
    sett_mins = ore_settimanali_long["Settimana"].min()

    lavori_df["Durata"] = lavori_df["Durata"].astype(int)
    lavori_df["Scadenze"] = lavori_df["Scadenze"].astype(int)
    lavori_da_fare = lavori_df.to_dict("records")

    # Assegnazioni
    assegnazioni = defaultdict(int)
    for lavoro in lavori_da_fare:
        nome = lavoro["Lavoro"]
        durata = lavoro["Durata"]
        scadenza = lavoro["Scadenze"]

        for settimana in range(sett_mins, scadenza):
            for persona in persone:
                ore_disp = ore_settimanali_long[
                    (ore_settimanali_long["Persona"] == persona) &
                    (ore_settimanali_long["Settimana"] == settimana)
                ]["OreDisponibili"].values
                if len(ore_disp) == 0:
                    continue

                ore_gia = sum(
                    assegnazioni[(persona, settimana, l["Lavoro"])]
                    for l in lavori_da_fare
                )
                ore_libere = ore_disp[0] - ore_gia
                if ore_libere <= 0:
                    continue

                ore_da_assegnare = min(durata, ore_libere)
                if ore_da_assegnare > 0:
                    assegnazioni[(persona, settimana, nome)] += ore_da_assegnare
                    durata -= ore_da_assegnare

                if durata <= 0:
                    break
            if durata <= 0:
                break

    # Tabella risultati
    sol_df = pd.DataFrame([
        {"Persona": k[0], "Settimana": k[1], "Lavoro": k[2], "Ore": v}
        for k, v in assegnazioni.items() if v > 0
    ])

    st.subheader("📅 Assegnazione settimanale per ciascuna persona")

    for persona in persone:
        st.markdown(f"### 👤 {persona}")
        pivot = sol_df[sol_df["Persona"] == persona].pivot_table(
            index="Lavoro", columns="Settimana", values="Ore", fill_value=0
        ).sort_index(axis=1)
        st.dataframe(pivot)


    # Esporta risultati
    st.subheader("⬇️ Esporta i risultati")
    csv = sol_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Scarica come CSV",
        data=csv,
        file_name="assegnazioni.csv",
        mime="text/csv"
    )

    try:
        import io
        from pandas import ExcelWriter

        output = io.BytesIO()
        with ExcelWriter(output, engine='xlsxwriter') as writer:
            sol_df.to_excel(writer, sheet_name="Assegnazioni", index=False)
            writer.save()
            xlsx_data = output.getvalue()

        st.download_button(
            label="📥 Scarica come Excel",
            data=xlsx_data,
            file_name="assegnazioni.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except:
        st.warning("⚠️ Impossibile esportare in Excel (modulo mancante)")
