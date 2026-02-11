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
        
        # Puxamos TUDO da tabela para inspecionar
        res_v = supabase.table("vendas").select("*").execute()
        df_v = pd.DataFrame(res_v.data)

        if df_v.empty:
            return {"erro": "O Supabase retornou uma lista vazia. Verifique se a tabela 'vendas' tem dados."}

        # --- DIAGNÓSTICO DE COLUNAS ---
        # Vamos descobrir como o banco chama a coluna de valor
        colunas_disponiveis = df_v.columns.tolist()
        
        # Tenta achar algo que pareça com 'valor' ou 'carimbo' independente de maiúsculas
        col_valor = next((c for c in colunas_disponiveis if 'valor' in c.lower()), None)
        col_data = next((c for c in colunas_disponiveis if 'carimbo' in c.lower() or 'data' in c.lower()), None)

        if not col_valor or not col_data:
            return {
                "erro": "Colunas não encontradas",
                "colunas_que_existem": colunas_disponiveis
            }

        # Força a conversão para números e datas usando as colunas que ele achou
        df_v[col_valor] = pd.to_numeric(df_v[col_valor], errors='coerce').fillna(0)
        df_v['dt'] = pd.to_datetime(df_v[col_data]).dt.tz_convert(tz)

        # Cálculos usando as colunas detectadas automaticamente
        v_total = df_v[col_valor].sum()
        v_hoje = df_v[df_v['dt'].dt.date == agora.date()][col_valor].sum()

        return {
            "debug": {
                "colunas_detectadas": {"valor": col_valor, "data": col_data},
                "total_linhas_no_banco": len(df_v)
            },
            "diario": {"vendas": float(v_hoje), "gastos": 0, "lucro": float(v_hoje)},
            "total_geral": {"vendas": float(v_total)},
            "atualizado_em": agora.strftime("%H:%M:%S")
        }

    except Exception as e:
        return {"erro": f"Erro técnico: {str(e)}"}

# Rotas do PWA (Mantidas)
@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
