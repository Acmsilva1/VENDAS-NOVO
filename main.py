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
        
        # LGPD: Selecionamos valor, data e produto (para contar unidades por vírgula)
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor, produto").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        def contar_unidades_reais(df_subset):
            if df_subset.empty: return 0
            # Explode as strings por vírgula e conta o total de elementos
            return df_subset['produto'].apply(lambda x: len(str(x).split(',')) if pd.notnull(x) else 0).sum()

        def processar_base_andre(df, is_venda=False):
            if df.empty: return 0, 0, 0, 0, 0, 0
            
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            # Normalização de fuso horário para bater com o hoje às 17h
            df['dt'] = pd.to_datetime(df['carimbo_data_hora']).dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz_local)
            
            # Filtros Temporais
            df_hoje = df[df['dt'].dt.date == agora.date()]
            df_mes = df[df['dt'].dt.month == agora.month]
            df_ano = df[df['dt'].dt.year == agora.year]
            
            # Se for venda, conta itens reais. Se for despesa, conta linhas
            q_hoje = contar_unidades_reais(df_hoje) if is_venda else len(df_hoje)
            q_mes = contar_unidades_reais(df_mes) if is_venda else len(df_mes)
            q_ano = contar_unidades_reais(df_ano) if is_venda else len(df_ano)
            
            return (
                float(df_hoje['valor'].sum()), int(q_hoje),
                float(df_mes['valor'].sum()), int(q_mes),
                float(df_ano['valor'].sum()), int(q_ano)
            )

        v_hoje, q_hoje, v_mes, q_mes, v_ano, q_ano = processar_base_andre(df_v, is_venda=True)
        d_hoje, _, d_mes, _, d_ano, _ = processar_base_andre(df_d, is_venda=False)

        return {
            "diario": {"vendas": v_hoje, "gastos": d_hoje, "lucro": v_hoje - d_hoje, "itens": q_hoje},
            "mensal": {"vendas": v_mes, "gastos": d_mes, "lucro": v_mes - d_mes, "itens": q_mes},
            "anual": {"vendas": v_ano, "gastos": d_ano, "lucro": v_ano - d_ano, "itens": q_ano},
            "atualizado_em": agora.strftime("%H:%M:%S") # Mata o undefined do frontend
        }
    except Exception as e:
        return {"erro": f"Erro na pipeline de contagem: {str(e)}"}

@app.get("/")
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
