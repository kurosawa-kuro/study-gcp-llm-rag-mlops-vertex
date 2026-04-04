# RAG評価基盤 設計書

プロジェクト: study-gcp-llm-rag-mlops-vertex
最終更新: 2026-04-04

---

## 1. 概要

### 目的

```text
動いているRAGシステムの品質を定量化する

・現状のベースラインを数値として記録する
・検索パターン（Vector / ES / Hybrid）の効果を定量化する
・業務提案時の根拠数値として使う
```

### 評価の2層構造

```text
Layer1: 検索品質評価（Retrieval評価）
  └── 正解ドキュメントが検索結果に含まれるか
  └── 指標: Recall@K / MRR

Layer2: 回答品質評価（Generation評価）
  └── 生成された回答が正解と一致するか
  └── 指標: Exact Match / ROUGE-L
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

---

## 3. 実装済み

### ディレクトリ構成

```text
scripts/eval/
  ├── evaluate.py             # メイン評価スクリプト（--search-type / --save-as / --top-k）
  ├── metrics.py              # 指標計算（recall_at_k / mrr / exact_match / rouge_l）
  ├── report.py               # 横並び比較レポート生成
  ├── queries_eval.jsonl      # 評価クエリ20件 + Ground Truth
  ├── results/                # 評価結果 JSON 保存先
  └── tests/
       ├── test_metrics.py    # 単体テスト（26件）
       └── test_report.py     # 単体テスト（7件）
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

### Makefile コマンド

```bash
make eval                  # hybrid検索で評価実行
make eval-baseline         # ベースライン記録
make eval-search-patterns  # vector / elasticsearch / hybrid 3パターン比較
```

### evaluate.py 処理フロー

```text
1. queries_eval.jsonl を読み込む
2. 各クエリで検索モジュールを直接呼び出し（API経由ではない）
   └── top_k=10 で検索結果を取得
3. 検索結果と Ground Truth を照合
   └── relevant_keywords が検索結果に含まれるか
4. Recall@K / MRR を算出
5. Gemini で回答生成 → expected_answer_keywords と照合
   └── Exact Match / ROUGE-L を算出
   └── レートリミット時は自動リトライ（最大5回・指数バックオフ）
6. 結果を JSON で保存
7. サマリーをコンソール出力
```

### Gemini API レートリミット

```text
有料プラン化済み（無料枠の日次20回制約は解消）
レートリミット到達時は evaluate.py が自動リトライする（最大5回・指数バックオフ）
```

---

## 4. 検証済みベースライン（2026-04-04）

サンプルデータ3文書・6チャンク / hybrid検索 / gemini-2.5-flash

```
┌─────────────┬────────┐
│    指標     │ スコア │
├─────────────┼────────┤
│ Recall@1    │ 0.8000 │
├─────────────┼────────┤
│ Recall@3    │ 1.0000 │
├─────────────┼────────┤
│ Recall@5    │ 1.0000 │
├─────────────┼────────┤
│ Recall@10   │ 1.0000 │
├─────────────┼────────┤
│ MRR         │ 0.9000 │
├─────────────┼────────┤
│ Exact Match │ 0.6500 │
├─────────────┼────────┤
│ ROUGE-L     │ 0.2007 │
└─────────────┴────────┘
```

```text
注意
  └── サンプルデータが少ないため検索品質は高く出ている
  └── ROUGE-L が低いのは Gemini の回答が自然言語で冗長なため（文字レベルLCSの特性）
  └── 本番データでは数値が変動する
  └── 傾向の把握が目的・絶対値にこだわらない
```

---

## 5. 比較評価の設計

### ハイブリッド検索の効果検証（実装済み）

```text
3パターンを比較（make eval-search-patterns）

  パターン1: Vector Searchのみ
  パターン2: Elasticsearchのみ
  パターン3: ハイブリッド（現状）

期待する結果
  └── パターン3が最も高いRecall@Kを示す
  └── これがElastic Cloud導入の定量的な根拠になる
```

### Embedding モデル比較（将来作業）

```text
比較軸
  ├── text-multilingual-embedding-002（現状）
  └── ELECTRA ファインチューニング済みモデル（将来検討）

比較レポート出力例

  指標          ベースライン    ELECTRA差し替え    差分
  ──────────────────────────────────────────────────
  Recall@1      0.80           ?                 ?
  Recall@5      1.00           ?                 ?
  MRR           0.90           ?                 ?
  Exact Match   0.65           ?                 ?

現状の Recall@3=1.0 で検索品質は十分高い
精度改善の必要性が出てから着手する
```

---

## 6. 業務への応用

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

## 7. 将来の拡張

### 優先度 高（安定化後に着手）

```text
LLM-as-Judge 導入
  └── Gemini が回答品質を1-5点で採点
  └── Exact Match / ROUGE-L では測れない回答の自然さ・有用性を評価
  └── Gemini API 有料プラン化が前提（無料枠では呼び出し回数が不足）

本番データでの再評価
  └── サンプル3文書ではなく実ドキュメントで評価
  └── BQ Vector Index が有効になる規模（5000行以上）でのベースライン計測
```

### 優先度 中

```text
BigQuery への評価結果蓄積
  └── 評価履歴を BigQuery に保存
  └── 時系列での品質変化を追跡
  └── Vertex AI Pipeline の品質ゲートに統合

E2E 評価の CI 組み込み
  └── deploy-all 後に自動で make eval を実行
  └── ベースラインより劣化したらアラート
```

### 優先度 低（将来検討）

```text
ELECTRA 差し替え比較
  └── ドメイン特化 Embedding への差し替え
  └── 現状の text-multilingual-embedding-002 で Recall@3=1.0 のため緊急性なし
  └── 本番データで精度不足が判明した場合に検討

Vertex AI Gemini への切替
  └── コンソール同意が必要で現状不可
  └── Google AI Studio で十分動作しており緊急性なし
```
