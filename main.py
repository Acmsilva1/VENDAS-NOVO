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

# CORREÇÃO DO BUG: Simplificação da conexão para evitar o erro de 'proxy'
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    # Removendo qualquer configuração extra que possa disparar o erro de argumento inesperado
    return create_client(url, key)

@app.get("/api/status")
async def api_status():
    try:
        supabase = get_supabase()
        tz_local = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz_local)
        
        # LGPD: Seleção focada em dados financeiros, ignorando 'dados_do_comprador'
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        def processar_base_andre(df):
            if df.empty: return 0, 0, 0
            
            # Conversão de valores
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
            # Tratamento da data ISO que vimos na sua imagem
            df['dt'] = pd.to_datetime(df['carimbo_data_hora']).dt.tz_localize('UTC', ambivalent='naive').dt.tz_convert(tz_local)
            
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
                "status": "Conectado",
                "vendas_encontradas": len(df_v)
            }
        }
    except Exception as e:
        # Se o erro de 'proxy' persistir, saberemos exatamente onde
        return {"erro": f"Erro na conexão ou processamento: {str(e)}"}

@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
