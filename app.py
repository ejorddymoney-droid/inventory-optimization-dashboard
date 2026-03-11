import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="SupplyChain Pro | IA d'Inventaire",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJECTION CSS (LOOK "STAKENT" DARK UI) ---
st.markdown("""
    <style>
    /* Conteneur principal */
    [data-testid="stAppViewContainer"] {
        background-color: #0D0E12;
    }
    [data-testid="stSidebar"] {
        background-color: #16171D;
        border-right: 1px solid #2D2E36;
    }
    
    /* Style des Cartes KPI - Glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 10px;
    }
    
    /* Typographie */
    h1, h2, h3, p, span, label {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Boutons personnalisés */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        box-shadow: 0px 0px 15px rgba(168, 85, 247, 0.5);
        transform: translateY(-2px);
    }

    /* Tableaux de données */
    div[data-testid="stDataFrame"] {
        background-color: #16171D;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE CALCULS ---
def calculer_metriques_inventaire(df):
    if df.empty: return df
    
    # 1. Valeur de Consommation Annuelle
    df['Valeur_Annuelle'] = df['Demande_Annuelle'] * df['Prix_Unitaire']
    
    # 2. EOQ (Formule de Wilson)
    # Formule : sqrt((2 * D * S) / H)
    df['EOQ'] = np.sqrt((2 * df['Demande_Annuelle'] * df['Cout_Commande']) / 
                        df['Cout_Possession_Unitaire'].replace(0, np.nan))
    df['EOQ'] = df['EOQ'].fillna(0).round(0).astype(int)
    
    # 3. Fréquence de commande
    df['Nombre_Commandes_An'] = (df['Demande_Annuelle'] / df['EOQ'].replace(0, np.nan)).fillna(0).round(1)
    
    # 4. Analyse de Pareto (ABC)
    df = df.sort_values(by='Valeur_Annuelle', ascending=False)
    valeur_totale = df['Valeur_Annuelle'].sum()
    df['Pourcentage_Contribution'] = (df['Valeur_Annuelle'] / valeur_totale) * 100
    df['Pourcentage_Cumulatif'] = df['Pourcentage_Contribution'].cumsum()
    
    def classer_abc(cum_pct):
        if cum_pct <= 80: return 'A (Critique)'
        elif cum_pct <= 95: return 'B (Modéré)'
        else: return 'C (Faible)'
    
    df['Classe_ABC'] = df['Pourcentage_Cumulatif'].apply(classer_abc)
    return df

# --- INITIALISATION DES DONNÉES ---
if 'data' not in st.session_state:
    donnees_initiales = pd.DataFrame([
        {"ID_Article": "X-101", "Nom_Article": "Microprocesseur A1", "Demande_Annuelle": 5000, "Cout_Commande": 120, "Cout_Possession_Unitaire": 15.0, "Prix_Unitaire": 450},
        {"ID_Article": "X-102", "Nom_Article": "Capteur Optique", "Demande_Annuelle": 12000, "Cout_Commande": 45, "Cout_Possession_Unitaire": 2.5, "Prix_Unitaire": 85},
        {"ID_Article": "Y-500", "Nom_Article": "Module de Puissance", "Demande_Annuelle": 800, "Cout_Commande": 250, "Cout_Possession_Unitaire": 45.0, "Prix_Unitaire": 1800},
        {"ID_Article": "Z-001", "Nom_Article": "Câblage Standard", "Demande_Annuelle": 50000, "Cout_Commande": 20, "Cout_Possession_Unitaire": 0.5, "Prix_Unitaire": 12},
        {"ID_Article": "Z-002", "Nom_Article": "Connecteur Plaqué Or", "Demande_Annuelle": 15000, "Cout_Commande": 60, "Cout_Possession_Unitaire": 4.0, "Prix_Unitaire": 35},
    ])
    st.session_state.data = calculer_metriques_inventaire(donnees_initiales)

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ SupplyChain AI")
    st.markdown("---")
    menu = st.radio("NAVIGATION PRINCIPALE", 
                    ["Tableau de Bord", "Éditeur de Stock", "Analyse ABC", "Stratégie EOQ", "Analyses & Conseils"], 
                    index=0)
    
    st.markdown("---")
    st.subheader("Importation / Exportation")
    fichier_charge = st.file_uploader("Charger un CSV Inventaire", type="csv")
    if fichier_charge:
        nouveau_df = pd.read_csv(fichier_charge)
        st.session_state.data = calculer_metriques_inventaire(nouveau_df)
        st.success("Données mises à jour !")

# --- COMPOSANTS UI ---

def carte_kpi(titre, valeur, delta=None):
    """Composant de carte KPI au style Stakent"""
    st.markdown(f"""
        <div class="metric-card">
            <p style="color: #9CA3AF !important; font-size: 0.9rem; margin:0;">{titre}</p>
            <h2 style="color: white !important; margin: 5px 0;">{valeur}</h2>
            {f'<p style="color: #10B981; font-size: 0.8rem; margin:0;">▲ {delta}</p>' if delta else ''}
        </div>
    """, unsafe_allow_html=True)

# --- PAGES ---

if menu == "Tableau de Bord":
    st.title("Vue d'Ensemble de l'Inventaire")
    df = st.session_state.data
    
    # Rangée supérieure : KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        carte_kpi("Valeur Totale du Stock", f"{df['Valeur_Annuelle'].sum():,.0f} €")
    with col2:
        carte_kpi("Articles Actifs (SKU)", f"{len(df)}")
    with col3:
        val_a = df[df['Classe_ABC'].str.contains('A')]['Pourcentage_Contribution'].sum()
        carte_kpi("Concentration Classe A", f"{val_a:.1f}%")
    with col4:
        avg_eoq = df['EOQ'].mean()
        carte_kpi("Taille Moyenne Commande", f"{avg_eoq:.0f} unités")

    # Rangée centrale : Graphiques
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.subheader("Consommation Annuelle par Article")
        fig = px.bar(df, x='Nom_Article', y='Valeur_Annuelle', color='Classe_ABC',
                     labels={'Valeur_Annuelle': 'Valeur (€)', 'Nom_Article': 'Article'},
                     color_discrete_sequence=["#a855f7", "#6366f1", "#4B5563"],
                     template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.subheader("Répartition Valeur ABC")
        fig_pie = px.pie(df, names='Classe_ABC', values='Valeur_Annuelle',
                         color_discrete_sequence=["#a855f7", "#6366f1", "#4B5563"],
                         hole=0.6, template="plotly_dark")
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

elif menu == "Éditeur de Stock":
    st.title("Gestion des Paramètres")
    st.markdown("Modifiez les paramètres ci-dessous pour simuler l'impact sur votre stock.")
    
    df_edite = st.data_editor(st.session_state.data, 
                               column_config={
                                   "ID_Article": "ID",
                                   "Nom_Article": "Désignation",
                                   "Demande_Annuelle": "Demande/An",
                                   "Cout_Commande": "Coût de Commande (€)",
                                   "Cout_Possession_Unitaire": "Coût de Possession/U",
                                   "Prix_Unitaire": "Prix Unitaire (€)"
                               },
                               num_rows="dynamic", use_container_width=True)
    
    if st.button("Appliquer les modifications & Recalculer"):
        st.session_state.data = calculer_metriques_inventaire(df_edite)
        st.success("Calculs mis à jour avec succès !")
        st.rerun()

elif menu == "Analyse ABC":
    st.title("Classification de Pareto (ABC)")
    df = st.session_state.data
    
    # Diagramme de Pareto
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Nom_Article'], y=df['Valeur_Annuelle'], name="Valeur Annuelle", marker_color='#6366f1'))
    fig.add_trace(go.Scatter(x=df['Nom_Article'], y=df['Pourcentage_Cumulatif'], name="% Cumulé", 
                             yaxis="y2", line=dict(color="#a855f7", width=3, shape='spline')))

    fig.update_layout(
        template="plotly_dark",
        yaxis=dict(title="Valeur Annuelle (€)"),
        yaxis2=dict(title="Pourcentage Cumulé (%)", overlaying="y", side="right", range=[0, 105]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df[['ID_Article', 'Nom_Article', 'Valeur_Annuelle', 'Pourcentage_Cumulatif', 'Classe_ABC']], use_container_width=True)

elif menu == "Stratégie EOQ":
    st.title("Optimisation de la Quantité Économique (EOQ)")
    df = st.session_state.data
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("Le modèle EOQ (Wilson) minimise la somme des coûts de possession et des coûts de passation de commande.")
        article_selectionne = st.selectbox("Focus sur un article", df['Nom_Article'].unique())
        infos_item = df[df['Nom_Article'] == article_selectionne].iloc[0]
        
        st.write(f"**Quantité Optimale (EOQ) :** {infos_item['EOQ']} unités")
        st.write(f"**Fréquence de Commande :** {infos_item['Nombre_Commandes_An']} fois / an")
    
    with col2:
        fig_eoq = px.scatter(df, x='Demande_Annuelle', y='EOQ', size='Valeur_Annuelle', 
                             color='Classe_ABC', hover_name='Nom_Article',
                             labels={'Demande_Annuelle': 'Demande Annuelle', 'EOQ': 'Quantité Économique'},
                             template="plotly_dark", title="EOQ vs Échelle de la Demande")
        fig_eoq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_eoq, use_container_width=True)

elif menu == "Analyses & Conseils":
    st.title("Analyse Stratégique IA")
    df = st.session_state.data
    
    # Logique d'insights automatique
    items_a = df[df['Classe_ABC'].str.contains('A')]
    top_item = df.iloc[0]
    
    st.markdown(f"""
    ### 🚩 Observations Critiques
    * **Concentration du Capital :** Vos articles de **Classe A** représentent **{len(items_a)}** références mais immobilisent **{items_a['Pourcentage_Contribution'].sum():.1f}%** de votre valeur annuelle de consommation. 
    * **Risque Majeur :** L'article `{top_item['Nom_Article']}` ({top_item['ID_Article']}) est votre actif le plus coûteux. Une réduction de 10% de son prix d'achat permettrait d'économiser **{top_item['Valeur_Annuelle']*0.1:,.0f} €** par an.
    * **Alerte Efficacité :** Les articles nécessitant plus de 24 commandes par an devraient être renégociés pour réduire les frais administratifs.
    
    ### 💡 Recommandations Stratégiques
    1. **Contrôle Strict :** Instaurer un inventaire tournant hebdomadaire pour les articles de Classe A.
    2. **Optimisation du Stock de Sécurité :** Pour les articles de Classe C comme `{df[df['Classe_ABC'].str.contains('C')].iloc[0]['Nom_Article']}`, vous pouvez augmenter les stocks de sécurité car leur coût de possession est négligeable par rapport au risque de rupture.
    3. **Négociation Fournisseur :** Grouper les commandes pour les articles à coût de passation élevé afin de se rapprocher de l'EOQ théorique.
    """)
