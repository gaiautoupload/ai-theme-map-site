# AI Theme Map Site

這個 repo 是 GitHub Pages 展示站。

內容來源：
- 本地研究工作區 `D:\map`
- 由 `publish_site.py` 一鍵同步 `Index.html` 與 `maps_repo.json`

部署方式：
- GitHub Pages
- branch: `main`
- folder: `/root`

Repo 位置：
- GitHub repository：`https://github.com/gaiautoupload/ai-theme-map-site`

官網網址：
- GitHub Pages 網址通常是：`https://gaiautoupload.github.io/ai-theme-map-site/`

我要怎麼在 GitHub 找到官網：
- 打開 repo：`https://github.com/gaiautoupload/ai-theme-map-site`
- 進入上方 `Settings`
- 左側找到 `Pages`
- 在 `GitHub Pages` / `Pages` 區塊會看到：
  - 目前部署來源（例如 `main` branch, `/root`）
  - 已發布的公開網站網址

正常我要在哪裡找到這個網址：
- 方法 1：直接看 repo 的 GitHub Pages 設定頁
  - Repo → `Settings` → `Pages`
- 方法 2：直接用規則推網址
  - 如果是 user/organization `gaiautoupload`
  - repo 名稱是 `ai-theme-map-site`
  - 則網址通常是：`https://gaiautoupload.github.io/ai-theme-map-site/`
- 方法 3：repo 首頁右側或首頁上方有時也會顯示 `Deployments` / `github-pages`
  - 點進去也能看到最近部署與站點連結

日常更新官網步驟：
- 先在 `D:\map` 更新資料
- 執行 `publish_site.py`
- 這會把 `index.html` 與 `maps_repo.json` 同步到 `D:\ai-theme-map-site`
- 然後自動：
  - `git add .`
  - `git commit`
  - `git push origin main`
- Push 完後，等 GitHub Pages 幾十秒到幾分鐘
- 再打開：`https://gaiautoupload.github.io/ai-theme-map-site/`

如果網站沒有立刻更新：
- 到 repo 的 `Actions` 看 deployment 是否完成
- 或到 `Settings` → `Pages` 看最近部署狀態
- 有時瀏覽器快取會影響，可強制重新整理
  - Windows: `Ctrl + F5`
  - Mac: `Cmd + Shift + R`
