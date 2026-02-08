import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import gsheets_plotly as gsplotly

from gsheets_api import authenticate_gsheets, retrieve_gsheets_values
from dataframe_utils import pre_processing
from constants import SPREADSHEET_ID, SPREADSHEET_RANGE, TOTAL_PNL, START_VALUE, TOTAL_PERCENT, LAST_EXIT_DATE

# Carrega as credenciais dos Secrets
creds = authenticate_gsheets(st.secrets["gcp_service_account"])

def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Formulário de login
    with st.form("login"):
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if password == st.secrets["MY_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    return False

if not check_password():
    st.stop() 

##
## Dataframe Pre-Processing
##
@st.cache_data
def get_data_from_google_sheets():

    result = retrieve_gsheets_values(creds, SPREADSHEET_ID, SPREADSHEET_RANGE)

    df = pd.DataFrame(result[1:], columns=result[0])
    
    df = pre_processing(df)

    return df

##
## Streamlit Configurations
##
st.set_page_config(layout='wide',
                   page_title="Controle Cripto",
                   page_icon=":green_heart:")

df = get_data_from_google_sheets()

st.sidebar.header("Configuração de Filtros:")
sb_coins = st.sidebar.multiselect("Criptos", 
                                 options=df['COIN'].unique(),
                                 default=df['COIN'].unique())
sb_category = st.sidebar.selectbox("Categorias", df['TIPO'].unique())


# Main page
st.title(":green_heart: Controle Cripto 💜")
st.markdown("##")



##
## Streamlit Dashboard
##

tabs = st.tabs(['Indicadores', 'Dashboard Estatico', 'Dashboard', 'Insights'])

#############
## METRICS ##
#############
with tabs[0]:
    gsplotly.painel_indicadores(df)


###############
## DASHBOARD ##
##  ESTATICO ##
###############
with tabs[1]:

    gsplotly.histograma(df)

################
## DASHBOARDS ##
################
with tabs[2]:

    gsplotly.performance_diaria(df)

    gsplotly.curva_patrimonio(df)

    fig_tree = px.treemap(df, path=['COIN'], values=df[TOTAL_PNL].abs(),
                        color=TOTAL_PNL, 
                        color_continuous_scale='RdYlGn',
                        title="🌲 Alocação e Performance por Ativo")
    st.plotly_chart(fig_tree, use_container_width=True)

with tabs[3]:

    # --- CÁLCULOS EXISTENTES (Mantidos conforme seu código) ---
    moeda_mais_frequente = df['COIN'].mode()[0]
    total_frequencia = df['COIN'].value_counts().iloc[0]
    trade_max = df.loc[df[TOTAL_PNL].idxmax()]
    trade_min = df.loc[df[TOTAL_PNL].idxmin()]
    ranking_moedas = df.groupby('COIN')[TOTAL_PNL].sum().sort_values(ascending=False)

    # --- NOVOS CÁLCULOS ---
    top_roi_perc = df.loc[df[TOTAL_PERCENT].idxmax()]
    pior_roi_perc = df.loc[df[TOTAL_PERCENT].idxmin()]

    df['DURATION'] = pd.to_datetime(df[LAST_EXIT_DATE]) - pd.to_datetime(df['DATAHORA'])
    trade_mais_longo = df.loc[df['DURATION'].idxmax()]

    df_long = df[df['TIPO'] == 'LONG']
    df_short = df[df['TIPO'] == 'SHORT']

    st.subheader("💡 Insights e Curiosidades")

    # LINHA 1: Resumo Financeiro
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Moeda Favorita", moeda_mais_frequente, f"{total_frequencia} trades")
    c2.metric("🚀 Maior Tacada ($)", trade_max['COIN'], f"$ {trade_max[TOTAL_PNL]:,.2f}")
    c3.metric("📉 Pior Pesadelo ($)", trade_min['COIN'], f"-$ {-1*trade_min[TOTAL_PNL]:,.2f}", delta_color='normal')

    st.divider()

    # LINHA 2: Desempenho Percentual e Tempo (MODIFICADO)
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.write("**🔥 Melhor ROI %**")
        st.write(f"{top_roi_perc['COIN']} ({top_roi_perc[TOTAL_PERCENT]:.2f}%)")
        st.caption(f"Valor: $ {top_roi_perc[TOTAL_PNL]:,.2f}") # Adicionado valor ganho
    with col_p2:
        st.write("**🧊 Pior ROI %**")
        st.write(f"{pior_roi_perc['COIN']} ({pior_roi_perc[TOTAL_PERCENT]:.2f}%)")
        st.caption(f"Valor: $ {pior_roi_perc[TOTAL_PNL]:,.2f}") # Adicionado valor perdido
    with col_p3:
        st.write("**⏳ Trade mais Longo**")
        st.write(f"{trade_mais_longo['COIN']}")
        st.caption(f"Duração: {trade_mais_longo['DURATION']}")

    st.divider()

    # LINHA 3: Estratégia (LONG vs SHORT) (MODIFICADO)
    st.markdown("### ⚖️ Performance por Tipo de Operação")
    l1, l2, s1, s2 = st.columns(4)
    
    if not df_long.empty:
        # Best LONG
        row_l_max = df_long.loc[df_long[TOTAL_PNL].idxmax()]
        l1.info(f"**Best LONG:** {row_l_max['COIN']} \n\n $ {row_l_max[TOTAL_PNL]:,.2f} | {row_l_max[TOTAL_PERCENT]:.2f}%")
        
        # Worst LONG
        row_l_min = df_long.loc[df_long[TOTAL_PNL].idxmin()]
        l2.warning(f"**Worst LONG:** {row_l_min['COIN']} \n\n $ {row_l_min[TOTAL_PNL]:,.2f} | {row_l_min[TOTAL_PERCENT]:.2f}%")
    
    if not df_short.empty:
        # Best SHORT
        row_s_max = df_short.loc[df_short[TOTAL_PNL].idxmax()]
        s1.info(f"**Best SHORT:** {row_s_max['COIN']} \n\n $ {row_s_max[TOTAL_PNL]:,.2f} | {row_s_max[TOTAL_PERCENT]:.2f}%")
        
        # Worst SHORT
        row_s_min = df_short.loc[df_short[TOTAL_PNL].idxmin()]
        s2.warning(f"**Worst SHORT:** {row_s_min['COIN']} \n\n $ {row_s_min[TOTAL_PNL]:,.2f} | {row_s_min[TOTAL_PERCENT]:.2f}%")

    # Ranking Acumulado
    st.divider()
    c4, c5 = st.columns(2)
    c4.success(f"💰 **Porto Seguro:** {ranking_moedas.index[0]} | $ {ranking_moedas.iloc[0]:,.2f}")
    c5.error(f"💸 **Ralo de Dinheiro:** {ranking_moedas.index[-1]} | $ {ranking_moedas.iloc[-1]:,.2f}")