import os
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import pytz
from supabase import create_client, Client
from cachetools import TTLCache

app = FastAPI()
templates = Jinja2Templates(directory="templates")
status_cache = TTLCache(maxsize=1, ttl=300)

def get_supabase() -> Client:
    return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# --- ROTAS PWA ---
@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")

@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")

def processar_dashboard():
    if "data" in status_cache: return status_cache["data"]

    supabase = get_supabase()
    tz = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz)
    hoje = agora.date()
    inicio_mes = hoje.replace(day=1)

    # --- EXTRAÇÃO (Usando os nomes das suas imagens do Supabase) ---
    res_v = supabase.table("vendas").select("carimbo_data_hora, produto, valor").execute()
    res_g = supabase.table("gastos").select("carimbo_data_hora, produto, quantidade, valor").execute()

    df_v = pd.DataFrame(res_v.data)
    df_g = pd.DataFrame(res_g.data)

    if df_v.empty: return {"erro": "Sem dados"}

    # --- TRANSFORMAÇÃO ---
    # Convertendo carimbo_data_hora para datetime real
    df_v['dt'] = pd.to_datetime(df_v['carimbo_data_hora']).dt.tz_convert(tz)
    df_g['dt'] = pd.to_datetime(df_g['carimbo_data_hora']).dt.tz_convert(tz)

    # Filtros Temporais
    v_hoje = df_v[df_v['dt'].dt.date == hoje]
    g_hoje = df_g[df_g['dt'].dt.date == hoje]
    v_mes = df_v[df_v['dt'].dt.date >= inicio_mes]
    g_mes = df_g[df_g['dt'].dt.date >= inicio_mes]

    # Auditoria Mensal (Agrupamento por mês)
    resumo_m = df_v.set_index('dt').resample('ME')['valor'].sum().to_frame(name='vendas')
    resumo_m['gastos'] = df_g.set_index('dt').resample('ME')['valor'].sum()
    resumo_m = resumo_m.fillna(0)
    resumo_m['mes'] = resumo_m.index.strftime('%m/%Y')

    resultado = {
        "resumo_hoje": {
            "faturamento": float(v_hoje['valor'].sum()),
            "pedidos": int(len(v_hoje)),
            "gastos": float(g_hoje['valor'].sum()),
            "qtd_gastos": int(g_hoje['quantidade'].sum()) if 'quantidade' in g_hoje else 0
        },
        "performance_mes": {
            "faturamento": float(v_mes['valor'].sum()),
            "gastos": float(g_mes['valor'].sum()),
            "lucro": float(v_mes['valor'].sum() - g_mes['valor'].sum())
        },
        "auditoria_mensal": resumo_m.to_dict(orient='records'),
        "atualizado_em": agora.strftime("%H:%M:%S")
    }

    status_cache["data"] = resultado
    return resultado

@app.get("/api/status")
async def api_status():
    try: return processar_dashboard()
    except Exception as e: return {"erro": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
