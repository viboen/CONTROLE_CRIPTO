
import pandas as pd

from constants import PNL_VALUE_COLS, FEES_COL, TOTAL_PNL, PNL_PERCENT_COLS, TOTAL_PERCENT, LAST_EXIT_DATE

def total_gain(df: pd.DataFrame):
    return int(df.loc[(df[TOTAL_PNL] > 0), TOTAL_PNL].sum())

def total_loss(df: pd.DataFrame):
    return int(df.loc[(df[TOTAL_PNL] < 0), TOTAL_PNL].sum())

def total_fees(df: pd.DataFrame):
    return int(df[FEES_COL].sum())*-1

def total_delta(df: pd.DataFrame):
    return int(total_gain(df) + total_loss(df) + total_fees(df))

def total_trades(df: pd.DataFrame):
    return int(df.shape[0])

def total_trades_gain(df: pd.DataFrame):
    return int(df[(df[TOTAL_PNL] > 0)].shape[0])

def total_trades_loss(df: pd.DataFrame):
    return int(df[(df[TOTAL_PNL] < 0)].shape[0])

def pre_processing(df: pd.DataFrame):

    df = df[df['DATAHORA'] != ""]
    df = df[df['STATUS'] == "FECHADO"]

    df['DATAHORA'] = pd.to_datetime(df['DATAHORA'])
    df['P1 DATE'] = pd.to_datetime(df['P1 DATE'])
    df['P2 DATE'] = pd.to_datetime(df['P2 DATE'])
    df['P3 DATE'] = pd.to_datetime(df['P3 DATE'])
    df['DIA'] = df['DATAHORA'].apply(lambda x: str(x.year) +'-'+ str(x.month).zfill(2) +'-'+ str(x.day).zfill(2))
    
    for col in PNL_VALUE_COLS:
        df[col] = df[col].str.replace('$', '')
        df[col] = df[col].str.replace(',', '')
        df[col] = pd.to_numeric(df[col], downcast='float')

    for col in PNL_PERCENT_COLS:
        df[col] = df[col].str.replace('%', '')
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    for col in ['P1 %', 'P2 %', 'P3 %']:
        df[col] = df[col].str.replace('%', '')
        df[col] = pd.to_numeric(df[col], downcast='float')

    df[TOTAL_PERCENT] = (
        ((df['P1 PNL %'] * df['P1 %'])/100) + 
        ((df['P2 PNL %'] * df['P2 %'])/100) + 
        ((df['P3 PNL %'] * df['P3 %'])/100)
    )

    # Converter para datetime (caso ainda não sejam)
    cols_date = ['P1 DATE', 'P2 DATE', 'P3 DATE']
    for col in cols_date:
        df[col] = pd.to_datetime(df[col])

    # Criar a coluna com a maior data
    df[LAST_EXIT_DATE] = df[cols_date].max(axis=1)

    df[TOTAL_PNL] = df[PNL_VALUE_COLS].sum(axis=1)
    df[FEES_COL] = df[FEES_COL].astype(float)

    df = df.sort_values(['DATAHORA'])

    df.to_csv('CONTROLE_CRIIPTO.csv')

    df = df[['DATAHORA','COIN','TIPO','STATUS','BUY AVG','BUY QNT','BUY CAPITAL',
             'P1 PNL','P1 PNL %',
             'P2 PNL','P2 PNL %',
             'P3 PNL','P3 PNL %',
             'P1 %','P2 %','P3 %',
             LAST_EXIT_DATE,FEES_COL,TOTAL_PNL,TOTAL_PERCENT,'DIA']]

    return df