import os
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import pytz
from supabase import create_client, Client

app = FastAPI()

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
        
        # LGPD: Seleciona apenas o estritamente necessário
        res_v = supabase.table("vendas").select("carimbo_data_hora, valor, produto").execute()
        res_d = supabase.table("despesas").select("carimbo_data_hora, valor").execute() 

        df_v = pd.DataFrame(res_v.data)
        df_d = pd.DataFrame(res_d.data)

        # Processamento de Datas
        for df in [df_v, df_d]:
            if not df.empty:
                df['dt'] = pd.to_datetime(df['carimbo_data_hora']).dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(tz_local)

        def contar_unidades_reais(df_subset):
            if df_subset.empty: return 0
            return df_subset['produto'].apply(lambda x: len(str(x).split(',')) if pd.notnull(x) else 0).sum()

        def processar_dados(df, filtro_dt, is_venda=False):
            if df.empty: return 0.0, 0
            subset = df[filtro_dt]
            valor = float(subset['valor'].apply(pd.to_numeric, errors='coerce').sum())
            qtd = int(contar_unidades_reais(subset)) if is_venda else len(subset)
            return valor, qtd

        # Cálculos de tempo
        v_h, q_h = processar_dados(df_v, df_v['dt'].dt.date == agora.date(), True)
        d_h, _ = processar_dados(df_d, df_d['dt'].dt.date == agora.date())
        
        v_m, q_m = processar_dados(df_v, (df_v['dt'].dt.month == agora.month) & (df_v['dt'].dt.year == agora.year), True)
        d_m, _ = processar_dados(df_d, (df_d['dt'].dt.month == agora.month) & (df_d['dt'].dt.year == agora.year))
        
        v_a, q_a = processar_dados(df_v, df_v['dt'].dt.year == agora.year, True)
        d_a, _ = processar_dados(df_d, df_d['dt'].dt.year == agora.year)

        # LÓGICA DAS 5 ÚLTIMAS VENDAS DO DIA
        ultimas_vendas = []
        if not df_v.empty:
            # Filtramos as vendas de hoje e ordenamos pela mais recente
            df_hoje = df_v[df_v['dt'].dt.date == agora.date()].sort_values(by='dt', ascending=False).head(5)
            for _, row in df_hoje.iterrows():
                ultimas_vendas.append({
                    "produto": str(row['produto'])[:30] + '...' if len(str(row['produto'])) > 30 else str(row['produto']),
                    "valor": float(row['valor']),
                    "data": row['dt'].strftime("%H:%M") # Apenas hora:minuto para o PWA ficar limpo
                })

        meses_nomes = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
        filtros = []
        for m in range(1, 13):
            vm, qm = processar_dados(df_v, (df_v['dt'].dt.month == m) & (df_v['dt'].dt.year == agora.year), True)
            gm, _ = processar_dados(df_d, (df_d['dt'].dt.month == m) & (df_d['dt'].dt.year == agora.year))
            if vm > 0 or gm > 0 or m == agora.month:
                filtros.append({"id": m, "mes": meses_nomes[m], "vendas": vm, "gastos": gm, "lucro": vm - gm, "itens": qm})

        return {
            "diario": {"vendas": v_h, "gastos": d_h, "lucro": v_h - d_h, "itens": q_h},
            "mensal": {"vendas": v_m, "gastos": d_m, "lucro": v_m - d_m, "itens": q_m},
            "anual": {"vendas": v_a, "gastos": d_a, "lucro": v_a - d_a, "itens": q_a},
            "ultimas_vendas": ultimas_vendas, # O novo ingrediente do seu JSON
            "filtros_mensais": filtros,
            "atualizado_em": agora.strftime("%H:%M:%S")
        }
    except Exception as e:
        return {"erro": str(e)}

# ... Resto das rotas (/manifest.json, /sw.js, /)
@app.get("/manifest.json")
async def get_manifest(): return FileResponse(os.path.join(BASE_DIR, "manifest.json"))

@app.get("/sw.js")
async def get_sw(): return FileResponse(os.path.join(BASE_DIR, "sw.js"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("index.html", {"request": request})
