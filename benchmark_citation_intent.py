#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Citation-intent classification benchmark (SciCite / ACL-ARC).

复用 task6.12 的 LLM 调用骨架，但做了三处必要改造：
  1) API key 从环境变量读取（不再硬编码）
  2) model / temperature / max_tokens 全部从 .env 读取，与正文一致
  3) 关闭规则 fallback —— benchmark 必须测 LLM 本身，失败则重试/记缺失

用法：
  # 先跑 SciCite
  python benchmark_citation_intent.py --dataset scicite --input test.jsonl
  # 再跑 ACL-ARC（同一套代码，只换 --dataset 和 --input）
  python benchmark_citation_intent.py --dataset aclarc --input acl_arc_test.jsonl

依赖： pip install pandas scikit-learn matplotlib requests python-dotenv
环境变量（建议放 .env，并加入 .gitignore）：
  LLM_API_KEY=sk-你的新key
  LLM_BASE_URL=https://api.deepseek.com
  LLM_MODEL=deepseek-chat
  LLM_TEMPERATURE=0
  LLM_MAX_TOKENS=512
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

# 可选：自动加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ----------------------------------------------------------------------------
# 配置：全部从环境变量读取，保证与正文打分一致
# ----------------------------------------------------------------------------
API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
API_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0"))
MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "512"))

MAX_RETRIES = 3          # API 失败重试次数（不再 fallback 到规则）
RETRY_SLEEP = 2.0        # 重试间隔秒


# ----------------------------------------------------------------------------
# 两个数据集的标签体系 + prompt + 字段映射
# ----------------------------------------------------------------------------
SCICITE_LABELS = ["background", "method", "result"]
ACLARC_LABELS = ["Background", "Motivation", "Uses", "Extends", "CompareOrContrast", "Future"]

PROMPT_SCICITE = """You are classifying the intent of ONE citation in a scientific paper.

Citation context:
{context}

Section: {sectionName}

Choose EXACTLY ONE label from the following three SciCite categories:
- background: the citation provides background information or prior work.
- method: the citing paper uses a method, tool, dataset, or technique from the cited work.
- result: the citing paper compares its results or findings with the cited work.

Return STRICT JSON only, no other text:
{{"label": "background|method|result"}}

Rules:
- Output the label string EXACTLY as written above (lowercase).
- Pick the single most appropriate label.
"""

PROMPT_ACLARC = """You are classifying the intent of ONE citation in a scientific paper.

Focus ONLY on the target citation marked as @@CITATION in the text below.
Do NOT classify other citations that may appear in the context.

Citing sentence:
{text}

Extended context (for reference only):
{extended_context}

Target citation (marked @@CITATION):
{cleaned_cite_text}

Choose EXACTLY ONE label from the following six ACL-ARC categories:
- Background: cited work gives background, prior knowledge, or general context.
- Motivation: cited work motivates the need for or illustrates a problem the citing work addresses.
- Uses: the citing work uses, applies, or builds on a method, tool, data, or idea from the cited work.
- Extends: the citing work extends, improves, or modifies the cited work.
- CompareOrContrast: the citing work compares or contrasts its approach/results with the cited work.
- Future: the cited work is mentioned as a direction for future work.

Return STRICT JSON only, no other text:
{{"intent": "Background|Motivation|Uses|Extends|CompareOrContrast|Future"}}

Rules:
- Output the label string EXACTLY as written above (case-sensitive).
- Pick the single most appropriate label even if multiple seem plausible.
"""

# 每个数据集的：标签列表 / prompt / json输出键 / 金标准字段 / prompt所需字段(带候选键)
DATASET_CONFIG = {
    "scicite": {
        "labels": SCICITE_LABELS,
        "prompt": PROMPT_SCICITE,
        "out_key": "label",
        "gold_field": "label",
        # prompt 占位符 -> 数据中可能的键名（按顺序探测第一个存在的）
        "fields": {
            "context": ["context", "string", "text"],
            "sectionName": ["sectionName", "section_name", "section_title"],
        },
    },
    "aclarc": {
        "labels": ACLARC_LABELS,
        "prompt": PROMPT_ACLARC,
        "out_key": "intent",
        "gold_field": "intent",
        "fields": {
            "text": ["text", "string", "context"],
            "extended_context": ["extended_context", "context"],
            "cleaned_cite_text": ["cleaned_cite_text", "text"],
        },
    },
}


# ----------------------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------------------
def pick_field(record: dict, candidates: List[str]) -> str:
    """从候选键里取第一个存在且非空的值，转成字符串。"""
    for key in candidates:
        if key in record and record[key] not in (None, ""):
            return str(record[key])
    return ""


def build_prompt(record: dict, cfg: dict) -> str:
    kwargs = {ph: pick_field(record, cands) for ph, cands in cfg["fields"].items()}
    return cfg["prompt"].format(**kwargs)


def normalize_label(raw: object, labels: List[str]) -> Optional[str]:
    """把模型输出规范化到金标准标签集合（大小写/常见变体容错）。"""
    if raw is None:
        return None
    text = str(raw).strip().lower().replace("_", "").replace("-", "").replace(" ", "")
    # 建一个 规范化形式 -> 官方标签 的映射
    canon = {lab.lower().replace("_", "").replace("-", "").replace(" ", ""): lab for lab in labels}
    if text in canon:
        return canon[text]
    # 常见变体容错
    aliases = {
        "compareorcontrast": "CompareOrContrast",
        "comparecontrast": "CompareOrContrast",
        "compare": "CompareOrContrast",
        "contrast": "CompareOrContrast",
        "comparison": "CompareOrContrast",
        "extend": "Extends",
        "extension": "Extends",
        "use": "Uses",
        "uses": "Uses",
        "futurework": "Future",
        "resultcomparison": "result",
        "results": "result",
        "methods": "method",
    }
    if text in aliases and aliases[text] in labels:
        return aliases[text]
    # 子串兜底：标签名出现在输出里
    for lab in labels:
        if lab.lower() in str(raw).strip().lower():
            return lab
    return None


def call_llm(prompt: str, out_key: str) -> Optional[str]:
    """调用 LLM，返回原始标签字符串。失败重试，不做规则 fallback。"""
    if not API_KEY:
        raise RuntimeError("缺少 LLM_API_KEY 环境变量，请在 .env 中配置（且勿提交到 Git）。")
    payload = {
        "model": API_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers, json=payload, timeout=90,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return str(parsed.get(out_key, "")).strip(), content
        except Exception as e:
            print(f"  ⚠️ API 第 {attempt}/{MAX_RETRIES} 次失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP)
    return None, None  # 全部重试失败 -> 记为缺失（不污染指标）


def plot_confusion(cm, labels, title, out_path):
    fig, ax = plt.subplots(figsize=(1.4 * len(labels) + 2, 1.4 * len(labels) + 1.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Gold")
    ax.set_title(title)
    thresh = cm.max() / 2.0 if cm.max() > 0 else 0.5
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=["scicite", "aclarc"])
    parser.add_argument("--input", required=True, help="test 集 jsonl 路径")
    parser.add_argument("--outdir", default="results", help="输出目录")
    parser.add_argument("--limit", type=int, default=0, help=">0 时只跑前 N 条（试跑用）")
    args = parser.parse_args()

    cfg = DATASET_CONFIG[args.dataset]
    labels = cfg["labels"]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 读 jsonl
    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if args.limit > 0:
        records = records[: args.limit]
    print(f"[{args.dataset}] 共 {len(records)} 条，模型={API_MODEL}, T={TEMPERATURE}, max_tokens={MAX_TOKENS}")

    rows = []
    n_fail = 0
    for i, rec in enumerate(records, 1):
        gold = str(rec.get(cfg["gold_field"], "")).strip()
        prompt = build_prompt(rec, cfg)
        raw, raw_content = call_llm(prompt, cfg["out_key"])
        pred = normalize_label(raw, labels) if raw is not None else None
        if pred is None:
            n_fail += 1
        rows.append({
            "idx": i - 1,
            "gold": gold,
            "pred_raw": raw if raw is not None else "",
            "pred": pred if pred is not None else "",
            "raw_response": raw_content if raw_content else "",
        })
        if i % 20 == 0:
            print(f"  进度 {i}/{len(records)}")

    pred_df = pd.DataFrame(rows)
    pred_path = outdir / f"predictions_{args.dataset}.csv"
    pred_df.to_csv(pred_path, index=False, encoding="utf-8-sig")

    # 只用「金标准非空 且 预测成功」的样本算指标
    valid = pred_df[(pred_df["gold"] != "") & (pred_df["pred"] != "")].copy()
    n_total = len(pred_df)
    n_valid = len(valid)
    print(f"[{args.dataset}] 有效 {n_valid}/{n_total}，解析/调用失败 {n_fail}")

    if n_valid == 0:
        print("没有有效样本，检查字段名或 API key。")
        return

    y_true = valid["gold"].tolist()
    y_pred = valid["pred"].tolist()

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    micro_f1 = f1_score(y_true, y_pred, labels=labels, average="micro", zero_division=0)
    per_class_f1 = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)

    # 指标表
    metric_rows = [
        {"metric": "accuracy", "value": round(acc, 4)},
        {"metric": "macro_f1", "value": round(macro_f1, 4)},
        {"metric": "micro_f1", "value": round(micro_f1, 4)},
        {"metric": "n_valid", "value": n_valid},
        {"metric": "n_total", "value": n_total},
        {"metric": "n_fail", "value": n_fail},
    ]
    for lab, f1v in zip(labels, per_class_f1):
        metric_rows.append({"metric": f"f1[{lab}]", "value": round(float(f1v), 4)})
    metrics_df = pd.DataFrame(metric_rows)
    metrics_path = outdir / f"metrics_{args.dataset}.csv"
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    # 完整分类报告（含 precision/recall/support）
    report = classification_report(y_true, y_pred, labels=labels, zero_division=0)
    (outdir / f"classification_report_{args.dataset}.txt").write_text(report, encoding="utf-8")

    # 混淆矩阵
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"gold:{l}" for l in labels],
                         columns=[f"pred:{l}" for l in labels])
    cm_df.to_csv(outdir / f"confusion_matrix_{args.dataset}.csv", encoding="utf-8-sig")
    plot_confusion(cm, labels, f"{args.dataset} confusion matrix",
                   outdir / f"confusion_matrix_{args.dataset}.png")

    print("\n===== 结果 =====")
    print(f"accuracy = {acc:.4f}")
    print(f"macro-F1 = {macro_f1:.4f}   <-- 重点")
    print(f"micro-F1 = {micro_f1:.4f}")
    print("per-class F1:")
    for lab, f1v in zip(labels, per_class_f1):
        print(f"  {lab:18s} {f1v:.4f}")
    print(f"\n输出已写入: {outdir}/")
    print(f"  - predictions_{args.dataset}.csv      (原始预测记录)")
    print(f"  - metrics_{args.dataset}.csv          (指标表)")
    print(f"  - classification_report_{args.dataset}.txt")
    print(f"  - confusion_matrix_{args.dataset}.csv / .png")


if __name__ == "__main__":
    main()
