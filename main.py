import os
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import pytz
from supabase import create_client, Client

app = FastAPI()

# Definição do caminho base para evitar o erro 404
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

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
        
        # LGPD: Selecionando apenas o financeiro e produtos
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor, produto").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        def contar_unidades_reais(df_subset):
            if df_subset.empty: return 0
            # Pipeline que entende a vírgula como separador de itens
            return df_subset['produto'].apply(lambda x: len(str(x).split(',')) if pd.notnull(x) else 0).sum()

        def processar_base(df, is_venda=False):
            if df.empty: return 0, 0, 0, 0, 0, 0
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df['dt'] = pd.to_datetime(df['carimbo_data_hora']).dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz_local)
            
            df_hoje = df[df['dt'].dt.date == agora.date()]
            df_mes = df[df['dt'].dt.month == agora.month]
            df_ano = df[df['dt'].dt.year == agora.year]
            
            q_hoje = contar_unidades_reais(df_hoje) if is_venda else len(df_hoje)
            q_mes = contar_unidades_reais(df_mes) if is_venda else len(df_mes)
            q_ano = contar_unidades_reais(df_ano) if is_venda else len(df_ano)
            
            return (float(df_hoje['valor'].sum()), int(q_hoje),
                    float(df_mes['valor'].sum()), int(q_mes),
                    float(df_ano['valor'].sum()), int(q_ano))

        v_h, q_h, v_m, q_m, v_a, q_a = processar_base(df_v, is_venda=True)
        d_h, _, d_m, _, d_a, _ = processar_base(df_d, is_venda=False)

        return {
            "diario": {"vendas": v_h, "gastos": d_h, "lucro": v_h - d_h, "itens": q_h},
            "mensal": {"vendas": v_m, "gastos": d_m, "lucro": v_m - d_m, "itens": q_m},
            "anual": {"vendas": v_a, "gastos": d_a, "lucro": v_a - d_a, "itens": q_a},
            "atualizado_em": agora.strftime("%H:%M:%S") # Mata o undefined
        }
    except Exception as e:
        return {"erro": str(e)}

# ROTAS PWA: Resolvendo o 404 com caminhos absolutos
@app.get("/manifest.json")
async def get_manifest():
    return FileResponse(os.path.join(BASE_DIR, "manifest.json"))

@app.get("/sw.js")
async def get_sw():
    return FileResponse(os.path.join(BASE_DIR, "sw.js"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
