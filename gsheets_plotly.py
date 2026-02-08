import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots

from constants import TOTAL_PNL, PNL_VALUE_COLS, FEES_COL, START_VALUE
import streamlit as st
import dataframe_utils

##  PAINEL INDICADORES
##
def painel_indicadores(df):

    ## Fig_1 = Total de Gasto Mensal
    ##
    
    total_gain = dataframe_utils.total_gain(df)
    total_loss = dataframe_utils.total_loss(df)
    total_fees = dataframe_utils.total_fees(df)
    total_delta = dataframe_utils.total_delta(df)
    current_value = START_VALUE + dataframe_utils.total_delta(df)
    total_trades = dataframe_utils.total_trades(df)
    total_trades_gain = dataframe_utils.total_trades_gain(df)
    total_trades_loss = dataframe_utils.total_trades_loss(df)
    hit_ratio = round((dataframe_utils.total_trades_gain(df)/dataframe_utils.total_trades(df))*100, 2)
    avg_gain = round(dataframe_utils.total_gain(df)/dataframe_utils.total_trades_gain(df), 2)
    avg_loss = round(dataframe_utils.total_loss(df)/dataframe_utils.total_trades_loss(df), 2)

    # Estilo dos Cards (CSS simples)
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 28px; }
        div.stMetric {
            background-color: #f8f9fb;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e6e9ef;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("💰 Resumo Financeiro")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Start Value", f"$ {START_VALUE:,.2f}")
    c2.metric("Current Value", f"$ {current_value:,.2f}", f"{total_delta:,.2f}")
    c3.metric("Total Gain", f"$ {total_gain:,.2f}", delta_color="normal")
    c4.metric("Total Loss", f"$ {-total_loss-total_fees:,.2f}", f"Fees: {total_fees:,.2f}", delta_color="inverse")

    st.divider()

    st.subheader("📊 Performance Operacional")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total Trades", total_trades)
    c6.metric("Taxa de Acerto", f"{hit_ratio}%")
    c7.metric("Trades Gain", total_trades_gain)
    c8.metric("Trades Loss", total_trades_loss)

    st.divider()

    st.subheader("📈 Médias e Custos")
    c9, c10, c11, c12 = st.columns(4)
    c9.metric("Avg Gain", f"$ {avg_gain:,.2f}")
    c10.metric("Avg Loss", f"$ {avg_loss:,.2f}")

## GRAFICO: HISTOGRAMA
##
def histograma(df: pd.DataFrame):

    # --- HISTOGRAMA DE GANHOS E PERDAS ---
    st.divider()
    st.subheader("📊 Distribuição de Ganhos e Perdas (Histograma)")

    # Criando uma coluna temporária para as cores (Verde para ganho, Vermelho para perda)
    # Usamos uma cópia para não afetar o DF original permanentemente
    df_hist = df.copy()
    df_hist['Resultado'] = df_hist[TOTAL_PNL].apply(lambda x: 'Ganho' if x >= 0 else 'Perda')

    fig_hist = px.histogram(
        df_hist,
        x=TOTAL_PNL,
        nbins=40, # Ajuste a densidade das barras aqui
        color='Resultado',
        color_discrete_map={'Ganho': "#15CF3E", 'Perda': '#ff4b4b'}, # Cores combinando com seu dash
        opacity=0.8,
        labels={TOTAL_PNL: 'Lucro/Prejuízo ($)', 'count': 'Frequência de Trades'},
        template="plotly_dark"
    )

    # Melhorando o visual do Histograma
    fig_hist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.1, # Espaço entre as barras
        showlegend=True,
        xaxis=dict(showgrid=False, zeroline=True, zerolinecolor='white'),
        yaxis=dict(showgrid=True, gridcolor="#222"),
        height=400
    )

    # Adiciona linha vertical no zero para destacar o divisor
    fig_hist.add_vline(x=0, line_dash="solid", line_color="white", line_width=1)

    st.plotly_chart(fig_hist, use_container_width=True)

## GRAFICO: PERFORMANCE DIARIA
##
def performance_diaria(df):
    
    st.divider()
    st.subheader("📈 Performance Diária (Net Gain/Loss)")

    # 1. Agrupar os dados por dia (certifique-se que a coluna de data esteja em datetime)
    # Aqui calculamos o Delta diário (Ganhos - Perdas - Taxas)
    df_diario = df.groupby(df['DATAHORA'].dt.date)[TOTAL_PNL].sum().reset_index()

    # 2. Definir as cores: Verde se > 0, Vermelho se < 0
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in df_diario[TOTAL_PNL]]

    # 3. Criar o gráfico de barras
    fig_daily = go.Figure(data=[
        go.Bar(
            x=df_diario['DATAHORA'],
            y=df_diario[TOTAL_PNL],
            marker_color=colors,
            hovertemplate="Data: %{x}<br>Resultado: $ %{y:,.2f}<extra></extra>"
        )
    ])

    # 4. Ajustar o layout para o modo escuro/limpo
    fig_daily.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis=dict(showgrid=False, title="DIA"),
        yaxis=dict(showgrid=True, gridcolor="#222", title="Resultado ($)"),
        height=450
    )

    # 5. Mostrar no Streamlit
    st.plotly_chart(fig_daily, use_container_width=True)

## GRAFICO: CURVA PATRIMONIO
##
def curva_patrimonio(df: pd.DataFrame):
    
    st.divider()
    st.subheader("📈 Curva de Patrimônio (Equity Curve)")

    # Agrupando por dia e somando o resultado (delta)
    df_diario = df.groupby(df['DATAHORA'].dt.date)[TOTAL_PNL].sum().reset_index()
    
    # Calculando a evolução acumulada
    df_diario['cum_delta'] = df_diario[TOTAL_PNL].cumsum()
    df_diario['current_value_evo'] = START_VALUE + df_diario['cum_delta']

    # 1. Criando o gráfico de linha
    fig_linha = go.Figure()

    fig_linha.add_trace(go.Scatter(
        x=df_diario['DATAHORA'],
        y=df_diario['current_value_evo'],
        mode='lines+markers',
        name='Patrimônio',
        line=dict(color='#00d4ff', width=3),
        marker=dict(size=8, symbol='circle'),
        fill='tozeroy', # Adiciona um preenchimento leve abaixo da linha
        fillcolor='rgba(0, 212, 255, 0.1)',
        hovertemplate="Data: %{x}<br>Patrimônio: $ %{y:,.2f}<extra></extra>"
    ))

    # 2. Configurações de Layout
    fig_linha.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", # Mostra o valor de todos os traces ao passar o mouse no eixo X
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True, 
            gridcolor="#222", 
            tickprefix="$ ",
            # Ajusta o range para não ficar "colado" no fundo
            range=[df_diario['current_value_evo'].min() * 0.98, df_diario['current_value_evo'].max() * 1.02]
        ),
        height=450
    )

    # 3. Adicionar linha horizontal de "Break-even" (Capital Inicial)
    fig_linha.add_hline(
        y=START_VALUE, 
        line_dash="dash", 
        line_color="gray", 
        annotation_text="Start", 
        annotation_position="bottom right"
    )

    st.plotly_chart(fig_linha, use_container_width=True)

##
##  HEADER
##
def charts_header_1(df, hcol):

    ## Fig = Total de GAIN
    ##

    # Mask: WHERE VALUE <= 0
    # GROUP
    df_gain = df.copy()
    for col in PNL_VALUE_COLS:
        df_gain.loc[df_gain[col] < 0, col] = 0
    df_gain = df_gain.groupby('STATUS')[PNL_VALUE_COLS].sum()
    df_gain['VALUE'] = df_gain.sum(axis=1)
    df_gain = df_gain.reset_index()
    df_gain['COLOR'] = 'Total_Gain'

    # Mask: WHERE VALUE >= 0
    # GROUP
    df_loss = df.copy()
    for col in PNL_VALUE_COLS:
        df_loss.loc[df_loss[col] > 0, col] = 0
    df_loss = df_loss.groupby('STATUS')[PNL_VALUE_COLS].sum()
    df_loss['VALUE'] = df_loss.sum(axis=1)
    df_loss['VALUE'] = df_loss['VALUE']*-1
    df_loss = df_loss.reset_index()
    df_loss['COLOR'] = 'Total_Loss'

    # FEES
    df_fees = df.copy()
    df_fees[FEES_COL] = df_fees[FEES_COL].astype(float)
    df_fees = df_fees.groupby('STATUS')[FEES_COL].sum()
    df_fees = df_fees.reset_index()
    df_fees.rename(columns={FEES_COL: 'VALUE'}, inplace=True)
    df_fees['COLOR'] = 'Total_Fees'

    

    df_chart = pd.concat([df_gain[['STATUS', 'VALUE', 'COLOR']], df_loss[['STATUS', 'VALUE', 'COLOR']], df_fees])

    fig = px.bar(df_chart, 
                   y='STATUS', 
                   x='VALUE', 
                   color='COLOR', text_auto=True, barmode='stack', orientation='h',
                   color_discrete_map={
                       'Total_Gain': 'green',
                       'Total_Loss': 'red',
                       'Total_Fees': 'darkred'})
    fig.update_xaxes(showticklabels=False, title=None)
    fig.update_yaxes(showticklabels=False, title=None)
    fig.update_layout(showlegend=False, margin=dict(t=100, b=100, pad=100))
    fig.update_traces(width=.3, textfont_size=20)
    hcol.plotly_chart(fig, use_container_width=True, showlegend="false")



