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
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

@app.get("/api/status")
async def api_status():
    try:
        supabase = get_supabase()
        tz_local = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz_local)
        
        # LGPD: Selecionando apenas o financeiro
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        def processar_base_andre(df):
            if df.empty: return 0, 0, 0
            
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
            # CORREÇÃO DO PANDAS: Removido 'ambivalent' para compatibilidade total
            # Convertendo a data ISO que vimos no seu zoom
            df['dt'] = pd.to_datetime(df['carimbo_data_hora']).dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz_local)
            
            hoje = df[df['dt'].dt.date == agora.date()]['valor'].sum()
            mes = df[df['dt'].dt.month == agora.month]['valor'].sum()
            ano = df[df['dt'].dt.year == agora.year]['valor'].sum()
            
            return hoje, mes, ano

        v_hoje, v_mes, v_ano = processar_base_andre(df_v)
        d_hoje, d_mes, d_ano = processar_base_andre(df_d)

        return {
            "diario": {"vendas": float(v_hoje), "gastos": float(d_hoje), "lucro": float(v_hoje - d_hoje)},
            "mensal": {"vendas": float(v_mes), "gastos": float(d_mes), "lucro": float(v_mes - d_mes)},
            "anual": {"vendas": float(v_ano), "gastos": float(d_ano), "lucro": float(v_ano - d_ano)},
            "debug": {
                "total_vendas": len(df_v),
                "total_despesas": len(df_d)
            }
        }
    except Exception as e:
        return {"erro": f"Erro técnico: {str(e)}"}

@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
