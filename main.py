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

@app.get("/api/status")
async def api_status():
    try:
        supabase = get_supabase()
        tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        
        # 1. BUSCA TOTAL (Lendo as tabelas inteiras)
        # LGPD: Selecionamos apenas valor e data, ignorando nomes e documentos
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        # Processamento de Vendas
        if not df_v.empty:
            df_v['valor'] = pd.to_numeric(df_v['valor'], errors='coerce').fillna(0)
            # Normalização de data para o timezone correto
            df_v['dt'] = pd.to_datetime(df_v['carimbo_data_hora']).dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz)
            
            v_hoje = df_v[df_v['dt'].dt.date == agora.date()]['valor'].sum()
            v_mes = df_v[df_v['dt'].dt.month == agora.month]['valor'].sum()
            v_ano = df_v[df_v['dt'].dt.year == agora.year]['valor'].sum()
        else:
            v_hoje = v_mes = v_ano = 0

        # Processamento de Despesas (Tabela 'despesas' conforme sua imagem)
        if not df_d.empty:
            df_d['valor'] = pd.to_numeric(df_d['valor'], errors='coerce').fillna(0)
            df_d['dt'] = pd.to_datetime(df_d['carimbo_data_hora']).dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz)
            
            d_hoje = df_d[df_d['dt'].dt.date == agora.date()]['valor'].sum()
            d_mes = df_d[df_d['dt'].dt.month == agora.month]['valor'].sum()
            d_ano = df_d[df_d['dt'].dt.year == agora.year]['valor'].sum()
        else:
            d_hoje = d_mes = d_ano = 0

        return {
            "diario": {"vendas": float(v_hoje), "gastos": float(d_hoje), "lucro": float(v_hoje - d_hoje)},
            "mensal": {"vendas": float(v_mes), "gastos": float(d_mes), "lucro": float(v_mes - d_mes)},
            "anual": {"vendas": float(v_ano), "gastos": float(d_ano), "lucro": float(v_ano - d_ano)},
            "timestamp": agora.strftime("%d/%m/%Y %H:%M:%S")
        }

    except Exception as e:
        return {"erro": f"Falha na consolidação: {str(e)}"}

# Rotas de Infraestrutura PWA
@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
