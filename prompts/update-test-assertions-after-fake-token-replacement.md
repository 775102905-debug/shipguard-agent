# AI Delivery Inspector — 测试断言同步修复（假密钥替换后）

> 保存时间: 2026-05-05
> 用于后续复盘、迭代、优化

## 背景

测试假密钥已从 `sk-`/`ghp_` 格式替换为明显假值（如 `FAKE_OPENAI_KEY_FOR_SCANNER_TEST`）。
测试断言需要同步更新，不再检查 `sk-`，改为检查 `SECRET`/`PASSWORD`/`Authorization`。

## 修改的文件（5 个）

| 文件 | 变更 |
|------|------|
| [scripts/smoke_test.py](file:///d:/Users/77510/Desktop/shipguard-agent/scripts/smoke_test.py) | `sk-` → `SECRET/PASSWORD/Authorization` |
| [scripts/test_upload.py](file:///d:/Users/77510/Desktop/shipguard-agent/scripts/test_upload.py) | `sk-` → `SECRET/PASSWORD/Authorization` |
| [scripts/read_results.py](file:///d:/Users/77510/Desktop/shipguard-agent/scripts/read_results.py) | `sk-` → `SECRET/PASSWORD/Authorization` |
| [smoke_test.py](file:///d:/Users/77510/Desktop/shipguard-agent/smoke_test.py) | 移除 `sk-`，添加 `Authorization` |
| [end_to_end_test.py](file:///d:/Users/77510/Desktop/shipguard-agent/end_to_end_test.py) | 移除 `sk-`，添加 `SECRET/PASSWORD/Authorization` |

## 验证结果

```
============================================================
  Results: 25 passed, 0 failed out of 25 checks
============================================================
```

- good_project: score=98, verdict=PASS
- bad_project: score=28, verdict=REJECT, HIGH=1, MED=14, LOW=1
- SECRET/PASSWORD/Authorization risk: 检测成功 ✅
