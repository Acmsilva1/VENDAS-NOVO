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
        
        # LGPD: Selecionamos apenas valor e data
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        def processar_df(df):
            if df.empty: return 0, 0, 0, 0
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            # A mágica está aqui: converter garantindo que o Pandas entenda o formato ISO do Supabase
            df['dt'] = pd.to_datetime(df['carimbo_data_hora'], errors='coerce').dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz)
            
            hoje = df[df['dt'].dt.date == agora.date()]['valor'].sum()
            mes = df[df['dt'].dt.month == agora.month]['valor'].sum()
            ano = df[df['dt'].dt.year == agora.year]['valor'].sum()
            total = df['valor'].sum()
            return hoje, mes, ano, total

        v_hoje, v_mes, v_ano, v_total = processar_df(df_v)
        d_hoje, d_mes, d_ano, d_total = processar_df(df_d)

        return {
            "diario": {"vendas": float(v_hoje), "gastos": float(d_hoje), "lucro": float(v_hoje - d_hoje)},
            "mensal": {"vendas": float(v_mes), "gastos": float(d_mes), "lucro": float(v_mes - d_mes)},
            "anual": {"vendas": float(v_ano), "gastos": float(d_ano), "lucro": float(v_ano - d_ano)},
            "acumulado_total": {"vendas": float(v_total), "gastos": float(d_total)},
            "debug": {"linhas_vendas": len(df_v), "data_servidor": agora.strftime("%Y-%m-%d")}
        }
    except Exception as e:
        return {"erro": str(e)}

@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
