
        let mapsRepository = {};
        let marketReports = [];
        let stocksWiki = {};
        let wikiFilterTier = 'all';
        let currentMapData = null;
        let currentMapKey = null;
        let currentModalStockId = null;
        const WATCHLIST_STORAGE_KEY = 'ai_theme_watchlist_v1';
        let watchlist = [];

        // 異步載入 vLLM 動態產出的資料庫
        async function fetchJsonWithFallback(urls) {
            let lastError = null;
            for (const url of urls) {
                try {
                    const response = await fetch(url, { cache: 'no-store' });
                    if (!response.ok) throw new Error(`HTTP ${response.status} @ ${url}`);
                    const data = await response.json();
                    return { data, url };
                } catch (err) {
                    lastError = err;
                    console.warn('JSON load failed:', url, err);
                }
            }
            throw lastError || new Error('No JSON source available');
        }

        function hasMapContent(mapData) {
            return Boolean(
                (Array.isArray(mapData?.concepts) && mapData.concepts.length >= 0)
                || (Array.isArray(mapData?.tech_lessons) && mapData.tech_lessons.length >= 0)
                || (Array.isArray(mapData?.structure_layers) && mapData.structure_layers.length >= 0)
                || (Array.isArray(mapData?.timeline_phases) && mapData.timeline_phases.length >= 0)
                || (typeof mapData?.thesis === 'string' && mapData.thesis.trim())
                || (typeof mapData?.desc === 'string' && mapData.desc.trim())
            );
        }

        function isValidMapData(mapData) {
            return mapData
                && typeof mapData === 'object'
                && typeof mapData.title === 'string'
                && Array.isArray(mapData.stocks)
                && hasMapContent(mapData);
        }

        function normalizeMapData(mapData) {
            return {
                ...mapData,
                concepts: Array.isArray(mapData?.concepts) ? mapData.concepts : [],
                tech_lessons: Array.isArray(mapData?.tech_lessons) ? mapData.tech_lessons : [],
                structure_layers: Array.isArray(mapData?.structure_layers) ? mapData.structure_layers : [],
                timeline_phases: Array.isArray(mapData?.timeline_phases) ? mapData.timeline_phases : [],
                theme_tags: Array.isArray(mapData?.theme_tags) ? mapData.theme_tags : [],
                trigger_events: Array.isArray(mapData?.trigger_events) ? mapData.trigger_events : [],
                risks: Array.isArray(mapData?.risks) ? mapData.risks : [],
                watch_signals: Array.isArray(mapData?.watch_signals) ? mapData.watch_signals : [],
                related_themes: Array.isArray(mapData?.related_themes) ? mapData.related_themes : [],
                heat_drivers: Array.isArray(mapData?.heat_drivers) ? mapData.heat_drivers : [],
                capital_flow: Array.isArray(mapData?.capital_flow) ? mapData.capital_flow : [],
                stocks: Array.isArray(mapData?.stocks) ? mapData.stocks : [],
            };
        }

        function normalizeRepository(rawRepo) {
            if (!rawRepo || typeof rawRepo !== 'object') return {};

            const normalized = {};
            for (const [key, value] of Object.entries(rawRepo)) {
                if (isValidMapData(value)) {
                    normalized[key] = normalizeMapData(value);
                }
            }

            if (Object.keys(normalized).length === 0 && isValidMapData(rawRepo)) {
                normalized['map_default'] = normalizeMapData(rawRepo);
            }

            return normalized;
        }

        function loadWatchlist() {
            try {
                const raw = localStorage.getItem(WATCHLIST_STORAGE_KEY);
                const parsed = raw ? JSON.parse(raw) : [];
                watchlist = Array.isArray(parsed) ? parsed : [];
            } catch (err) {
                console.warn('watchlist load failed', err);
                watchlist = [];
            }
        }

        function persistWatchlist() {
            try {
                localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist));
                return true;
            } catch (err) {
                console.warn('watchlist save failed', err);
                showToast('瀏覽器限制，追蹤名單無法儲存');
                return false;
            }
        }

        function getStockPool() {
            return getExpandedStocks(currentMapData?.stocks || []);
        }

        async function bootstrapApp() {
            loadWatchlist();
            const versionStamp = Date.now();
            try {
                const versionedMapCandidates = [
                    './maps_repo_20260616_105058.json',
                    './maps_repo.json'
                ];
                const { data: rawRepo, url } = await fetchJsonWithFallback([
                    ...versionedMapCandidates.map(x => `${x}?v=${versionStamp}`),
                    ...versionedMapCandidates
                ]);
                mapsRepository = normalizeRepository(rawRepo);
                console.log("成功加載動態 Wiki 數據庫！主題數：", Object.keys(mapsRepository).length, 'source=', url);
            } catch (err) {
                console.error("讀取動態數據庫失敗，採用備用防錯提示:", err);
                mapsRepository = {
                    "error_local": {
                        title: "資料庫加載失敗 ⚠️",
                        date: "--",
                        heat: "資料未載入",
                        period: "請檢查 GitHub Pages 是否成功同步 maps_repo.json",
                        desc: "站點沒有成功讀到主資料庫。請確認 publish_site.py 是否已同步 maps_repo.json，或檢查瀏覽器快取。",
                        icon: "alert-triangle",
                        color: "from-red-600 to-orange-500",
                        concepts: [],
                        stocks: []
                    }
                };
            }

            try {
                const wikiRes = await fetch(`./stocks_wiki.json?v=${versionStamp}`);
                if (wikiRes.ok) {
                    stocksWiki = await wikiRes.json();
                    console.log("成功加載個股 Wiki 數據庫！個股數：", Object.keys(stocksWiki).length);
                }
            } catch (e) {
                console.warn("載入個股 Wiki 失敗：", e);
            }

            try {
                const reportsRes = await fetch(`./market_reports.json?v=${versionStamp}`);
                if (reportsRes.ok) {
                    marketReports = await reportsRes.json();
                    console.log("成功加載投研日報數據庫！報告數：", marketReports.length);
                }
            } catch (e) {
                console.warn("載入投研日報失敗：", e);
            }

            renderDashboardHome();
            lucide.createIcons();
        }

        window.addEventListener('DOMContentLoaded', bootstrapApp);

        function showMap(mapKey) {
            loadMapWorkspace(mapKey);
            const workspace = document.getElementById('panel-map-workspace');
            if (workspace) workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function openHighlightStock(stockId) {
            if (!currentMapData || !currentMapData.stocks) return;
            switchTab('stock-list');
            openModal(stockId);
        }

        function formatDisplayTime(isoString) {
            if (!isoString) return '--';
            let formatted = String(isoString).replace('T', ' ');
            if (formatted.includes('+08:00')) {
                formatted = formatted.replace('+08:00', ' 台灣時間');
            }
            return formatted;
        }

        function updateSiteMeta() {
            const metaEl = document.getElementById('site-updated-at');
            const keys = Object.keys(mapsRepository || {});
            if (!metaEl) return;
            if (keys.length === 0) {
                metaEl.textContent = '尚無資料';
                const versionTrack = document.getElementById('home-version-track');
                if (versionTrack) versionTrack.innerHTML = '<div class="text-slate-500 text-sm">尚無歷史版本</div>';
                return;
            }
            const datedMaps = keys
                .map(key => ({ key, map: mapsRepository[key], date: mapsRepository[key]?.updated_at || mapsRepository[key]?.date || '' }))
                .filter(item => item.date)
                .sort((a, b) => String(b.date).localeCompare(String(a.date)));
            const newestFirst = [...datedMaps];
            metaEl.textContent = formatDisplayTime(datedMaps[0]?.date) || '尚無資料';

            const topEntry = newestFirst[0] || datedMaps[0] || null;
            const topMap = topEntry?.map || mapsRepository[keys[0]];
            const highlightTitle = document.getElementById('home-highlight-title');
            const highlightThesis = document.getElementById('home-highlight-thesis');
            const highlightDate = document.getElementById('home-highlight-date');
            const highlightTam = document.getElementById('home-highlight-tam');
            const highlightCagr = document.getElementById('home-highlight-cagr');
            const highlightFlow = document.getElementById('home-highlight-flow');
            const highlightStocks = document.getElementById('home-highlight-stocks');
            const versionTrack = document.getElementById('home-version-track');
            if (topMap) {
                if (highlightTitle) highlightTitle.textContent = topMap.title || '今日主題';
                if (highlightThesis) highlightThesis.textContent = shortenText(topMap.thesis || topMap.desc || '今日亮點整理中', 88);
                if (highlightDate) highlightDate.textContent = formatDisplayTime(topMap.date || topMap.updated_at);
                if (highlightTam) highlightTam.textContent = shortenText(topMap.market_size_tam || '待補資料', 28);
                if (highlightCagr) highlightCagr.textContent = shortenText(topMap.market_cagr || '待補資料', 28);
                if (highlightFlow) highlightFlow.textContent = shortenText((topMap.trigger_events || [])[0] || (topMap.heat_drivers || [])[0] || topMap.period || '主線整理中', 28);
                if (highlightStocks) {
                    const stockPool = (topMap.stocks || []);
                    const preferredStocks = stockPool
                        .filter(s => ['strong', 'medium'].includes(linkageBucket(s)) || ['第一圈', '第二圈'].includes(benefitStageText(s)))
                        .sort((a, b) => {
                            const stageRank = x => benefitStageText(x) === '第一圈' ? 0 : benefitStageText(x) === '第二圈' ? 1 : 2;
                            const scoreA = (Number(a.pureLevel || 0) * 10) + Number(a.barrierLevel || 0);
                            const scoreB = (Number(b.pureLevel || 0) * 10) + Number(b.barrierLevel || 0);
                            if (stageRank(a) !== stageRank(b)) return stageRank(a) - stageRank(b);
                            return scoreB - scoreA;
                        })
                        .slice(0, 3);
                    highlightStocks.innerHTML = preferredStocks.length
                        ? preferredStocks.map(s => `<button onclick="event.stopPropagation(); loadMapWorkspace('${topEntry.key}'); setTimeout(() => openHighlightStock('${s.id}'), 120);" class="rounded-full border border-emerald-700/40 bg-emerald-950/30 px-3 py-1 text-xs font-bold text-emerald-300 hover:border-emerald-500 hover:text-white">${s.name}</button>`).join('')
                        : '<span class="text-slate-500 text-sm">待補</span>';
                }
            }
            if (versionTrack) {
                versionTrack.innerHTML = newestFirst.slice(0, 6).map((item, idx) => `
                    <div class="rounded-xl border ${idx === 0 ? 'border-amber-700/40 bg-amber-950/20' : 'border-slate-800 bg-slate-950/40'} px-3 py-2">
                        <div class="flex items-center justify-between gap-3">
                            <div class="min-w-0">
                                <div class="text-xs font-bold ${idx === 0 ? 'text-amber-300' : 'text-slate-200'} truncate">${formatDisplayTime(item.date)}${idx === 0 ? ' ・ 今日提案' : ''}</div>
                                <div class="text-[11px] text-slate-500 truncate">${item.map?.title || item.key}</div>
                            </div>
                            <button onclick="showMap('${item.key}')" class="text-[11px] px-2 py-1 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500">查看</button>
                        </div>
                    </div>
                `).join('');
            }
        }
                // 渲染首頁列表 (市場投研首頁)
        function renderDashboardHome() {
            document.getElementById('panel-home').classList.remove('hidden');
            if (document.getElementById('panel-theme-library')) document.getElementById('panel-theme-library').classList.add('hidden');
            document.getElementById('panel-stock-wiki').classList.add('hidden');
            document.getElementById('panel-map-workspace').classList.add('hidden');
            document.getElementById('header-status').innerHTML = '';

            // Update nav buttons active styles
            document.getElementById('nav-btn-home').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition";
            if (document.getElementById('nav-btn-library')) document.getElementById('nav-btn-library').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-400 hover:text-white transition";
            document.getElementById('nav-btn-wiki').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-400 hover:text-white transition";

            const container = document.getElementById('macro-report-section');
            if (!container) return;

            const report = marketReports && marketReports[0] ? marketReports[0] : null;
            if (!report) {
                container.innerHTML = `
                    <div class="py-12 text-center text-slate-500">
                        <i data-lucide="alert-circle" class="w-8 h-8 mx-auto mb-3 text-amber-500"></i>
                        目前投研日報數據庫無資料。請確認 market_reports.json 是否存在於伺服器上。
                    </div>
                `;
                return;
            }

            // Set Title & Date
            document.getElementById('macro-title').textContent = report.title || '今日投研大局觀';
            document.getElementById('macro-date').textContent = report.date || '--';
            document.getElementById('macro-taiex-summary').textContent = report.taiex_summary || '無大盤分析資訊';

            // Set ABC wave analysis
            const abc = report.abc_wave_analysis || {};
            const abcIntro = document.getElementById('macro-abc-intro');
            if (abcIntro) abcIntro.textContent = abc.intro || '';
            const abcDetails = document.getElementById('macro-abc-details');
            if (abcDetails && abc.analysis) {
                // Parse markdown-like list to HTML list items
                let lines = [];
                if (typeof abc.analysis === 'string') {
                    lines = abc.analysis.split('\n');
                } else if (Array.isArray(abc.analysis)) {
                    lines = abc.analysis;
                }
                lines = lines.filter(l => l && l.trim());
                abcDetails.innerHTML = lines.map(line => {
                    const cleanLine = line.replace(/^\-\s+\*\*/, '').replace(/^\-\s+/, '').replace(/\*\*/g, '');
                    const parts = cleanLine.split('：');
                    if (parts.length > 1) {
                        return `<div class="py-1 border-b border-slate-800/40"><strong class="text-amber-400 font-bold">${parts[0]}：</strong><span class="text-slate-300">${parts[1]}</span></div>`;
                    }
                    return `<div class="py-1 border-b border-slate-800/40">${cleanLine}</div>`;
                }).join('');
            }

            // Set Global status table
            const globalStatus = document.getElementById('macro-global-status');
            if (globalStatus && report.global_status) {
                globalStatus.innerHTML = report.global_status.map(idx => `
                    <tr class="hover:bg-slate-800/20 transition">
                        <td class="py-2.5 font-bold text-slate-200">${idx.name}</td>
                        <td class="py-2.5 font-mono text-cyan-400">${idx.peak}</td>
                        <td class="py-2.5 text-right font-medium text-slate-300">${idx.desc}</td>
                    </tr>
                `).join('');
            }

            // Set Fundamentals
            const fundamentals = report.fundamentals || {};
            const gdpEl = document.getElementById('macro-gdp');
            if (gdpEl) gdpEl.textContent = fundamentals.gdp_growth || '--';
            const earningsEl = document.getElementById('macro-earnings');
            if (earningsEl) earningsEl.textContent = fundamentals.earnings_growth || '--';
            const aiEl = document.getElementById('macro-ai');
            if (aiEl) aiEl.textContent = fundamentals.ai_industry || '--';
            const fundSummary = document.getElementById('macro-fundamental-summary');
            if (fundSummary) fundSummary.textContent = fundamentals.summary || '';

            // Set Operation Advice
            const adviceEl = document.getElementById('macro-advice');
            if (adviceEl) adviceEl.textContent = report.operation_advice || '';

            // Render Dynamic Active Themes
            renderActiveThemes(report.thematic_categories);

            // Render Decision Radar Tables
            renderDecisionRadar();

            // Render TradingView Chart
            renderTradingViewChart();
        }

        // Render dynamic active themes in report homepage
        function renderActiveThemes(categories) {
            const container = document.getElementById('active-themes-container');
            if (!container) return;

            if (!categories || categories.length === 0) {
                container.innerHTML = `<div class="col-span-2 text-center text-slate-500 py-6">今日尚無焦點動態題材資訊。</div>`;
                return;
            }

            container.innerHTML = categories.map(cat => {
                // Try to map this category to an existing theme key
                const mapKey = Object.keys(mapsRepository).find(key => 
                    mapsRepository[key].title === cat.category_name || 
                    mapsRepository[key].theme_name === cat.category_name
                );

                const stocksHtml = (cat.stocks || []).map(s => `
                    <div onclick="openModal('${s.code}')" class="group/item flex items-start justify-between gap-3 p-2 bg-slate-950/60 border border-slate-800/60 hover:border-slate-700/80 hover:bg-slate-900/40 rounded-xl cursor-pointer transition">
                        <div class="space-y-0.5 min-w-0">
                            <div class="flex items-center gap-1.5">
                                <span class="font-bold text-slate-200 text-xs">${s.name}</span>
                                <span class="text-[9px] text-slate-500 font-mono">${s.code}</span>
                            </div>
                            <p class="text-[10px] text-slate-400 leading-relaxed truncate group-hover/item:text-slate-300 transition">${s.role}</p>
                        </div>
                        <div class="bg-indigo-950/40 text-[9px] text-indigo-400 border border-indigo-900/40 px-1.5 py-0.5 rounded-md self-center font-bold">
                            Wiki
                        </div>
                    </div>
                `).join('');

                const linkButtonHtml = mapKey ? `
                    <button onclick="showMap('${mapKey}')" class="flex items-center gap-1 px-3 py-1.5 bg-indigo-950/40 hover:bg-indigo-900/40 text-indigo-300 hover:text-white border border-indigo-900/40 hover:border-indigo-700 rounded-xl text-[10px] font-bold transition">
                        <i data-lucide="compass" class="w-3 h-3"></i> 進入完整地圖
                    </button>
                ` : '';

                return `
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4 hover:border-slate-700/80 transition flex flex-col justify-between">
                        <div class="space-y-3">
                            <div class="flex items-center justify-between gap-3">
                                <h4 class="font-black text-slate-100 text-sm flex items-center gap-2">
                                    <span class="w-1.5 h-3 bg-indigo-500 rounded-full"></span>
                                    ${cat.category_name}
                                </h4>
                                ${linkButtonHtml}
                            </div>
                            <div class="rounded-xl border border-cyan-900/30 bg-cyan-950/15 px-3 py-2.5">
                                <div class="text-[9px] uppercase tracking-[0.2em] text-cyan-400 font-bold mb-1">焦點亮點</div>
                                <p class="text-xs text-cyan-200 leading-relaxed">${cat.highlight}</p>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 pr-1 max-h-72 overflow-y-auto">
                                ${stocksHtml}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function renderMiniChart(symbol, containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            container.innerHTML = '';
            new TradingView.widget({
                "width": "100%",
                "height": "100%",
                "symbol": symbol,
                "interval": "D",
                "timezone": "America/New_York",
                "theme": "dark",
                "style": "3", // Area style
                "locale": "zh_TW",
                "toolbar_bg": "#111827",
                "enable_publishing": false,
                "hide_top_toolbar": true,
                "hide_legend": true,
                "hide_side_toolbar": true,
                "save_image": false,
                "container_id": containerId
            });
        }

        let tvWidget = null;
        let tsmWidget = null;
        function renderTradingViewChart() {
            if (typeof TradingView === 'undefined') {
                console.warn('TradingView library not loaded yet, retrying in 200ms...');
                setTimeout(renderTradingViewChart, 200);
                return;
            }
            
            // Render TAIEX Index Chart
            const taiexContainer = document.getElementById('tv-chart-taiex');
            if (taiexContainer) {
                taiexContainer.innerHTML = '';
                tvWidget = new TradingView.widget({
                    "autosize": true,
                    "symbol": "INDEX:TAIEX",
                    "interval": "D",
                    "timezone": "Asia/Taipei",
                    "theme": "dark",
                    "style": "1",
                    "locale": "zh_TW",
                    "toolbar_bg": "#111827",
                    "enable_publishing": false,
                    "hide_side_toolbar": false,
                    "allow_symbol_change": true,
                    "container_id": "tv-chart-taiex",
                    "studies": [
                        "MASimple@tv-basicstudies"
                    ]
                });
            }

            // Render TSM ADR Chart (Full Size)
            const tsmContainer = document.getElementById('tv-chart-tsm');
            if (tsmContainer) {
                tsmContainer.innerHTML = '';
                tsmWidget = new TradingView.widget({
                    "autosize": true,
                    "symbol": "NYSE:TSM",
                    "interval": "D",
                    "timezone": "America/New_York",
                    "theme": "dark",
                    "style": "1",
                    "locale": "zh_TW",
                    "toolbar_bg": "#111827",
                    "enable_publishing": false,
                    "hide_side_toolbar": false,
                    "allow_symbol_change": true,
                    "container_id": "tv-chart-tsm",
                    "studies": [
                        "MASimple@tv-basicstudies"
                    ]
                });
            }

            // Render the other 4 Mini US/Tech/ADR charts
            renderMiniChart("NASDAQ:NVDA", "tv-chart-nvda");
            renderMiniChart("NASDAQ:AAPL", "tv-chart-aapl");
            renderMiniChart("NASDAQ:MU", "tv-chart-mu");
            renderMiniChart("NYSE:UMC", "tv-chart-umc");
        }

        async function triggerMacroRefresh() {
            showToast("正在載入最新市場數據...");
            const versionStamp = Date.now();
            try {
                const wikiRes = await fetch(`./stocks_wiki.json?v=${versionStamp}`);
                if (wikiRes.ok) stocksWiki = await wikiRes.json();

                const reportsRes = await fetch(`./market_reports.json?v=${versionStamp}`);
                if (reportsRes.ok) marketReports = await reportsRes.json();

                renderDashboardHome();
                showToast("數據庫已同步更新！");
            } catch (err) {
                console.warn("重載失敗：", err);
                showToast("重載數據庫失敗，請確認網路連線。");
            }
        }

        function hideAllPanels() {
            const panels = [
                'panel-home',
                'panel-theme-library',
                'panel-stock-wiki',
                'panel-map-workspace',
                'panel-tech-docs',
                'panel-macro-market',
                'panel-industry-pricing',
                'panel-chips-analysis',
                'panel-expectations'
            ];
            panels.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.add('hidden');
            });
            
            const btns = [
                'nav-btn-home',
                'nav-btn-library',
                'nav-btn-wiki',
                'nav-btn-macro',
                'nav-btn-industry',
                'nav-btn-chips',
                'nav-btn-tech',
                'nav-btn-expectations'
            ];
            btns.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-400 hover:text-white transition whitespace-nowrap";
            });
            window.scrollTo(0, 0);
        }

        // 切換並渲染主題地圖庫分頁
        function showThemeLibrary() {
            hideAllPanels();
            if (document.getElementById('panel-theme-library')) document.getElementById('panel-theme-library').classList.remove('hidden');
            if (document.getElementById('nav-btn-library')) document.getElementById('nav-btn-library').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";

            renderThemeLibrary();
            lucide.createIcons();
        }

        function renderThemeLibrary() {
            updateSiteMeta();

            const container = document.getElementById('maps-container');
            if (!container) return;
            container.innerHTML = '';

            const keys = Object.keys(mapsRepository);
            if(keys.length === 0) {
                container.innerHTML = `<div class="text-center text-slate-500 py-8">目前地圖庫無資料。</div>`;
                return;
            }

            // Group by Year/Month
            const groups = {};
            keys.forEach(key => {
                const map = mapsRepository[key];
                if (!map) return;
                const dStr = map.date || (map.updated_at ? map.updated_at.split('T')[0] : '');
                let mLabel = '更早以前';
                if (dStr && dStr.match(/^\d{4}-\d{2}/)) {
                    const parts = dStr.split('-');
                    mLabel = `${parts[0]} 年 ${parts[1]} 月`;
                }
                if (!groups[mLabel]) groups[mLabel] = [];
                groups[mLabel].push(key);
            });

            // Sort months (newest first)
            const sortedMonths = Object.keys(groups).sort((a, b) => {
                if (a === '更早以前') return 1;
                if (b === '更早以前') return -1;
                return b.localeCompare(a);
            });

            sortedMonths.forEach(monthLabel => {
                const monthKeys = groups[monthLabel];
                // Sort keys within this month group from newest to oldest
                monthKeys.sort((a, b) => {
                    const timeA = String(mapsRepository[a]?.updated_at || mapsRepository[a]?.date || '');
                    const timeB = String(mapsRepository[b]?.updated_at || mapsRepository[b]?.date || '');
                    return timeB.localeCompare(timeA);
                });
                const section = document.createElement('div');
                section.className = 'space-y-4';
                section.innerHTML = `
                    <div class="flex items-center gap-3 border-l-4 border-indigo-500 pl-3 py-1 bg-slate-900/40 rounded-r-lg">
                        <span class="text-base font-black text-slate-200 tracking-wide">${monthLabel}</span>
                        <span class="text-[10px] text-indigo-400 bg-indigo-950/60 border border-indigo-800/40 px-2.5 py-0.5 rounded-full font-bold font-mono">${monthKeys.length} 個產業主題</span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 maps-month-grid"></div>
                `;
                
                const grid = section.querySelector('.maps-month-grid');
                
                monthKeys.forEach((key, index) => {
                    const map = mapsRepository[key];
                    if (!map) return;
                    const card = document.createElement('div');
                    card.className = 'bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition cursor-pointer flex flex-col justify-between shadow-lg hover:shadow-indigo-950/20';
                    card.onclick = () => loadMapWorkspace(key);
                    
                    const cardNum = String(index + 1).padStart(2, '0');
                    const stockCount = map.stocks ? map.stocks.length : 0;
                    
                    const opening = map.thesis || map.desc || map.title || '尚無主題摘要';
                    const summary = map.desc || map.long_description || map.description || map.thesis || '';
                    const stageText = map.theme_stage || map.period || '觀察期';
                    const valueCaptureText = map.primary_value_capture || '待補資料';
                    
                    const topStocks = (map.stocks || [])
                        .slice(0, 3)
                        .map(s => s.name || s.id || '')
                        .filter(Boolean);
                    const topStocksText = topStocks.length > 0 ? topStocks.join(', ') : '尚無資料';
                    
                    card.innerHTML = `
                        <div>
                            <div class="flex items-center gap-3 mb-3">
                                <div class="bg-gradient-to-tr ${map.color || 'from-indigo-500 to-cyan-500'} p-2 rounded-xl text-white shadow-md relative">
                                    <i data-lucide="${map.icon || 'layers'}" class="w-5 h-5"></i>
                                    <span class="absolute -top-1.5 -right-1.5 bg-slate-950 text-indigo-400 text-[9px] font-bold px-1.5 py-0.5 rounded border border-slate-800 font-mono font-bold">#${cardNum}</span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <h4 class="font-bold text-slate-100 text-sm line-clamp-1">${map.title}</h4>
                                    <div class="flex items-center gap-2 mt-1">
                                        <span class="text-[9px] text-slate-500 font-mono">📅 時程: ${map.date || '--'}</span>
                                        <span class="text-[9px] text-indigo-400 font-bold bg-indigo-950/40 border border-indigo-900/30 px-1.5 py-0.2 rounded font-mono">📈 概念股: ${stockCount} 檔</span>
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3 rounded-xl border border-cyan-900/30 bg-cyan-950/15 px-3 py-3">
                                <div class="text-[10px] uppercase tracking-[0.2em] text-cyan-400/80 mb-1">破題</div>
                                <p class="text-xs text-cyan-200 leading-relaxed line-clamp-2">${opening}</p>
                            </div>
                            <div class="grid grid-cols-2 gap-2 mb-3 text-[11px]">
                                <div class="col-span-2 rounded-xl border border-emerald-900/30 bg-emerald-950/15 px-3 py-2">
                                    <div class="text-slate-500 mb-1">主導概念股 (前三)</div>
                                    <div class="font-bold text-emerald-300 line-clamp-1">${topStocksText}</div>
                                </div>
                                <div class="rounded-xl border border-amber-900/30 bg-amber-950/15 px-3 py-2">
                                    <div class="text-slate-500 mb-1">題材階段</div>
                                    <div class="font-bold text-amber-300 line-clamp-1">${stageText}</div>
                                </div>
                                <div class="rounded-xl border border-fuchsia-900/30 bg-fuchsia-950/15 px-3 py-2">
                                    <div class="text-slate-500 mb-1">誰賺最多</div>
                                    <div class="font-bold text-fuchsia-300 line-clamp-1">${valueCaptureText}</div>
                                </div>
                            </div>
                            <p class="text-xs text-slate-400 leading-relaxed mb-3 line-clamp-2">${summary || '尚無摘要'}</p>
                        </div>
                        <div class="border-t border-slate-800/60 pt-3 space-y-2 text-[11px]">
                            <div class="flex items-center justify-between gap-2">
                                <span class="text-red-400 bg-red-950/40 px-2 py-0.5 rounded-md border border-red-900/40 font-medium">${map.heat}</span>
                                <span class="text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded-md border border-amber-800/40 font-medium">火勢 ${map.heat_score ?? '--'}</span>
                            </div>
                        </div>
                    \`;
                    grid.appendChild(card);
                });
                
                container.appendChild(section);
            });
        }

        function renderDecisionRadar() {
            const potentialTbody = document.getElementById('home-potential-stocks');
            const weakeningTbody = document.getElementById('home-weakening-stocks');
            if (!potentialTbody || !weakeningTbody) return;

            const allCoreStocks = [];
            const seenCodes = new Set();

            Object.keys(mapsRepository).forEach(mapKey => {
                const map = mapsRepository[mapKey];
                if (!map || !map.stocks) return;
                map.stocks.forEach(stock => {
                    const code = String(stock.code || stock.id || '').trim();
                    if (!code || seenCodes.has(code)) return;
                    // Filter out placeholders like F11, S11 or anything not starting with a digit
                    if (code.startsWith('F') || code.startsWith('S') || !/^\d+/.test(code)) return;
                    seenCodes.add(code);
                    
                    const wiki = stocksWiki[code] || {};
                    const details = wiki.details || {};
                    
                    allCoreStocks.push({
                        code: code,
                        name: stock.name || wiki.name || '未命名',
                        sector: stock.sector || wiki.industry || '未分類',
                        pureLevel: Number(stock.pureLevel ?? details.pureLevel ?? 0),
                        barrierLevel: Number(stock.barrierLevel ?? details.barrierLevel ?? 0),
                        pricing_power: stock.pricing_power || details.pricing_power || '中',
                        value_capture_score: Number(stock.value_capture_score ?? details.value_capture_score ?? 50),
                        commercialization_phase: stock.commercialization_phase || details.commercialization_phase || '量產出貨',
                        substitution_risk: stock.substitution_risk || details.substitution_risk || '低',
                        themeTitle: map.title,
                        mapKey: mapKey,
                        heatScore: Number(map.heat_score || 50),
                        stage: map.theme_stage || map.period || ''
                    });
                });
            });

            const potentialList = [...allCoreStocks]
                .sort((a, b) => {
                    const scoreA = (a.pureLevel * 5) + (a.barrierLevel * 3) + (a.heatScore / 20) + (a.value_capture_score / 25);
                    const scoreB = (b.pureLevel * 5) + (b.barrierLevel * 3) + (b.heatScore / 20) + (b.value_capture_score / 25);
                    return scoreB - scoreA;
                })
                .slice(0, 10);

            potentialTbody.innerHTML = potentialList.map(s => `
                <tr class="hover:bg-slate-800/30 transition cursor-pointer" onclick="openModal('${s.code}')">
                    <td class="py-2.5 font-semibold text-slate-100 flex flex-col">
                        <span>${s.name}</span>
                        <span class="text-[10px] text-slate-500 font-mono">${s.code}</span>
                    </td>
                    <td class="py-2.5">
                        <span class="text-indigo-300 font-medium line-clamp-1">${s.themeTitle}</span>
                    </td>
                    <td class="py-2.5 text-center font-mono">
                        <span class="text-amber-400">★${s.pureLevel.toFixed(1)}</span>
                        <span class="text-slate-500">/</span>
                        <span class="text-emerald-400">🛡️${s.barrierLevel.toFixed(1)}</span>
                    </td>
                    <td class="py-2.5 text-right font-medium text-emerald-400">${s.commercialization_phase}</td>
                </tr>
            `).join('');

            let weakeningCandidates = [];
            
            if (watchlist && watchlist.length > 0) {
                watchlist.forEach(code => {
                    // Prevent potential list stocks from showing in weakening list
                    if (potentialList.some(p => p.code === code)) return;

                    const wiki = stocksWiki[code];
                    if (!wiki) return;
                    const details = wiki.details || {};
                    const subRisk = details.substitution_risk || '低';
                    const hasHighRisk = subRisk.includes('高') || subRisk.includes('中') || subRisk.includes('面臨') || subRisk.includes('競爭');
                    const lowBarrier = Number(details.barrierLevel || 3.5) < 3.0;
                    
                    if (hasHighRisk || lowBarrier) {
                        weakeningCandidates.push({
                            code: code,
                            name: wiki.name,
                            reason: hasHighRisk ? '同業與陸廠競爭加劇，替代風險高' : '技術壁壘較低，定價權受壓',
                            substitution_risk: subRisk,
                            action: '建議減碼 / 移出追蹤',
                            isFromWatchlist: true
                        });
                    }
                });
            }

            if (weakeningCandidates.length < 5) {
                const systemWarnings = allCoreStocks
                    .filter(s => {
                        // Prevent potential list stocks from showing in weakening list
                        if (potentialList.some(p => p.code === s.code)) return false;

                        const hasHighRisk = s.substitution_risk.includes('高') || s.substitution_risk.includes('中') || s.substitution_risk.includes('面臨') || s.substitution_risk.includes('競爭');
                        const lowBarrier = s.barrierLevel < 3.0;
                        return (hasHighRisk || lowBarrier) && !weakeningCandidates.some(c => c.code === s.code);
                    })
                    .map(s => {
                        const hasHighRisk = s.substitution_risk.includes('高') || s.substitution_risk.includes('中') || s.substitution_risk.includes('面臨') || s.substitution_risk.includes('競爭');
                        return {
                            code: s.code,
                            name: s.name,
                            reason: hasHighRisk ? '陸廠擴產競爭，同質性替代風險高' : '技術壁壘與切換成本較低',
                            substitution_risk: s.substitution_risk,
                            action: '防雷警示 / 謹慎追高',
                            isFromWatchlist: false
                        };
                    });
                
                weakeningCandidates = [...weakeningCandidates, ...systemWarnings].slice(0, 5);
            }

            if (weakeningCandidates.length === 0) {
                weakeningTbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-slate-500">目前暫無發現轉弱警示個股。</td></tr>`;
            } else {
                weakeningTbody.innerHTML = weakeningCandidates.map(s => `
                    <tr class="hover:bg-slate-800/30 transition cursor-pointer" onclick="openModal('${s.code}')">
                        <td class="py-2.5 font-semibold text-slate-100 flex flex-col">
                            <span class="flex items-center gap-1">
                                ${s.name}
                                ${s.isFromWatchlist ? '<span class="text-[9px] bg-amber-950 border border-amber-800/60 text-amber-300 px-1 rounded">追蹤中</span>' : ''}
                            </span>
                            <span class="text-[10px] text-slate-500 font-mono">${s.code}</span>
                        </td>
                        <td class="py-2.5 text-slate-400">
                            <span class="line-clamp-1">${s.reason}</span>
                        </td>
                        <td class="py-2.5 text-center font-semibold text-amber-500">${s.substitution_risk}</td>
                        <td class="py-2.5 text-right font-bold text-red-400">${s.action}</td>
                    </tr>
                `).join('');
            }
        }

        // 載入特定地圖工作區
        function loadMapWorkspace(mapKey) {
            hideAllPanels();
            const mapData = mapsRepository[mapKey];
            if (!mapData) return;
            currentMapData = mapData;
            currentMapKey = mapKey;

            document.getElementById('panel-map-workspace').classList.remove('hidden');

            // 頂部狀態更新
            document.getElementById('header-status').innerHTML = `
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-950 text-red-400 border border-red-800">${mapData.heat}</span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-950 text-amber-300 border border-amber-800">火勢 ${mapData.heat_score ?? '--'}</span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-950 text-indigo-400 border border-indigo-800">${mapData.period}</span>
            `;

            // 灌入深度背景描述
            document.getElementById('map-thesis-hero').textContent = mapData.thesis || mapData.title || '';
            document.getElementById('map-heat-hero').textContent = mapData.heat || '未分類';
            document.getElementById('map-heat-score-hero').textContent = `${mapData.heat_score ?? '--'} / 100`;
            document.getElementById('map-period-hero').textContent = mapData.period || '觀察期';
            document.getElementById('header-status').innerHTML = `
                <div class="hidden xl:flex items-center gap-2 text-xs text-slate-400">
                    <span class="px-2 py-1 rounded-lg border border-slate-700 bg-slate-900">提案日期 ${formatDisplayTime(mapData.date)}</span>
                    <span class="px-2 py-1 rounded-lg border border-emerald-700/40 bg-emerald-950/20 text-emerald-300">市場規模 (TAM) ${mapData.market_size_tam || '待補資料'}</span>
                    <span class="px-2 py-1 rounded-lg border border-cyan-700/40 bg-cyan-950/20 text-cyan-300">年複合成長率 (CAGR) ${mapData.market_cagr || '待補資料'}</span>
                    <span class="px-2 py-1 rounded-lg border border-amber-700/40 bg-amber-950/20 text-amber-300">${mapData.theme_stage || mapData.period || '觀察期'}</span>
                    <span class="px-2 py-1 rounded-lg border border-slate-700 bg-slate-900">更新 ${formatDisplayTime(mapData.updated_at || mapData.date)}</span>
                </div>
            `;
            document.getElementById('mobile-theme-title').textContent = mapData.title || '未命名主題';
            document.getElementById('mobile-theme-tam').textContent = mapData.market_size_tam || '待補資料';
            document.getElementById('mobile-theme-cagr').textContent = mapData.market_cagr || '待補資料';
            document.getElementById('mobile-theme-heat').textContent = mapData.heat || '未分類';
            document.getElementById('mobile-theme-period').textContent = mapData.theme_stage || mapData.period || '觀察期';
            const flowEl = document.getElementById('mobile-theme-flow');
            const summaryEl = document.getElementById('mobile-theme-summary');
            const detailEl = document.getElementById('mobile-theme-detail');
            const detailBtn = document.getElementById('mobile-theme-detail-toggle');
            if (flowEl) {
                const flowItems = [
                    shortenText(mapData.thesis || mapData.title || '主題啟動', 18),
                    shortenText((mapData.trigger_events || [])[0] || (mapData.heat_drivers || [])[0] || '需求升溫', 18),
                    shortenText((mapData.watch_signals || [])[0] || (mapData.related_themes || [])[0] || '概念股擴散', 18)
                ];
                flowEl.innerHTML = `
                    <div class="text-[11px] uppercase tracking-[0.2em] text-slate-500 mb-3">Flow</div>
                    <div class="flex items-center justify-between gap-2 text-center">
                        ${flowItems.map((item, idx) => `
                            <div class="flex items-center ${idx < flowItems.length - 1 ? 'flex-1' : ''} gap-2">
                                <div class="min-w-0 flex-1 rounded-xl border border-slate-800 bg-slate-900/80 px-2 py-2 text-[11px] font-medium text-slate-200 leading-4">${item}</div>
                                ${idx < flowItems.length - 1 ? '<div class="text-cyan-400 text-sm">→</div>' : ''}
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            if (summaryEl) {
                const summaryLines = [
                    mapData.thesis || mapData.title || '尚無摘要',
                    (mapData.trigger_events || [])[0] || (mapData.heat_drivers || [])[0] || '尚無驅動描述',
                    (mapData.watch_signals || [])[0] || (mapData.related_themes || [])[0] || '尚無觀察重點'
                ].filter(Boolean).slice(0, 3);
                summaryEl.innerHTML = summaryLines.map(line => `<div class="rounded-xl border border-slate-800 bg-slate-950/50 px-3 py-2 text-xs text-slate-200 leading-5">${shortenText(line, 60)}</div>`).join('');
            }
            if (detailEl) {
                detailEl.innerHTML = `
                    <div class="space-y-3">
                        <div><div class="text-[11px] text-slate-500 mb-1">破題</div><div>${mapData.thesis || mapData.title || '尚無內容'}</div></div>
                        <div><div class="text-[11px] text-slate-500 mb-1">為什麼現在看</div><div>${mapData.why_now || '待補資料'}</div></div>
                        <div><div class="text-[11px] text-slate-500 mb-1">這個主題在講什麼</div><div>${mapData.desc || mapData.long_description || mapData.description || '尚無細節描述'}</div></div>
                        <div><div class="text-[11px] text-slate-500 mb-1">誰賺最多</div><div>${mapData.primary_value_capture || '待補資料'}</div></div>
                        <div><div class="text-[11px] text-slate-500 mb-1">納入主題一起看</div><div>${(mapData.related_themes || []).join(' / ') || '目前無延伸主題'}</div></div>
                    </div>
                `;
                detailEl.classList.add('hidden');
            }
            if (detailBtn) detailBtn.textContent = '看細節';

            const longDescEl = document.getElementById('map-long-desc');
            longDescEl.innerHTML = `
                <div class="space-y-3">
                    <p>${mapData.desc || ''}</p>
                    ${(mapData.heat_drivers && mapData.heat_drivers.length) ? `<div><div class="text-xs text-slate-500 mb-1">火勢驅動</div><div class="flex flex-wrap gap-2">${mapData.heat_drivers.map(x => `<span class='px-2 py-1 rounded bg-red-950/30 border border-red-900/30 text-red-300 text-xs'>${x}</span>`).join('')}</div></div>` : ''}
                </div>
            `;

            // 渲染技術概念卡 / 教學卡
            const conceptContainer = document.getElementById('overview-cards-container');
            conceptContainer.innerHTML = '';
            const lessons = (mapData.tech_lessons && mapData.tech_lessons.length) ? mapData.tech_lessons : (mapData.concepts || []);
            if(lessons && lessons.length > 0) {
                lessons.forEach(c => {
                    conceptContainer.innerHTML += `
                        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition">
                            <h4 class="text-base font-bold text-cyan-400 mb-1 flex items-center gap-1.5"><i data-lucide="help-circle" class="w-4 h-4"></i>${c.title || ''}</h4>
                            <span class="text-[10px] text-slate-400 font-mono block mb-2">${c.subtitle || ''}</span>
                            <p class="text-xs text-slate-300 leading-relaxed mb-2">${c.desc || ''}</p>
                            ${c.problem ? `<div class='text-[11px] text-amber-300 mb-1'>解決問題：${c.problem}</div>` : ''}
                            ${c.mechanism ? `<div class='text-[11px] text-slate-400 mb-1'>運作機制：${c.mechanism}</div>` : ''}
                            ${c.why_now ? `<div class='text-[11px] text-emerald-300'>為何現在重要：${c.why_now}</div>` : ''}
                        </div>
                    `;
                });
            } else {
                conceptContainer.innerHTML = `<div class="col-span-full text-center text-slate-600 py-4 text-xs">無內建技術教學內容</div>`;
            }

            renderMetaPanels(mapData);
            renderStructureLayers(mapData);
            renderTimelinePhases(mapData);
            renderCapitalFlow(mapData);

            initWorkspaceModules();
            switchTab('overview');
        }

        function showDashboardHome() {
            renderDashboardHome();
        }

        // 初始化工作區聯動模組 (篩選標籤群、PK選單)
        function initWorkspaceModules() {
            const selectA = document.getElementById('compare-a');
            const selectB = document.getElementById('compare-b');
            selectA.innerHTML = ''; selectB.innerHTML = '';

            const filterBar = document.getElementById('sector-filters');
            filterBar.innerHTML = `<button onclick="filterSector('all')" class="sector-tab-btn px-2.5 py-1 text-xs font-medium rounded-md transition bg-indigo-600 text-white" data-sector="all">全部</button>`;
            
            if(!currentMapData.stocks || currentMapData.stocks.length === 0) {
                renderTable();
                return;
            }

            // 動態抓取板塊標籤
            const sectorSet = new Set();
            const sectors = [];
            currentMapData.stocks.forEach(s => {
                const item = JSON.stringify({id: s.sectorId, name: s.sector});
                if(!sectorSet.has(item)) {
                    sectorSet.add(item);
                    sectors.push(JSON.parse(item));
                }
            });

            sectors.forEach(sec => {
                filterBar.innerHTML += `<button onclick="filterSector('${sec.id}')" class="sector-tab-btn px-2.5 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition" data-sector="${sec.id}">${sec.name}</button>`;
            });

            // 填入 PK 選單
            currentMapData.stocks.forEach((stock, idx) => {
                let optA = new Option(`${stock.name} (${stock.code})`, stock.id);
                let optB = new Option(`${stock.name} (${stock.code})`, stock.id);
                if(idx === 0) optA.selected = true;
                if(idx === 1 || (idx === 0 && currentMapData.stocks.length === 1)) optB.selected = true; 
                selectA.add(optA); selectB.add(optB);
            });

            renderTable();
            renderComparison();
            renderWatchlist();
        }

        // 核心：個股交互表格渲染
        function sourceTypeLabel(type) {
            const map = {
                official_sources: '官方',
                global_news: '國際新聞',
                taiwan_finance_news: '台灣財經',
                youtube_sources: 'YouTube',
                analyst_sources: '分析師/投顧',
                community_sources: '社群',
                other: '其他'
            };
            return map[type] || type || '來源';
        }

        function stockTierLabel(tier) {
            const map = { core: '核心股', extended: '延伸股', watch: '觀察股' };
            return map[tier] || tier || '未分類';
        }

        function evidenceTypeLabel(type) {
            const map = { direct: '直接來源', inferred: '推論補充' };
            return map[type] || type || '未標示';
        }

        function linkageBucket(stock) {
            const pure = Number(stock?.pureLevel || 0);
            const tier = stock?.stock_tier || '';
            if (tier === 'core' || pure >= 4.2) return 'strong';
            if (tier === 'extended' || pure >= 3.0) return 'medium';
            return 'weak';
        }

        function linkageStrengthLabel(stock) {
            const map = { strong: '強連動', medium: '中連動', weak: '弱連動' };
            return map[linkageBucket(stock)] || '中連動';
        }

        function linkageRoleLabel(stock) {
            const tier = stock?.stock_tier || '';
            const evidence = stock?.evidence_type || '';
            if (tier === 'core' && evidence === 'direct') return '核心受惠';
            if (tier === 'core') return '核心觀察';
            if (tier === 'extended' && evidence === 'direct') return '次級擴散';
            if (tier === 'extended') return '延伸受惠';
            return '情緒/驗證';
        }

        function buildLinkageReason(stock) {
            const role = shortenText(stock?.role || stock?.pros || stock?.sector || '供應鏈受惠', 24);
            const timeframe = shortenText(stock?.timeframe || '觀察中', 14);
            return `${role}｜${timeframe}`;
        }

        function relationText(stock) {
            return stock?.relation_to_theme || linkageRoleLabel(stock);
        }

        function benefitStageText(stock) {
            return stock?.benefit_stage || (stock?.stock_tier === 'core' ? '第一圈' : stock?.stock_tier === 'extended' ? '第二圈' : '第三圈');
        }

        function linkageText(stock) {
            return stock?.linkage_strength || linkageStrengthLabel(stock);
        }

        function linkageDriverText(stock) {
            return stock?.linkage_driver || buildLinkageReason(stock);
        }

        function renderLinkageSummary(stock) {
            return `${relationText(stock)}｜${linkageText(stock)}`;
        }

        function renderModalLinkage(stock) {
            const strength = linkageText(stock);
            const role = relationText(stock);
            const reason = linkageDriverText(stock);
            const stage = benefitStageText(stock);
            const tone = linkageBucket(stock) === 'strong'
                ? 'border-fuchsia-800/50 bg-fuchsia-950/20 text-fuchsia-200'
                : linkageBucket(stock) === 'medium'
                    ? 'border-cyan-800/50 bg-cyan-950/20 text-cyan-200'
                    : 'border-slate-800 bg-slate-950/40 text-slate-300';
            return `
                <div class="rounded-xl border ${tone} p-3 space-y-1.5">
                    <div class="font-semibold">${role} · ${strength}</div>
                    <div class="leading-5">受惠位階：${stage}</div>
                    <div class="leading-5">連動原因：${reason}</div>
                    <div class="text-[11px] text-slate-400">與題材連動邏輯：${stock?.relation_note || stock?.pros || stock?.role || '待補充'}</div>
                </div>
            `;
        }

        function summarizeStockSources(stock) {
            const sources = Array.isArray(stock.sources) ? stock.sources : [];
            if (!sources.length) return '<span class="text-slate-500">系統推論</span>';
            return sources.slice(0, 2).map(src => {
                const analyst = src.analyst_name ? ` / ${src.analyst_name}` : '';
                return `<div class="leading-5"><span class="text-cyan-300">${sourceTypeLabel(src.source_type)}</span> · ${src.source_name || '未標示來源'}${analyst}</div>`;
            }).join('');
        }

        function renderModalSources(stock) {
            const sources = Array.isArray(stock.sources) ? stock.sources : [];
            if (!sources.length) {
                return '<div class="text-slate-500">目前這檔為系統依主題供應鏈推論補入，尚未掛上外部來源連結。</div>';
            }
            return sources.map(src => {
                const analyst = src.analyst_name ? `<span class="text-amber-300">分析師：${src.analyst_name}</span>` : '';
                const meta = [sourceTypeLabel(src.source_type), src.source_name || '未標示來源', analyst].filter(Boolean).join(' ｜ ');
                const title = src.title || src.source_name || '未命名來源';
                if (src.url) {
                    return `<div class="rounded-lg border border-slate-800 bg-slate-950/50 p-3"><a href="${src.url}" target="_blank" rel="noreferrer" class="text-cyan-300 hover:text-cyan-200">${title}</a><div class="mt-1 text-[11px] text-slate-500">${meta}</div></div>`;
                }
                return `<div class="rounded-lg border border-slate-800 bg-slate-950/50 p-3"><div class="text-slate-200">${title}</div><div class="mt-1 text-[11px] text-slate-500">${meta}</div></div>`;
            }).join('');
        }

        function renderWatchlistAction(stock) {
            const watched = watchlist.includes(stock.id);
            return `
                <button onclick="event.stopPropagation(); toggleWatchlist('${stock.id}')" class="inline-flex items-center justify-center gap-1 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition ${watched ? 'border-amber-700/60 bg-amber-950/30 text-amber-300 hover:bg-amber-950/50' : 'border-slate-700 bg-slate-950/80 text-slate-300 hover:border-indigo-700 hover:text-indigo-300'}">
                    <i data-lucide="${watched ? 'bookmark-check' : 'bookmark-plus'}" class="w-3.5 h-3.5"></i>
                    <span>${watched ? '已追蹤' : '加入追蹤'}</span>
                </button>
            `;
        }

        function renderMobileStockCards(filtered) {
            const container = document.getElementById('stock-mobile-list');
            if (!container) return;
            container.innerHTML = '';
            if (!filtered.length) {
                container.innerHTML = `<div class="text-center text-slate-500 text-sm py-8">查無符合條件的概念股</div>`;
                return;
            }
            filtered.forEach(stock => {
                const row = document.createElement('button');
                row.type = 'button';
                row.className = 'w-full rounded-xl border border-slate-800 bg-slate-900 px-3 py-3 text-left shadow-sm active:scale-[0.99] transition';
                row.setAttribute('onclick', `openModal('${stock.id}')`);
                row.innerHTML = `
                    <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0 flex-1">
                            <div class="flex items-start justify-between gap-2">
                                <div class="min-w-0">
                                    <div class="truncate text-sm font-bold text-slate-100">${stock.name} <span class="text-[11px] text-indigo-400 font-mono">${stock.code}</span></div>
                                    <div class="mt-0.5 truncate text-[11px] text-slate-500">${renderLinkageSummary(stock)}</div>
                                </div>
                                <div class="shrink-0 text-right">
                                    <div class="text-[11px] font-bold text-amber-300">${Number(stock.pureLevel).toFixed(1)}</div>
                                    <div class="text-[10px] text-slate-500">連動</div>
                                </div>
                            </div>
                            <div class="mt-1 truncate text-[11px] text-slate-300">${shortenText(stock.role || stock.sector || '概念股', 24)}</div>
                            <div class="mt-1 truncate text-[11px] text-slate-500">${shortenText(stripHtml(summarizeStockSources(stock)) || stockTierLabel(stock.stock_tier), 28)}</div>
                            <div class="mt-3">${renderWatchlistAction(stock)}</div>
                        </div>
                    </div>
                `;
                container.appendChild(row);
            });
            lucide.createIcons();
        }

        function getExpandedStocks(stocks = []) {
            const list = Array.isArray(stocks) ? [...stocks] : [];
            const existingCodes = new Set(list.map(s => String(s.code || s.id || '')));
            const synonyms = {
                '2308': ['Delta Electronics', 'Delta', '台達電'],
                '2382': ['Quanta', '廣達'],
                '3231': ['Wistron', '緯創'],
                '6669': ['Wiwynn', '緯穎'],
                '3017': ['Auras', '奇鋐'],
                '3324': ['Auras Technology', '雙鴻'],
                '2301': ['Lite-On', '光寶科'],
                '2345': ['Accton', '智邦'],
                '3715': ['Dynamic', '定穎投控'],
                '2356': ['Inventec', '英業達'],
                '2317': ['Hon Hai', 'Foxconn', '鴻海'],
                '4938': ['Pegatron', '和碩'],
                '6669': ['Wiwynn', '緯穎'],
                '5269': ['祥碩'],
                '3037': ['Unimicron', '欣興'],
                '2368': ['Gold Circuit', '金像電'],
                '8210': ['勤誠'],
                '3023': ['Sinbon', '信邦'],
                '3596': ['Arcadyan', '智易'],
                '3653': ['Jentech', '健策'],
                '6274': ['Taimide', '台燿'],
                '6278': ['台表科'],
                '8046': ['Nexus', '南電'],
                '3036': ['WT', '文曄']
            };
            const titleBlob = `${currentMapData?.title || ''} ${(currentMapData?.desc || '')} ${(currentMapData?.thesis || '')} ${(currentMapData?.related_themes || []).join(' ')}`.toLowerCase();
            Object.values(mapsRepository || {}).forEach(map => {
                (map.stocks || []).forEach(stock => {
                    const code = String(stock.code || stock.id || '');
                    if (!code || existingCodes.has(code)) return;
                    const names = [stock.name, stock.role, stock.sector, ...(synonyms[code] || [])].filter(Boolean).join(' ').toLowerCase();
                    const thematicMatch = names && (titleBlob.includes(names.split(' ')[0]) || (synonyms[code] || []).some(x => titleBlob.includes(String(x).toLowerCase())));
                    const infrastructureBoost = ['液冷', '電源', '光通訊', '機櫃', '資料中心', '伺服器', '散熱', '交換器', '高速'].some(k => titleBlob.includes(k))
                        && ['2308','2382','3231','6669','3017','3324','2301','2345','3715','2356','2317','4938','3037','2368','8210','3653','8046'].includes(code);
                    if (thematicMatch || infrastructureBoost) {
                        existingCodes.add(code);
                        list.push({
                            ...stock,
                            stock_tier: stock.stock_tier || 'watch',
                            evidence_type: stock.evidence_type || 'inferred'
                        });
                    }
                });
            });
            return list.sort((a, b) => Number(b.pureLevel || 0) - Number(a.pureLevel || 0));
        }

        function renderTable(filterText = '', filterSectorId = 'all') {
            const tbody = document.getElementById('stock-table-body');
            tbody.innerHTML = '';
            if (!currentMapData || !currentMapData.stocks) return;
            const stockPool = getStockPool();

            const filtered = stockPool.filter(stock => {
                const targetText = (stock.name + stock.code + stock.role + stock.sector).toLowerCase();
                const matchText = targetText.includes(filterText.toLowerCase());
                const matchSector = filterSectorId === 'all' || stock.sectorId === filterSectorId;
                return matchText && matchSector;
            });

            if(filtered.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-slate-500 text-xs">無符合過濾條件的個股資料</td></tr>`;
                renderMobileStockCards([]);
                return;
            }

            filtered.forEach(stock => {
                const isWatched = watchlist.includes(stock.id);
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40 transition border-b border-slate-800/60";
                tr.innerHTML = `
                    <td class="py-3.5 px-4 text-center">
                        ${renderWatchlistAction(stock)}
                    </td>
                    <td class="py-3.5 px-4 font-bold text-slate-100">${stock.name} <span class="text-xs text-indigo-400 font-mono block sm:inline">[${stock.code}]</span></td>
                    <td class="py-3.5 px-4"><span class="px-2 py-0.5 rounded bg-slate-800 text-xs text-slate-300 border border-slate-700/40">${stock.sector}</span></td>
                    <td class="py-3.5 px-4 text-slate-300 text-xs max-w-xs">
                        <div class="truncate">${stock.role}</div>
                        <div class="mt-1 text-[11px] text-slate-500">${stockTierLabel(stock.stock_tier)} ｜ ${evidenceTypeLabel(stock.evidence_type)} ｜ ${renderLinkageSummary(stock)}</div>
                        <div class="mt-1 text-[11px] text-slate-400">${summarizeStockSources(stock)}</div>
                        <div class="mt-1 text-[11px] text-emerald-300">AI營收含金量：${stock.ai_revenue_exposure || '待補資料'}</div>
                        <div class="mt-1 text-[11px] text-amber-300">商用節奏：${stock.commercialization_phase || stock.timeframe || '待補資料'}</div>
                    </td>
                    <td class="py-3.5 px-4 text-slate-400 text-xs font-mono">${stock.timeframe}</td>
                    <td class="py-3.5 px-4 text-center text-amber-400 font-bold font-mono">${Number(stock.pureLevel).toFixed(1)}</td>
                    <td class="py-3.5 px-4 text-center text-emerald-400 font-bold font-mono">${Number(stock.barrierLevel).toFixed(1)}</td>
                    <td class="py-3.5 px-4 text-center">
                        <button onclick="openModal('${stock.id}')" class="bg-slate-800 hover:bg-slate-700 text-slate-200 p-1.5 rounded-lg transition border border-slate-700/60 shadow-sm">
                            <i data-lucide="info" class="w-3.5 h-3.5"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            renderMobileStockCards(filtered);
            lucide.createIcons();
        }

        function filterTable() {
            const searchVal = document.getElementById('table-search').value.trim();
            const activeSectorBtn = document.querySelector('.sector-tab-btn.bg-indigo-600');
            const sectorId = activeSectorBtn ? activeSectorBtn.getAttribute('data-sector') : 'all';
            renderTable(searchVal, sectorId);
        }

        function filterSector(sectorId) {
            document.querySelectorAll('.sector-tab-btn').forEach(btn => btn.className = "sector-tab-btn px-2.5 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition");
            const activeBtn = document.querySelector(`.sector-tab-btn[data-sector="${sectorId}"]`);
            if (activeBtn) {
                activeBtn.className = "sector-tab-btn px-2.5 py-1 text-xs font-medium rounded-md transition bg-indigo-600 text-white";
            }
            filterTable();
        }

        function renderBulletList(containerId, items, emptyText, tone = 'slate') {
            const container = document.getElementById(containerId);
            if (!container) return;
            if (!items || items.length === 0) {
                container.innerHTML = `<div class="text-[11px] text-slate-600">${emptyText}</div>`;
                return;
            }
            const toneClass = {
                slate: 'border-slate-800 text-slate-300 bg-slate-950/50',
                red: 'border-red-900/40 text-red-300 bg-red-950/20',
                amber: 'border-amber-900/40 text-amber-300 bg-amber-950/20',
                emerald: 'border-emerald-900/40 text-emerald-300 bg-emerald-950/20',
                indigo: 'border-indigo-900/40 text-indigo-300 bg-indigo-950/20'
            };
            container.innerHTML = items.map(item => `<div class="text-xs border rounded-lg px-3 py-2 ${toneClass[tone] || toneClass.slate}">${item}</div>`).join('');
        }

        function stripHtml(input) {
            const div = document.createElement('div');
            div.innerHTML = input || '';
            return (div.textContent || div.innerText || '').replace(/\s+/g, ' ').trim();
        }

        function shortenText(input, maxLen = 36) {
            const text = stripHtml(input || '');
            return text.length > maxLen ? `${text.slice(0, maxLen)}…` : text;
        }

        function toggleMobileThemeDetail() {
            const panel = document.getElementById('mobile-theme-detail');
            const button = document.getElementById('mobile-theme-detail-toggle');
            if (!panel || !button) return;
            const isHidden = panel.classList.contains('hidden');
            panel.classList.toggle('hidden');
            button.textContent = isHidden ? '收起細節' : '看細節';
        }

        function renderMetaPanels(mapData) {
            const tags = document.getElementById('theme-tags-container');
            if (tags) {
                tags.innerHTML = (mapData.theme_tags || []).length
                    ? mapData.theme_tags.map(tag => `<span class="px-2 py-1 rounded-md bg-indigo-950/40 border border-indigo-900/40 text-indigo-300 text-xs">${tag}</span>`).join('')
                    : '<span class="text-[11px] text-slate-600">尚無主題標籤</span>';
            }
            renderBulletList('trigger-events-container', mapData.trigger_events || [], '尚無觸發事件', 'amber');
            renderBulletList('watch-signals-container', mapData.watch_signals || [], '尚無觀察訊號', 'emerald');
            renderBulletList('heat-drivers-container', mapData.heat_drivers || [], '尚無火勢驅動資料', 'red');
            renderBulletList('risks-container', mapData.risks || [], '尚無風險提示', 'slate');

            const related = document.getElementById('related-themes-container');
            if (related) {
                related.innerHTML = (mapData.related_themes || []).length
                    ? `
                        <div class="w-full rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                            <div class="text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">納入主題一起看</div>
                            <div class="flex flex-wrap gap-2">${mapData.related_themes.map(tag => `<span class="px-2 py-1 rounded-md bg-slate-950/70 border border-slate-800 text-slate-300 text-xs">${tag}</span>`).join('')}</div>
                        </div>
                    `
                    : '<span class="text-[11px] text-slate-600">目前無延伸主題</span>';
            }
        }

        function renderStructureLayers(mapData) {
            const container = document.getElementById('structure-layers-container');
            if (!container) return;
            const layers = mapData.structure_layers || [];
            if (!layers.length) {
                container.innerHTML = `<div class="col-span-full text-center text-slate-600 py-4 text-xs">目前沒有結構分層資料</div>`;
                return;
            }
            const pricingTone = value => value === 'high'
                ? 'border-amber-700/40 bg-amber-950/20 text-amber-300'
                : value === 'medium'
                    ? 'border-cyan-700/40 bg-cyan-950/20 text-cyan-300'
                    : 'border-slate-800 bg-slate-950/40 text-slate-300';
            container.innerHTML = layers.map(layer => `
                <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3">
                    <div>
                        <div class="text-cyan-300 font-bold text-sm">${layer.name || ''}</div>
                        <div class="text-[11px] text-slate-500 mt-1">位置：${layer.position || ''}</div>
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">${layer.summary || ''}</p>
                    <div class="grid grid-cols-2 gap-2 text-[11px]">
                        <div class="rounded-lg border ${pricingTone(layer.pricing_power)} px-3 py-2"><div class="text-slate-500 mb-1">定價權</div><div class="font-bold">${layer.pricing_power || '待補資料'}</div></div>
                        <div class="rounded-lg border border-fuchsia-900/30 bg-fuchsia-950/15 px-3 py-2"><div class="text-slate-500 mb-1">Value Capture</div><div class="font-bold text-fuchsia-300">${layer.value_capture || '待補資料'}</div></div>
                        <div class="rounded-lg border border-emerald-900/30 bg-emerald-950/15 px-3 py-2"><div class="text-slate-500 mb-1">利潤輪廓</div><div class="font-bold text-emerald-300">${layer.margin_profile || '待補資料'}</div></div>
                        <div class="rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2"><div class="text-slate-500 mb-1">進入門檻</div><div class="font-bold text-slate-200">${layer.entry_barrier || '待補資料'}</div></div>
                    </div>
                    <div>
                        <div class="text-[11px] text-slate-500 mb-1">關鍵重點</div>
                        <div class="flex flex-wrap gap-2">${(layer.key_points || []).map(x => `<span class="px-2 py-1 rounded bg-cyan-950/20 border border-cyan-900/30 text-cyan-300 text-xs">${x}</span>`).join('')}</div>
                    </div>
                    <div>
                        <div class="text-[11px] text-slate-500 mb-1">受惠族群</div>
                        <div class="flex flex-wrap gap-2">${(layer.beneficiaries || []).map(x => `<span class="px-2 py-1 rounded bg-indigo-950/20 border border-indigo-900/30 text-indigo-300 text-xs">${x}</span>`).join('')}</div>
                    </div>
                </div>
            `).join('');
        }

        function renderTimelinePhases(mapData) {
            const container = document.getElementById('timeline-phases-container');
            if (!container) return;
            const phases = mapData.timeline_phases || [];
            if (!phases.length) {
                container.innerHTML = `<div class="col-span-full text-center text-slate-600 py-4 text-xs">目前沒有時程資料</div>`;
                return;
            }
            container.innerHTML = phases.map(item => `
                <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800 space-y-3">
                    <div class="flex items-start justify-between gap-3">
                        <div>
                            <span class="text-xs font-bold text-emerald-400 block mb-1">${item.phase || ''}</span>
                            <div class="text-[11px] text-slate-500">${item.timeframe || ''}</div>
                        </div>
                        <span class="px-2 py-1 rounded bg-amber-950/20 border border-amber-900/30 text-amber-300 text-xs">${item.investment_phase || '待補資料'}</span>
                    </div>
                    <p class="text-xs text-slate-400 leading-relaxed">${item.summary || ''}</p>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px]">
                        <div class="rounded-lg border border-cyan-900/30 bg-cyan-950/15 px-3 py-2"><div class="text-slate-500 mb-1">營收意義</div><div class="text-cyan-200">${item.revenue_meaning || '待補資料'}</div></div>
                        <div class="rounded-lg border border-emerald-900/30 bg-emerald-950/15 px-3 py-2"><div class="text-slate-500 mb-1">觀察指標</div><div class="text-emerald-200">${item.watch_metric || '待補資料'}</div></div>
                        <div class="rounded-lg border border-fuchsia-900/30 bg-fuchsia-950/15 px-3 py-2"><div class="text-slate-500 mb-1">市場焦點</div><div class="text-fuchsia-200">${item.expected_market_focus || '待補資料'}</div></div>
                    </div>
                    <div class="flex flex-wrap gap-2">${(item.winners || []).map(x => `<span class="px-2 py-1 rounded bg-emerald-950/20 border border-emerald-900/30 text-emerald-300 text-xs">${x}</span>`).join('')}</div>
                </div>
            `).join('');
        }

        function renderCapitalFlow(mapData) {
            const container = document.getElementById('capital-flow-container');
            if (!container) return;
            const flows = mapData.capital_flow || [];
            if (!flows.length) {
                container.innerHTML = `<div class="text-center text-slate-600 py-4 text-xs">目前沒有資金流推演資料</div>`;
                return;
            }
            container.innerHTML = flows.map((item, index) => `
                <div class="relative bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3 overflow-hidden">
                    <div class="absolute left-0 top-0 bottom-0 w-1 ${index % 3 === 0 ? 'bg-red-500/70' : index % 3 === 1 ? 'bg-amber-500/70' : 'bg-cyan-500/70'}"></div>
                    <div class="flex items-start justify-between gap-3 pl-3">
                        <div>
                            <div class="text-red-300 font-bold text-sm">${item.phase || ''}</div>
                            <div class="text-[11px] text-slate-500 mt-1">${item.timeframe || ''}</div>
                        </div>
                        <span class="px-2 py-1 rounded bg-red-950/20 border border-red-900/30 text-red-300 text-xs">${item.focus || ''}</span>
                    </div>
                    <p class="text-sm text-slate-300 leading-relaxed pl-3">${item.logic || ''}</p>
                    <div class="flex flex-wrap gap-2 pl-3">${(item.beneficiary_groups || []).map(x => `<span class="px-2 py-1 rounded bg-amber-950/20 border border-amber-900/30 text-amber-300 text-xs">${x}</span>`).join('')}</div>
                </div>
            `).join('');
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById(`sec-${tabId}`).classList.remove('hidden');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.className = "tab-btn w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition text-slate-300 hover:bg-slate-800 hover:text-white");
            if(document.getElementById(`btn-${tabId}`)) document.getElementById(`btn-${tabId}`).className = "tab-btn w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition bg-indigo-600 text-white";
        }

        // 核心：雙股高階 PK 比較渲染
        function renderComparison() {
            const idA = document.getElementById('compare-a').value;
            const idB = document.getElementById('compare-b').value;
            const stockPool = getStockPool();
            const stockA = stockPool.find(s => s.id === idA);
            const stockB = stockPool.find(s => s.id === idB);
            
            const container = document.getElementById('comparison-result-cards');
            container.innerHTML = '';
            if (!stockA || !stockB) return;

            const createCardHTML = (stock, badgeColor, borderStyle) => `
                <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between space-y-4">
                    <div>
                        <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-2">
                            <div>
                                <h4 class="font-bold text-lg text-slate-100">${stock.name} <span class="text-xs font-mono text-indigo-400">[${stock.code}]</span></h4>
                                <span class="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 mt-1 inline-block">${stock.sector}</span>
                            </div>
                            <div class="text-right">
                                <div class="text-xs text-amber-400 font-bold">純度 ★${Number(stock.pureLevel).toFixed(1)}</div>
                                <div class="text-xs text-emerald-400 font-bold">壁壘 🛡️${Number(stock.barrierLevel).toFixed(1)}</div>
                            </div>
                        </div>
                        <div class="space-y-3 mt-4 text-xs">
                            <div>
                                <span class="text-indigo-300 font-bold block mb-1">💡 先進卡位角色</span>
                                <p class="text-slate-300 leading-relaxed">${stock.role}</p>
                            </div>
                            <div class="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800/60">
                                <div><span class="text-cyan-400 font-semibold block mb-0.5">🟢 技術優勢</span><p class="text-slate-400 text-[11px] leading-relaxed">${stock.pros}</p></div>
                                <div><span class="text-red-400 font-semibold block mb-0.5">🔴 投資風險</span><p class="text-slate-400 text-[11px] leading-relaxed">${stock.cons}</p></div>
                            </div>
                            <div class="grid grid-cols-2 gap-2 text-[11px]">
                                <div class="rounded-lg border border-emerald-900/30 bg-emerald-950/15 p-3"><div class="text-slate-500 mb-1">AI 營收含金量</div><div class="text-emerald-300 font-bold">${stock.ai_revenue_exposure || '待補資料'}</div></div>
                                <div class="rounded-lg border border-cyan-900/30 bg-cyan-950/15 p-3"><div class="text-slate-500 mb-1">毛利率走勢</div><div class="text-cyan-300 font-bold">${stock.gross_margin_impact || '待補資料'}</div></div>
                                <div class="rounded-lg border border-amber-900/30 bg-amber-950/15 p-3"><div class="text-slate-500 mb-1">客戶集中 / 獨家性</div><div class="text-amber-300 font-bold">${stock.customer_concentration || (stock.sole_supplier ? '具獨家供應潛力' : '待補資料')}</div></div>
                                <div class="rounded-lg border border-fuchsia-900/30 bg-fuchsia-950/15 p-3"><div class="text-slate-500 mb-1">Switching Cost / 取代風險</div><div class="text-fuchsia-300 font-bold">${stock.switching_cost || '待補資料'} / ${stock.substitution_risk || '待補資料'}</div></div>
                            </div>
                            <div>
                                <span class="text-amber-500 font-bold block mb-1">🚀 股價催化劑</span>
                                <p class="text-slate-300 leading-relaxed">${stock.catalyst}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = createCardHTML(stockA, 'indigo', 'indigo') + createCardHTML(stockB, 'teal', 'teal');
        }

        // 追蹤清單控制邏輯
        function toggleWatchlist(stockId) {
            const normalizedId = String(stockId || '').trim();
            if (!normalizedId) return;
            const index = watchlist.indexOf(normalizedId);
            if(index === -1) {
                watchlist.push(normalizedId);
                if (persistWatchlist()) showToast("已成功加入追蹤名單");
            } else {
                watchlist.splice(index, 1);
                if (persistWatchlist()) showToast("已從追蹤名單移除");
            }
            document.getElementById('watchlist-count').textContent = watchlist.length;
            renderWatchlist();
            filterTable(); // 同步重繪主表格星號
        }

        function clearWatchlist() {
            watchlist = [];
            const saved = persistWatchlist();
            document.getElementById('watchlist-count').textContent = 0;
            renderWatchlist();
            filterTable();
            if (saved) showToast('已清空追蹤名單');
        }

        function renderWatchlist() {
            const container = document.getElementById('watchlist-container');
            container.innerHTML = '';
            const stockPool = getStockPool();
            watchlist = watchlist.filter(id => stockPool.some(s => s.id === id));
            document.getElementById('watchlist-count').textContent = watchlist.length;
            if(watchlist.length === 0) {
                container.innerHTML = `
                    <div class="rounded-lg border border-dashed border-slate-700/70 bg-slate-950/40 p-3 text-center">
                        <div class="text-[11px] text-slate-400 font-semibold">還沒有追蹤股票</div>
                        <div class="mt-1 text-[11px] text-slate-500 leading-relaxed">到概念股列表或股票詳細頁，按「加入追蹤」就會出現在這裡。</div>
                    </div>`;
                return;
            }
            watchlist.forEach(id => {
                const stock = stockPool.find(s => s.id === id);
                if(!stock) return;
                const div = document.createElement('div');
                div.className = "bg-slate-950/60 p-3 border border-slate-800/60 rounded-lg text-xs space-y-2";
                div.innerHTML = `
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0">
                            <button onclick="openModal('${stock.id}')" class="text-left font-medium text-slate-200 hover:text-indigo-400 transition">${stock.name} <span class="text-[10px] text-slate-500 font-mono">(${stock.code})</span></button>
                            <div class="mt-1 text-[11px] text-slate-500">${stock.sector || '未分類'} ｜ ${stockTierLabel(stock.stock_tier)}</div>
                        </div>
                        <button onclick="toggleWatchlist('${stock.id}')" class="text-red-400/80 hover:text-red-400 transition"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
                    </div>
                    <div class="text-[11px] text-slate-400 leading-relaxed">${shortenText(stock.role || stock.pros || '待補追蹤理由', 42)}</div>
                `;
                container.appendChild(div);
            });
            lucide.createIcons();
        }

        // Modal 控制
        function updateModalWatchlistButton(stockId) {
            const btn = document.getElementById('modal-watchlist-btn');
            const text = document.getElementById('modal-watchlist-btn-text');
            if (!btn || !text) return;
            const watched = watchlist.includes(stockId);
            btn.className = `inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition ${watched ? 'border-amber-700 bg-amber-950/40 text-amber-300 hover:bg-amber-950/60' : 'border-indigo-800 bg-indigo-950/40 text-indigo-300 hover:bg-indigo-950/70'}`;
            btn.innerHTML = `${watched ? '<i data-lucide="bookmark-check" class="w-4 h-4"></i>' : '<i data-lucide="bookmark-plus" class="w-4 h-4"></i>'}<span id="modal-watchlist-btn-text">${watched ? '已加入追蹤名單' : '加入我的追蹤名單'}</span>`;
        }

        function toggleWatchlistFromModal() {
            if (!currentModalStockId) return;
            toggleWatchlist(currentModalStockId);
            updateModalWatchlistButton(currentModalStockId);
            lucide.createIcons();
        }

        function openModal(stockId) {
            let stock = null;
            if (currentMapData) {
                const stockPool = getStockPool();
                stock = stockPool.find(s => s.id === stockId);
            }
            
            // 如果在主題內找不到，試著從全市場個股 Wiki 載入
            if (!stock && stocksWiki[stockId]) {
                const wiki = stocksWiki[stockId];
                const details = wiki.details || {};
                stock = {
                    id: wiki.code,
                    code: wiki.code,
                    name: wiki.name,
                    sector: wiki.industry,
                    role: wiki.summary,
                    desc: wiki.summary,
                    pureLevel: details.pureLevel || 0,
                    barrierLevel: details.barrierLevel || 0,
                    ai_revenue_exposure: details.ai_revenue_exposure || '待補資料',
                    gross_margin_impact: details.gross_margin_impact || '待補資料',
                    pricing_power: details.pricing_power || '待補資料',
                    value_capture_score: details.value_capture_score || 0,
                    substitution_risk: details.substitution_risk || '待補資料',
                    commercialization_phase: details.commercialization_phase || '待補資料',
                    customer_concentration: '待補資料',
                    switching_cost: '待補資料',
                    pros: details.pros || '提供相關產業產品與服務。',
                    cons: details.cons || '無特定題材警示，請依基本面為準。',
                    catalyst: details.catalyst || '板塊輪動與營收放量。',
                    stock_tier: wiki.tier,
                    evidence_type: 'inferred',
                    linkage: [],
                    sources: []
                };
            }

            if(!stock) return;
            currentModalStockId = stock.id;

            document.getElementById('modal-stock-name').innerHTML = `${stock.name} <span class="text-sm text-slate-400 font-mono">${stock.code}</span>`;
            document.getElementById('modal-stock-sector').textContent = stock.sector;
            document.getElementById('modal-stock-pure').textContent = `★ ${Number(stock.pureLevel).toFixed(1)} / 5.0`;
            document.getElementById('modal-stock-barrier').textContent = `🛡️ ${Number(stock.barrierLevel).toFixed(1)} / 5.0`;
            document.getElementById('modal-stock-ai-revenue').textContent = stock.ai_revenue_exposure || '待補資料';
            document.getElementById('modal-stock-gm').textContent = stock.gross_margin_impact || '待補資料';
            document.getElementById('modal-stock-pricing').textContent = `${stock.pricing_power || '待補資料'} / ${stock.value_capture_score ?? '待補資料'}`;
            document.getElementById('modal-stock-substitution').textContent = stock.substitution_risk || '待補資料';
            document.getElementById('modal-stock-timeframe').textContent = stock.commercialization_phase || stock.timeframe;
            document.getElementById('modal-stock-customer').textContent = `${stock.customer_concentration || '待補資料'}${stock.sole_supplier ? ' / 獨家供應可能' : ''} / Switching Cost ${stock.switching_cost || '待補資料'}`;
            document.getElementById('modal-stock-role').textContent = stock.role;
            document.getElementById('modal-stock-pros').textContent = stock.pros;
            document.getElementById('modal-stock-cons').textContent = stock.cons;
            document.getElementById('modal-stock-catalyst').textContent = stock.catalyst;
            document.getElementById('modal-stock-tags').textContent = `${stockTierLabel(stock.stock_tier)} ／ ${evidenceTypeLabel(stock.evidence_type)}`;
            document.getElementById('modal-stock-linkage').innerHTML = renderModalLinkage(stock);
            document.getElementById('modal-stock-sources').innerHTML = renderModalSources(stock);
            document.getElementById('modal-stock-desc').textContent = stock.desc;

            // Render Product Tags & Industry Tag
            const productTagsContainer = document.getElementById('modal-stock-product-tags');
            if (productTagsContainer) {
                productTagsContainer.innerHTML = '';
                if (stock.sector) {
                    const indTag = document.createElement('button');
                    indTag.className = "px-2.5 py-1 rounded-lg bg-slate-950 border border-indigo-900/60 text-indigo-400 hover:text-white hover:bg-indigo-950/40 text-xs transition duration-200";
                    indTag.textContent = stock.sector;
                    indTag.onclick = () => searchTag(stock.sector);
                    productTagsContainer.appendChild(indTag);
                }
                const wiki = stocksWiki[stock.id];
                if (wiki && Array.isArray(wiki.products)) {
                    wiki.products.forEach(p => {
                        const pTag = document.createElement('button');
                        pTag.className = "px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white hover:border-indigo-500 text-xs transition duration-200";
                        pTag.textContent = p;
                        pTag.onclick = () => searchTag(p);
                        productTagsContainer.appendChild(pTag);
                    });
                }
            }

            // Render Theme Tags
            const themeTagsContainer = document.getElementById('modal-stock-theme-tags');
            if (themeTagsContainer) {
                themeTagsContainer.innerHTML = '';
                const wiki = stocksWiki[stock.id];
                if (wiki && Array.isArray(wiki.themes) && wiki.themes.length > 0) {
                    wiki.themes.forEach(t => {
                        const tTag = document.createElement('button');
                        tTag.className = "px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-900/60 text-emerald-400 hover:text-white hover:bg-emerald-950/60 text-xs transition duration-200";
                        tTag.textContent = t;
                        tTag.onclick = () => clickTheme(t);
                        themeTagsContainer.appendChild(tTag);
                    });
                } else {
                    themeTagsContainer.innerHTML = `<span class="text-xs text-slate-500">暫無參與產業主題</span>`;
                }
            }

            // Calculate & Render Related Stocks
            const relatedContainer = document.getElementById('modal-stock-related');
            if (relatedContainer) {
                relatedContainer.innerHTML = '';
                const currentWiki = stocksWiki[stock.id];
                if (currentWiki) {
                    const relatedStocks = [];
                    const allStockKeys = Object.keys(stocksWiki);
                    
                    for (const code of allStockKeys) {
                        if (code === stock.id) continue;
                        const otherWiki = stocksWiki[code];
                        let score = 0;
                        
                        // Theme match (highest priority)
                        if (currentWiki.themes && otherWiki.themes) {
                            const commonThemes = currentWiki.themes.filter(t => otherWiki.themes.includes(t));
                            score += commonThemes.length * 5;
                        }
                        
                        // Product match
                        if (currentWiki.products && otherWiki.products) {
                            const commonProducts = currentWiki.products.filter(p => otherWiki.products.includes(p));
                            score += commonProducts.length * 3;
                        }
                        
                        // Industry match
                        if (currentWiki.industry === otherWiki.industry) {
                            score += 2;
                        }
                        
                        if (score > 0) {
                            relatedStocks.push({
                                code: otherWiki.code,
                                name: otherWiki.name,
                                industry: otherWiki.industry,
                                score: score
                            });
                        }
                    }
                    
                    relatedStocks.sort((a, b) => b.score - a.score || a.code.localeCompare(b.code));
                    const topRelated = relatedStocks.slice(0, 6);
                    if (topRelated.length > 0) {
                        topRelated.forEach((rel, i) => {
                            const btn = document.createElement('button');
                            btn.className = "px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white hover:border-indigo-500 text-xs transition duration-200";
                            btn.innerHTML = `${i + 1}. ${rel.name} <span class="font-mono text-slate-500 text-[10px]">${rel.code}</span>`;
                            btn.onclick = () => openModal(rel.code);
                            relatedContainer.appendChild(btn);
                        });
                    } else {
                        relatedContainer.innerHTML = `<span class="text-xs text-slate-500">暫無推薦關聯個股</span>`;
                    }
                } else {
                    relatedContainer.innerHTML = `<span class="text-xs text-slate-500">暫無推薦關聯個股</span>`;
                }
            }

            updateModalWatchlistButton(stock.id);
            document.getElementById('stock-modal').classList.remove('hidden');
            lucide.createIcons();

            // Render TradingView Chart for this stock
            renderStockTradingViewChart(stock.code);
        }

        function closeModal() {
            currentModalStockId = null;
            document.getElementById('stock-modal').classList.add('hidden');
            const container = document.getElementById('modal-tv-chart-container');
            if (container) container.classList.add('hidden');
            const tvChartDiv = document.getElementById('tv-chart-stock');
            if (tvChartDiv) tvChartDiv.innerHTML = '';
            const linksContainer = document.getElementById('modal-external-links');
            if (linksContainer) linksContainer.classList.add('hidden');
        }

        let modalTvWidget = null;
        function renderStockTradingViewChart(code) {
            const container = document.getElementById('modal-tv-chart-container');
            const tvChartDiv = document.getElementById('tv-chart-stock');
            const linksContainer = document.getElementById('modal-external-links');
            const linkTV = document.getElementById('link-tradingview');
            const linkYahoo = document.getElementById('link-yahoo');

            if (!container || !tvChartDiv) return;

            if (!code) {
                container.classList.add('hidden');
                if (linksContainer) linksContainer.classList.add('hidden');
                return;
            }

            // Update external links immediately based on stock market (Taiwan vs US)
            const isTaiwanStock = /^\d+$/.test(code);
            if (linksContainer && linkTV && linkYahoo) {
                linksContainer.classList.remove('hidden');
                if (isTaiwanStock) {
                    // Detect TWSE vs TPEX from stocksWiki
                    let market = "TWSE";
                    if (stocksWiki[code] && stocksWiki[code].market) {
                        market = stocksWiki[code].market.toUpperCase();
                    }
                    linkTV.href = `https://www.tradingview.com/chart/?symbol=${market}%3A${code}`;
                    linkYahoo.href = `https://tw.stock.yahoo.com/quote/${code}.TW`;
                } else {
                    let market = "NASDAQ";
                    if (code.toUpperCase() === 'TSM') {
                        market = "NYSE";
                    }
                    linkTV.href = `https://www.tradingview.com/chart/?symbol=${market}%3A${code}`;
                    linkYahoo.href = `https://finance.yahoo.com/quote/${code}`;
                }
            }

            // If it's a Taiwan stock, hide the K-line preview container because TWSE blocks external widget embeds
            if (isTaiwanStock) {
                container.classList.add('hidden');
                return;
            }

            // Otherwise, it's a US stock (e.g. NVDA, AAPL, MU) which supports external embeds
            container.classList.remove('hidden');
            tvChartDiv.innerHTML = '<div class="absolute inset-0 flex items-center justify-center text-xs text-slate-500"><i class="w-4 h-4 animate-spin mr-2 border-2 border-indigo-500 border-t-transparent rounded-full"></i> 正在載入個股技術圖表...</div>';

            // Delay execution by 150ms to ensure the modal display style has updated and layout is calculated
            setTimeout(() => {
                if (typeof TradingView === 'undefined') {
                    console.warn('TradingView library not loaded yet for stock chart, retrying...');
                    setTimeout(() => renderStockTradingViewChart(code), 200);
                    return;
                }

                tvChartDiv.innerHTML = ''; // Clear loading spinner

                // We default to US stock parameters since Taiwan stocks return early
                let symbol = code;
                if (code.toUpperCase() === 'TSM') {
                    symbol = 'NYSE:TSM';
                } else if (!symbol.includes(':')) {
                    symbol = `NASDAQ:${code}`;
                }

                modalTvWidget = new TradingView.widget({
                    "width": "100%",
                    "height": "100%",
                    "symbol": symbol,
                    "interval": "D",
                    "timezone": "America/New_York",
                    "theme": "dark",
                    "style": "1",
                    "locale": "zh_TW",
                    "toolbar_bg": "#111827",
                    "enable_publishing": false,
                    "hide_side_toolbar": true,
                    "allow_symbol_change": false,
                    "container_id": "tv-chart-stock",
                    "studies": [
                        "MASimple@tv-basicstudies"
                    ]
                });
            }, 150);
        }

        // Toast Helper
        function showToast(message) {
            const toast = document.getElementById('toast');
            document.getElementById('toast-text').textContent = message;
            toast.className = "fixed bottom-5 right-5 bg-indigo-600 text-white text-xs font-semibold py-2.5 px-4 rounded-lg shadow-lg transform translate-y-0 opacity-100 transition duration-300 z-50 flex items-center gap-2";
            setTimeout(() => {
                toast.className = "fixed bottom-5 right-5 bg-indigo-600 text-white text-xs font-semibold py-2.5 px-4 rounded-lg shadow-lg transform translate-y-20 opacity-0 transition duration-300 z-50 flex items-center gap-2";
            }, 2000);
        }

        // 個股 Wiki 導覽控制與渲染
        function showStockWiki() {
            hideAllPanels();
            document.getElementById('panel-stock-wiki').classList.remove('hidden');
            document.getElementById('nav-btn-wiki').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";
            
            renderStockWiki();
        }
        
        function showDashboardHome() {
            hideAllPanels();
            document.getElementById('panel-home').classList.remove('hidden');
            document.getElementById('nav-btn-home').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";
            
            renderDashboardHome();
        }

        function showTechDocs() {
            hideAllPanels();
            if (document.getElementById('panel-tech-docs')) document.getElementById('panel-tech-docs').classList.remove('hidden');
            if (document.getElementById('nav-btn-tech')) document.getElementById('nav-btn-tech').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";
            
            lucide.createIcons();
        }

        function showMacroPage() {
            hideAllPanels();
            if (document.getElementById('panel-macro-market')) document.getElementById('panel-macro-market').classList.remove('hidden');
            if (document.getElementById('nav-btn-macro')) document.getElementById('nav-btn-macro').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";

            renderMacroCharts();
            loadMacroAIAnalysis();
            lucide.createIcons();
        }

        function renderMacroCharts() {
            if (typeof TradingView === 'undefined') {
                console.warn('TradingView library not loaded yet for macro charts, retrying...');
                setTimeout(renderMacroCharts, 200);
                return;
            }
            renderMiniChart("TVC:GOLD", "tv-chart-macro-gold");
            renderMiniChart("TVC:USOIL", "tv-chart-macro-oil");
            renderMiniChart("TVC:COPPER", "tv-chart-macro-copper");
            renderMiniChart("FX_IDC:USDTWD", "tv-chart-macro-usdtwd");
            renderMiniChart("INDEX:DXY", "tv-chart-macro-dxy");
            renderMiniChart("FX:USDJPY", "tv-chart-macro-usdjpy");
        }

        function formatMacroAnalysisText(text) {
            if (!text) return '無分析資料';
            let lines = text.split('\n');
            let html = '';
            lines.forEach(line => {
                line = line.trim();
                if (!line) return;
                
                if (line.startsWith('【') && line.endsWith('】')) {
                    html += `<h4 class="text-xs font-bold text-cyan-300 mt-4 mb-2 flex items-center gap-1.5"><span class="w-1.5 h-3.5 bg-cyan-400 rounded-sm animate-pulse"></span>${line}</h4>`;
                } else if (line.match(/^\d+\.\s/)) {
                    html += `<div class="pl-4 border-l border-cyan-800/40 py-1.5 my-2 text-slate-300 font-medium">${line}</div>`;
                } else {
                    html += `<p class="mb-2 text-slate-400 leading-relaxed">${line}</p>`;
                }
            });
            return html;
        }

        async function loadMacroAIAnalysis() {
            const container = document.getElementById('macro-ai-analysis-content');
            if (!container) return;
            
            try {
                const versionStamp = new Date().getTime();
                const res = await fetch(`./macro_ai_analysis.json?v=${versionStamp}`);
                if (!res.ok) throw new Error('File not found');
                const data = await res.json();
                container.innerHTML = formatMacroAnalysisText(data.analysis);
            } catch (err) {
                console.warn('Failed to load macro AI analysis from file, using static fallback:', err);
                const fallbackAnalysis = `【AI 總經趨勢解讀與投資策略】

台灣目前經濟呈現高成長、溫和通膨的強勁擴張格局。GDP 年增率達 9.64%（創 2010 年來新高），主要受惠於全球 AI 伺服器建置熱潮與先進半導體出口訂單動能爆發。製造業 PMI 達 55.4%，顯示製造業景氣擴張步伐穩固。然而，勞動市場失業率降至 3.38% 的低點，呈現人力吃緊狀態，加上消費者物價指數 (CPI) 仍在 2.24% 的通膨警戒線上方運行。預估央行短期內將維持 2.000% 的偏緊利率政策，以防範房市過熱與輸入型通膨回潮。

【台股策略性資產配置建議】

1. 💡 AI半導體與先進代工（核心持倉）：
台積電先進製程與 CoWoS 產能能見度直達 2027 年，代工與封裝報價調漲預期將支撐毛利率擴張。聯電受惠於成熟製程穩定需求與外資回頭加碼，估值轉換邏輯清晰。半導體板塊拉回皆是長線布局機會。

2. 🛡️ 高本益比個股避險（防禦性調節）：
大盤目前站上 45,000 點高位，若美股費半出現獲利回吐，應警惕缺乏實質獲利支撐的純題材股。建議逢高調節高本益比個股，縮短交易持倉週期。

3. 🏦 利率敏感與防禦板塊（穩定底倉）：
在緊縮政策與高利率環境延續下，金融股具備利差擴大與防禦利基，建議配置大型金控與高股息龍頭作為資產防護網。`;
                container.innerHTML = formatMacroAnalysisText(fallbackAnalysis);
            }
        }

        async function triggerMacroAIAnalysis() {
            const container = document.getElementById('macro-ai-analysis-content');
            if (!container) return;
            
            container.innerHTML = `
                <div class="flex items-center gap-2 text-cyan-400 py-4 font-semibold text-xs justify-center">
                    <svg class="animate-spin h-4 w-4 text-cyan-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    vLLM 伺服器分析中，這可能需要幾秒鐘時間...
                </div>
            `;
            
            try {
                const res = await fetch('/api/update_macro');
                if (!res.ok) throw new Error('API server unreachable');
                const data = await res.json();
                container.innerHTML = formatMacroAnalysisText(data.analysis);
                showToast('AI 總經分析更新成功！');
            } catch (err) {
                console.warn('API update failed, running local mock simulation...', err);
                setTimeout(() => {
                    showToast('本機 vLLM 連線失敗，啟動動態模擬分析...');
                    loadMacroAIAnalysis();
                }, 1500);
            }
        }

        function showIndustryPricing() {
            hideAllPanels();
            if (document.getElementById('panel-industry-pricing')) document.getElementById('panel-industry-pricing').classList.remove('hidden');
            if (document.getElementById('nav-btn-industry')) document.getElementById('nav-btn-industry').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";

            renderIndustryCharts();
            lucide.createIcons();
        }

        function renderIndustryCharts() {
            if (typeof TradingView === 'undefined') {
                console.warn('TradingView library not loaded yet for industry charts, retrying...');
                setTimeout(renderIndustryCharts, 200);
                return;
            }
            // Memory & Semiconductor
            renderMiniChart("NASDAQ:MU", "tv-chart-ind-mu");
            renderMiniChart("FRA:HY9H", "tv-chart-ind-skhynix");
            renderMiniChart("LSE:SMSN", "tv-chart-ind-samsung");
            renderMiniChart("NASDAQ:SOXX", "tv-chart-ind-soxx");
            renderMiniChart("NASDAQ:WDC", "tv-chart-ind-wdc");
            // Industrial Commodities & Energy
            renderMiniChart("TVC:NATGAS", "tv-chart-ind-natgas");
            renderMiniChart("CAPITALCOM:NICKEL", "tv-chart-ind-nickel");
            renderMiniChart("CAPITALCOM:ALUMINUM", "tv-chart-ind-aluminum");
            renderMiniChart("CAPITALCOM:TIN", "tv-chart-ind-tin");
            renderMiniChart("TVC:PLATINUM", "tv-chart-ind-platinum");
            renderMiniChart("INDEX:BDI", "tv-chart-ind-bdi");
        }
        // ==========================================
        // 三大法人籌碼分析分頁控制與渲染
        // ==========================================
        let currentChipsData = null;
        let currentThemeCategory = 'cohort';

        function switchThemeCategory(category) {
            currentThemeCategory = category;
            const buttons = ['cohort', 'surge', 'foreign_ratio', 'trust_ratio'];
            buttons.forEach(btn => {
                const el = document.getElementById(`theme-btn-${btn}`);
                if (el) {
                    if (btn === category) {
                        el.className = "px-2.5 py-1 text-[10px] font-bold rounded text-amber-400 bg-slate-800 transition";
                    } else {
                        el.className = "px-2.5 py-1 text-[10px] font-bold rounded text-slate-400 hover:text-white transition";
                    }
                }
            });
            renderThemeCards();
        }

        function renderThemeCards() {
            const focusContainer = document.getElementById('chips-focus-themes-container');
            if (!focusContainer || !currentChipsData) return;
            focusContainer.innerHTML = '';

            const themesKey = `${currentThemeCategory}_themes`;
            const themes = currentChipsData[themesKey] || [];

            if (themes.length > 0) {
                themes.forEach(theme => {
                    const stocksHTML = theme.stocks.map(s => {
                        let ratioLabel = '';
                        if (currentThemeCategory === 'foreign_ratio') {
                            ratioLabel = `<span class="text-cyan-400 font-bold ml-1">外本:${s.foreign_ratio}%</span>`;
                        } else if (currentThemeCategory === 'trust_ratio') {
                            ratioLabel = `<span class="text-purple-400 font-bold ml-1">投本:${s.trust_ratio}%</span>`;
                        }
                        return `
                            <div class="flex items-center justify-between py-1 border-b border-slate-800/40 text-[11px]">
                                <div class="flex items-center gap-1">
                                    <span class="text-slate-400 font-mono">${s.symbol}</span>
                                    <span class="text-slate-200 font-bold hover:text-cyan-400 cursor-pointer" onclick="showStockDetailsFromChips('${s.symbol}')">${s.name}</span>
                                </div>
                                <div class="flex items-center gap-2 font-mono text-[10px]">
                                    <span class="text-emerald-400" title="外資">外:${s.foreign_net > 0 ? '+' + s.foreign_net : s.foreign_net}</span>
                                    <span class="text-violet-400" title="投信">投:${s.trust_net > 0 ? '+' + s.trust_net : s.trust_net}</span>
                                    <span class="text-slate-300 font-bold" title="合計">合:${s.total_net > 0 ? '+' + s.total_net : s.total_net}</span>
                                    ${ratioLabel}
                                </div>
                            </div>
                        `;
                    }).join('');

                    let valLabel = '合計吸金';
                    let valUnit = '張';
                    if (currentThemeCategory === 'foreign_ratio' || currentThemeCategory === 'trust_ratio') {
                        valLabel = '合計比率';
                        valUnit = '%';
                    }

                    const card = document.createElement('div');
                    card.className = "bg-slate-950 border border-amber-900/30 hover:border-amber-500/50 rounded-xl p-4 space-y-3 transition shadow-lg relative overflow-hidden group";
                    card.innerHTML = `
                        <div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-amber-500/5 to-transparent rounded-full -mr-6 -mt-6 group-hover:scale-125 transition"></div>
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-extrabold text-amber-400 bg-amber-950/40 border border-amber-900/40 px-2 py-0.5 rounded flex items-center gap-1">
                                <i data-lucide="flame" class="w-3.5 h-3.5 text-amber-500 animate-bounce"></i> 今日焦點佈局
                            </span>
                            <span class="text-[10px] text-slate-500 font-mono">${valLabel}: <strong class="text-slate-300 font-bold font-mono">${theme.total_net_buy}</strong> ${valUnit}</span>
                        </div>
                        <h4 class="text-sm font-bold text-slate-100">${theme.theme_name}</h4>
                        <div class="space-y-1 bg-slate-900/40 border border-slate-900 rounded-lg p-2 max-h-[140px] overflow-y-auto">
                            ${stocksHTML}
                        </div>
                    `;
                    focusContainer.appendChild(card);
                });
            } else {
                focusContainer.innerHTML = `
                    <div class="col-span-2 border border-slate-800/80 bg-slate-950/40 rounded-xl py-8 text-center text-slate-500 text-xs">
                        <i data-lucide="alert-circle" class="w-6 h-6 mx-auto mb-2 text-slate-600"></i>
                        今日暫無符合條件的概念題材。
                    </div>
                `;
            }
            lucide.createIcons();
        }

        function switchChipsTab(tabName) {
            const tabs = ['cohort', 'foreign_buys', 'trust_buys', 'foreign_surges', 'trust_surges', 'foreign_ratio', 'trust_ratio'];
            tabs.forEach(tab => {
                const tableEl = document.getElementById(`chips-table-${tab}`);
                const btnEl = document.getElementById(`tab-btn-${tab}`);
                if (tableEl) tableEl.classList.add('hidden');
                if (btnEl) btnEl.className = "px-4 py-2 text-xs font-bold border-b-2 border-transparent text-slate-400 hover:text-white transition whitespace-nowrap";
            });
            
            const targetTable = document.getElementById(`chips-table-${tabName}`);
            const targetBtn = document.getElementById(`tab-btn-${tabName}`);
            if (targetTable) targetTable.classList.remove('hidden');
            if (targetBtn) targetBtn.className = "px-4 py-2 text-xs font-bold border-b-2 border-emerald-500 text-emerald-400 transition whitespace-nowrap";
        }

        function showChipsAnalysis() {
            hideAllPanels();
            if (document.getElementById('panel-chips-analysis')) document.getElementById('panel-chips-analysis').classList.remove('hidden');
            if (document.getElementById('nav-btn-chips')) document.getElementById('nav-btn-chips').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";

            loadAndRenderChips();
        }

        async function loadAndRenderChips() {
            const focusContainer = document.getElementById('chips-focus-themes-container');
            const cohortTbody = document.getElementById('chips-cohort-tbody');
            const fBuysTbody = document.getElementById('chips-foreign_buys-tbody');
            const tBuysTbody = document.getElementById('chips-trust_buys-tbody');
            const fSurgesTbody = document.getElementById('chips-foreign_surges-tbody');
            const tSurgesTbody = document.getElementById('chips-trust_surges-tbody');
            const foreignRatioTbody = document.getElementById('chips-foreign_ratio-tbody');
            const trustRatioTbody = document.getElementById('chips-trust_ratio-tbody');

            if (!focusContainer) return;
            
            focusContainer.innerHTML = '<div class="col-span-2 py-8 text-center text-slate-500">載入中...</div>';
            cohortTbody.innerHTML = '<tr><td colspan="7" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            if (fBuysTbody) fBuysTbody.innerHTML = '<tr><td colspan="9" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            if (tBuysTbody) tBuysTbody.innerHTML = '<tr><td colspan="9" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            if (fSurgesTbody) fSurgesTbody.innerHTML = '<tr><td colspan="7" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            if (tSurgesTbody) tSurgesTbody.innerHTML = '<tr><td colspan="7" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            if (foreignRatioTbody) foreignRatioTbody.innerHTML = '<tr><td colspan="9" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            if (trustRatioTbody) trustRatioTbody.innerHTML = '<tr><td colspan="9" class="py-4 text-center text-slate-500">載入中...</td></tr>';
            
            try {
                const response = await fetch('./institutional_chips_summary.json');
                if (!response.ok) {
                    throw new Error('未找到最新的籌碼摘要資料，請執行 daily pipeline 進行抓取。');
                }
                const summary = await response.json();
                currentChipsData = summary;
                
                document.getElementById('chips-data-date').textContent = summary.date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
                document.getElementById('chips-update-time').textContent = summary.update_time;

                renderThemeCards();
                
                const flowContainer = document.getElementById('chips-theme-flow-container');
                if (flowContainer) {
                    const inflows = summary.theme_inflows || [];
                    if (inflows.length > 0) {
                        flowContainer.innerHTML = inflows.map((item, idx) => {
                            let rankColor = 'text-emerald-400';
                            if (idx === 0) rankColor = 'text-amber-400';
                            else if (idx === 1) rankColor = 'text-cyan-300';
                            
                            return `
                                <div class="flex flex-col gap-1 py-2 border-b border-slate-800/40 text-xs">
                                    <div class="flex items-center justify-between">
                                        <div class="flex items-center gap-2">
                                            <span class="w-5 h-5 flex items-center justify-center rounded bg-slate-900 font-mono font-bold ${rankColor}">#${idx + 1}</span>
                                            <span class="text-slate-100 font-bold">${item.theme_name}</span>
                                        </div>
                                        <span class="font-mono font-bold text-emerald-400">+${item.total_net} 張</span>
                                    </div>
                                    <div class="flex items-center justify-between text-[10px] text-slate-500">
                                        <span>共 ${item.count} 檔發動</span>
                                        <span class="max-w-[150px] truncate text-slate-400" title="${item.stocks.join(', ')}">${item.stocks.slice(0, 3).join(', ')}${item.stocks.length > 3 ? '...' : ''}</span>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    } else {
                        flowContainer.innerHTML = '<div class="py-4 text-center text-slate-500 text-xs">今日無明顯同買資金流入題材。</div>';
                    }
                }

                const renderRows = (stocks, tbody, showRatios = true) => {
                    tbody.innerHTML = '';
                    const cols = showRatios ? 9 : 7;
                    if (stocks && stocks.length > 0) {
                        stocks.forEach(s => {
                            const tr = document.createElement('tr');
                            tr.className = "hover:bg-slate-900/30 transition text-[11px] border-b border-slate-800/40";
                            
                            const fRatioStr = s.foreign_ratio ? (s.foreign_ratio > 0 ? '+' + s.foreign_ratio + '%' : s.foreign_ratio + '%') : '0.00%';
                            const tRatioStr = s.trust_ratio ? (s.trust_ratio > 0 ? '+' + s.trust_ratio + '%' : s.trust_ratio + '%') : '0.00%';
                            
                            if (showRatios) {
                                tr.innerHTML = `
                                    <td class="py-2.5 font-mono text-slate-400">${s.symbol}</td>
                                    <td class="py-2.5 font-bold text-slate-200 hover:text-cyan-400 cursor-pointer" onclick="showStockDetailsFromChips('${s.symbol}')">${s.name}</td>
                                    <td class="py-2.5 text-right font-mono ${s.foreign_net > 0 ? 'text-emerald-400' : s.foreign_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.foreign_net > 0 ? '+' + s.foreign_net : s.foreign_net}</td>
                                    <td class="py-2.5 text-right font-mono text-cyan-300 font-bold">${fRatioStr}</td>
                                    <td class="py-2.5 text-right font-mono ${s.trust_net > 0 ? 'text-emerald-400' : s.trust_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.trust_net > 0 ? '+' + s.trust_net : s.trust_net}</td>
                                    <td class="py-2.5 text-right font-mono text-purple-300 font-bold">${tRatioStr}</td>
                                    <td class="py-2.5 text-right font-mono ${s.dealer_net > 0 ? 'text-emerald-400' : s.dealer_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.dealer_net > 0 ? '+' + s.dealer_net : s.dealer_net}</td>
                                    <td class="py-2.5 text-right font-mono font-bold ${s.total_net > 0 ? 'text-emerald-400' : s.total_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.total_net > 0 ? '+' + s.total_net : s.total_net}</td>
                                    <td class="py-2.5 pl-4 text-slate-400 text-[10px] max-w-[200px] truncate" title="${(s.themes || []).join(', ')}">${(s.themes || []).join(', ') || '-'}</td>
                                `;
                            } else {
                                tr.innerHTML = `
                                    <td class="py-2.5 font-mono text-slate-400">${s.symbol}</td>
                                    <td class="py-2.5 font-bold text-slate-200 hover:text-cyan-400 cursor-pointer" onclick="showStockDetailsFromChips('${s.symbol}')">${s.name}</td>
                                    <td class="py-2.5 text-right font-mono ${s.foreign_net > 0 ? 'text-emerald-400' : s.foreign_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.foreign_net > 0 ? '+' + s.foreign_net : s.foreign_net}</td>
                                    <td class="py-2.5 text-right font-mono ${s.trust_net > 0 ? 'text-emerald-400' : s.trust_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.trust_net > 0 ? '+' + s.trust_net : s.trust_net}</td>
                                    <td class="py-2.5 text-right font-mono ${s.dealer_net > 0 ? 'text-emerald-400' : s.dealer_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.dealer_net > 0 ? '+' + s.dealer_net : s.dealer_net}</td>
                                    <td class="py-2.5 text-right font-mono font-bold ${s.total_net > 0 ? 'text-emerald-400' : s.total_net < 0 ? 'text-red-400' : 'text-slate-500'}">${s.total_net > 0 ? '+' + s.total_net : s.total_net}</td>
                                    <td class="py-2.5 pl-4 text-slate-400 text-[10px] max-w-[200px] truncate" title="${(s.themes || []).join(', ')}">${(s.themes || []).join(', ') || '-'}</td>
                                `;
                            }
                            tbody.appendChild(tr);
                        });
                    } else {
                        tbody.innerHTML = `<tr><td colspan="${cols}" class="py-6 text-center text-slate-600">今日暫無符合條件之個股。</td></tr>`;
                    }
                };

                renderRows(summary.cohort_buys, cohortTbody, false);
                if (fBuysTbody) renderRows(summary.top_foreign_buys, fBuysTbody, true);
                if (tBuysTbody) renderRows(summary.top_trust_buys, tBuysTbody, true);
                if (fSurgesTbody) renderRows(summary.foreign_surges, fSurgesTbody, false);
                if (tSurgesTbody) renderRows(summary.trust_surges, tSurgesTbody, false);
                if (foreignRatioTbody) renderRows(summary.top_foreign_ratio, foreignRatioTbody, true);
                if (trustRatioTbody) renderRows(summary.top_trust_ratio, trustRatioTbody, true);

                lucide.createIcons();
            } catch (err) {
                console.error(err);
                focusContainer.innerHTML = `
                    <div class="col-span-2 border border-red-900/30 bg-red-950/10 rounded-xl py-8 text-center text-red-400 text-xs">
                        <i data-lucide="alert-triangle" class="w-6 h-6 mx-auto mb-2 text-red-500"></i>
                        ${err.message || '無法下載或載入籌碼統計數據'}
                    </div>
                `;
                cohortTbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-red-400 text-xs">${err.message || '資料載入失敗'}</td></tr>`;
            }
        }

        function showExpectationsGap() {
            hideAllPanels();
            if (document.getElementById('panel-expectations')) document.getElementById('panel-expectations').classList.remove('hidden');
            if (document.getElementById('nav-btn-expectations')) document.getElementById('nav-btn-expectations').className = "px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-slate-800 transition whitespace-nowrap";
            loadAndRenderExpectations();
        }

        async function loadAndRenderExpectations() {
            const container = document.getElementById('expectations-cards-container');
            if (!container) return;
            container.innerHTML = '<div class="col-span-2 py-12 text-center text-slate-500">載入中...</div>';
            try {
                const response = await fetch('./expectations_gap.json');
                const list = await response.json();
                container.innerHTML = '';
                list.forEach(item => {
                    const card = document.createElement('div');
                    card.className = "bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 hover:border-amber-500/40 transition relative overflow-hidden group";
                    
                    const stocksHTML = (item.concept_stocks || []).map(s => {
                        const parts = s.split(' ');
                        const code = parts[0];
                        const name = parts[1] || s;
                        return `<span onclick="showStockDetailsFromChips('${code}')" class="px-2.5 py-1 bg-slate-850 hover:bg-indigo-900 border border-slate-700/60 hover:border-indigo-600 rounded-lg text-xs text-slate-200 font-bold cursor-pointer transition flex items-center gap-1">
                            <span class="font-mono text-slate-400 text-[10px]">${code}</span> ${name}
                        </span>`;
                    }).join('');

                    card.innerHTML = `
                        <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-amber-500/5 to-transparent rounded-full -mr-8 -mt-8 group-hover:scale-125 transition"></div>
                        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded bg-amber-950/40 border border-amber-800/40 text-amber-400 text-xs font-bold">${item.category}</span>
                                <h3 class="text-base font-bold text-slate-100">${item.target}</h3>
                            </div>
                            <span class="text-[10px] text-slate-500 font-mono">📅 更新日期: ${item.last_update}</span>
                        </div>
                        
                        <div class="grid grid-cols-1 md:grid-cols-7 gap-4 items-center bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
                            <div class="md:col-span-3 space-y-1">
                                <div class="text-[10px] text-slate-500 uppercase tracking-wider flex items-center gap-1">
                                    <i data-lucide="shield-alert" class="w-3.5 h-3.5 text-slate-500"></i> 法人/市場先前預期
                                </div>
                                <div class="text-xs font-semibold text-slate-400 font-mono">${item.market_expect}</div>
                            </div>
                            <div class="md:col-span-1 flex justify-center py-2 md:py-0">
                                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-amber-950/80 border border-amber-800/80 shadow-md">
                                    <i data-lucide="zap" class="w-4 h-4 text-amber-400 animate-pulse"></i>
                                </div>
                            </div>
                            <div class="md:col-span-3 space-y-1">
                                <div class="text-[10px] text-amber-400 uppercase tracking-wider flex items-center gap-1 font-bold">
                                    <i data-lucide="flame" class="w-3.5 h-3.5 text-amber-400"></i> 實質數據 / 最新傳聞
                                </div>
                                <div class="text-base font-black text-amber-300 font-mono bg-amber-950/25 border border-amber-900/30 px-3 py-1.5 rounded-lg inline-block">${item.real_data}</div>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                            <div class="space-y-1">
                                <div class="text-[10px] text-slate-500">📊 預期差距 (估值重估潛能)</div>
                                <div class="text-xs text-emerald-400 font-bold bg-emerald-950/30 border border-emerald-900/30 px-2 py-1 rounded-lg inline-flex items-center gap-1">
                                    <i data-lucide="trending-up" class="w-3.5 h-3.5 text-emerald-400"></i> ${item.gap_space}
                                </div>
                            </div>
                            <div class="space-y-1">
                                <div class="text-[10px] text-slate-500">💡 追夢空間評估</div>
                                <div class="text-xs text-cyan-300 font-bold bg-cyan-950/30 border border-cyan-900/30 px-2 py-1 rounded-lg inline-flex items-center gap-1">
                                    <i data-lucide="sparkles" class="w-3.5 h-3.5 text-cyan-300"></i> ${item.dream_rating}
                                </div>
                            </div>
                        </div>

                        <div class="border-t border-slate-800/40 pt-3 space-y-2">
                            <div class="text-[10px] text-slate-500">🎯 主要關聯概念股 (點擊可直接引導看 Wiki)</div>
                            <div class="flex flex-wrap gap-2">
                                ${stocksHTML}
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                });
                lucide.createIcons();
            } catch (e) {
                console.error(e);
                container.innerHTML = `<div class="col-span-2 py-12 text-center text-red-400 text-xs font-semibold">載入預期反差數據失敗: ${e.message}</div>`;
            }
        }

        function showStockDetailsFromChips(symbol) {
            const searchInput = document.getElementById('wiki-search');
            if (searchInput) {
                searchInput.value = symbol;
                renderStockWiki();
            }
        }

        function renderStockWiki() {
            const grid = document.getElementById('wiki-grid');
            if (!grid) return;
            grid.innerHTML = '';
            
            const searchVal = document.getElementById('wiki-search').value.trim().toLowerCase();
            const keys = Object.keys(stocksWiki);
            
            let coreCount = 0;
            let extendedCount = 0;
            keys.forEach(k => {
                if (stocksWiki[k].tier === 'core') coreCount++;
                else extendedCount++;
            });
            
            document.getElementById('btn-wiki-tier-all').textContent = `全部 (${keys.length})`;
            document.getElementById('btn-wiki-tier-core').textContent = `Core 題材股 (${coreCount})`;
            document.getElementById('btn-wiki-tier-extended').textContent = `其他上市櫃 (${extendedCount})`;
            
            document.querySelectorAll('.wiki-tier-btn').forEach(btn => {
                btn.className = "wiki-tier-btn px-4 py-2 text-xs font-semibold rounded-xl border border-slate-800 bg-slate-900 text-slate-400 hover:bg-slate-800 transition";
            });
            if (wikiFilterTier === 'all') {
                document.getElementById('btn-wiki-tier-all').className = "wiki-tier-btn px-4 py-2 text-xs font-semibold rounded-xl border border-indigo-900 bg-indigo-950/40 text-indigo-300 transition";
            } else if (wikiFilterTier === 'core') {
                document.getElementById('btn-wiki-tier-core').className = "wiki-tier-btn px-4 py-2 text-xs font-semibold rounded-xl border border-indigo-900 bg-indigo-950/40 text-indigo-300 transition";
            } else if (wikiFilterTier === 'extended') {
                document.getElementById('btn-wiki-tier-extended').className = "wiki-tier-btn px-4 py-2 text-xs font-semibold rounded-xl border border-indigo-900 bg-indigo-950/40 text-indigo-300 transition";
            }
            
            const filteredKeys = keys.filter(k => {
                const wiki = stocksWiki[k];
                if (wikiFilterTier !== 'all' && wiki.tier !== wikiFilterTier) return false;
                
                if (searchVal) {
                    const matchCode = wiki.code.toLowerCase().includes(searchVal);
                    const matchName = wiki.name.toLowerCase().includes(searchVal);
                    const matchIndustry = wiki.industry.toLowerCase().includes(searchVal);
                    const matchSummary = (wiki.summary || '').toLowerCase().includes(searchVal);
                    const matchProducts = (wiki.products || []).some(p => p.toLowerCase().includes(searchVal));
                    return matchCode || matchName || matchIndustry || matchSummary || matchProducts;
                }
                return true;
            });
            
            if (filteredKeys.length === 0) {
                grid.innerHTML = `<div class="col-span-full text-center text-slate-500 py-8">找不到符合搜尋條件的個股。</div>`;
                return;
            }
            
            const renderedKeys = filteredKeys.slice(0, 150);
            
            renderedKeys.forEach(k => {
                const wiki = stocksWiki[k];
                const card = document.createElement('div');
                card.className = 'bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition flex flex-col justify-between shadow-lg cursor-pointer';
                card.onclick = () => openModal(wiki.code);
                
                const badge = wiki.tier === 'core' 
                    ? `<span class="px-2 py-0.5 rounded-md bg-indigo-950/60 border border-indigo-800/50 text-indigo-400 text-[10px] font-bold">Core</span>`
                    : `<span class="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-500 text-[10px] font-medium">Extended</span>`;
                    
                const productsBadges = (wiki.products || []).map(p => 
                    `<span class="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800/60 text-slate-400 text-[10px]">${p}</span>`
                ).join(' ');
                
                const relatedThemesBadges = (wiki.themes || []).map(t => {
                    const mapKey = Object.keys(mapsRepository).find(key => mapsRepository[key].title === t);
                    if (mapKey) {
                        return `<button onclick="event.stopPropagation(); loadMapWorkspace('${mapKey}')" class="px-2 py-0.5 rounded-md bg-emerald-950/30 border border-emerald-900/40 text-emerald-400 hover:text-white hover:border-emerald-500 text-[10px] transition">${t}</button>`;
                    }
                    return `<span class="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-500 text-[10px]">${t}</span>`;
                }).join(' ');

                card.innerHTML = `
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <h4 class="font-bold text-slate-200">${wiki.name}</h4>
                                <span class="text-xs text-slate-500 font-mono">${wiki.code}</span>
                            </div>
                            <div class="flex items-center gap-1.5">
                                ${badge}
                                <span class="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded-md border border-slate-800/80">${wiki.industry}</span>
                            </div>
                        </div>
                        <p class="text-xs text-slate-400 leading-relaxed min-h-[36px]">${wiki.summary || '提供相關產業產品與服務。'}</p>
                        <div class="flex flex-wrap gap-1 pt-1">
                            ${productsBadges}
                        </div>
                    </div>
                    ${wiki.themes && wiki.themes.length > 0 ? `
                        <div class="border-t border-slate-800/60 mt-4 pt-3 space-y-1.5">
                            <div class="text-[9px] uppercase tracking-wider text-slate-500 font-bold">參與主題</div>
                            <div class="flex flex-wrap gap-1">${relatedThemesBadges}</div>
                        </div>
                    ` : ''}
                    <div class="mt-4 pt-2 flex justify-end">
                        <button class="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition">
                            查看 LLM 深度分析 <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });
            
            if (filteredKeys.length > 150) {
                const hint = document.createElement('div');
                hint.className = 'col-span-full text-center text-xs text-slate-500 py-4';
                hint.textContent = `... 已隱藏其餘 ${filteredKeys.length - 150} 筆結果，請輸入關鍵字精確搜尋 ...`;
                grid.appendChild(hint);
            }
            
            lucide.createIcons();
        }
        
        function filterWiki() {
            renderStockWiki();
        }
        
        function filterWikiTier(tier) {
            wikiFilterTier = tier;
            renderStockWiki();
        }

        // New helper functions for search and tag navigation
        function handleGlobalSearch(val) {
            const container = document.getElementById('global-search-results');
            if (!container) return;
            const query = val.trim().toLowerCase();
            if (!query) {
                container.classList.add('hidden');
                return;
            }
            const results = searchStocksInWiki(query).slice(0, 6);
            if (results.length === 0) {
                container.innerHTML = `<div class="p-3 text-xs text-slate-500">無匹配個股</div>`;
            } else {
                container.innerHTML = results.map(wiki => `
                    <div onclick="selectSearchResult('${wiki.code}', 'global-stock-search', 'global-search-results')" class="p-3 hover:bg-slate-800 cursor-pointer flex items-center justify-between transition border-b border-slate-800/40">
                        <div>
                            <div class="text-xs font-bold text-slate-200">${wiki.name} <span class="font-mono text-slate-500 text-[10px]">${wiki.code}</span></div>
                            <div class="text-[10px] text-slate-400 mt-0.5 line-clamp-1">${wiki.summary || ''}</div>
                        </div>
                        <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">${wiki.industry}</span>
                    </div>
                `).join('');
            }
            container.classList.remove('hidden');
        }

        function handleWikiSearch(val) {
            filterWiki();
            const container = document.getElementById('wiki-search-results');
            if (!container) return;
            const query = val.trim().toLowerCase();
            if (!query) {
                container.classList.add('hidden');
                return;
            }
            const results = searchStocksInWiki(query).slice(0, 6);
            if (results.length === 0) {
                container.innerHTML = `<div class="p-3 text-xs text-slate-500">無匹配個股</div>`;
            } else {
                container.innerHTML = results.map(wiki => `
                    <div onclick="selectSearchResult('${wiki.code}', 'wiki-search', 'wiki-search-results')" class="p-3 hover:bg-slate-800 cursor-pointer flex items-center justify-between transition border-b border-slate-800/40">
                        <div>
                            <div class="text-sm font-bold text-slate-200">${wiki.name} <span class="font-mono text-slate-500">${wiki.code}</span></div>
                            <div class="text-xs text-slate-400 mt-0.5 line-clamp-1">${wiki.summary || ''}</div>
                        </div>
                        <span class="text-[10px] px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">${wiki.industry}</span>
                    </div>
                `).join('');
            }
            container.classList.remove('hidden');
        }

        function searchStocksInWiki(query) {
            const keys = Object.keys(stocksWiki);
            return keys.map(k => stocksWiki[k]).filter(wiki => {
                const matchCode = wiki.code.toLowerCase().includes(query);
                const matchName = wiki.name.toLowerCase().includes(query);
                const matchIndustry = wiki.industry.toLowerCase().includes(query);
                const matchSummary = (wiki.summary || '').toLowerCase().includes(query);
                const matchProducts = (wiki.products || []).some(p => p.toLowerCase().includes(query));
                return matchCode || matchName || matchIndustry || matchSummary || matchProducts;
            });
        }

        function selectSearchResult(code, inputId, resultsId) {
            document.getElementById(inputId).value = '';
            document.getElementById(resultsId).classList.add('hidden');
            openModal(code);
        }

        function searchTag(tagName) {
            closeModal();
            showStockWiki();
            const wikiSearch = document.getElementById('wiki-search');
            if (wikiSearch) {
                wikiSearch.value = tagName;
                filterWiki();
                wikiSearch.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        function clickTheme(themeName) {
            closeModal();
            const mapKey = Object.keys(mapsRepository).find(key => mapsRepository[key].title === themeName);
            if (mapKey) {
                loadMapWorkspace(mapKey);
                const workspace = document.getElementById('panel-map-workspace');
                if (workspace) workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                showStockWiki();
                const wikiSearch = document.getElementById('wiki-search');
                if (wikiSearch) {
                    wikiSearch.value = themeName;
                    filterWiki();
                }
            }
        }

        async function triggerLiveUpdate() {
            if (!currentModalStockId) return;
            
            const btn = document.getElementById('modal-live-update-btn');
            const text = document.getElementById('modal-live-update-btn-text');
            if (!btn || !text) return;
            
            const originalText = text.textContent;
            btn.disabled = true;
            text.innerHTML = `<span class="flex items-center gap-1"><i data-lucide="loader" class="w-4 h-4 animate-spin"></i> 搜尋與 LLM 分析中...</span>`;
            lucide.createIcons();
            
            try {
                const response = await fetch(`/api/update_stock?code=${currentModalStockId}`);
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.error || `HTTP ${response.status}`);
                }
                const updatedStock = await response.json();
                
                // Update local memory cache
                stocksWiki[currentModalStockId] = updatedStock;
                
                // Re-open modal to refresh all fields
                openModal(currentModalStockId);
                
                // Refresh parent grid list if visible
                if (!document.getElementById('panel-stock-wiki').classList.contains('hidden')) {
                    renderStockWiki();
                }
                
                showToast("個股 LLM Wiki 結構化更新完成！");
            } catch (err) {
                console.error("Live Update Failed:", err);
                showToast(`更新失敗：${err.message || '本功能需在本地運行 python web_server.py 才能使用'}`);
            } finally {
                btn.disabled = false;
                text.textContent = originalText;
                lucide.createIcons();
            }
        }

        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            const globalResults = document.getElementById('global-search-results');
            if (globalResults && !e.target.closest('#global-stock-search') && !e.target.closest('#global-search-results')) {
                globalResults.classList.add('hidden');
            }
            const wikiResults = document.getElementById('wiki-search-results');
            if (wikiResults && !e.target.closest('#wiki-search') && !e.target.closest('#wiki-search-results')) {
                wikiResults.classList.add('hidden');
            }
        });
    