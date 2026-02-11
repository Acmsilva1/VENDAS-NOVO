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
        # Definimos o fuso local para Vitória/ES (GMT-3)
        tz_local = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz_local)
        
        # LGPD: Seleção estrita de colunas conforme suas tabelas
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        def processar_base_andre(df):
            if df.empty: return 0, 0, 0
            
            # Converte valor para numérico
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
            # TRATAMENTO DE DATA ISO:
            # O Pandas lê o formato AAAA-MM-DD nativamente, mas precisamos forçar a consciência de fuso
            df['dt'] = pd.to_datetime(df['carimbo_data_hora']).dt.tz_localize('UTC').dt.tz_convert(tz_local)
            
            # Filtros comparando com o 'agora' do seu fuso
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
                "lidas_vendas": len(df_v),
                "lidas_despesas": len(df_d),
                "horario_consulta": agora.strftime("%H:%M:%S")
            }
        }
    except Exception as e:
        return {"erro": f"Bug no processamento: {str(e)}"}

# Rotas PWA
@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
async def get_sw(): return FileResponse("sw.js")
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
