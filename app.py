import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="SupplyChain Pro | Inventory AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJECTION CSS POUR LE LOOK "STAKENT" (DARK UI) ---
st.markdown("""
    <style>
    /* Global Theme Overrides */
    [data-testid="stAppViewContainer"] {
        background-color: #0D0E12;
    }
    [data-testid="stSidebar"] {
        background-color: #16171D;
        border-right: 1px solid #2D2E36;
    }
    
    /* Card Style - Glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 10px;
    }
    
    /* Typography */
    h1, h2, h3, p, span {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom Sidebar styling */
    .stRadio > div {
        background-color: transparent !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        box-shadow: 0px 0px 15px rgba(168, 85, 247, 0.5);
        transform: translateY(-2px);
    }

    /* Editable Dataframe overrides */
    div[data-testid="stDataFrame"] {
        background-color: #16171D;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE CALCULS ---
def calculate_supply_chain_metrics(df):
    if df.empty: return df
    
    # 1. Valeur Annuelle
    df['Valeur_Annuelle'] = df['Demande_Annuelle'] * df['Prix_Unitaire']
    
    # 2. EOQ (Wilson Formula)
    df['EOQ'] = np.sqrt((2 * df['Demande_Annuelle'] * df['Cout_Commande']) / 
                        df['Cout_Possession_Unitaire'].replace(0, np.nan))
    df['EOQ'] = df['EOQ'].fillna(0).round(0).astype(int)
    
    # 3. Fréquence
    df['Nombre_Commandes_An'] = (df['Demande_Annuelle'] / df['EOQ'].replace(0, np.nan)).fillna(0).round(1)
    
    # 4. Pareto ABC
    df = df.sort_values(by='Valeur_Annuelle', ascending=False)
    total_value = df['Valeur_Annuelle'].sum()
    df['Pourcentage_Contribution'] = (df['Valeur_Annuelle'] / total_value) * 100
    df['Pourcentage_Cumulatif'] = df['Pourcentage_Contribution'].cumsum()
    
    def classify(cum_pct):
        if cum_pct <= 80: return 'A (Critique)'
        elif cum_pct <= 95: return 'B (Moyen)'
        else: return 'C (Faible)'
    
    df['Classe_ABC'] = df['Pourcentage_Cumulatif'].apply(classify)
    return df

# --- INITIALISATION DES DONNÉES ---
if 'data' not in st.session_state:
    initial_data = pd.DataFrame([
        {"Article_ID": "X-101", "Nom_Article": "Microchip A1", "Demande_Annuelle": 5000, "Cout_Commande": 120, "Cout_Possession_Unitaire": 15.0, "Prix_Unitaire": 450},
        {"Article_ID": "X-102", "Nom_Article": "Capteur Optique", "Demande_Annuelle": 12000, "Cout_Commande": 45, "Cout_Possession_Unitaire": 2.5, "Prix_Unitaire": 85},
        {"Article_ID": "Y-500", "Nom_Article": "Module Puissance", "Demande_Annuelle": 800, "Cout_Commande": 250, "Cout_Possession_Unitaire": 45.0, "Prix_Unitaire": 1800},
        {"Article_ID": "Z-001", "Nom_Article": "Câblage Standard", "Demande_Annuelle": 50000, "Cout_Commande": 20, "Cout_Possession_Unitaire": 0.5, "Prix_Unitaire": 12},
        {"Article_ID": "Z-002", "Nom_Article": "Connecteur Gold", "Demande_Annuelle": 15000, "Cout_Commande": 60, "Cout_Possession_Unitaire": 4.0, "Prix_Unitaire": 35},
    ])
    st.session_state.data = calculate_supply_chain_metrics(initial_data)

# --- SIDEBAR (STYLE STAKENT) ---
with st.sidebar:
    st.title("🛡️ SupplyChain AI")
    st.markdown("---")
    menu = st.radio("MAIN NAVIGATION", 
                    ["Dashboard", "Inventory Editor", "ABC Analysis", "EOQ Strategy", "Insights"], 
                    index=0)
    
    st.markdown("---")
    st.subheader("Import / Export")
    uploaded_file = st.file_uploader("Upload Inventory CSV", type="csv")
    if uploaded_file:
        new_df = pd.read_csv(uploaded_file)
        st.session_state.data = calculate_supply_chain_metrics(new_df)
        st.success("Data Updated!")

# --- UI COMPONENTS ---

def kpi_card(label, value, delta=None, color="#6366f1"):
    """Composant de carte KPI personnalisée pour le look Stakent"""
    st.markdown(f"""
        <div class="metric-card">
            <p style="color: #9CA3AF !important; font-size: 0.9rem; margin:0;">{label}</p>
            <h2 style="color: white !important; margin: 5px 0;">{value}</h2>
            {f'<p style="color: #10B981; font-size: 0.8rem; margin:0;">▲ {delta}</p>' if delta else ''}
        </div>
    """, unsafe_allow_html=True)

# --- PAGES ---

if menu == "Dashboard":
    st.title("Executive Inventory Overview")
    df = st.session_state.data
    
    # Top Row KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Total Inventory Value", f"${df['Valeur_Annuelle'].sum():,.0f}")
    with col2:
        kpi_card("Active SKU Count", f"{len(df)} Items")
    with col3:
        a_val = df[df['Classe_ABC'].str.contains('A')]['Pourcentage_Contribution'].sum()
        kpi_card("Class A Concentration", f"{a_val:.1f}%")
    with col4:
        avg_eoq = df['EOQ'].mean()
        kpi_card("Avg Order Size (EOQ)", f"{avg_eoq:.0f} units")

    # Middle Row - Large Charts
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.subheader("Annual Consumption by Article")
        fig = px.bar(df, x='Nom_Article', y='Valeur_Annuelle', color='Classe_ABC',
                     color_discrete_sequence=["#a855f7", "#6366f1", "#4B5563"],
                     template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                          margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.subheader("ABC Value Split")
        fig_pie = px.pie(df, names='Classe_ABC', values='Valeur_Annuelle',
                         color_discrete_sequence=["#a855f7", "#6366f1", "#4B5563"],
                         hole=0.6, template="plotly_dark")
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

elif menu == "Inventory Editor":
    st.title("Data Management")
    st.markdown("Edit your inventory parameters below to simulate changes.")
    
    edited_df = st.data_editor(st.session_state.data, 
                               column_config={
                                   "Article_ID": "ID",
                                   "Nom_Article": "Item Name",
                                   "Demande_Annuelle": "Annual Demand",
                                   "Cout_Commande": "Order Cost ($)",
                                   "Cout_Possession_Unitaire": "Holding Cost/Unit",
                                   "Prix_Unitaire": "Unit Price ($)"
                               },
                               num_rows="dynamic", use_container_width=True)
    
    if st.button("Apply Changes & Re-Calculate"):
        st.session_state.data = calculate_supply_chain_metrics(edited_df)
        st.rerun()

elif menu == "ABC Analysis":
    st.title("Pareto (ABC) Classification")
    df = st.session_state.data
    
    # Pareto Chart
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Nom_Article'], y=df['Valeur_Annuelle'], name="Annual Value", marker_color='#6366f1'))
    fig.add_trace(go.Scatter(x=df['Nom_Article'], y=df['Pourcentage_Cumulatif'], name="% Cumulative", 
                             yaxis="y2", line=dict(color="#a855f7", width=3, shape='spline')))

    fig.update_layout(
        template="plotly_dark",
        yaxis=dict(title="Annual Value ($)"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df[['Article_ID', 'Nom_Article', 'Valeur_Annuelle', 'Pourcentage_Cumulatif', 'Classe_ABC']], use_container_width=True)

elif menu == "EOQ Strategy":
    st.title("Economic Order Quantity Optimization")
    df = st.session_state.data
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("The EOQ model minimizes the sum of holding costs and ordering costs.")
        selected_item = st.selectbox("Detailed Focus", df['Nom_Article'].unique())
        item_data = df[df['Nom_Article'] == selected_item].iloc[0]
        
        st.write(f"**EOQ:** {item_data['EOQ']} units")
        st.write(f"**Orders / Year:** {item_data['Nombre_Commandes_An']}")
    
    with col2:
        fig_eoq = px.scatter(df, x='Demande_Annuelle', y='EOQ', size='Valeur_Annuelle', 
                             color='Classe_ABC', hover_name='Nom_Article',
                             template="plotly_dark", title="EOQ vs Demand Scale")
        fig_eoq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_eoq, use_container_width=True)

elif menu == "Insights":
    st.title("AI Business Insights")
    df = st.session_state.data
    
    # Logic based insights
    a_items = df[df['Classe_ABC'].str.contains('A')]
    top_item = df.iloc[0]
    
    st.markdown(f"""
    ### 🚩 Critical Observations
    * **Inventory Concentration:** Your **Class A** items represent **{len(a_items)}** SKUs but account for **{a_items['Pourcentage_Contribution'].sum():.1f}%** of your total capital tie-up. 
    * **Highest Risk:** `{top_item['Nom_Article']}` ({top_item['Article_ID']}) is your most valuable asset. A 10% reduction in its lead time or unit price would save **${top_item['Valeur_Annuelle']*0.1:,.0f}** annually.
    * **Efficiency Alert:** Items requiring more than 24 orders per year may benefit from bulk negotiation to reduce ordering frequency.
    
    ### 💡 Recommendations
    1. **Strict Monitoring:** Implement weekly cycle counting for Class A items.
    2. **Buffer Optimization:** Class C items like `{df[df['Classe_ABC'].str.contains('C')].iloc[0]['Nom_Article']}` should have higher safety stocks since their holding cost is negligible.
    3. **Vendor Consolidation:** Group orders for items with high ordering costs to optimize the EOQ.
    """)
