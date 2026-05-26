from pathlib import Path
p = Path(r'D:\ai-theme-map-site\index.html')
text = p.read_text(encoding='utf-8')

text = text.replace(
'''                <div id="mobile-theme-hero" class="mobile-theme-hero bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                    <div class="flex items-start justify-between gap-3">
                        <div>
                            <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">Theme Focus</div>
                            <div id="mobile-theme-title" class="mt-1 text-lg font-bold text-white leading-snug"></div>
                        </div>
                        <div class="shrink-0">
                            <svg width="54" height="54" viewBox="0 0 54 54" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="27" cy="27" r="26" stroke="#334155" stroke-width="2"/>
                                <path d="M27 9L31.8 21.2L45 27L31.8 32.8L27 45L22.2 32.8L9 27L22.2 21.2L27 9Z" fill="#22d3ee" fill-opacity="0.22" stroke="#22d3ee" stroke-width="2"/>
                            </svg>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-2">
                        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                            <div class="text-[10px] text-slate-500">熱度</div>
                            <div id="mobile-theme-heat" class="mt-1 text-sm font-bold text-red-300"></div>
                        </div>
                        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                            <div class="text-[10px] text-slate-500">分數</div>
                            <div id="mobile-theme-score" class="mt-1 text-sm font-bold text-amber-300"></div>
                        </div>
                        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                            <div class="text-[10px] text-slate-500">階段</div>
                            <div id="mobile-theme-period" class="mt-1 text-sm font-bold text-indigo-300"></div>
                        </div>
                    </div>
                    <div id="mobile-theme-flow" class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4"></div>
                    <div id="mobile-theme-summary" class="space-y-2"></div>
                    <button id="mobile-theme-detail-toggle" type="button" onclick="toggleMobileThemeDetail()" class="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-2.5 text-sm font-semibold text-slate-200">看細節</button>
                    <div id="mobile-theme-detail" class="hidden rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-sm text-slate-300 leading-7"></div>
                    <div id="representative-stocks-container" class="grid grid-cols-1 gap-3"></div>
                </div>
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-4 mobile-overview-compact">
                    <div class="xl:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                        <div>
                            <div class="text-[11px] text-slate-500 mb-1">主題 Thesis</div>
                            <div id="map-thesis-hero" class="text-lg font-bold text-cyan-300 leading-relaxed"></div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
                                <div class="text-[11px] text-slate-500 mb-1">火勢狀態</div>
                                <div id="map-heat-hero" class="text-sm font-bold text-red-300"></div>
                            </div>
                            <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
                                <div class="text-[11px] text-slate-500 mb-1">火勢分數</div>
                                <div id="map-heat-score-hero" class="text-sm font-bold text-amber-300"></div>
                            </div>
                            <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
                                <div class="text-[11px] text-slate-500 mb-1">所處階段</div>
                                <div id="map-period-hero" class="text-sm font-bold text-indigo-300"></div>
                            </div>
                        </div>
                        <div>
                            <h3 class="text-sm font-bold text-indigo-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                                <i data-lucide="file-text" class="w-4 h-4"></i> 議題深度背景摘要
                            </h3>
                            <div id="map-long-desc" class="text-slate-300 text-sm leading-relaxed"></div>
                        </div>
                    </div>
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                        <div>
                            <div class="text-[11px] text-slate-500 mb-1">主題標籤</div>
                            <div id="theme-tags-container" class="flex flex-wrap gap-2"></div>
                        </div>
                        <div>
                            <div class="text-[11px] text-slate-500 mb-1">關鍵觸發事件</div>
                            <div id="trigger-events-container" class="space-y-2"></div>
                        </div>
                        <div>
                            <div class="text-[11px] text-slate-500 mb-1">觀察訊號</div>
                            <div id="watch-signals-container" class="space-y-2"></div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="overview-cards-container"></div>''',
'''                <div id="mobile-theme-hero" class="mobile-theme-hero bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                    <div class="flex items-start justify-between gap-3">
                        <div>
                            <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">Theme Focus</div>
                            <div id="mobile-theme-title" class="mt-1 text-lg font-bold text-white leading-snug"></div>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-2">
                        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-3"><div class="text-[10px] text-slate-500">熱度</div><div id="mobile-theme-heat" class="mt-1 text-sm font-bold text-red-300"></div></div>
                        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-3"><div class="text-[10px] text-slate-500">分數</div><div id="mobile-theme-score" class="mt-1 text-sm font-bold text-amber-300"></div></div>
                        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-3"><div class="text-[10px] text-slate-500">階段</div><div id="mobile-theme-period" class="mt-1 text-sm font-bold text-indigo-300"></div></div>
                    </div>
                    <div id="mobile-theme-summary" class="space-y-2"></div>
                    <div id="representative-stocks-container" class="grid grid-cols-1 gap-3"></div>
                </div>
                <div class="space-y-5 mobile-overview-compact">
                    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                        <div class="flex items-start justify-between gap-4 flex-wrap">
                            <div class="space-y-2 max-w-4xl">
                                <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">主題總覽</div>
                                <h2 id="vera-top-title" class="text-2xl md:text-3xl font-black text-white leading-tight"></h2>
                                <p id="map-thesis-hero" class="text-base md:text-lg font-semibold text-cyan-300 leading-relaxed"></p>
                            </div>
                            <div class="flex flex-wrap gap-2 items-center">
                                <span id="map-heat-hero" class="px-3 py-1.5 rounded-full text-xs font-bold bg-red-950/50 text-red-300 border border-red-800/50"></span>
                                <span id="map-heat-score-hero" class="px-3 py-1.5 rounded-full text-xs font-bold bg-amber-950/50 text-amber-300 border border-amber-800/50"></span>
                                <span id="map-period-hero" class="px-3 py-1.5 rounded-full text-xs font-bold bg-indigo-950/50 text-indigo-300 border border-indigo-800/50"></span>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                            <div class="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-950/50 p-5">
                                <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500 mb-3">這是什麼題材</div>
                                <div id="map-long-desc" class="text-slate-300 text-sm leading-7"></div>
                            </div>
                            <div class="rounded-2xl border border-slate-800 bg-slate-950/50 p-5 space-y-4">
                                <div>
                                    <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500 mb-2">主題標籤</div>
                                    <div id="theme-tags-container" class="flex flex-wrap gap-2"></div>
                                </div>
                                <div>
                                    <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500 mb-2">關鍵觸發</div>
                                    <div id="trigger-events-container" class="space-y-2"></div>
                                </div>
                                <div>
                                    <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500 mb-2">觀察訊號</div>
                                    <div id="watch-signals-container" class="space-y-2"></div>
                                </div>
                            </div>
                        </div>
                    </section>
                    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                        <div class="flex items-center justify-between gap-4 flex-wrap">
                            <div>
                                <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">題材演變</div>
                                <h3 class="mt-1 text-xl font-bold text-white">這個題材怎麼一路演變過來</h3>
                            </div>
                        </div>
                        <div id="vera-evolution-cards" class="grid grid-cols-1 md:grid-cols-3 gap-4"></div>
                    </section>
                    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                        <div>
                            <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">代表股票</div>
                            <h3 class="mt-1 text-xl font-bold text-white">這個題材代表的股票是什麼</h3>
                        </div>
                        <div id="vera-stock-picks" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"></div>
                    </section>
                    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                        <div>
                            <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">台灣概念股重點解說</div>
                            <h3 class="mt-1 text-xl font-bold text-white">像研究筆記一樣，一檔一檔看</h3>
                        </div>
                        <div id="vera-stock-explain" class="space-y-4"></div>
                    </section>
                    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                        <div>
                            <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500">補充觀念</div>
                            <h3 class="mt-1 text-xl font-bold text-white">延伸觀念與結構資訊</h3>
                        </div>
                        <div id="overview-cards-container" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
                    </section>
                </div>''')

marker = "        function renderRepresentativeStocks(mapData) {"
insert = '''        function veraEvolutionSteps(mapData) {\n            return [\n                {\n                    title: '題材起點',\n                    body: (mapData?.trigger_events || [])[0] || (mapData?.heat_drivers || [])[0] || '平台升級訊號出現，市場開始注意。',\n                    tone: 'from-cyan-500/15 to-slate-950'\n                },\n                {\n                    title: '中段擴散',\n                    body: (mapData?.trigger_events || [])[2] || (mapData?.heat_drivers || [])[2] || '資金從主晶片擴散到散熱、供電與互連。',\n                    tone: 'from-amber-500/15 to-slate-950'\n                },\n                {\n                    title: '現在焦點',\n                    body: (mapData?.watch_signals || [])[0] || (mapData?.heat_drivers || [])[3] || '接下來看法說、接單與交付節奏是否證實。',\n                    tone: 'from-emerald-500/15 to-slate-950'\n                }\n            ];\n        }\n\n        function stockExplainText(stock) {\n            return stock.desc || stock.pros || stock.catalyst || stock.role || '屬於此題材的重要觀察標的。';\n        }\n\n        function renderVeraOverview(mapData) {\n            const topTitle = document.getElementById('vera-top-title');\n            if (topTitle) topTitle.textContent = mapData.title || '';\n\n            const evo = document.getElementById('vera-evolution-cards');\n            if (evo) {\n                evo.innerHTML = veraEvolutionSteps(mapData).map((step, idx) => `\n                    <article class="rounded-2xl border border-slate-800 bg-gradient-to-br ${step.tone} p-5">\n                        <div class="text-[11px] uppercase tracking-[0.25em] text-slate-500 mb-2">STEP ${idx + 1}</div>\n                        <h4 class="text-lg font-bold text-white mb-2">${step.title}</h4>\n                        <p class="text-sm text-slate-300 leading-7">${step.body}</p>\n                    </article>\n                `).join('');\n            }\n\n            const picks = document.getElementById('vera-stock-picks');\n            if (picks) {\n                picks.innerHTML = topRepresentativeStocks(mapData, 6).map(stock => `\n                    <button onclick="openModal('${stock.id}')" class="text-left rounded-2xl border border-slate-800 bg-slate-950/60 p-5 hover:border-cyan-600/40 transition">\n                        <div class="flex items-start justify-between gap-3">\n                            <div>\n                                <div class="text-lg font-bold text-white">${stock.name}</div>\n                                <div class="text-xs font-mono text-cyan-300 mt-1">${stockCode(stock)}</div>\n                            </div>\n                            <span class="px-2.5 py-1 rounded-full text-[11px] border border-cyan-800/50 text-cyan-300">${benefitStageText(stock)}</span>\n                        </div>\n                        <div class="mt-3 text-sm text-slate-300 leading-7">${stock.role || stock.sector || '代表概念股'}</div>\n                    </button>\n                `).join('');\n            }\n\n            const explain = document.getElementById('vera-stock-explain');\n            if (explain) {\n                explain.innerHTML = (Array.isArray(mapData?.stocks) ? mapData.stocks : []).map((stock, idx) => `\n                    <article class="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">\n                        <div class="flex items-start justify-between gap-4 flex-wrap">\n                            <div>\n                                <div class="text-[11px] uppercase tracking-[0.2em] text-slate-500">概念股 ${idx + 1}</div>\n                                <h4 class="mt-1 text-xl font-bold text-white">${stock.name} <span class="text-sm text-cyan-300 font-mono">${stockCode(stock)}</span></h4>\n                            </div>\n                            <div class="flex flex-wrap gap-2">\n                                <span class="px-2.5 py-1 rounded-full text-[11px] border border-slate-700 text-slate-300">${stock.sector || '供應鏈角色'}</span>\n                                <span class="px-2.5 py-1 rounded-full text-[11px] border border-emerald-700/40 text-emerald-300">${benefitStageText(stock)}</span>\n                            </div>\n                        </div>\n                        <div class="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-4">\n                            <div class="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/70 p-4">\n                                <div class="text-[11px] text-slate-500 mb-2">重點解說</div>\n                                <p class="text-sm text-slate-200 leading-7">${stockExplainText(stock)}</p>\n                            </div>\n                            <div class="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">\n                                <div><div class="text-[11px] text-slate-500">關聯環節</div><div class="text-sm text-white mt-1">${stock.role || stock.sector || '供應鏈一環'}</div></div>\n                                <div><div class="text-[11px] text-slate-500">概念亮點</div><div class="text-sm text-slate-300 mt-1">${stock.catalyst || stock.pros || '關注規格升級與接單變化'}</div></div>\n                                <div><div class="text-[11px] text-slate-500">風險提醒</div><div class="text-sm text-slate-300 mt-1">${stock.cons || '需持續驗證導入速度與獲利轉化。'}</div></div>\n                            </div>\n                        </div>\n                    </article>\n                `).join('');\n            }\n        }\n\n'''
if marker in text and 'function veraEvolutionSteps(mapData)' not in text:
    text = text.replace(marker, insert + marker)

text = text.replace("            renderMetaPanels(mapData);\n            renderStructureLayers(mapData);\n            renderTimelinePhases(mapData);\n            renderCapitalFlow(mapData);\n            renderRepresentativeStocks(mapData);\n", "            renderMetaPanels(mapData);\n            renderStructureLayers(mapData);\n            renderTimelinePhases(mapData);\n            renderCapitalFlow(mapData);\n            renderRepresentativeStocks(mapData);\n            renderVeraOverview(mapData);\n")
text = text.replace("            document.getElementById('map-thesis-hero').textContent = mapData.thesis || mapData.title || '';\n", "            document.getElementById('map-thesis-hero').textContent = mapData.thesis || mapData.title || '';\n            const veraTopTitle = document.getElementById('vera-top-title'); if (veraTopTitle) veraTopTitle.textContent = mapData.title || '';\n")

p.write_text(text, encoding='utf-8')
print('done')
