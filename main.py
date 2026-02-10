import os
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import pytz
from supabase import create_client, Client
from cachetools import TTLCache

app = FastAPI()
templates = Jinja2Templates(directory="templates")
dashboard_cache = TTLCache(maxsize=1, ttl=300)

def get_supabase() -> Client:
    return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

def processar_dashboard_unificado():
    if "data" in dashboard_cache:
        return dashboard_cache["data"]

    supabase = get_supabase()
    
    # --- [ETL] EXTRAÇÃO SEGURA (LGPD COMPLIANT) ---
    # Selecionamos apenas o necessário. 'dados do comprador' fica no limbo, onde deve estar.
    res_vendas = supabase.table("vendas").select("carimbo_data_hora, produto, valor").execute()
    res_gastos = supabase.table("gastos").select("carimbo_data_hora, produto, quantidade, valor").execute()

    df_vendas = pd.DataFrame(res_vendas.data)
    df_gastos = pd.DataFrame(res_gastos.data)

    if df_vendas.empty: return {"erro": "Sem dados de vendas"}

    # --- [TRANSFORMAÇÃO] PADRONIZAÇÃO DE TIPOS ---
    tz = pytz.timezone('America/Sao_Paulo')
    
    # Supabase retorna timestamptz como string ISO, o pandas resolve bem:
    df_vendas['DT'] = pd.to_datetime(df_vendas['carimbo_data_hora']).dt.tz_convert(tz)
    df_gastos['DT'] = pd.to_datetime(df_gastos['carimbo_data_hora']).dt.tz_convert(tz)
    
    # Datas para filtros
    hoje = datetime.now(tz).date()
    inicio_mes = hoje.replace(day=1)

    # --- [INTELIGÊNCIA] EXPLOSÃO DE PRODUTOS ---
    # Se o 'produto' vier como "Calabresa, Queijo", o código separa e rateia o valor
    df_vendas['PROD_LIST'] = df_vendas['produto'].astype(str).str.split(',')
    df_exploded = df_vendas.explode('PROD_LIST')
    df_exploded['PROD_LIST'] = df_exploded['PROD_LIST'].str.strip().str.upper()
    df_exploded['VAL_UNIT'] = df_vendas['valor'] / df_vendas['PROD_LIST'].transform(len)

    # --- [AUDITORIA] MÉTRICAS MENSAIS & PREDICATIVAS ---
    # Agrupamento para o gráfico histórico
    resumo_m = df_vendas.set_index('DT').resample('ME')['valor'].sum().to_frame(name='vendas')
    gastos_m = df_gastos.set_index('DT').resample('ME')['valor'].sum()
    resumo_m['gastos'] = gastos_m
    resumo_m = resumo_m.fillna(0)
    resumo_m['lucro'] = resumo_m['vendas'] - resumo_m['gastos']
    resumo_m['mes'] = resumo_m.index.strftime('%m/%Y')

    # --- [OPERACIONAL] VISÃO HOJE ---
    v_hoje = df_vendas[df_vendas['DT'].dt.date == hoje]
    g_hoje = df_gastos[df_gastos['DT'].dt.date == hoje]

    resultado = {
        "resumo_hoje": {
            "faturamento": float(v_hoje['valor'].sum()),
            "gastos": float(g_hoje['valor'].sum()),
            "pedidos": len(v_hoje)
        },
        "performance_mes": {
            "faturamento": float(df_vendas[df_vendas['DT'].dt.date >= inicio_mes]['valor'].sum()),
            "gastos": float(df_gastos[df_gastos['DT'].dt.date >= inicio_mes]['valor'].sum())
        },
        "auditoria_mensal": resumo_m.to_dict(orient='records'),
        "ranking_produtos": df_exploded.groupby('PROD_LIST')['VAL_UNIT'].sum().nlargest(5).reset_index().to_dict(orient='records'),
        "ranking_insumos": df_gastos.groupby('produto')['valor'].sum().nlargest(5).reset_index().to_dict(orient='records'),
        "atualizado_em": datetime.now(tz).strftime("%H:%M:%S")
    }

    dashboard_cache["data"] = resultado
    return resultado

@app.get("/api/status")
async def api_status():
    try:
        return processar_dashboard_unificado()
    except Exception as e:
        return {"erro": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
