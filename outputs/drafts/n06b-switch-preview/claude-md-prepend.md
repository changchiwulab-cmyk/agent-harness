> **依賴**：agent-governance plugin v0.1.0+（repo: `changchiwulab-cmyk/agent-governance`，private）。
> 缺席時自動降回本 repo `scripts/` fallback；CI 在「裝/未裝 plugin」雙路徑均綠。
> 路由由 `scripts/check_plugin_present.sh` 決定，切換依據 D007 + N06b（task `20260509-N09`）。
