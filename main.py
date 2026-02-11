<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão André - BI Final</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #0f0f0f; color: #e5e7eb; font-family: 'Inter', sans-serif; }
        .card-glass { background: #1a1a1a; border: 1px solid #2d2d2d; border-radius: 1rem; }
        select { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2310b981'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='C19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 0.5rem center; background-size: 1rem; padding-right: 2rem; }
    </style>
</head>
<body class="p-4 max-w-4xl mx-auto mb-10">
    <header class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-xl font-black tracking-tight text-white uppercase">Analytics Estratégico</h1>
            <p class="text-gray-500 text-[10px] uppercase tracking-widest">Performance 2026</p>
        </div>
        <div id="timestamp" class="text-emerald-500 font-mono text-sm tracking-tighter">--:--:--</div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div class="card-glass p-5">
            <p class="text-[10px] text-gray-500 font-bold uppercase mb-2">Hoje</p>
            <div id="v_diario" class="text-2xl font-bold text-white">R$ 0,00</div>
            <div class="text-[10px] text-blue-400 mt-1 mb-3 font-mono"><span id="q_diario">0</span> ITENS</div>
            <div class="flex justify-between text-[10px] border-t border-gray-800 pt-3">
                <span class="text-red-500 uppercase">Gasto: <span id="g_diario">R$ 0,00</span></span>
                <span class="text-emerald-500 font-bold" id="l_diario">R$ 0,00</span>
            </div>
        </div>
        <div class="card-glass p-5">
            <p class="text-[10px] text-gray-500 font-bold uppercase mb-2">Mês Atual</p>
            <div id="v_mensal" class="text-2xl font-bold text-white">R$ 0,00</div>
            <div class="text-[10px] text-blue-400 mt-1 mb-3 font-mono"><span id="q_mensal">0</span> ITENS</div>
            <div class="flex justify-between text-[10px] border-t border-gray-800 pt-3">
                <span class="text-red-500 uppercase">Gasto: <span id="g_mensal">R$ 0,00</span></span>
                <span class="text-emerald-500 font-bold" id="l_mensal">R$ 0,00</span>
            </div>
        </div>
        <div class="card-glass p-5 border-emerald-900/20">
            <p class="text-[10px] text-gray-500 font-bold uppercase mb-2">Ano Total</p>
            <div id="v_anual" class="text-2xl font-bold text-white">R$ 0,00</div>
            <div class="text-[10px] text-blue-400 mt-1 mb-3 font-mono"><span id="q_anual">0</span> ITENS</div>
            <div class="flex justify-between text-[10px] border-t border-gray-800 pt-3">
                <span class="text-red-500 uppercase">Gasto: <span id="g_anual">R$ 0,00</span></span>
                <span class="text-emerald-500 font-bold" id="l_anual">R$ 0,00</span>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="card-glass p-6">
            <h2 class="text-[10px] font-bold text-gray-500 uppercase mb-4 text-center">Composição Anual (%)</h2>
            <div class="h-56 flex justify-center">
                <canvas id="chartPizza"></canvas>
            </div>
        </div>
        <div class="card-glass p-6">
            <h2 class="text-[10px] font-bold text-gray-500 uppercase mb-4 text-center">Vendas por Mês (R$)</h2>
            <div class="h-56">
                <canvas id="chartBarras"></canvas>
            </div>
        </div>
    </div>

    <section class="card-glass p-6">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-xs font-bold text-gray-400 uppercase">Histórico Detalhado</h2>
            <select id="seletor_mes" class="bg-black border border-gray-700 text-xs rounded-lg px-4 py-1 outline-none text-emerald-500 font-bold"></select>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-black/40 p-4 rounded-lg border border-gray-800">
                <p class="text-[9px] text-gray-500 uppercase mb-1">Vendas no Mês</p>
                <p id="det_vendas" class="text-lg font-bold text-white">R$ 0,00</p>
                <p id="det_itens" class="text-[9px] text-blue-400 font-mono">0 ITENS</p>
            </div>
            <div class="bg-black/40 p-4 rounded-lg border border-gray-800">
                <p class="text-[9px] text-gray-500 uppercase mb-1">Gastos no Mês</p>
                <p id="det_gastos" class="text-lg font-bold text-red-500">R$ 0,00</p>
            </div>
            <div class="bg-black/40 p-4 rounded-lg border border-emerald-900/30">
                <p class="text-[9px] text-gray-500 uppercase mb-1">Lucro Líquido</p>
                <p id="det_lucro" class="text-lg font-bold text-emerald-500">R$ 0,00</p>
            </div>
        </div>
    </section>

    <script>
        Chart.register(ChartDataLabels);

        let dadosMensais = [];
        let pizzaChart, barChart;
        const fmt = (v) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        async function initDash() {
            try {
                const r = await fetch('/api/status');
                const d = await r.json();
                
                document.getElementById('timestamp').innerText = d.atualizado_em;

                const cards = ['diario', 'mensal', 'anual'];
                cards.forEach(p => {
                    document.getElementById(`v_${p}`).innerText = fmt(d[p].vendas);
                    document.getElementById(`g_${p}`).innerText = fmt(d[p].gastos);
                    document.getElementById(`l_${p}`).innerText = fmt(d[p].lucro);
                    document.getElementById(`q_${p}`).innerText = d[p].itens;
                });

                dadosMensais = d.filtros_mensais;
                
                const sel = document.getElementById('seletor_mes');
                if(sel.options.length === 0) {
                    sel.innerHTML = dadosMensais.map(m => `<option value="${m.id}">${m.mes}</option>`).join('');
                    sel.value = new Date().getMonth() + 1;
                }
                atualizarDetalhe(sel.value);

                renderPizza(d.anual.lucro, d.anual.gastos);
                renderBarras(dadosMensais);

            } catch (e) { console.error("Erro no fetch:", e); }
        }

        function renderPizza(lucro, gastos) {
            const ctx = document.getElementById('chartPizza');
            const total = lucro + gastos;
            if(pizzaChart) pizzaChart.destroy();
            
            pizzaChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Lucro', 'Gastos'],
                    datasets: [{
                        data: [lucro, gastos],
                        backgroundColor: ['#10b981', '#ef4444'],
                        borderWidth: 0,
                        cutout: '70%'
                    }]
                },
                options: {
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#888', font: { size: 10 }, padding: 20 } },
                        datalabels: {
                            color: '#fff',
                            font: { weight: 'bold', size: 11 },
                            formatter: (val) => total > 0 ? ((val/total)*100).toFixed(1) + '%' : ''
                        }
                    }
                }
            });
        }

        function renderBarras(meses) {
            const ctx = document.getElementById('chartBarras');
            if(barChart) barChart.destroy();
            
            barChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: meses.map(m => m.mes.substring(0,3)),
                    datasets: [{
                        data: meses.map(m => m.vendas),
                        backgroundColor: '#3b82f6',
                        borderRadius: 5
                    }]
                },
                options: {
                    layout: { padding: { top: 25 } },
                    scales: { 
                        y: { display: false },
                        x: { ticks: { color: '#555', font: { size: 10 } }, grid: { display: false } }
                    },
                    plugins: {
                        legend: { display: false },
                        datalabels: {
                            anchor: 'end',
                            align: 'top',
                            color: '#3b82f6',
                            font: { weight: 'bold', size: 9 },
                            formatter: (val) => val > 0 ? 'R$' + Math.round(val) : ''
                        }
                    }
                }
            });
        }

        function atualizarDetalhe(id) {
            const m = dadosMensais.find(x => x.id == id);
            if(m) {
                document.getElementById('det_vendas').innerText = fmt(m.vendas);
                document.getElementById('det_gastos').innerText = fmt(m.gastos);
                document.getElementById('det_lucro').innerText = fmt(m.lucro); // Popula o novo campo de lucro
                document.getElementById('det_itens').innerText = `${m.itens} ITENS`;
            }
        }

        document.getElementById('seletor_mes').addEventListener('change', (e) => atualizarDetalhe(e.target.value));
        initDash();
        setInterval(initDash, 60000);
    </script>
</body>
</html>