import streamlit as st
import json
import os
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE E COSTANTI ---
API_KEY = "" # Gestito dall'ambiente
DB_FILE = "ideas_db.json"

# Configurazione Pagina Streamlit
st.set_page_config(
    page_title="IdeaFlow - Incubatore di Idee",
    page_icon="🚀",
    layout="wide"
)

# --- FUNZIONI DI SUPPORTO (DATA PERSISTENCE) ---
def load_ideas():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_ideas(ideas):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, indent=4)

# --- INTEGRAZIONE AI ---
def get_ai_analysis(idea):
    """Chiama l'API Gemini per analizzare l'idea imprenditoriale."""
    prompt = f"""
    Analizza questa idea imprenditoriale:
    Titolo: {idea['title']}
    Descrizione: {idea.get('description', '')}
    Problema: {idea['problem']}
    Soluzione: {idea['solution']}
    
    Fornisci una risposta in formato JSON puro (senza markdown) con questi campi:
    1. "market_trends": breve analisi dei trend.
    2. "risks": lista di 3 rischi principali (Test del Cimitero).
    3. "naming": lista di 3 nomi creativi.
    4. "steps": lista delle prime 3 azioni da fare.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        result = response.json()
        return json.loads(result['candidates'][0]['content']['parts'][0]['text'])
    except Exception as e:
        st.error(f"Errore durante l'analisi AI: {e}")
        return None

# --- UI PRINCIPALE ---
def main():
    # Inizializzazione stato
    if "ideas" not in st.session_state:
        st.session_state.ideas = load_ideas()

    # Sidebar per la navigazione
    st.sidebar.title("🚀 IdeaFlow")
    menu = st.sidebar.radio("Navigazione", ["Dashboard", "Aggiungi Idea", "Archivio Idee"])

    if menu == "Dashboard":
        render_dashboard()
    elif menu == "Aggiungi Idea":
        render_add_idea()
    elif menu == "Archivio Idee":
        render_archive()

def render_dashboard():
    st.title("📊 Panoramica Incubatore")
    
    if not st.session_state.ideas:
        st.info("Non ci sono ancora idee. Inizia aggiungendone una dal menu laterale!")
        return

    # Calcolo statistiche
    df = pd.DataFrame(st.session_state.ideas)
    best_idea = df.loc[df['score'].astype(float).idxmax()]

    col1, col2, col3 = st.columns(3)
    col1.metric("Idee Totali", len(df))
    col2.metric("Punteggio Top", f"{best_idea['score']}")
    col3.metric("Migliore Opportunità", best_idea['title'])

    st.divider()
    
    # Grafico comparativo
    st.subheader("Confronto Punteggi ICE")
    df_chart = df[['title', 'score']].copy()
    df_chart['score'] = df_chart['score'].astype(float)
    st.bar_chart(df_chart.set_index('title'))

def render_add_idea():
    st.title("💡 Nuova Idea Imprenditoriale")
    
    with st.form("idea_form"):
        title = st.text_input("Titolo dell'Idea", placeholder="E.g. Food Delivery per celiaci")
        
        col1, col2 = st.columns(2)
        with col1:
            problem = st.text_area("Il Problema", placeholder="Qual è il dolore che risolvi?")
        with col2:
            solution = st.text_area("La Soluzione", placeholder="Come intendi risolverlo?")
            
        st.markdown("### 📈 Validazione ICE (Punteggio 1-10)")
        c1, c2, c3 = st.columns(3)
        impact = c1.slider("Impatto (Valore)", 1, 10, 5)
        confidence = c2.slider("Fiducia (Successo)", 1, 10, 5)
        ease = c3.slider("Facilità (Esecuzione)", 1, 10, 5)
        
        submitted = st.form_submit_button("Salva Idea")
        
        if submitted:
            if title and problem and solution:
                score = (impact * confidence * ease) / 10
                new_idea = {
                    "id": len(st.session_state.ideas) + 1,
                    "title": title,
                    "problem": problem,
                    "solution": solution,
                    "impact": impact,
                    "confidence": confidence,
                    "ease": ease,
                    "score": score,
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "ai_analysis": None
                }
                st.session_state.ideas.append(new_idea)
                save_ideas(st.session_state.ideas)
                st.success("Idea salvata con successo!")
            else:
                st.warning("Compila tutti i campi obbligatori.")

def render_archive():
    st.title("📂 Archivio Idee")
    
    if not st.session_state.ideas:
        st.write("L'archivio è vuoto.")
        return

    # Selettore idea
    idea_titles = [i['title'] for i in st.session_state.ideas]
    selected_title = st.selectbox("Seleziona un'idea per i dettagli", idea_titles)
    
    # Trova l'idea selezionata
    idea = next(item for item in st.session_state.ideas if item["title"] == selected_title)

    col_title, col_action = st.columns([3, 1])
    with col_title:
        st.header(f"{idea['title']}")
        st.caption(f"Creata il {idea['date']} | Score ICE: **{idea['score']}**")
    
    with col_action:
        if st.button("🧠 Avvia Analisi AI", use_container_width=True):
            with st.spinner("L'AI Co-Founder sta analizzando..."):
                analysis = get_ai_analysis(idea)
                if analysis:
                    # Aggiorna lo stato e il file
                    for idx, i in enumerate(st.session_state.ideas):
                        if i['title'] == selected_title:
                            st.session_state.ideas[idx]['ai_analysis'] = analysis
                    save_ideas(st.session_state.ideas)
                    st.rerun()

    tab1, tab2 = st.tabs(["Dettagli Progetto", "Analisi AI Co-Founder"])
    
    with tab1:
        st.subheader("Problema")
        st.write(idea['problem'])
        st.subheader("Soluzione")
        st.write(idea['solution'])
        
        st.divider()
        st.subheader("Metriche ICE")
        st.json({
            "Impatto": idea['impact'],
            "Fiducia": idea['confidence'],
            "Facilità": idea['ease']
        })

    with tab2:
        if idea.get('ai_analysis'):
            ai = idea['ai_analysis']
            
            c1, c2 = st.columns(2)
            with c1:
                st.error("⚠️ Test del Cimitero (Rischi)")
                for risk in ai['risks']:
                    st.write(f"- {risk}")
            
            with c2:
                st.success("✅ Prossimi Passi")
                for step in ai['steps']:
                    st.write(f"- {step}")
            
            st.divider()
            st.info(f"💡 **Trend di Mercato:** {ai['market_trends']}")
            
            st.subheader("🏷️ Suggerimenti Nomi")
            st.write(", ".join(ai['naming']))
        else:
            st.info("Clicca sul pulsante 'Avvia Analisi AI' per generare approfondimenti strategici.")

if __name__ == "__main__":
    main()
