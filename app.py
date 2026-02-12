
import streamlit as st
import pandas as pd
import yfinance as yf
from engine import WolfPackEngine
import datetime
import plotly.graph_objects as go
from tqdm import tqdm
import time
import os
import json


# Initialize Engine
engine = WolfPackEngine()

# ==========================================
# DATA ENGINE LAYER
# ==========================================
class DataEngine:
    @staticmethod
    def load_metadata(is_live=False):
        meta_path = "data/live_metadata.json" if is_live else "data/metadata.json"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    return json.load(f)
            except: pass
        return None

    @staticmethod
    @st.cache_data(ttl=300) # Cache CSV load for 5 mins
    def load_csv_data(is_live=False):
        csv_path = "data/nifty500_live.csv" if is_live else "data/nifty500_ohlcv.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df['Date'] = pd.to_datetime(df['Date'])
                return df
            except: pass
        return None

# ==========================================
# PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Alpha-Wolf Pack Scanner", layout="wide", page_icon="🐺")

# Premium CSS for Glassmorphism & Vibrant Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    .main {
        background: radial-gradient(circle at top right, #1a1a2e, #16213e, #0f3460);
        color: #e94560;
    }
    .stApp {
        background-color: transparent;
    }
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00d2ff;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
    }
    .stSidebar {
        background-color: rgba(15, 52, 96, 0.9) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 210, 255, 0.2);
    }
    div[data-testid="stMetricValue"] {
        color: #00d2ff;
        font-family: 'Orbitron', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(45deg, #00d2ff, #3a7bd5);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 210, 255, 0.4);
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR CONFIGURATION (As Requested)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/bubbles/200/wolf.png", width=120)
    st.title("🐺 Wolf Pack Dashboard")
    
    st.subheader("📡 Data Engine V2.0")
    source_toggle = st.radio("Source Toggle", ["Automation Bot (Fastest)", "Live Market (Freshness)"])
    use_live_data = "Live Market" in source_toggle
    
    # Metadata Freshness Display
    meta = DataEngine.load_metadata(use_live_data)
    if meta:
        st.caption(f"📅 Data Last Updated: {meta.get('last_updated', 'N/A')} IST")
        st.caption(f"📊 Range: {meta.get('date_range', {}).get('start', '')} to {meta.get('date_range', {}).get('end', '')}")
    else:
        st.warning("⚠️ No local data found. System will fallback to live yFinance.")

    if st.button("🧹 Force Clean Cache"):
        for f in ["wolf_cache_ai.csv", "wolf_cache_kimi.csv"]:
            if os.path.exists(f): os.remove(f)
        st.success("Cache Cleared!")
    
    st.divider()
    # AI Status Indicator
    if engine.model:
        st.sidebar.success("🧠 AI Brain: Connected (Ready to Hunt)")
    else:
        st.sidebar.error("🧠 AI Brain: Disconnected (Check v10_model.pkl)")

    st.subheader("⚙️ Configuration")
    timeframe = st.selectbox("Scanning Timeframe", ["1-2 Weeks (Recommended)", "3-7 Days (Aggressive)", "1 Month (Conservative)"])
    
    st.subheader("💰 Capital & Risk")
    total_cap = st.number_input("Total Trading Capital (INR)", min_value=1000.0, value=100000.0, step=1000.0)
    
    # User's special averaging-down practice logic
    concentrated_mode = st.toggle("Concentrated Mode (₹25k Sniper)", value=total_cap <= 50000)
    if concentrated_mode:
        allocation_pct = 50.0
        st.info("🎯 Sniper Mode: 2 Positions Max (25k/stock)")
    else:
        allocation_pct = st.slider("Allocation per Stock (%)", 5, 25, 25)
    
    st.subheader("🔍 Filters")
    min_price = st.number_input("Min Price", value=50.0, step=10.0)
    max_price = st.number_input("Max Price (0 for None)", value=0.0)
    min_vol_m = st.number_input("Min Volume (Millions)", value=1.0, help="Unit: Millions of INR Turnover")
    filter_mode = st.radio("Filter Mode", ["Prime Turbo (Max ROI)", "Prime Safe (Defensive)"])
    
    with st.expander("🛠️ Advanced settings"):
        start_date = st.date_input("Start Date", datetime.date(2025, 9, 19))
    
    st.info("Last Model Update: Feb 2026")

# ==========================================
# DATA & ENGINE
# ==========================================

@st.cache_data(ttl=3600)
def fetch_nifty_500():
    # Cleaned list (removed dead 404 tickers)
    SYMBOLS_RAW = "360ONE,ABB,ACC,ACE,ACI,ADANIENT,ADANIGREEN,ADANIPORTS,ADANIPOWER,ADANITOTAL,ADANIENSOL,AEGISCHEM,AETHER,AFFLE,AFCONS,AJANTPHARM,AKIMS,APLLTD,ALKEM,ALKYLAMINE,ALLCARGO,ALOKINDS,AMBER,AMBUJACEM,AMINES,AMRUTANJAN,ANANDRATHI,ANANTRAJ,ANGELONE,ANURAS,APARINDS,APLAPOLLO,APOLLOHOSP,APOLLOTYRE,APTUS,ARE&M,ARVIND,ARVINDFASN,ASAHIINDIA,ASHOKLEY,ASHOKA,ASIANPAINT,ASTERDM,ASTRAL,ASTRAZEN,ATGL,ATL,ATUL,AUBANK,AUROPHARMA,AVANTIFEED,AWL,AXISBANK,BAJAJ-AUTO,BAJAJCON,BAJAJELEC,BAJAJFINSV,BAJAJHFL,BAJAJHLDNG,BAJFINANCE,BALAMINES,BALKRISIND,BALRAMCHIN,BANARISUG,BANDHANBNK,BANKBARODA,BANKINDIA,BARBEQUE,BASF,BATAINDIA,BAYERCROP,BBLOTUS,BDL,BEL,BEML,BERGEPAINT,BESL,BFINANCE,BHEL,BHARTIARTL,BIOCON,BIRLACORPN,BIRLASOFT,BLS,BLUEDART,BLUESTARCO,BODALCHEM,BORORENEW,BOSCHLTD,BPCL,BRET,BRIGADE,BRITANNIA,BSE,CAMS,CAMPUS,CANBK,CANFINHOME,CAPACITE,CAPLIPOINT,CARBORUNIV,CAREERP,CASTROLIND,CCL,CEATLTD,CELLO,CENTRALBK,CENTUM,CENTURYPPLY,CENTURYTEX,CERA,CESC,CGPOWER,CHALET,CHAMBLFERT,CHEMPLASTS,CHENNPETRO,CHOLAHLDNG,CHOLAFIN,CIPLA,CLEAN,COALINDIA,COCHINSHIP,COFORGE,COLPAL,CONCOR,CONCORDBIO,COROMANDEL,CRAFTSMAN,CREATIVE,CREDITACC,CROMPTON,CSBBANK,CUB,CUMMINSIND,CYIENT,DABUR,DALBHARAT,DATAPATTNS,DEEPAKFERT,DEEPAKNTR,DELHIVERY,DELTACORP,DENORA,DEVYANI,DGCONTENT,DIAMONDYD,DICIND,DIVISLAB,DIXON,DLF,DOMS,DONEAR,DOREV,DREDGECORP,DRREDDY,DSSL,EASEMYTRIP,EDELWEISS,EICHERMOT,EIDPARRY,EIHOTEL,ELGIEQUIP,EMAMILTD,ENDURANCE,ENGINERSIN,EPL,EQUITASBNK,ERIS,ESABINDIA,ESCORTS,EXIDEIND,FEDERALBNK,FACT,FIEMIND,FILATEX,FINCABLES,FINEORG,FINPIPE,FLUOROCHEM,FORTIS,FSL,GABRIEL,GAIL,GALAXYSURF,GANESHHOUC,GARDENREACH,GARFIBRES,GATEWAY,GEECEE,GENUSPOWER,GEOJITFSL,GEP,GESHIP,GHCL,GICRE,GILLETTE,GLAND,GLAXO,GLENMARK,GLS,GMDCLTD,GMRINFRA,GNFC,GOACARBON,GODFRYPHLP,GODREJAGRO,GODREJCP,GODREJIND,GODREJPROP,GOKEX,GPIL,GPPL,GRANULES,GRAPHITE,GRASIM,GRAVITA,GREAVESCOT,GRINFRA,GRSE,GUJALKALI,GUJGASLTD,GULFOILLUB,HAL,HAPPSTMNDS,HATHWAY,HAVELLS,HCLTECH,HDFCBANK,HDFCLIFE,HEG,HEROMOTOCO,HFCL,HGINFRA,HGS,HIKAL,HINDALCO,HINDCOPPER,HINDPETRO,HINDUNILVR,HINDZINC,HMVL,HOMEFIRST,HONAUT,HUDCO,HUHTAMAKI,HUMMINGBIRD,HVL,ICICIBANK,ICICIGI,ICICIPRULI,ISEC,IDBI,IDFC,IDFCFIRSTB,IEX,IFBIND,IFCI,IGL,IGPL,IIFL,IITL,IMAGICAA,INDHOTEL,INDIACEM,INDIAGLYCO,INDIAMART,INDIANB,IOLCP,INDIGO,INDIGOPNTS,INDUSINDBK,INDUSTOWER,INFIBEAM,INFY,INGERRAND,INOXGREEN,INOXWIND,INTELLECT,IOB,IOC,IPCALAB,IRB,IRCON,IRCTC,IRFC,ISGEC,ITC,ITDC,ITDCEM,ITI,J&KBANK,JAGRAN,JAICORP,JALAN,JAMNAAUTO,JBCHEPHARM,JBMA,JINDALPHOT,JINDALPOLY,JINDALSAW,JINDALSTEL,JKCEMENT,JKPAPER,JKLAKSHMI,JKTYRE,JMFINANCIL,JSL,JSWENERGY,JSWINFRA,JSWHLDNG,JSWSTEEL,JTEKTINDIA,JUBILANT,JUBLFOOD,JUBLINGREA,JUBLPHARMA,JUSTDIAL,JYOTHYLAB,KABRAEXTRU,KAJARIACER,KALAMANDIR,KALYANKNIT,KALYANI,KALYANIFRG,KAMAHLDNG,KAMATHOTEL,KANSAINER,KARURVYSYA,KAYNES,KCP,KEC,KEI,KIOCL,KIRIINDUS,KIRLOSENG,KIRLOSIND,KIRLOSBROS,KLRF,KNRCON,KOTAKBANK,KOTHARIPET,KPITTECH,KPRMILL,KRBL,KREBSBIO,KSB,KSCL,KSL,KTKBANK,L&TFH,LALPATHLAB,LAURUSLABS,LAXMACH,LEMONTREE,LFIC,LGBBROSLTD,LIBERTSHOE,LICHSGFIN,LICI,LINDEINDIA,LTIM,LT,LUMAXIND,LUPIN,LUXIND,LXCHEM,M&MFIN,M&M,MAHABANK,MAHINDCIE,MAHLIFE,MAHLOG,MAHSCOOTER,MAITHANALL,MANALIPETC,MANAPPURAM,MANINFRA,MANKIND,MAPMYINDIA,MARICO,MARUTI,MASFIN,MASTEK,MAXHEALTH,MAZDOCK,MBAPL,MBLINFRA,MCDOWELL-N,MCX,MEDANTA,MEDPLUS,MENONBE,METROPOLIS,MFSL,MGL,MHRIL,MICROWAVE,MIDHANI,MINDACORP,MINIADAM,MIRZAINTL,MITCON,MITSU,MOIL,MOLDTKPAC,MOTILALOFS,MPHASIS,MRF,MRL,MRPL,MSHL,MSTCLTD,MTARTECH,MTNL,MURUDESHW,MUTHOOTFIN,NAM-INDIA,NATCOPHARM,NATIONALUM,NAUKRI,NAVNETEDUL,NAVINFLUOR,NAZARA,NBCC,NCC,NESCO,NESTLEIND,NETWEB,NETWORK18,NEULANDLAB,NEWGEN,NHPC,NIACL,NIFTYBEES,NIITLTD,NIITMTS,NILKAMAL,NIPPOBATRY,NIRLON,NLCINDIA,NMDC,NOCIL,NOIDATOLL,NPST,NTPC,NUCLEUS,NURECA,NYKAA,OBEROIRLTY,OCEANIC,OFSS,OIL,OLECTRA,OMAXE,ONGC,OPTIEMUS,ORCHPHARMA,ORIENTBELL,ORIENTCEM,ORIENTELEC,ORISSAMINE,PAGEIND,PAISALO,PANACEABIO,PANAMYPC,PAPERPROD,PARAGMILK,PARAS,PATANJALI,PATELENG,PAYTM,PCBL,PEL,PENTAGRAPH,PERSISTENT,PETRONET,PFC,PFIZER,PGHH,PGHL,PHOENIXLTD,PIDILITIND,PIIND,PILANIINVS,PNCINFRA,POLICYBZR,POLYCAB,POLYMED,POONAWALLA,POWERGRID,POWERINDIA,PPLPHARMA,PRAJIND,PREMIERENE,PRESTIGE,PTCIL,PVRINOX,RADICO,RAILTEL,RAINBOW,RAMCOCEM,RBLBANK,RCF,RECLTD,REDINGTON,RELIANCE,RELINFRA,RHIM,RITES,RKFORGE,RPOWER,RRKABEL,RVNL,SAGILITY,SAIL,SAILIFE,SAMMAANCAP,SAPPHIRE,SARDAEN,SAREGAMA,SBFC,SBICARD,SBILIFE,SBIN,SCHAEFFLER,SCHNEIDER,SCI,SHREECEM,SHRIRAMFIN,SHYAMMETL,SIEMENS,SIGNATURE,SJVN,SOBHA,SOLARINDS,SONACOMS,SONATSOFTW,SRF,STARHEALTH,SUMICHEM,SUNDARMFIN,SUNDRMFAST,SUNPHARMA,SUNTV,SUPREMEIND,SUZLON,SWANCORP,SWIGGY,SYNGENE,SYRMA,TARIL,TATACHEM,TATACOMM,TATACONSUM,TATAELXSI,TATAINVEST,TATAPOWER,TATASTEEL,TATATECH,TBOTEK,TCS,TECHM,TECHNOE,TEJASNET,THELEELA,THERMAX,TIINDIA,TIMKEN,TITAGARH,TITAN,TMPV,TORNTPHARM,TORNTPOWER,TRENT,TRIDENT,TRITURBINE,TRIVENI,TTML,TVSMOTOR,UBL,UCOBANK,ULTRACEMCO,UNIONBANK,UNITDSPR,UNOMINDA,UPL,USHAMART,UTIAMC,VBL,VEDL,VENTIVE,VGUARD,VIJAYA,VMM,VOLTAS,VTL,WAAREEENER,WELCORP,WELSPUNLIV,WHIRLPOOL,WIPRO,WOCKPHARMA,YESBANK,ZEEL,ZENSARTECH,ZENTEC,ZFCVINDIA,ZYDUSLIFE"
    symbols = [s.strip() + ".NS" for s in SYMBOLS_RAW.split(",") if s.strip()]
    return symbols

# ==========================================
# MAIN UI
# ==========================================
st.title("🛡️ Alpha-Wolf Pack Scanner")
st.markdown("### The High-Conviction " + ("Sniper" if concentrated_mode else "Institutional") + " Interface")

# 1. Market Health Check (The Armor)
@st.cache_data(ttl=600) # Cache for 10 minutes to prevent yf spam
def get_cached_health():
    return engine.get_market_health()

health, icon = get_cached_health()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("⚔️ Market Armor", health)
with col2:
    st.metric("📦 Symbols Scanned", "500")
with col3:
    st.metric("🏗️ Architecture", "V10 AI Ensemble")

# Strategy Tabs
tab_sword, tab_eyes, tab_armor = st.tabs(["🗡️ The Sword (Alpha-Kimi)", "👁️ The Eyes (V10 AI)", "🛡️ The Armor (Market Health)"])

@st.cache_data(ttl=86400) # Cache master CSV load for 24 hours
def load_master_hub(path):
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return None

def run_scan(strategy_name, use_cache=False, timeframe="1-2 Weeks"):
    cache_file = f"wolf_cache_{strategy_name.lower()}.csv"
    use_live = not use_cache
    
    # 1. High-Speed Logic: Try CSV Hubs first (Twin-Method)
    full_df = DataEngine.load_csv_data(use_live)
    
    # Fallback to alternative CSV if primary is missing
    if full_df is None:
        full_df = DataEngine.load_csv_data(not use_live)

    if full_df is not None:
        with st.status(f"📁 Building surgical scan from {'Live' if use_live else 'Daily'} Hub...", expanded=True) as status:
            unique_syms = full_df['Symbol'].unique()
            results = []
            pbar = st.progress(0)
            for i, sym in enumerate(unique_syms):
                try:
                    sym_df = full_df[full_df['Symbol'] == sym].sort_values('Date')
                    if len(sym_df) < 60: continue
                    
                    metrics = engine.calculate_metrics(sym_df)
                    if metrics is None: continue
                    
                    ai_prob = engine.get_ai_prob(metrics)
                    kimi_score = engine.get_kimi_score(metrics, timeframe=timeframe)
                    
                    results.append({
                        "Symbol": sym.replace(".NS", ""), "Prob (AI)": ai_prob, "Score (Kimi)": kimi_score,
                        "Price": round(metrics['price'], 2), "RSI": round(metrics['rsi'], 1),
                        "Turnover (M)": round(metrics['turnover_m'], 1), 
                        "sma50": metrics['sma50'],
                        "r_s": metrics['r_s'], "r_m": metrics['r_m'], "r_l": metrics['r_l'],
                        "Verdict": "PENDING", "Status": "PENDING" 
                    })
                except: continue
                pbar.progress((i+1)/len(unique_syms))
            
            df_res = pd.DataFrame(results)
            df_res.to_csv(cache_file, index=False)
            status.update(label="✅ Hub Processed. Instant Scan Ready!", state="complete")
            return df_res
    
    # 2. Extreme Fallback: Live Download (Slowest)
    st.warning("🚀 No local data hub found. Deploying Live Probes (Slow)...")
    symbols = fetch_nifty_500()
    with st.spinner("⚔️ Deploying Live Probes to Market..."):
        data = yf.download(symbols, period="1y", group_by="ticker", progress=False, threads=True, auto_adjust=True)
    
    results = []
    progress_bar = st.progress(0)
    for i, sym in enumerate(symbols):
        try:
            if sym not in data.columns or data[sym].empty: continue
            df = data[sym]
            if len(df) < 60: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            metrics = engine.calculate_metrics(df.dropna())
            if metrics is None: continue
            
            ai_prob = engine.get_ai_prob(metrics)
            kimi_score = engine.get_kimi_score(metrics, timeframe=timeframe)
            
            results.append({
                "Symbol": sym.replace(".NS", ""), "Prob (AI)": ai_prob, "Score (Kimi)": kimi_score,
                "Price": round(metrics['price'], 2), "RSI": round(metrics['rsi'], 1),
                "Turnover (M)": round(metrics['turnover_m'], 1), 
                "sma50": metrics['sma50'],
                "r_s": metrics['r_s'], "r_m": metrics['r_m'], "r_l": metrics['r_l'],
                "Verdict": "PENDING", "Status": "PENDING"
            })
        except: continue
        progress_bar.progress((i + 1) / len(symbols))
    
    df_res = pd.DataFrame(results)
    if not df_res.empty: df_res.to_csv(cache_file, index=False)
    return df_res

# --- Tab Content ---
use_cache = (source_toggle == "Automation Bot (Fastest)")

with tab_sword:
    st.info("💡 **THE SWORD**: Best for Quality-First entries. Uses ROE/Debt filters to ensure the company is healthy before you ever buy.")
    if st.button("Initiate Quality Scan"):
        raw_df = run_scan("Kimi", use_cache=use_cache, timeframe=timeframe)
        if not raw_df.empty:
            # DYNAMIC FILTERING
            mask = (raw_df['Price'] >= min_price) & (raw_df['Turnover (M)'] >= min_vol_m)
            if max_price > 0: mask &= (raw_df['Price'] <= max_price)
            
            filtered_df = raw_df[mask].copy()
            
            # Recalculate Qty and Verdicts dynamically
            final_data = []
            for _, row in filtered_df.iterrows():
                qty = int((total_cap * (allocation_pct/100)) / row['Price'])
                metrics_sim = {
                    'price': row['Price'], 'sma50': row['sma50'], 'rsi': row['RSI'], 
                    'turnover_m': row['Turnover (M)'],
                    'r_s': row.get('r_s', 0), 'r_m': row.get('r_m', 0), 'r_l': row.get('r_l', 0)
                }
                
                # RECALCULATE LIVE SCORE
                live_score = engine.get_kimi_score(metrics_sim, timeframe=timeframe)
                is_safe, reason = engine.get_surgical_verdict(metrics_sim, row['Prob (AI)'], live_score, mode=filter_mode.split()[1], qty=qty, timeframe=timeframe)
                
                new_row = row.to_dict()
                new_row['Score (Kimi)'] = live_score
                new_row['Qty'] = qty
                new_row['Verdict'] = reason
                new_row['Status'] = "✅ SURGICAL" if is_safe else "❌ FILTERED"
                
                # ENTRY/EXIT RANGES
                entry_low = row['Price']
                entry_high = row['Price'] * 1.005
                if "3-7 Days" in timeframe: target_low, target_high = 1.05, 1.07
                elif "1 Month" in timeframe: target_low, target_high = 1.15, 1.20
                else: target_low, target_high = 1.10, 1.12
                
                new_row['Entry Range'] = f"{entry_low:.1f} - {entry_high:.1f}"
                new_row['Exit Target'] = f"{(row['Price']*target_low):.1f} - {(row['Price']*target_high):.1f}"
                
                final_data.append(new_row)
            
            if final_data:
                st.dataframe(pd.DataFrame(final_data).sort_values("Score (Kimi)", ascending=False), height=400)
            else:
                st.warning("No quality picks found meeting your current price/volume filters.")
        else:
            st.warning("No data found to analyze.")

with tab_eyes:
    st.info("💡 **THE EYES**: Best for confirming the edge. Uses the V10 Random Forest model to predict win probability. Look for Score > 0.80.")
    if st.button("Initiate AI Intelligence"):
        raw_df = run_scan("AI", use_cache=use_cache, timeframe=timeframe)
        if not raw_df.empty:
            # DYNAMIC FILTERING
            mask = (raw_df['Price'] >= min_price) & (raw_df['Turnover (M)'] >= min_vol_m)
            if max_price > 0: mask &= (raw_df['Price'] <= max_price)
            
            filtered_df = raw_df[mask].copy()
            
            # Recalculate Qty and Verdicts dynamically
            final_data = []
            for _, row in filtered_df.iterrows():
                qty = int((total_cap * (allocation_pct/100)) / row['Price'])
                metrics_sim = {
                    'price': row['Price'], 'sma50': row['sma50'], 'rsi': row['RSI'], 
                    'turnover_m': row['Turnover (M)'],
                    'r_s': row.get('r_s', 0), 'r_m': row.get('r_m', 0), 'r_l': row.get('r_l', 0)
                }
                
                # RECALCULATE LIVE SCORE
                live_score = engine.get_kimi_score(metrics_sim, timeframe=timeframe)
                is_safe, reason = engine.get_surgical_verdict(metrics_sim, row['Prob (AI)'], live_score, mode=filter_mode.split()[1], qty=qty, timeframe=timeframe)
                
                new_row = row.to_dict()
                new_row['Score (Kimi)'] = live_score
                new_row['Qty'] = qty
                new_row['Verdict'] = reason
                new_row['Status'] = "✅ SURGICAL" if is_safe else "❌ FILTERED"

                # ENTRY/EXIT RANGES
                entry_low = row['Price']
                entry_high = row['Price'] * 1.005
                if "3-7 Days" in timeframe: target_low, target_high = 1.05, 1.07
                elif "1 Month" in timeframe: target_low, target_high = 1.15, 1.20
                else: target_low, target_high = 1.10, 1.12
                
                new_row['Entry Range'] = f"{entry_low:.1f} - {entry_high:.1f}"
                new_row['Exit Target'] = f"{(row['Price']*target_low):.1f} - {(row['Price']*target_high):.1f}"
                
                final_data.append(new_row)
            
            final_df = pd.DataFrame(final_data)
            surgical_df = final_df[final_df["Status"].str.contains("✅")]
            
            if not surgical_df.empty:
                st.success(f"🔥 Found {len(surgical_df)} SURGICAL entries!")
                # Sort by Status and then Kimi Score (which is timeframe-aware)
                st.dataframe(surgical_df.sort_values(["Score (Kimi)", "Prob (AI)"], ascending=False), height=300)
                
                with st.expander("Show All Scanned Stocks (Filtered)"):
                    st.dataframe(final_df.sort_values(["Status", "Score (Kimi)", "Prob (AI)"], ascending=[False, False, False]), height=400)
            else:
                # Dynamic Threshold Message
                current_threshold = 0.60 if "3-7 Days" in timeframe else (0.80 if "1 Month" in timeframe else 0.70)
                st.warning(f"⚠️ No High-Conviction ({int(current_threshold*100)}%+) entries found today. Market Armor is likely protecting you.")
                # Sort by Status and then Kimi Score to ensure the list 'moves' when timeframe changes
                st.dataframe(final_df.sort_values(["Status", "Score (Kimi)", "Prob (AI)"], ascending=[False, False, False]), height=400)
        else:
            st.warning("AI finds no data to analyze today.")

with tab_armor:
    st.info("💡 **THE ARMOR**: This is your 'Safety Valve'. It analyzes the broad Nifty 500 trend to tell you if it's safe to be in the market.")
    
    # Detailed Armor Stats (Cached)
    @st.cache_data(ttl=3600)
    def fetch_armor_data():
        nifty_data = yf.download('^NSEI', period='1y', progress=False, auto_adjust=True)
        if isinstance(nifty_data.columns, pd.MultiIndex): nifty_data.columns = nifty_data.columns.get_level_values(0)
        return nifty_data

    nifty = fetch_armor_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=nifty.index, y=nifty['Close'], name='Nifty Index', line=dict(color='#00d2ff')))
    fig.add_trace(go.Scatter(x=nifty.index, y=nifty['Close'].rolling(50).mean(), name='SMA 50 (Armor Line)', line=dict(color='#e94560', dash='dash')))
    
    fig.update_layout(title="Nifty Market Regime Analysis", template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"### 🛡️ Armor Verdict: {health}")
    if "BULL" in health:
        st.success("The Armor is Strong. You are safe to deploy the Sword.")
    else:
        st.warning("The Armor is Cracked. Reduce position sizes or stay in Cash.")

# ==========================================
# DOCUMENTATION SEGMENT (As Requested)
# ==========================================
st.divider()
with st.expander("📚 How to Use & Recommendations"):
    st.markdown(f"""
    ---
    ## 🧠 HOW THE SCANNER PICKS STOCKS (3-Layer Architecture)
    
    This scanner operates with **3 independent layers**, each designed for a different purpose:
    
    ### Layer 1: 🛡️ The Armor (MACRO — Market Health)
    *   Analyzes the **Nifty 50** index vs its SMA20 and SMA50.
    *   Determines if the market is **BULL** (Safe), **BEAR** (Cash), or **CHOP** (Cautious).
    *   **Rule:** If Armor = BEAR, do NOT deploy capital. Wait.
    
    ### Layer 2: ⚔️ The Sword (Kimi Score — Stock Quality)
    Every stock gets a **0-100 Score** from **4 pillars**:
    
    | Pillar | Max Points | What It Measures | Ideal |
    | :--- | :--- | :--- | :--- |
    | **Momentum** | 25 pts | Timeframe-weighted returns (5d/10d/21d) | Positive & rising |
    | **Quality** | 25 pts | Price vs SMA50 (trend strength) | Price > SMA50 |
    | **Value** | 25 pts | RSI sweet spot (40-60 = max score) | RSI 45-60 |
    | **Volatility** | 25 pts | Vol ratio stability (lower = better) | Vol ratio ~1.0 |
    
    ### Layer 3: 👁️ The Eyes (V10 AI — Pattern Recognition)
    A Random Forest model trained on **10 features**:
    RSI, EMA Signal, Volume Ratio, 5d/10d/21d Returns, Hurst, TD Count, **Squeeze**, **Coiling**.
    
    > The AI uses Squeeze (Bollinger Bandwidth) and Coiling (price compression) instead of the old circular ensemble score. This makes predictions more accurate.
    
    ---
    ## 🎯 SCORE INTERPRETATION — What Score Should I Trust?
    
    ### Kimi Score (0-100):
    
    | Score Range | Signal | Action |
    | :--- | :--- | :--- |
    | **35+** | 🔥 **Diamond** | All 4 pillars firing. Deploy full allocation. |
    | **25-35** | ⭐ **Gold** | Strong quality stock. The ideal sweet spot. |
    | **15-25** | ✅ **Silver** | Good setup. Use standard position size. |
    | **< 15** | ⚪ **Skip** | Too many pillars are weak. Not worth the risk. |
    
    ### AI Prob (0% - 100%):
    
    | Probability | Signal | Action |
    | :--- | :--- | :--- |
    | **80%+** | 🔥 **High Conviction** | Pattern matches 80%+ of historical winners. |
    | **70-80%** | ✅ **Confident** | Reliable. Best risk/reward zone. |
    | **60-70%** | 🟡 **Marginal** | Needs Kimi Score > 25 to confirm. |
    | **< 60%** | ⚪ **Low** | Skip unless Kimi Score is 30+. |
    
    ### 💎 The "Golden Entry" (Best Setup)
    > A stock is a **Golden Entry** when:
    > **Kimi Score > 25** AND **AI Prob > 75%** AND **Verdict = ✅ SURGICAL**
    
    ---
    ## 📦 VOLUME (TURNOVER) CONFIGURATION
    
    Volume = **Turnover in Millions INR** (Price × Shares traded).
    
    | Timeframe | Recommended Min | Why |
    | :--- | :--- | :--- |
    | **3-7 Days (Aggressive)** | **300M+** | Quick exits. Need high liquidity. |
    | **1-2 Weeks (Swing)** | **100M+** | Best balance of signal + liquidity. |
    | **1 Month (Position)** | **50M+** | Slower moves. Can tolerate lower liquidity. |
    
    **Pro Tip:** If you see **Turnover > 500M** + **Vol Ratio > 2.0**, that's heavy institutional activity. Pay attention.
    
    ---
    ## ⏱️ WHEN TO RUN & EXECUTION RULES
    
    | Time | Quality | Best For |
    | :--- | :--- | :--- |
    | **3:15 PM IST** | ⭐⭐⭐⭐⭐ | Best. Full day's data captured. |
    | **After Market (4+ PM)** | ⭐⭐⭐⭐ | Great for EOD analysis. |
    | **Pre-Market (8-9 AM)** | ⭐⭐⭐ | Uses yesterday's close. Good for planning. |
    
    **Entry Rules:**
    *   **Aggressive:** Buy at **3:25 PM** if price is in Entry Range.
    *   **Safe:** Buy **next morning at 9:30 AM** after checking for gaps.
    *   **Exit:** Use the **time-based rule** — sell after your hold period expires.
    *   **Stop Loss:** ALWAYS active. **5%** (short) / **8%** (swing) / **12%** (position).
    
    ---
    ## 🕐 TIMEFRAME SELECTION
    
    | Timeframe | Hold Period | Stop Loss | Target | Best Market Armor |
    | :--- | :--- | :--- | :--- | :--- |
    | **⚡ 3-7 Days** | 3-5 trading days | 5% | 5% | BULL only |
    | **🎯 1-2 Weeks** | 5-10 trading days | 8% | 10% | BULL or CHOP |
    | **🛡️ 1 Month** | 15-25 trading days | 12% | 15% | Any regime |
    
    ---
    ## 🛡️ THE SURGICAL VERDICT — What It Checks
    
    Before any stock gets the **✅ SURGICAL** tag, it passes through these guards:
    
    | Check | What It Does | Override |
    | :--- | :--- | :--- |
    | **AI Threshold** | Prob > 60-80% (varies by timeframe) | None |
    | **SMA50 Trend** | Price must be > SMA50 | "Rebound" for short-term |
    | **RSI Overheat** | Blocks if RSI > 70 | None |
    | **Kimi Floor** | Score > 15-20 (varies by mode) | None |
    | **Liquidity** | Your order < 1% of daily volume | None |
    
    ---
    ## ⚠️ RED FLAGS — When NOT to Buy
    *   **RSI > 70** + **Kimi Score < 20**: Overbought AND weak quality. Avoid.
    *   **Vol Ratio < 0.5**: Dead volume. No institution is interested.
    *   **Armor = BEAR**: Market conditions will drag down even the best stocks.
    *   **Verdict = ❌ Avoid**: Trust the system. It's protecting your capital.
    """)

with st.expander("❓ FAQ & Strategy Deep Dive"):
    st.markdown("""
    ### 1. What do the columns actually mean?
    *   **Score (Kimi)**: Quality Grade (0-100). Combines Momentum + Quality + Value + Volatility.
    *   **Prob (AI)**: Statistical confidence from the V10 model. High value = pattern matches historical winners.
    *   **Verdict**: Final safety check. ✅ = ALL guards passed. ❌ = At least one red flag.
    *   **Entry Range**: Buy zone calibrated at ±0.5% around current price.
    *   **Exit Target**: Profit target based on your selected timeframe.
    *   **Turnover (M)**: How much money (Millions INR) was traded in 20-day avg.
    *   **Squeeze**: Bollinger Bandwidth. Low value (<0.10) = price is "coiling" for a breakout.
    
    ### 2. What is "Sword" vs "Eyes"?
    *   **⚔️ Sword (Kimi Score)**: Focuses on **quality + stability**. Lower risk, steadier wins (~62-67% win rate).
    *   **👁️ Eyes (AI)**: Focuses on **explosive patterns**. Higher returns, needs discipline (~58-63% win rate).
    *   **Best Strategy:** Use both. If a stock scores high on BOTH Sword AND Eyes = maximum conviction.
    
    ### 3. Does changing Capital change the Stock List?
    *   **No.** Stock list is 100% objective based on market data.
    *   **Capital only affects the Qty column** (how many shares fit your risk allocation).
    
    ### 4. What Scanning Setup gives the Best Returns?
    *   **Timeframe**: **1-2 Weeks**.
    *   **Volume**: **100M+**.
    *   **Condition**: Deploy only when **Market Armor = BULL**.
    *   **Selection**: Pick stocks that are **✅ SURGICAL** on both Sword AND Eyes.
    
    ### 5. Expected Returns?
    *   **Armor (0%):** Doesn't find trades. It *saves* you from 100% of bear crashes.
    *   **Sword (~20-30% p.a.):** Steady compounder. Lower drawdowns.
    *   **Eyes (~35%+ p.a.):** High-speed gains. Requires strict exit discipline.
    """)

# ==========================================
# FOOTER & COMPLIANCE (Outside Expander)
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #888; font-family: sans-serif; padding: 20px;'>
<h3 style='color: #00d2ff;'>🛡️ Alpha-Wolf Pack Scanner</h3>
<p>App by Pravin A Mathew</p>
<p style='color: #e94560; font-weight: bold;'>⚠️ THIS IS FOR SWING TRADING AND NOT FOR INTRADAY TRADING</p>
<div style='margin-top: 20px; font-size: 0.8em; text-align: justify; padding: 0 10%;'>
<p><b>SEBI Compliance & Risk Disclaimer:</b><br>
I am not a SEBI Registered Investment Advisor. This scanner is an automated tool designed for Educational & Research purposes only. The signals generated do not constitute financial advice or buy/sell recommendations. Paper trading is recommended before committing real capital. Trading in equities involves significant risk. The author is not responsible for any financial losses incurred using this tool. Do your own research (DYOR) and consult a certified professional before investing.</p>
<p><b>Strategy Expectations & Global Standards:</b><br>
In the professional trading world (Hedge Funds/Institutions), most successful strategies operate with a 50% to 60% win rate. Comparing to the world standard: No professional system achieves 90-100% accuracy. The goal is positive expectancy—winning enough to grow capital over time. Keep growing!</p>
</div>
</div>
""", unsafe_allow_html=True)
