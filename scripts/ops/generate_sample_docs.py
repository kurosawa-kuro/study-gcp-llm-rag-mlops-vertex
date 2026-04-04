"""サンプル社内ドキュメントを大量生成する

BQ Vector Index の検証に5000チャンク以上が必要。
800文字チャンク × 50文字オーバーラップ → 1チャンクあたり約750文字の新規テキストが必要。
5500チャンク × 750文字 ≈ 4.1M文字 → 約100ファイル × 40,000文字/ファイル

Usage: python3 scripts/ops/generate_sample_docs.py [output_dir] [num_files]
"""

import sys
import random
from pathlib import Path

OUTPUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/sample_bulk")
NUM_FILES = int(sys.argv[2]) if len(sys.argv) > 2 else 100

# --- テンプレート素材 ---

DEPARTMENTS = [
    "総務部", "人事部", "経理部", "営業部", "開発部", "マーケティング部",
    "法務部", "情報システム部", "品質管理部", "カスタマーサポート部",
    "経営企画部", "広報部", "購買部", "製造部", "研究開発部",
]

TOPICS = {
    "就業規則": [
        ("勤務時間", "所定労働時間は1日{h}時間、1週{w}時間とする。始業時刻は{start}、終業時刻は{end}とする。休憩時間は{break_min}分とし、{break_start}から{break_end}までとする。フレックスタイム制を適用する部署においては、コアタイムを{core_start}から{core_end}までとする。"),
        ("休日", "休日は土曜日、日曜日、国民の祝日、年末年始（{nenmatsu}）、夏季休暇（{natsu}）とする。業務上の必要がある場合は、会社は休日を他の日に振り替えることができる。振替休日は{furikae}日以内に取得すること。"),
        ("有給休暇", "年次有給休暇は入社{months}ヶ月経過後、所定労働日の{ratio}割以上出勤した場合に{days}日付与する。勤続{y2}年で{d2}日、勤続{y3}年で{d3}日を付与する。有給休暇の取得は{notice}営業日前までに所属部門の上長に申請すること。"),
        ("時間外労働", "時間外労働は月{max_ot}時間を上限とする。時間外労働を行う場合は事前に上長の承認を得ること。深夜労働（{night_start}〜{night_end}）については別途割増賃金を支払う。時間外労働の割増率は{ot_rate}%とする。"),
        ("リモートワーク", "リモートワークは週{rw_days}日まで認める。リモートワーク時もコアタイム（{core_start}〜{core_end}）は連絡可能な状態を維持すること。リモートワーク手当として月額{rw_allowance}円を支給する。"),
        ("服務規律", "従業員は会社の名誉・信用を損なう行為をしてはならない。業務上知り得た機密情報を第三者に漏洩してはならない。SNS等への投稿においては、会社の機密情報や顧客情報を含む内容を禁止する。違反した場合は{penalty}の対象となる。"),
        ("懲戒", "懲戒処分は、けん責、減給、出勤停止、降格、諭旨解雇、懲戒解雇の{types}種類とする。減給は1回の額が平均賃金の{gen_rate}分の1を超えず、総額が一賃金支払期における賃金総額の{gen_total}分の1を超えないものとする。"),
        ("退職", "退職を希望する者は、退職予定日の{retire_notice}日前までに退職届を提出すること。会社は退職届の受理後{retire_process}日以内に退職手続きを完了する。退職時には会社から貸与された物品をすべて返却すること。"),
        ("教育訓練", "会社は従業員の能力開発のため、年間{training_hours}時間の教育訓練を実施する。外部研修の費用は年間{training_budget}万円を上限として会社が負担する。資格取得奨励制度として、指定資格の取得時に{cert_bonus}万円の一時金を支給する。"),
        ("安全衛生", "会社は労働安全衛生法に基づき、安全衛生委員会を設置する。健康診断は年{health_check}回実施する。ストレスチェックは年{stress_check}回実施し、高ストレス者には産業医面談を推奨する。"),
    ],
    "経費精算規定": [
        ("交通費", "公共交通機関の利用を原則とする。タクシーは{taxi_limit}円以上の場合は事前承認が必要。通勤交通費は月額{commute_max}円を上限とする。ICカードの利用履歴を証拠として提出すること。"),
        ("出張旅費", "出張の宿泊費は1泊{hotel_max}円を上限とする。{special_area}は{hotel_special}円まで認める。日当は日帰り{daily_day}円、宿泊を伴う場合は{daily_stay}円とする。出張報告書は帰社後{report_days}営業日以内に提出すること。"),
        ("会議費", "会議費は1人あたり{meeting_max}円を上限とする。社外の方を含む場合は{meeting_ext}円まで認める。アルコールを含む場合は接待交際費として処理すること。"),
        ("接待交際費", "接待交際費は1回あたり{entertain_max}円を上限とする。事前に部門長の承認を得ること。参加者の氏名・所属・人数を記録すること。接待の目的と成果を報告書に記載すること。"),
        ("備品購入", "1件{supply_limit}円未満の備品は部門予算から支出可能。{supply_limit}円以上は稟議が必要。PCおよび周辺機器は情報システム部を通じて購入すること。"),
        ("精算手続", "経費精算は発生日から{settle_days}営業日以内に申請すること。{receipt_limit}円以上の支出は領収書の原本が必要。領収書を紛失した場合は{lost_limit}円未満であれば支出証明書で代替可能。"),
        ("海外出張", "海外出張の日当は地域により異なる。アジア圏{overseas_asia}円、欧米圏{overseas_west}円、その他{overseas_other}円。航空券はエコノミークラスを原則とする。ビジネスクラスは{biz_hours}時間以上のフライトで認める。"),
        ("通信費", "業務用携帯電話の通信費は会社負担とする。個人携帯を業務使用する場合は月額{phone_allowance}円の通信手当を支給する。海外ローミング料金は事前申請の上、実費を精算する。"),
    ],
    "情報セキュリティ規程": [
        ("アクセス管理", "業務システムへのアクセスは最小権限の原則に基づき付与する。パスワードは{pw_len}文字以上、英数字記号を含むこと。パスワードは{pw_change}日ごとに変更すること。{mfa}段階認証を必須とする。"),
        ("データ分類", "情報資産は機密度に応じて{class_num}段階に分類する。極秘（レベル{l1}）：経営戦略・人事情報等。秘密（レベル{l2}）：顧客情報・技術情報等。社外秘（レベル{l3}）：社内規程・業務マニュアル等。公開（レベル{l4}）：プレスリリース等。"),
        ("インシデント対応", "セキュリティインシデントを発見した場合は{incident_hours}時間以内に情報システム部に報告すること。情報システム部はインシデント対応チームを編成し、{response_hours}時間以内に初動対応を完了する。重大インシデントは経営層に即時報告する。"),
        ("外部媒体", "USBメモリ等の外部記憶媒体の使用は原則禁止とする。業務上必要な場合は情報システム部の許可を得ること。許可された外部媒体は暗号化を必須とする。紛失時は{lost_report}時間以内に報告すること。"),
        ("テレワーク", "テレワーク時はVPN接続を必須とする。公共Wi-Fiの使用は禁止する。画面ロックは{screen_lock}分で自動設定すること。のぞき見防止フィルターの使用を推奨する。"),
        ("メール利用", "業務メールの私的利用は禁止する。添付ファイルは{attach_max}MBを上限とする。機密情報を含むファイルの送信時は暗号化またはパスワード保護を行うこと。不審なメールを受信した場合は開かずに情報システム部に転送すること。"),
        ("ソフトウェア管理", "業務PCへのソフトウェアのインストールは情報システム部の許可を得ること。ライセンス管理台帳を情報システム部が一元管理する。OSおよびソフトウェアのセキュリティアップデートは配信後{update_days}日以内に適用すること。"),
    ],
    "コンプライアンス規程": [
        ("基本方針", "当社は法令遵守を経営の基本方針とする。全従業員は関連法令および社内規程を遵守し、高い倫理観を持って行動すること。コンプライアンス委員会は四半期ごとに開催し、遵守状況を確認する。"),
        ("内部通報", "法令違反または社内規程違反を発見した場合は、内部通報窓口に通報することができる。通報者の秘密は厳守し、通報を理由とする不利益な取扱いは一切行わない。通報の受付は{hotline}で行う。"),
        ("利益相反", "従業員は会社の利益と個人の利益が相反する取引を行ってはならない。競合他社との取引や投資は事前に法務部に届出を行うこと。取引先からの個人的な贈答品の受領は{gift_limit}円を上限とする。"),
        ("反社会的勢力", "反社会的勢力との一切の関係を排除する。取引先が反社会的勢力と判明した場合は直ちに取引を中止する。契約書には反社会的勢力排除条項を含めること。"),
        ("個人情報保護", "個人情報の取得は利用目的を明示した上で、本人の同意を得て行う。取得した個人情報は利用目的の範囲内で適切に管理する。個人情報の第三者提供は法令に基づく場合を除き、本人の同意を得ること。個人情報の保管期間は{retention_years}年とする。"),
        ("ハラスメント防止", "セクシャルハラスメント、パワーハラスメント、マタニティハラスメント等のあらゆるハラスメントを禁止する。ハラスメント相談窓口を設置し、相談者のプライバシーを保護する。ハラスメントが認定された場合は懲戒処分の対象とする。"),
    ],
    "BCP（事業継続計画）": [
        ("基本方針", "大規模災害、感染症パンデミック、システム障害等の緊急事態発生時においても、重要業務を継続または早期復旧するための計画を定める。BCPの見直しは年{bcp_review}回実施する。"),
        ("対策本部", "緊急事態発生時は社長を本部長とする対策本部を設置する。対策本部は{hq_hours}時間以内に初動対応を完了する。連絡網は四半期ごとに更新し、全従業員に周知する。"),
        ("リモートワーク体制", "緊急事態時は全従業員がリモートワークに移行できる体制を整備する。VPN同時接続数は全従業員の{vpn_ratio}%をカバーする。クラウドサービスを活用し、オフィス外からの業務遂行を可能にする。"),
        ("データバックアップ", "重要データは{backup_freq}に1回バックアップを取得する。バックアップデータは{backup_site}に保管する。復旧手順は年{dr_test}回のDR訓練で検証する。RPO（目標復旧時点）は{rpo}時間、RTO（目標復旧時間）は{rto}時間とする。"),
        ("安否確認", "災害発生時は安否確認システムを通じて全従業員の安否を確認する。確認メールの送信は発災後{anpi_min}分以内に行う。従業員は受信後{anpi_reply}時間以内に回答すること。"),
    ],
}

def _rand_params():
    """テンプレート用のランダムパラメータを生成"""
    return {
        "h": random.choice([7, 7.5, 8]),
        "w": random.choice([35, 37.5, 40]),
        "start": random.choice(["8:30", "9:00", "9:30", "10:00"]),
        "end": random.choice(["17:00", "17:30", "18:00", "18:30"]),
        "break_min": random.choice([45, 60]),
        "break_start": "12:00",
        "break_end": random.choice(["12:45", "13:00"]),
        "core_start": random.choice(["10:00", "10:30", "11:00"]),
        "core_end": random.choice(["15:00", "15:30", "16:00"]),
        "nenmatsu": f"12月{random.randint(28,30)}日〜1月{random.randint(3,4)}日",
        "natsu": f"8月{random.randint(13,14)}日〜8月{random.randint(15,16)}日",
        "furikae": random.randint(14, 30),
        "months": random.choice([6, 6]),
        "ratio": 8,
        "days": 10,
        "notice": random.choice([2, 3, 5]),
        "y2": random.choice([2, 3]),
        "d2": random.choice([12, 14]),
        "y3": random.choice([4, 5, 6]),
        "d3": random.choice([16, 18, 20]),
        "max_ot": random.choice([30, 36, 45]),
        "night_start": "22:00",
        "night_end": "5:00",
        "ot_rate": random.choice([25, 30]),
        "rw_days": random.choice([2, 3, 4]),
        "rw_allowance": random.choice([3000, 5000, 8000]),
        "penalty": random.choice(["懲戒処分", "けん責処分", "減給処分"]),
        "types": random.choice([5, 6]),
        "gen_rate": random.choice([2, 2]),
        "gen_total": 10,
        "retire_notice": random.choice([14, 30, 60]),
        "retire_process": random.choice([7, 14]),
        "training_hours": random.choice([20, 40, 60]),
        "training_budget": random.choice([10, 20, 30]),
        "cert_bonus": random.choice([3, 5, 10]),
        "health_check": random.choice([1, 2]),
        "stress_check": 1,
        "taxi_limit": random.choice([2000, 3000, 5000]),
        "commute_max": random.choice([30000, 50000]),
        "hotel_max": random.choice([8000, 10000, 12000]),
        "special_area": random.choice(["東京23区・大阪市内", "東京都内・大阪府内"]),
        "hotel_special": random.choice([10000, 12000, 15000]),
        "daily_day": random.choice([1000, 2000]),
        "daily_stay": random.choice([2000, 3000]),
        "report_days": random.choice([3, 5, 7]),
        "meeting_max": random.choice([3000, 5000]),
        "meeting_ext": random.choice([5000, 8000]),
        "entertain_max": random.choice([10000, 20000, 30000]),
        "supply_limit": random.choice([10000, 30000, 50000]),
        "settle_days": random.choice([5, 7, 10]),
        "receipt_limit": random.choice([1000, 3000]),
        "lost_limit": random.choice([1000, 3000]),
        "overseas_asia": random.choice([3000, 5000]),
        "overseas_west": random.choice([5000, 8000]),
        "overseas_other": random.choice([4000, 6000]),
        "biz_hours": random.choice([6, 8]),
        "phone_allowance": random.choice([2000, 3000, 5000]),
        "pw_len": random.choice([8, 10, 12]),
        "pw_change": random.choice([60, 90]),
        "mfa": 2,
        "class_num": 4,
        "l1": 4, "l2": 3, "l3": 2, "l4": 1,
        "incident_hours": random.choice([1, 2, 4]),
        "response_hours": random.choice([4, 8, 24]),
        "lost_report": random.choice([1, 2, 4]),
        "screen_lock": random.choice([3, 5, 10]),
        "attach_max": random.choice([10, 20, 25]),
        "update_days": random.choice([3, 5, 7]),
        "hotline": random.choice(["内部通報専用ダイヤル", "コンプライアンス窓口", "ethics@example.co.jp"]),
        "gift_limit": random.choice([3000, 5000]),
        "retention_years": random.choice([3, 5, 7]),
        "bcp_review": random.choice([1, 2]),
        "hq_hours": random.choice([1, 2]),
        "vpn_ratio": random.choice([80, 100]),
        "backup_freq": random.choice(["日次", "週次"]),
        "backup_site": random.choice(["遠隔地データセンター", "クラウドストレージ"]),
        "dr_test": random.choice([1, 2]),
        "rpo": random.choice([1, 4, 24]),
        "rto": random.choice([4, 8, 24]),
        "anpi_min": random.choice([15, 30]),
        "anpi_reply": random.choice([1, 2, 3]),
    }


def generate_document(company_name: str, doc_type: str, dept: str, version: int) -> str:
    """1文書分のテキストを生成する"""
    params = _rand_params()
    sections = TOPICS[doc_type]

    lines = [f"{company_name} {doc_type}（{dept}版 v{version}）\n"]
    lines.append(f"制定日: 2024年{random.randint(1,12)}月{random.randint(1,28)}日")
    lines.append(f"改訂日: 2026年{random.randint(1,4)}月{random.randint(1,28)}日")
    lines.append(f"管理部門: {dept}\n")

    for i, (title, template) in enumerate(sections, 1):
        lines.append(f"第{i}章 {title}\n")
        # テンプレートにパラメータを埋め込み
        try:
            content = template.format(**params)
        except KeyError:
            content = template
        # 同じセクションを変形して繰り返し、文書量を増やす
        lines.append(f"第{i}条（{title}の基本方針）")
        lines.append(content)
        lines.append("")
        lines.append(f"第{i}条の2（{title}の補足規定）")
        lines.append(f"前条の規定にかかわらず、{dept}において特別な事情がある場合は、部門長の承認を得て適用を除外することができる。")
        lines.append(f"適用除外の期間は最大{random.randint(1,6)}ヶ月とし、期間満了後は再申請を行うこと。")
        lines.append("")
        lines.append(f"第{i}条の3（{title}に関する届出）")
        lines.append(f"本章に定める事項に関する届出は、社内ポータルサイトの「{title}申請フォーム」から行うこと。")
        lines.append(f"届出の処理は受理後{random.randint(1,5)}営業日以内に完了する。不備がある場合は差し戻しとなる。")
        lines.append("")

    lines.append("附則")
    lines.append(f"本規程は2026年{random.randint(1,4)}月{random.randint(1,28)}日から施行する。")
    lines.append(f"本規程の改廃は{dept}が起案し、経営会議の承認を得て行う。\n")

    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    company_names = [
        "株式会社テックイノベーション", "株式会社グローバルソリューションズ",
        "株式会社ネクストフロンティア", "株式会社デジタルクリエイト",
        "株式会社サンライズシステム", "株式会社フューチャービジョン",
        "株式会社クラウドブリッジ", "株式会社インテリジェントワークス",
        "株式会社プログレスラボ", "株式会社エコシステムズ",
    ]

    doc_types = list(TOPICS.keys())
    total_files = 0

    for i in range(NUM_FILES):
        company = company_names[i % len(company_names)]
        doc_type = doc_types[i % len(doc_types)]
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        version = (i // len(doc_types)) + 1

        content = generate_document(company, doc_type, dept, version)
        filename = f"{doc_type}_{dept}_v{version}.txt"
        (OUTPUT_DIR / filename).write_text(content, encoding="utf-8")
        total_files += 1

    total_chars = sum(f.stat().st_size for f in OUTPUT_DIR.glob("*.txt"))
    est_chunks = total_chars // 750  # 800文字チャンク - 50オーバーラップ
    print(f"生成完了: {total_files} ファイル, 約 {total_chars:,} 文字, 推定 {est_chunks:,} チャンク")


if __name__ == "__main__":
    main()
