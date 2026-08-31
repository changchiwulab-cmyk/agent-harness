---
description: 一鍵跑全套本地回歸（Ruby + Python 單元 + e2e + evals + 衍生物漂移 + 治理指標）
allowed-tools: Bash
---

# 全套本地回歸

跑 CI 同款檢查，**不新增任何驗證邏輯**，只編排既有 script。提交前與收尾前各跑一次。

```bash
set +e; fail=0

echo "── Ruby 一致性與預算 ──"
ruby scripts/check_spec_consistency.rb        || fail=1
ruby scripts/test_check_spec_consistency.rb   || fail=1
ruby scripts/check_dual_path_categories.rb    || fail=1
ruby scripts/test_check_dual_path_categories.rb || fail=1
ruby scripts/check_context_budget.rb          || fail=1
ruby scripts/test_check_context_budget.rb     || fail=1
ruby scripts/check_decision_revisit.rb        || fail=1
ruby scripts/test_check_decision_revisit.rb   || fail=1
ruby -e 'require "yaml"; Dir.glob("**/*.yaml").each{|p| YAML.load_file(p)}; puts "ALL_YAML_OK"' || fail=1

echo "── Python 單元測試 ──"
for t in scripts/test_*.py; do
  python3 "$t" >/dev/null 2>&1 || { echo "FAIL $t"; fail=1; }
done

echo "── e2e ──"
for t in tests/e2e/test_*.py; do
  python3 "$t" >/dev/null 2>&1 || { echo "FAIL $t"; fail=1; }
done

echo "── evals ──"
python3 scripts/run_evals.py || fail=1

echo "── 衍生物漂移 ──"
scripts/sync_derived.sh --check || fail=1

echo "── 新鮮度（納入退出狀態）──"
python3 scripts/check_native_overlap_freshness.py || fail=1

# 治理指標**刻意不納入** fail：governance_metrics.py 對 warn/alert 回非零，但那是
# 「該討論的訊號」不是「回歸」——它自己就寫明 alert → 開 retro task、warn → 下次 retro
# 帶討論。把它接進退出狀態會讓 /harness-check 因為 M1（本月建卡數）這類指標長期紅著，
# 而長期紅的檢查等於沒有檢查。故明確分開印，並標示不影響 exit code。
echo "── 治理指標（advisory，不影響退出狀態）──"
python3 scripts/governance_metrics.py | sed -n '/## 摘要/,/^$/p'
metrics_rc=${PIPESTATUS[0]}
[ "$metrics_rc" = 0 ] || echo "  ⚠️ 指標有 warn/alert（rc=$metrics_rc）——請帶進下次 retro，非本次回歸紅燈"

if [ "$fail" = 0 ]; then
  echo "✅ ALL GREEN"
else
  echo "❌ 有紅燈，見上方輸出"
fi
# 退出狀態必須反映結果：呼叫端與 failure_counter 的 PostToolUse hook 是靠
# 工具成功/失敗判斷的，印紅字卻 exit 0 會讓熔斷計數看到一次「成功」。
exit "$fail"
```

## 紅燈處理

**不要硬修**。定位到是哪一支失敗、貼出最後幾行輸出、判斷是本次改動造成還是既有漂移，
再決定修或回報。連續失敗 3 次即停（硬規則 3）。
