import streamlit as st
import pandas as pd
from pyproj import Transformer
import gpxpy
import gpxpy.gpx
from io import BytesIO
import io

# Configurazione della pagina
st.set_page_config(
    page_title="Convertitore UTM → GPX",
    page_icon="🗺️",
    layout="wide"
)

# Titolo e descrizione
st.title("🗺️ Convertitore Coordinate UTM → GPX")
st.markdown("""
Questa applicazione converte file Excel o CSV contenenti coordinate UTM in file GPX.
Carica il tuo file, seleziona la zona UTM corretta e scarica il file GPX generato.
""")

# Sidebar per le impostazioni
st.sidebar.header("⚙️ Impostazioni")

# Zone UTM comuni per l'Italia
zone_utm = st.sidebar.selectbox(
    "Seleziona la Zona UTM",
    options=["32N", "33N", "34N", "32S", "33S"],
    index=0,
    help="Seleziona la zona UTM del tuo sistema di coordinate (Italia: principalmente 32N e 33N)"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📋 Formato file richiesto
Il file deve contenere le colonne:
- **Est** (coordinata Est UTM)
- **Nord** (coordinata Nord UTM)
- **Nome Grotta** (nome del punto)
- **Quota** (elevazione in metri)
- **CP** (Catasto Provinciale)
- **Area** (area di riferimento)
- **Comune** (nome del comune)
""")

# Upload file
uploaded_file = st.file_uploader(
    "📁 Carica il file Excel o CSV",
    type=["csv", "xlsx"],
    help="Seleziona un file .csv o .xlsx contenente le coordinate UTM"
)

def parse_zone(zone_str):
    """Estrae il numero di zona e l'emisfero dalla stringa zona UTM"""
    zone_number = int(zone_str[:-1])
    hemisphere = zone_str[-1]
    return zone_number, hemisphere

def convert_utm_to_latlon(est, nord, zone_utm):
    """Converte coordinate UTM in Lat/Lon (WGS84)"""
    try:
        zone_number, hemisphere = parse_zone(zone_utm)
        
        # Definisce il sistema di coordinate UTM
        if hemisphere == 'N':
            utm_crs = f"EPSG:326{zone_number:02d}"
        else:  # S
            utm_crs = f"EPSG:327{zone_number:02d}"
        
        # Crea il transformer da UTM a WGS84
        transformer = Transformer.from_crs(
            utm_crs,
            "EPSG:4326",  # WGS84 (lat/lon)
            always_xy=True
        )
        
        # Converte le coordinate (attenzione: pyproj usa x,y -> lon,lat)
        lon, lat = transformer.transform(est, nord)
        return lat, lon
    except Exception as e:
        st.error(f"Errore nella conversione: {e}")
        return None, None

def create_gpx(df, zone_utm, colonna_nome=None):
    """Crea un file GPX dai dati del DataFrame"""
    gpx = gpxpy.gpx.GPX()
    
    # Crea un track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    
    # Crea un segment nel track
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Contatori per statistiche
    punti_convertiti = 0
    punti_saltati = 0
    
    for idx, row in df.iterrows():
        try:
            # Estrae i dati
            est = row.get('Est', None)
            nord = row.get('Nord', None)
            
            # Cerca il nome usando la colonna identificata
            if colonna_nome:
                nome = row.get(colonna_nome, f'Punto_{idx}')
                if pd.isna(nome) or str(nome).strip() == '':
                    nome = f'Punto_{idx}'
            else:
                nome = f'Punto_{idx}'
            
            quota = row.get('Quota', None)
            cp = row.get('CP', '')
            area = row.get('Area', '')
            comune = row.get('Comune', '')
            
            # Verifica che Est e Nord siano presenti
            if pd.isna(est) or pd.isna(nord):
                punti_saltati += 1
                continue
            
            # Converte le coordinate
            lat, lon = convert_utm_to_latlon(float(est), float(nord), zone_utm)
            
            if lat is None or lon is None:
                punti_saltati += 1
                continue
            
            # Crea la descrizione
            desc_parts = []
            if not pd.isna(cp) and str(cp).strip():
                desc_parts.append(f"CP: {cp}")
            if not pd.isna(area) and str(area).strip():
                desc_parts.append(f"Area: {area}")
            if not pd.isna(comune) and str(comune).strip():
                desc_parts.append(f"Comune: {comune}")
            
            descrizione = " | ".join(desc_parts) if desc_parts else ""
            
            # Gestisce l'elevazione
            elevation = float(quota) if not pd.isna(quota) else None
            
            # Crea il waypoint
            waypoint = gpxpy.gpx.GPXWaypoint(
                latitude=lat,
                longitude=lon,
                elevation=elevation,
                name=str(nome),
                description=descrizione
            )
            
            gpx.waypoints.append(waypoint)
            punti_convertiti += 1
            
        except Exception as e:
            st.warning(f"⚠️ Errore nel processare la riga {idx}: {e}")
            punti_saltati += 1
            continue
    
    return gpx, punti_convertiti, punti_saltati

# Processamento del file
if uploaded_file is not None:
    try:
        # Legge il file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File caricato con successo! ({len(df)} righe)")
        
        # Mostra anteprima dei dati
        st.subheader("📊 Anteprima dei dati")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Verifica le colonne necessarie
        colonne_richieste = ['Est', 'Nord']
        colonne_mancanti = [col for col in colonne_richieste if col not in df.columns]
        
        if colonne_mancanti:
            st.error(f"❌ Colonne mancanti: {', '.join(colonne_mancanti)}")
            st.info("Il file deve contenere almeno le colonne: Est, Nord")
        else:
            # Identifica la colonna del nome (ricerca case-insensitive)
            st.info(f"📋 Colonne presenti nel file: {', '.join(df.columns.tolist())}")
            
            possibili_colonne_nome = ['nome grotta', 'nome', 'grotta', 'denominazione', 'nome_grotta', 'name']
            colonna_nome = None
            
            # Crea un dizionario per mappare colonne lowercase alle colonne originali
            colonne_lower = {col.lower().strip(): col for col in df.columns}
            
            for possibile_nome in possibili_colonne_nome:
                if possibile_nome in colonne_lower:
                    colonna_nome = colonne_lower[possibile_nome]
                    break
            
            if colonna_nome:
                st.success(f"✅ Utilizzo della colonna '{colonna_nome}' per i nomi dei punti")
            else:
                st.warning(f"⚠️ Nessuna colonna nome trovata. I punti saranno numerati automaticamente.")
            
            # Prepara i dati per la mappa
            st.subheader("🗺️ Anteprima sulla mappa")
            
            map_data = []
            for idx, row in df.iterrows():
                try:
                    est = row.get('Est', None)
                    nord = row.get('Nord', None)
                    
                    # Cerca il nome nella colonna identificata
                    if colonna_nome:
                        nome = row.get(colonna_nome, f'Punto_{idx}')
                        if pd.isna(nome) or str(nome).strip() == '':
                            nome = f'Punto_{idx}'
                    else:
                        nome = f'Punto_{idx}'
                    
                    if pd.isna(est) or pd.isna(nord):
                        continue
                    
                    lat, lon = convert_utm_to_latlon(float(est), float(nord), zone_utm)
                    
                    if lat is not None and lon is not None:
                        map_data.append({
                            'lat': lat, 
                            'lon': lon,
                            'nome': str(nome)
                        })
                except:
                    continue
            
            if map_data:
                map_df = pd.DataFrame(map_data)
                st.map(map_df, zoom=10)
                st.info(f"📍 Visualizzati {len(map_df)} punti sulla mappa")
                
                # Mostra anche la legenda con i nomi
                with st.expander("📋 Elenco punti sulla mappa"):
                    for i, punto in enumerate(map_data, 1):
                        st.write(f"{i}. {punto['nome']}")
            else:
                st.warning("⚠️ Nessun punto valido da visualizzare sulla mappa")
            
            # Pulsante per generare il GPX
            st.subheader("💾 Genera e scarica il file GPX")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("🔄 Genera GPX", type="primary", use_container_width=True):
                    with st.spinner("Conversione in corso..."):
                        gpx, punti_convertiti, punti_saltati = create_gpx(df, zone_utm, colonna_nome)
                        
                        # Converte il GPX in stringa
                        gpx_string = gpx.to_xml()
                        
                        # Salva in sessione
                        st.session_state['gpx_data'] = gpx_string
                        st.session_state['punti_convertiti'] = punti_convertiti
                        st.session_state['punti_saltati'] = punti_saltati
                        
                        st.success("✅ File GPX generato con successo!")
            
            # Mostra statistiche e pulsante download se il GPX è stato generato
            if 'gpx_data' in st.session_state:
                with col2:
                    st.download_button(
                        label="⬇️ Scarica file GPX",
                        data=st.session_state['gpx_data'],
                        file_name="coordinate_convertite.gpx",
                        mime="application/gpx+xml",
                        use_container_width=True
                    )
                
                # Statistiche
                st.metric("Punti convertiti", st.session_state['punti_convertiti'])
                if st.session_state['punti_saltati'] > 0:
                    st.warning(f"⚠️ {st.session_state['punti_saltati']} punti saltati per dati mancanti o errori")
    
    except Exception as e:
        st.error(f"❌ Errore nel processare il file: {e}")
        st.exception(e)

else:
    # Messaggio quando non c'è file caricato
    st.info("👆 Carica un file Excel o CSV per iniziare")
    
    # Esempio di struttura dati
    st.subheader("📝 Esempio di struttura dati")
    
    example_data = {
        'Nome Grotta': ['Grotta del Vento', 'Grotta Grande', 'Grotta Azzurra'],
        'Est': [650000, 651500, 652000],
        'Nord': [4850000, 4851000, 4852000],
        'Quota': [1200, 1350, 980],
        'CP': ['TO-001', 'TO-002', 'TO-003'],
        'Area': ['Val di Susa', 'Val di Susa', 'Val Chisone'],
        'Comune': ['Bardonecchia', 'Oulx', 'Fenestrelle']
    }
    
    example_df = pd.DataFrame(example_data)
    st.dataframe(example_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🗺️ Convertitore UTM → GPX | Datum: WGS84 | Sviluppato con Streamlit</p>
</div>
""", unsafe_allow_html=True)
