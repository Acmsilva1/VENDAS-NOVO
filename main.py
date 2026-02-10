import os
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import pytz
from supabase import create_client, Client

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_supabase() -> Client:
    return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")

@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")

@app.get("/api/status")
async def api_status():
    try:
        supabase = get_supabase()
        tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        
        # Referências temporais
        hoje = agora.date()
        mes_atual = agora.month
        ano_atual = agora.year

        # EXTRAÇÃO (Baseado nas colunas reais das suas imagens)
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_g = supabase.table("gastos").select("carimbo_data_hora, valor").execute()

        df_v = pd.DataFrame(res_v.data)
        df_g = pd.DataFrame(res_g.data)

        if df_v.empty: return {"erro": "Sem dados de vendas"}

        # Conversão de data
        df_v['dt'] = pd.to_datetime(df_v['carimbo_data_hora']).dt.tz_convert(tz)
        df_g['dt'] = pd.to_datetime(df_g['carimbo_data_hora']).dt.tz_convert(tz)

        # --- LÓGICA DE TRANSPARÊNCIA TOTAL ---
        
        # 1. VISÃO DIÁRIA (Real hoje)
        v_hoje = df_v[df_v['dt'].dt.date == hoje]['valor'].sum()
        g_hoje = df_g[df_g['dt'].dt.date == hoje]['valor'].sum()

        # 2. VISÃO MENSAL (Acumulado do mês)
        v_mes = df_v[(df_v['dt'].dt.month == mes_atual) & (df_v['dt'].dt.year == ano_atual)]['valor'].sum()
        g_mes = df_g[(df_g['dt'].dt.month == mes_atual) & (df_g['dt'].dt.year == ano_atual)]['valor'].sum()

        # 3. VISÃO ANUAL (O "Big Picture")
        v_ano = df_v[df_v['dt'].dt.year == ano_atual]['valor'].sum()
        g_ano = df_g[df_g['dt'].dt.year == ano_atual]['valor'].sum()

        return {
            "diario": {"vendas": float(v_hoje), "gastos": float(g_hoje), "lucro": float(v_hoje - g_hoje)},
            "mensal": {"vendas": float(v_mes), "gastos": float(g_mes), "lucro": float(v_mes - g_mes)},
            "anual": {"vendas": float(v_ano), "gastos": float(g_ano), "lucro": float(v_ano - g_ano)},
            "atualizado_em": agora.strftime("%H:%M:%S")
        }

    except Exception as e:
        return {"erro": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
