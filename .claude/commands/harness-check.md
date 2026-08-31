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

echo "── 治理指標 / 新鮮度 ──"
python3 scripts/check_native_overlap_freshness.py || fail=1
python3 scripts/governance_metrics.py | sed -n '1,20p'

[ "$fail" = 0 ] && echo "✅ ALL GREEN" || echo "❌ 有紅燈，見上方輸出"
```

## 紅燈處理

**不要硬修**。定位到是哪一支失敗、貼出最後幾行輸出、判斷是本次改動造成還是既有漂移，
再決定修或回報。連續失敗 3 次即停（硬規則 3）。
