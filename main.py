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
async def get_manifest():
    return FileResponse("manifest.json", media_type="application/json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("sw.js", media_type="application/javascript")

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

        # EXTRAÇÃO (LGPD: Apenas colunas financeiras)
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_g = supabase.table("gastos").select("carimbo_data_hora, valor").execute()

        df_v = pd.DataFrame(res_v.data)
        df_g = pd.DataFrame(res_g.data)

        if df_v.empty:
            return {"erro": "Tabela de vendas retornou vazia do Supabase"}

        # --- LIMPEZA DE DADOS (The Data Fix) ---
        # Garante que 'valor' seja número e trata datas
        df_v['valor'] = pd.to_numeric(df_v['valor'], errors='coerce').fillna(0)
        df_g['valor'] = pd.to_numeric(df_g['valor'], errors='coerce').fillna(0)
        
        # Converter para datetime e forçar fuso horário
        df_v['dt'] = pd.to_datetime(df_v['carimbo_data_hora']).dt.tz_convert(tz)
        if not df_g.empty:
            df_g['dt'] = pd.to_datetime(df_g['carimbo_data_hora']).dt.tz_convert(tz)

        # 1. CÁLCULO DIÁRIO (Usando .date() para comparação direta)
        v_dia = df_v[df_v['dt'].dt.date == hoje]['valor'].sum()
        g_dia = df_g[df_g['dt'].dt.date == hoje]['valor'].sum() if not df_g.empty else 0

        # 2. CÁLCULO MENSAL
        v_mes = df_v[(df_v['dt'].dt.month == mes_atual) & (df_v['dt'].dt.year == ano_atual)]['valor'].sum()
        g_mes = df_g[(df_g['dt'].dt.month == mes_atual) & (df_g['dt'].dt.year == ano_atual)]['valor'].sum() if not df_g.empty else 0

        # 3. CÁLCULO ANUAL
        v_ano = df_v[df_v['dt'].dt.year == ano_atual]['valor'].sum()
        g_ano = df_g[df_g['dt'].dt.year == ano_atual]['valor'].sum() if not df_g.empty else 0
        
        # 4. TOTAL HISTÓRICO (Para debug)
        v_total = df_v['valor'].sum()
        g_total = df_g['valor'].sum()

        return {
            "diario": {"vendas": float(v_dia), "gastos": float(g_dia), "lucro": float(v_dia - g_dia)},
            "mensal": {"vendas": float(v_mes), "gastos": float(g_mes), "lucro": float(v_mes - g_mes)},
            "anual": {"vendas": float(v_ano), "gastos": float(g_ano), "lucro": float(v_ano - g_ano)},
            "total_geral": {"vendas": float(v_total), "gastos": float(g_total)},
            "atualizado_em": agora.strftime("%H:%M:%S")
        }

    except Exception as e:
        return {"erro": f"Erro na lógica: {str(e)}"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
