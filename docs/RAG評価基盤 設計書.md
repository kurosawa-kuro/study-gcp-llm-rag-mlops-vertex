# RAG評価基盤 設計書

プロジェクト: multicloud-mlops-llm-platform / study-gcp-llm-rag-mlops-vertex
最終更新: 2026-04-04

---

## 1. 概要

### 目的

```text
動いているRAGシステムの品質を定量化する

・現状のベースラインを数値として記録する
・ELECTRA差し替え後との比較基準を作る
・ハイブリッド検索（Vector + ES）の効果を定量化する
・業務提案時の根拠数値として使う
```

### 評価の2層構造

```text
Layer1: 検索品質評価（Retrieval評価）
  └── 正解ドキュメントが検索結果に含まれるか
  └── 指標: Recall@K / MRR

Layer2: 回答品質評価（Generation評価）
  └── 生成された回答が正解と一致するか
  └── 指標: Exact Match / ROUGE-L / LLM-as-Judge
```

---

## 2. 評価指標の定義

### Layer1: 検索品質

#### Recall@K

```text
定義
  └── 正解チャンクがTop-K検索結果に含まれる割合

計算式
  Recall@K = 正解チャンクがTop-Kに含まれたクエリ数 / 全クエリ数

例
  クエリ10件中8件でTop-5に正解が含まれた
  → Recall@5 = 0.80

評価するK値
  └── K=1, 3, 5, 10
```

#### MRR（Mean Reciprocal Rank）

```text
定義
  └── 最初の正解チャンクが何番目に出たかの逆数の平均

計算式
  MRR = (1/|Q|) × Σ (1 / rank_i)

例
  クエリ1: 3番目に正解 → 1/3
  クエリ2: 1番目に正解 → 1/1
  クエリ3: 5番目に正解 → 1/5
  MRR = (1/3 + 1/1 + 1/5) / 3 = 0.511

意味
  └── 1.0に近いほど正解が上位に出ている
  └── 検索の「当たり率」を示す
```

### Layer2: 回答品質

#### Exact Match

```text
定義
  └── 期待する回答キーワードが全て含まれるか

計算式
  EM = 全キーワードが含まれる回答数 / 全クエリ数

用途
  └── 数値・日付・固有名詞の正確さを測る
  └── 例: 「3営業日前」が回答に含まれるか
```

#### ROUGE-L

```text
定義
  └── 期待回答と生成回答の最長共通部分列の重複率

用途
  └── 回答の網羅性を測る
  └── 長い回答の品質評価に適している
```

#### LLM-as-Judge（Phase2で導入）

```text
定義
  └── Geminiに回答の品質を1-5点で採点させる

用途
  └── 人間の感覚に近い品質評価
  └── Exact MatchやROUGEでは測れない
      回答の自然さ・有用性を評価

Phase1では省略
  └── コストがかかる（Gemini呼び出し回数が増える）
  └── まずRecall@KとMRRで土台を作る
```

---

## 3. 評価データ設計

### ディレクトリ構成

```text
scripts/eval/
  ├── queries_eval.jsonl      # 評価クエリ + Ground Truth
  ├── evaluate.py             # 評価スクリプト（メイン）
  ├── metrics.py              # 指標計算ロジック
  ├── report.py               # 結果レポート生成
  └── results/                # 評価結果の保存先
       ├── baseline_YYYYMMDD.json   # ベースライン結果
       └── electra_YYYYMMDD.json    # ELECTRA差し替え後結果
```

### queries_eval.jsonl の設計

```json
{
  "query_id": "q001",
  "query": "有給休暇の申請手続きを教えてください",
  "expected_answer_keywords": ["3営業日前", "上長", "申請"],
  "relevant_source": "就業規則_sample.txt",
  "relevant_keywords": ["年次有給休暇", "申請", "営業日"]
}
```

#### フィールド定義

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `query_id` | string | クエリの一意ID |
| `query` | string | 検索クエリ（自然文） |
| `expected_answer_keywords` | list | 回答に含まれるべきキーワード |
| `relevant_source` | string | 正解ドキュメントのファイル名 |
| `relevant_keywords` | list | 正解チャンクに含まれるキーワード |

#### なぜチャンクIDではなくキーワードで判定するか

```text
チャンクIDでの判定の問題
  └── 再Ingestion時にIDが変わる可能性
  └── チャンク分割の変更でIDが変わる

キーワードでの判定
  └── チャンク内容の変化に強い
  └── 複数チャンクに正解が分散していても対応できる
  └── 実務的な評価に近い
```

### サンプルクエリセット（20件）

```text
就業規則関連（7件）
  q001: 有給休暇の申請手続きを教えてください
  q002: リモートワークは何日まで可能ですか
  q003: 遅刻した場合の扱いはどうなりますか
  q004: 勤務時間は何時から何時ですか
  q005: 残業の申請方法を教えてください
  q006: 育児休業は取得できますか
  q007: 試用期間はどのくらいですか

経費精算関連（7件）
  q008: 交通費の精算方法を教えてください
  q009: 出張旅費の上限はいくらですか
  q010: 領収書が必要な金額の基準は何円ですか
  q011: 経費精算の締め日はいつですか
  q012: 接待費の申請方法を教えてください
  q013: タクシー代は経費になりますか
  q014: 海外出張の日当はいくらですか

FAQ関連（6件）
  q015: パソコンが壊れた場合はどうすればいいですか
  q016: 社員証を紛失した場合の手続きは
  q017: 健康診断はいつ受けられますか
  q018: 社内Wi-Fiのパスワードはどこで確認できますか
  q019: 退職時の手続きを教えてください
  q020: 慶弔見舞金の申請方法を教えてください
```

---

## 4. 評価スクリプト設計

### evaluate.py 処理フロー

```text
1. queries_eval.jsonl を読み込む
2. 各クエリで QA API に /query リクエスト
   └── top_k=10 で検索結果を取得
3. 検索結果と Ground Truth を照合
   └── relevant_keywords が検索結果に含まれるか
4. Recall@K / MRR を算出
5. 回答と expected_answer_keywords を照合
   └── Exact Match を算出
6. 結果を JSON で保存
7. サマリーをコンソール出力
```

### metrics.py の関数設計

```python
def recall_at_k(results: list, relevant_keywords: list, k: int) -> float:
    """
    Top-K結果にrelevant_keywordsを含むチャンクがあるか判定
    """

def mrr(results_list: list, relevant_keywords_list: list) -> float:
    """
    全クエリのMRRを算出
    """

def exact_match(answer: str, keywords: list) -> bool:
    """
    回答に全キーワードが含まれるか判定
    """

def rouge_l(answer: str, expected: str) -> float:
    """
    ROUGE-Lスコアを算出
    """
```

### 出力フォーマット（results/baseline_YYYYMMDD.json）

```json
{
  "timestamp": "2026-04-04T10:00:00",
  "model": "Vertex AI Embedding + gemini-2.5-flash",
  "search_type": "hybrid (vector + elasticsearch)",
  "top_k": 10,
  "num_queries": 20,
  "retrieval": {
    "recall@1": 0.40,
    "recall@3": 0.65,
    "recall@5": 0.80,
    "recall@10": 0.90,
    "mrr": 0.58
  },
  "generation": {
    "exact_match": 0.75,
    "rouge_l": 0.68
  },
  "per_query": [
    {
      "query_id": "q001",
      "query": "有給休暇の申請手続きを教えてください",
      "recall@5": 1,
      "rank": 2,
      "exact_match": true,
      "answer": "有給休暇の申請は..."
    }
  ]
}
```

---

## 5. 比較評価の設計

### ベースライン vs ELECTRA 比較

```text
比較軸
  ├── Vertex AI Embedding（現状）
  └── ELECTRA ファインチューニング済みモデル（将来）

比較レポート出力例

  指標          ベースライン    ELECTRA差し替え    差分
  ──────────────────────────────────────────────────
  Recall@1      0.40           0.52              +0.12 ✅
  Recall@5      0.80           0.88              +0.08 ✅
  MRR           0.58           0.67              +0.09 ✅
  Exact Match   0.75           0.78              +0.03 ✅
```

### ハイブリッド検索の効果検証

```text
3パターンを比較

  パターン1: Vector Searchのみ
  パターン2: Elasticsearchのみ
  パターン3: ハイブリッド（現状）

期待する結果
  └── パターン3が最も高いRecall@Kを示す
  └── これがElastic Cloud導入の定量的な根拠になる
```

---

## 6. Makefile コマンド設計

```makefile
# 評価実行
eval:
    python scripts/eval/evaluate.py

# ベースライン記録
eval-baseline:
    python scripts/eval/evaluate.py --save-as baseline

# 比較レポート
eval-compare:
    python scripts/eval/report.py \
        --before results/baseline_*.json \
        --after results/electra_*.json

# 検索パターン比較
eval-search-patterns:
    python scripts/eval/evaluate.py --search-type vector
    python scripts/eval/evaluate.py --search-type elasticsearch
    python scripts/eval/evaluate.py --search-type hybrid
```

---

## 7. 実装スケジュール

```text
Day1: Ground Truth整備
  ├── queries_eval.jsonl 作成（20件）
  └── キーワード設計（relevant_keywords / expected_answer_keywords）

Day2: 評価スクリプト実装
  ├── metrics.py（Recall@K / MRR / Exact Match）
  ├── evaluate.py（メインフロー）
  └── 動作確認

Day3: ベースライン計測・比較
  ├── ベースライン数値を記録
  ├── 検索パターン比較（Vector / ES / Hybrid）
  └── results/baseline_YYYYMMDD.json 保存

Day4: レポート整備
  ├── report.py（比較レポート生成）
  └── Makefile コマンド追加
```

---

## 8. 期待するベースライン数値

```text
現状構成（Vertex AI Embedding + Hybrid検索）での期待値

Recall@5:  0.75〜0.85
  └── サンプルデータが少ない（3ファイル）ので高めになる想定

MRR: 0.55〜0.70
  └── 日本語検索精度に依存

Exact Match: 0.70〜0.80
  └── Gemini 2.5 Flash の回答精度次第

注意
  └── サンプルデータが少ないため数値は高く出やすい
  └── 本番データでは数値が下がる可能性がある
  └── 傾向の把握が目的・絶対値にこだわらない
```

---

## 9. 業務への応用

```text
この評価基盤が業務で直結する理由

業務（ELECTRAベクトル検索）
  └── 現状「良い検索結果」の定義が曖昧
  └── 評価基盤がない → 品質改善の根拠がない

この個人学習で構築したもの
  └── Ground Truth設計の方法論
  └── Recall@K / MRRの実装経験
  └── ベースライン vs 改善後の比較手法

業務チームへの提案
  └── 「評価クエリセットを整備しましょう」
  └── 「まずRecall@Kでベースラインを取りましょう」
  └── 設計書・実装経験を持って提案できる
```

---

## 10. 将来の拡張

```text
Phase2: LLM-as-Judge導入
  └── Geminiが回答品質を1-5点で採点
  └── 人間の感覚に近い品質評価

Phase3: BigQueryへの評価結果蓄積
  └── 評価履歴をBigQueryに保存
  └── 時系列での品質変化を追跡
  └── Vertex AI Pipelineの品質ゲートに統合

Phase4: 自動評価Pipeline
  └── 新モデルデプロイ時に自動評価実行
  └── ベースラインより劣化したら自動ロールバック
  └── Champion/Challenger の完成形
```