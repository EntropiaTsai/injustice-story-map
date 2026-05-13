"""
合併 NHRM 爬蟲結果與 twtjdb 資料，輸出地圖用的 JSON。

以 NHRM 記錄為主（12,060 筆），透過 twtjdb_ids 連結 twtjdb 資料取得
判決詳情與座標。找不到座標的，依下列優先順序嘗試 geocode：
  1. twtjdb 已有座標（被捕前居住地，最可靠）
  2. NHRM city 欄位（若省份為臺灣）
  3. NHRM introduction 文字擷取縣市名
  4. twtjdb native_province/native_city（籍貫，最後手段）

輸出：
  data/processed/nhrm_merged.json    全部 12,060 筆
  public/data/nhrm_map_ready.json    僅有座標的筆數（供網頁使用）

用法：
  python merge_nhrm.py
  python merge_nhrm.py --nhrm data/raw/nhrm_all.jsonl
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]

# ── 台灣縣市座標（與 process_twtjdb.py 共用同一份對照表）─────────────────────
TAIWAN_LOCATIONS: dict[str, tuple[float, float]] = {
    # ── 直轄市、縣市 ──────────────────────────────────────────────────────────
    "台北市": (25.0330, 121.5654), "臺北市": (25.0330, 121.5654),
    "新北市": (25.0120, 121.4651),
    "桃園市": (24.9937, 121.3010),
    "台中市": (24.1477, 120.6736), "臺中市": (24.1477, 120.6736),
    "台南市": (22.9999, 120.2270), "臺南市": (22.9999, 120.2270),
    "高雄市": (22.6273, 120.3014),
    "基隆市": (25.1276, 121.7392),
    "新竹市": (24.8066, 120.9686),
    "嘉義市": (23.4801, 120.4491),
    "宜蘭縣": (24.7021, 121.7378),
    "新竹縣": (24.8387, 121.0177),
    "苗栗縣": (24.5602, 120.8214),
    "彰化縣": (24.0684, 120.5820),
    "南投縣": (23.9609, 120.9718),
    "雲林縣": (23.7092, 120.4313),
    "嘉義縣": (23.4518, 120.2554),
    "屏東縣": (22.5519, 120.5487),
    "台東縣": (22.7972, 121.0713), "臺東縣": (22.7972, 121.0713),
    "花蓮縣": (23.9872, 121.6015),
    "澎湖縣": (23.5711, 119.5795),
    "金門縣": (24.4493, 118.3767),
    "連江縣": (26.1505, 119.9289),
    "台北縣": (25.0120, 121.4651), "臺北縣": (25.0120, 121.4651),
    "高雄縣": (22.6273, 120.3014),
    "台南縣": (22.9999, 120.2270), "臺南縣": (22.9999, 120.2270),
    "桃園縣": (24.9937, 121.3010),
    "台中縣": (24.1477, 120.6736), "臺中縣": (24.1477, 120.6736),
    # 台灣省/臺灣省 刻意省略：幾乎都是機構名前綴，geocode 到台灣中心無意義
    # ── 離島 ─────────────────────────────────────────────────────────────────
    "綠島":   (22.6607, 121.4920),
    "火燒島": (22.6607, 121.4920),
    # ── 台北市各行政區 ────────────────────────────────────────────────────────
    "中正區": (25.0408, 121.5176),
    "大同區": (25.0628, 121.5118),
    "中山區": (25.0637, 121.5296),
    "松山區": (25.0511, 121.5776),
    "大安區": (25.0264, 121.5431),
    "信義區": (25.0340, 121.5645),
    "文山區": (24.9925, 121.5667),
    "南港區": (25.0552, 121.6078),
    "士林區": (25.0936, 121.5240),
    "北投區": (25.1317, 121.4989),
    "內湖區": (25.0756, 121.5936),
    "萬華區": (25.0374, 121.4994),
    # ── 高雄市各行政區 ────────────────────────────────────────────────────────
    "苓雅區": (22.6172, 120.3091),
    "前金區": (22.6328, 120.3012),
    "新興區": (22.6295, 120.3027),
    "鹽埕區": (22.6271, 120.2869),
    "鼓山區": (22.6586, 120.2881),
    "旗津區": (22.5813, 120.2763),
    "前鎮區": (22.5927, 120.3268),
    "小港區": (22.5567, 120.3527),
    "三民區": (22.6543, 120.3074),
    "楠梓區": (22.7213, 120.3149),
    "仁武區": (22.7063, 120.3543),
    # ── 台南市各行政區/鄉鎮 ──────────────────────────────────────────────────
    "中西區": (22.9965, 120.2026),
    "安南區": (23.0531, 120.1736),
    "安平區": (22.9950, 120.1668),
    "安定區": (23.0558, 120.2386),
    "安定鄉": (23.0558, 120.2386),
    "新化區": (23.0364, 120.3127),
    "永康區": (23.0335, 120.2608),
    "新豐區": (23.0976, 120.2477),
    "柳營區": (23.2265, 120.3409),
    "麻豆區": (23.1784, 120.2533),
    "佳里區": (23.1721, 120.1844),
    # ── 台中市各行政區 ────────────────────────────────────────────────────────
    "豐原區": (24.2537, 120.7196),
    "大甲區": (24.3544, 120.6216),
    "清水區": (24.3636, 120.5638),
    "沙鹿區": (24.2923, 120.5663),
    "龍井區": (24.2401, 120.5463),
    "烏日區": (24.1006, 120.6415),
    "霧峰區": (24.0573, 120.7178),
    "太平區": (24.1291, 120.7178),
    "北屯區": (24.1757, 120.6966),
    "西屯區": (24.1653, 120.6383),
    "南屯區": (24.1301, 120.6438),
    # ── 新北市各行政區 ────────────────────────────────────────────────────────
    "新莊區": (25.0365, 121.4396),
    "三峽區": (24.9386, 121.3673),
    "蘆洲區": (25.0830, 121.4739),
    "泰山區": (25.0588, 121.4289),
    "瑞芳區": (25.1093, 121.8066),
    "金山區": (25.2213, 121.6438),
    "萬里區": (25.1801, 121.6786),
    # ── 桃園市各行政區 ────────────────────────────────────────────────────────
    "平鎮區": (24.9457, 121.2248),
    "八德區": (24.9526, 121.2892),
    "楊梅區": (24.9142, 121.1462),
    "龜山區": (25.0371, 121.3572),
    "大溪區": (24.8778, 121.2888),
    # ── 屏東縣各鄉鎮 ─────────────────────────────────────────────────────────
    "屏東市": (22.6753, 120.4870),
    "潮州鎮": (22.5492, 120.5460),
    "東港鎮": (22.4636, 120.4527),
    "恆春鎮": (21.9328, 120.7415),
    "萬丹鄉": (22.5960, 120.4966),
    "里港鄉": (22.7765, 120.4784),
    # ── 彰化縣各鄉鎮 ─────────────────────────────────────────────────────────
    "鹿港鎮": (24.0523, 120.4348),
    "鹿港":   (24.0523, 120.4348),
    "和美鎮": (24.1148, 120.5081),
    "二林鎮": (23.9134, 120.3895),
    "溪湖鎮": (23.9584, 120.4709),
    "田中鎮": (23.8700, 120.5378),
    "溪洲鄉": (23.8586, 120.4913),
    "溪洲":   (23.8586, 120.4913),
    # ── 雲林縣各鄉鎮 ─────────────────────────────────────────────────────────
    "西螺鎮": (23.8009, 120.4666),
    "土庫鎮": (23.6726, 120.3957),
    "北港鎮": (23.5701, 120.3053),
    "北港":   (23.5701, 120.3053),
    "斗南鎮": (23.6796, 120.4834),
    "林內鄉": (23.7613, 120.6053),
    "林內":   (23.7613, 120.6053),
    # ── 嘉義縣各鄉鎮 ─────────────────────────────────────────────────────────
    "朴子市": (23.4577, 120.2449),
    "布袋鎮": (23.3791, 120.1653),
    "民雄鄉": (23.5594, 120.4304),
    "大林鎮": (23.6056, 120.4698),
    "水上鄉": (23.4393, 120.3940),
    # ── 苗栗縣各鄉鎮 ─────────────────────────────────────────────────────────
    "頭份市": (24.6878, 120.8756),
    "通霄鎮": (24.4882, 120.6935),
    "苑裡鎮": (24.4326, 120.6527),
    # ── 南投縣各鄉鎮 ─────────────────────────────────────────────────────────
    "草屯鎮": (24.0555, 120.6808),
    "集集鎮": (23.8313, 120.7894),
    "竹山鎮": (23.7548, 120.6712),
    "名間鄉": (23.8803, 120.7038),
    # ── 花蓮縣各鄉鎮 ─────────────────────────────────────────────────────────
    "新城鄉": (24.1212, 121.6574),   # 花蓮縣新城鄉
    "新城":   (24.1212, 121.6574),
    "壽豐鄉": (23.9031, 121.5266),
    "光復鄉": (23.6766, 121.4320),
    "吉安鄉": (23.9704, 121.5768),
    "鳳林鎮": (23.7465, 121.4417),
    # ── 台東縣各鄉鎮 ─────────────────────────────────────────────────────────
    "卑南鄉": (22.7398, 121.0789),
    "關山鎮": (23.0528, 121.1672),
    "池上鄉": (23.1089, 121.2233),
    "成功鎮": (23.0994, 121.3706),
    "東河鄉": (23.1167, 121.2500),
    # ── 宜蘭縣各鄉鎮 ─────────────────────────────────────────────────────────
    "礁溪鄉": (24.8202, 121.7720),
    "三星鄉": (24.6567, 121.6488),
    "冬山鄉": (24.6529, 121.7990),
    "五結鄉": (24.6812, 121.8118),
    # ── 區/鎮/設施（短名對照）────────────────────────────────────────────────
    "內湖":   (25.0630, 121.5939),
    "景美":   (24.9984, 121.5415),
    "新店":   (24.9716, 121.5378),
    "板橋":   (25.0141, 121.4617),
    "淡水":   (25.1711, 121.4497),
    "三重":   (25.0620, 121.4924),
    "中和":   (24.9999, 121.4889),
    "永和":   (25.0133, 121.5195),
    "台北":   (25.0330, 121.5654), "臺北": (25.0330, 121.5654),
    "北市":   (25.0330, 121.5654),
    "基隆":   (25.1276, 121.7392),
    "桃園":   (24.9937, 121.3010),
    "新竹":   (24.8066, 120.9686),
    "苗栗":   (24.5602, 120.8214),
    "竹南":   (24.6874, 120.8639),
    "中壢":   (24.9636, 121.2249),
    "台中":   (24.1477, 120.6736), "臺中": (24.1477, 120.6736),
    "豐原":   (24.2537, 120.7196),
    "清水":   (24.3636, 120.5638),
    "土城":   (24.9750, 121.4378),
    "彰化":   (24.0684, 120.5820),
    "員林":   (23.9586, 120.5710),
    "南投":   (23.9609, 120.9718),
    "埔里":   (23.9611, 120.9735),
    "雲林":   (23.7092, 120.4313),
    "斗六":   (23.7104, 120.5428),
    "虎尾":   (23.7082, 120.4394),
    "嘉義":   (23.4801, 120.4491),
    "台南":   (22.9999, 120.2270), "臺南": (22.9999, 120.2270),
    "新營":   (23.3116, 120.3123),
    "善化":   (23.1434, 120.2977),
    "歸仁":   (22.9654, 120.2914),
    "高雄":   (22.6273, 120.3014),
    "岡山":   (22.7953, 120.2949),
    "鳳山":   (22.6271, 120.3567),
    "旗山":   (22.8878, 120.4806),
    "左營":   (22.6911, 120.2954),
    "屏東":   (22.5519, 120.5487),
    "澎湖":   (23.5711, 119.5795),
    "馬公":   (23.5642, 119.5631),
    "花蓮":   (23.9872, 121.6015),
    "玉里":   (23.6327, 121.3149),
    "台東":   (22.7972, 121.0713), "臺東": (22.7972, 121.0713),
    "泰源":   (23.1167, 121.2500),
    "宜蘭":   (24.7021, 121.7378),
    "羅東":   (24.6776, 121.7712),
    "漁翁島": (23.6000, 119.5000),
    "臺灣大學": (25.0174, 121.5396), "台灣大學": (25.0174, 121.5396),
    "馬場町": (25.0302, 121.5057),
    "六張犁": (25.0244, 121.5607),
    "士林":   (25.0878, 121.5240),
    "北投":   (25.1317, 121.4989),
    "木柵":   (24.9983, 121.5681),
    "萬華":   (25.0374, 121.5000),
    "大稻埕": (25.0568, 121.5108),
    "汐止":   (25.0698, 121.6604),
    "金瓜石": (25.1093, 121.8525),
    "蘇澳":   (24.5978, 121.8438),
    "頭城":   (24.8460, 121.8188),
    "台東市": (22.7972, 121.0713), "臺東市": (22.7972, 121.0713),
    "關山":   (23.0528, 121.1672),
    "池上":   (23.1089, 121.2233),
    "成功":   (23.0994, 121.3706),
    # ── 報社/媒體（案發地） ───────────────────────────────────────────────────
    # ── 基隆市特定地點 ───────────────────────────────────────────────────────
    "八堵":      (25.0795, 121.6899),   # 基隆市八堵區（八堵火車站）
    "暖暖":      (25.0833, 121.7300),   # 基隆市暖暖區
    # ── 苗栗縣特定地點 ───────────────────────────────────────────────────────
    "後龍":      (24.6216, 120.7959),   # 苗栗縣後龍鎮（後龍車站）
    "銅鑼":      (24.5124, 120.7924),   # 苗栗縣銅鑼鄉
    # ── 台南特定地點 ─────────────────────────────────────────────────────────
    "灣裡":      (22.9587, 120.2068),   # 台南市南區灣裡（台糖灣裡糖廠）
    # ── 台東縣特定地點 ───────────────────────────────────────────────────────
    "大武":      (22.3557, 120.8948),   # 台東縣大武鄉（氣象局大武測候所）
    # ── 新北市特定地點 ───────────────────────────────────────────────────────
    "八里":      (25.1432, 121.4004),   # 新北市八里區（八里坌碼頭）
    # ── 特定機構（不含行政區短名） ────────────────────────────────────────────
    "松山煙廠":  (25.0511, 121.5776),   # 台北市松山區（台灣省專賣局松山煙廠）
    "松山菸廠":  (25.0511, 121.5776),
    "松山煙草":  (25.0511, 121.5776),
    "松山倉庫":  (25.0511, 121.5776),
    "淡江中學":  (25.1711, 121.4497),   # 新北市淡水（真理大學旁）
    "臺灣廣播公司":   (25.0459, 121.5249),  # 台北市中正區
    "臺灣廣播電臺":   (25.0459, 121.5249),
    "臺灣省通運公司": (25.0330, 121.5654),  # 台北市
    "行政長官公署":   (25.0437, 121.5073),  # 台北市
    "臺灣省行政長官": (25.0437, 121.5073),
    "玉山林場":       (23.4801, 120.4491),  # 嘉義縣（嘉義林區管理處轄區）
    # ── 報社/媒體（案發地） ───────────────────────────────────────────────────
    "台灣新生報": (25.0518, 121.5432),   # 台北市中山區復興北路40號
    "新生報":    (25.0518, 121.5432),
    "中央日報":  (25.0452, 121.5201),   # 台北市
    "自立晚報":  (25.0437, 121.5073),   # 台北市
    "民族晚報":  (25.0452, 121.5153),   # 台北市
    "全民日報":  (25.0452, 121.5153),   # 台北市
    # ── 大學/院校（精確地址）─────────────────────────────────────────────────
    "臺灣省立師範學院": (25.0264, 121.5277),   # 台北市大安區和平東路一段162號 → 師大
    "臺灣師範學院":     (25.0264, 121.5277),   # 同上（舊稱）
    "臺灣師範大學":     (25.0264, 121.5277),
    "臺北師範學校":     (25.0353, 121.5110),   # 台北市中正區愛國西路1號 → 台北市立大學
    "臺北師範":         (25.0353, 121.5110),
    "省立師範":         (25.0264, 121.5277),
    "台灣大學":         (25.0174, 121.5396),   # 台北市羅斯福路四段1號
    "臺灣大學":         (25.0174, 121.5396),
    "台大":             (25.0174, 121.5396),
    "臺大":             (25.0174, 121.5396),
    "臺中師範學校":     (24.1523, 120.6782),   # 台中市民權路85號 → 台中教育大學
    "臺中師範":         (24.1523, 120.6782),
    "台中師範":         (24.1523, 120.6782),
    "臺灣省立農學院":   (24.1143, 120.6855),   # 台中市南區 → 中興大學前身
    "台灣省立農學院":   (24.1143, 120.6855),
    "臺灣省立工學院":   (23.0015, 120.2195),   # 台南市東區大學路1號 → 成功大學
    "臺南工學院":       (23.0015, 120.2195),
    "台南工學院":       (23.0015, 120.2195),
    "成功大學":         (23.0015, 120.2195),
    "國防醫學院":       (25.0780, 121.5495),   # 台北市中山區大直
    "海軍軍官學校":     (22.6233, 120.2724),   # 高雄市左營區
    "陸軍官校":         (22.6271, 120.3567),   # 高雄市鳳山
    "空軍軍官學校":     (22.7832, 120.2707),   # 高雄市岡山區後協里（Plus Code Q7MC+76）
    "空軍機械學校":     (22.7832, 120.2707),   # 同上
    "空軍官校":         (22.7832, 120.2707),   # 同上（簡稱）
    "空軍通信電子學校": (22.7832, 120.2707),   # 同上
    "空軍航空技術學校": (22.7832, 120.2707),   # 同上
    "空軍機校":         (22.7832, 120.2707),   # 同上（簡稱）
    "金門怒潮軍政學校": (24.4493, 118.3767),   # 金門縣
    "政治大學":         (24.9872, 121.5788),   # 台北市文山區指南路
    "政工幹部學校":     (24.9872, 121.5788),   # 同上（政大前身）
    "陽明山":           (25.1524, 121.5609),   # 台北市（陽明山管理局轄區）
    "花蓮女中":         (23.9872, 121.6015),   # 花蓮市
    "花蓮師範":         (23.9872, 121.6015),   # 花蓮市
    # ── 工廠/國營事業 ────────────────────────────────────────────────────────
    "潭子糖廠":         (24.2113, 120.7040),   # 台中市潭子區（帝國製糖潭子工場）
    "溪湖糖廠":         (23.9584, 120.4709),   # 彰化縣溪湖鎮
    "溪湖":             (23.9584, 120.4709),   # 彰化縣溪湖鎮短稱
    "麻佳":             (23.1784, 120.2533),   # 台南市麻豆區（臺糖麻佳總廠）
    "達見":             (24.2620, 121.0395),   # 台中市和平區（台電達見水庫工程處）
    "海軍士兵學校":     (22.6911, 120.2954),   # 高雄市左營區
    "海軍軍士學校":     (22.6911, 120.2954),   # 同上（改名後）
    "高雄煉油廠":       (22.7213, 120.3149),   # 高雄市楠梓區中山路1號
    "苗栗探勘處":       (24.5602, 120.8214),   # 苗栗市
    "高雄機械廠":       (22.6543, 120.3074),   # 高雄市三民區
    "高雄機務段":       (22.6273, 120.3014),   # 高雄站周邊
    "嘉義機務段":       (23.4801, 120.4491),   # 嘉義市
    "臺中紙廠":         (24.2537, 120.7196),   # 台中市豐原區
    "台中紙廠":         (24.2537, 120.7196),
    "岡山機械廠":       (22.7953, 120.2949),   # 高雄市岡山
    "基隆煤礦":         (25.1276, 121.7392),   # 基隆市
    "金瓜石礦山":       (25.1093, 121.8525),   # 新北市瑞芳
    "臺陽礦業":         (25.1093, 121.8525),   # 新北市瑞芳
    "第四酒廠":         (24.1477, 120.6736),   # 台中市（專賣局台中酒廠）
    # ── 軍事機關（審判/關押地） ───────────────────────────────────────────────
    "鳳山招待所":           (22.6307, 120.3746),   # 高雄市鳳山區勝利路（原日本海軍鳳山無線電信所）
    "明德訓練班":           (22.6307, 120.3746),   # 同上
    "鳳山無線電信所":       (22.6307, 120.3746),   # 同上
    "景美看守所":           (24.9984, 121.5415),   # 台北市文山區景美
    "軍法處看守所":         (24.9984, 121.5415),
    "新生訓導處":           (22.6607, 121.4920),   # 綠島
    "台灣省保安司令部":     (25.0437, 121.5073),   # 台北市博愛路（保安處）
    "臺灣省保安司令部":     (25.0437, 121.5073),
    "警備總部":             (25.0437, 121.5073),   # 台北市（警備總司令部）
    "保密局南所":           (25.0378, 121.5089),   # 台北市中正區延平南路133巷（非鳳山）
    "延平南路看守所":       (25.0378, 121.5089),   # 同上
    "臺灣省生產教育實驗所": (24.9795, 121.4617),   # 新北市土城區仁愛路23號
    "仁愛教育實驗所":       (24.9795, 121.4617),   # 同上（1974年改名）
    "生教所":               (24.9795, 121.4617),
    "海軍反共先鋒訓練營":   (23.9586, 120.5710),   # 彰化縣員林（2-3期，最多人）
    "反共先鋒營":           (23.9586, 120.5710),
    "先鋒營":               (23.9586, 120.5710),
    "安坑":                 (24.9716, 121.5378),   # 新北市新店安坑
    # ── 收容機構名稱（無地名前綴仍可比對） ─────────────────────────────────────────
    "新生總隊":             (25.0482, 121.6366),   # 台北市內湖新生訓導總隊
    "內湖新生":             (25.0482, 121.6366),   # 同上
    "國防部臺灣軍人監獄":   (24.9716, 121.5378),   # 新北市新店安坑（同安坑）
    "國防部軍人監獄":       (24.9716, 121.5378),   # 同上（省略「臺灣」）
    "職訓總隊":             (24.9795, 121.4617),   # 新北市土城（臺灣警備總司令部職業訓導總隊）
    "職業訓導總隊":         (24.9795, 121.4617),   # 同上（全稱）
    "職業訓導第":           (24.9795, 121.4617),   # 職業訓導第一/二/三總隊
    "職訓第":               (24.9795, 121.4617),   # 職訓第一總隊等簡稱
    "青年訓導總隊":         (25.0330, 121.5654),   # 台北市（青訓總隊）
    "國防部軍法局":         (25.0330, 121.5654),   # 台北市（軍法局）
    "大直勞動訓導營":       (25.0780, 121.5495),   # 台北市大直（同國防醫學院區）
    "陸軍總司令部":         (25.0437, 121.5073),   # 台北市（陸軍總部）
    "陸軍總司令部看守所":   (25.0437, 121.5073),   # 同上
    "聯合勤務總司令部":     (25.0437, 121.5073),   # 台北市（聯勤總部）
    "保密局":               (25.0378, 121.5089),   # 台北市（同延平南路看守所區）
    "海軍總司令部":         (22.6729, 120.2889),   # 高雄市左營區（海軍總部）
    "憲兵第八團":           (25.0437, 121.5073),   # 台北市
    "憲兵第8團":            (25.0437, 121.5073),   # 同上（數字寫法）
    "臺灣警備總司令部看守所": (24.9984, 121.5415), # 台北市文山（同景美看守所）
    "金門":                 (24.4493, 118.3765),   # 金門縣
    "馬祖":                 (26.1504, 119.9318),   # 連江縣馬祖
}


CHINESE_NUMS: dict[str, int] = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
}


def derive_penalty_level(judgment: dict | None, nhrm_penalty: list) -> str:
    """從 twtjdb 判決或 NHRM 刑罰欄位推導刑罰等級。"""
    # 優先用 twtjdb 結構化欄位
    if judgment:
        if judgment.get("has_death_penalty") or judgment.get("has_life_sentence"):
            return "death"
        text = str(judgment.get("penalty_text") or "")
        if "死刑" in text:
            return "death"
        arabic = [int(m) for m in re.findall(r"有期徒刑(\d+)年", text)]
        chinese = [v for k, v in CHINESE_NUMS.items() if f"有期徒刑{k}年" in text]
        years = arabic + chinese
        if years:
            return "heavy" if max(years) >= 10 else "light"

    # fallback：NHRM penalty term
    for p in (nhrm_penalty or []):
        term = (p.get("term") or "") + (p.get("penalty_text") or "")
        if "死刑" in term or "無期" in term:
            return "death"
        arabic = [int(m) for m in re.findall(r"(\d+)年", term)]
        chinese = [v for k, v in CHINESE_NUMS.items() if f"{k}年" in term]
        years = arabic + chinese
        if years:
            return "heavy" if max(years) >= 10 else "light"

    return "unknown"


_GEOCODE_SORTED: list[tuple[str, tuple[float, float]]] = []

def geocode(text: str | None) -> tuple[float, float] | None:
    """比對 TAIWAN_LOCATIONS，優先採最長 key（避免短字匹配遮蔽長字）。"""
    global _GEOCODE_SORTED
    if not _GEOCODE_SORTED:
        _GEOCODE_SORTED = sorted(TAIWAN_LOCATIONS.items(), key=lambda x: -len(x[0]))
    if not text:
        return None
    for key, coords in _GEOCODE_SORTED:
        if key in text:
            return coords
    return None


# 在 introduction 裡出現「台灣省」幾乎都是機構名前綴，不是地點，需排除
_INTRO_EXCLUDE = {"台灣省", "臺灣省"}


def extract_location_from_intro(text: str | None) -> str | None:
    """從傳記文字擷取案發地名。優先掃前 200 字，優先比對較長（更精確）的鍵。"""
    if not text:
        return None
    head = text[:200]
    sorted_keys = sorted(TAIWAN_LOCATIONS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in _INTRO_EXCLUDE:
            continue
        if key in head:
            return key
    # fallback：掃全文（仍排除泛稱）
    for key in sorted_keys:
        if key in _INTRO_EXCLUDE:
            continue
        if key in text:
            return key
    return None


# ── 載入資料 ───────────────────────────────────────────────────────────────────

def load_twtjdb() -> dict[str, dict]:
    """回傳 {twtjdb_id: person_dict}。"""
    persons: dict[str, dict] = {}
    for fname in ("twtjdb_map_ready.json", "twtjdb_pending.json"):
        with open(REPO / "data/processed" / fname, encoding="utf-8") as f:
            for p in json.load(f)["persons"]:
                persons[str(p["id"])] = p
    return persons


def load_nhrm(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ── 合併單筆 ───────────────────────────────────────────────────────────────────

def merge_one(nhrm: dict, twtjdb: dict[str, dict]) -> dict[str, Any]:
    # 找第一筆有效的 twtjdb 記錄
    twtjdb_rec: dict | None = None
    twtjdb_id: str | None = None
    for tid in (nhrm.get("twtjdb_ids") or []):
        if tid in twtjdb:
            twtjdb_rec = twtjdb[tid]
            twtjdb_id = tid
            break

    # ── 座標 ──────────────────────────────────────────────────────────────────
    lat = lng = None
    location_source: str | None = None
    location_raw: str | None = None

    # 1. twtjdb 已有座標
    if twtjdb_rec and twtjdb_rec.get("lat"):
        lat = twtjdb_rec["lat"]
        lng = twtjdb_rec["lng"]
        location_raw = twtjdb_rec.get("location_raw")
        location_source = "twtjdb"

    # 2. NHRM city（省份為臺灣時）
    if lat is None:
        province = nhrm.get("province") or ""
        city = nhrm.get("city") or ""
        if "臺灣" in province or "台灣" in province:
            coords = geocode(city)
            if coords:
                lat, lng = coords
                location_raw = city
                location_source = "nhrm_city"

    # 2.5. 若只有縣市級，試著從 introduction 精煉到區/鎮/鄉
    if location_source == "nhrm_city":
        refined = extract_location_from_intro(nhrm.get("introduction"))
        if refined and refined != location_raw:
            refined_coords = geocode(refined)
            if refined_coords and refined_coords != (lat, lng):
                lat, lng = refined_coords
                location_raw = refined
                location_source = "nhrm_intro"

    # 3. NHRM place 欄位（關押地/案發地，如「綠島」「泰源」「鳳山」）
    if lat is None:
        place = nhrm.get("place") or ""
        coords = geocode(place)
        if coords:
            lat, lng = coords
            location_raw = place
            location_source = "nhrm_place"

    # 4. introduction 文字擷取（案發地常在前 150 字）
    if lat is None:
        extracted = extract_location_from_intro(nhrm.get("introduction"))
        coords = geocode(extracted)
        if coords:
            lat, lng = coords
            location_raw = extracted
            location_source = "nhrm_intro"

    # 5. twtjdb 籍貫（最後手段）
    if lat is None and twtjdb_rec:
        native = (twtjdb_rec.get("native_province") or "") + (twtjdb_rec.get("native_city") or "")
        coords = geocode(native)
        if coords:
            lat, lng = coords
            location_raw = native
            location_source = "native"

    # ── 判決資料（從 twtjdb 取，較結構化） ───────────────────────────────────
    judgment: dict | None = None
    if twtjdb_rec:
        j = twtjdb_rec.get("judgment") or twtjdb_rec.get("final_judgment") or {}
        judgment = {
            "authority": j.get("authority"),
            "year_roc": j.get("year_roc"),
            "penalty_text": j.get("penalty_text"),
            "has_death_penalty": j.get("has_death_penalty", False),
            "has_life_sentence": j.get("has_life_sentence", False),
            "organization": j.get("organization"),
        }

    nhrm_penalty = nhrm.get("penalty") or []
    penalty_level = derive_penalty_level(judgment, nhrm_penalty)

    return {
        "nhrm_id": nhrm["nhrm_id"],
        "twtjdb_id": twtjdb_id,
        "name": nhrm.get("name"),
        "nickname": nhrm.get("nickname"),
        "gender": nhrm.get("gender"),
        "birth_year": nhrm.get("birth_year"),
        "death_year": nhrm.get("death_year"),
        "province": nhrm.get("province"),
        "city": nhrm.get("city"),
        "place": nhrm.get("place"),
        "lat": lat,
        "lng": lng,
        "location_source": location_source,
        "location_raw": location_raw,
        "penalty_level": penalty_level,
        "image_url": nhrm.get("image_url"),
        "introduction": nhrm.get("introduction"),
        "nhrm_url": nhrm.get("url"),
        "judgment": judgment,
        "nhrm_penalty": nhrm_penalty,
        "cases": nhrm.get("cases") or [],
        "related_persons": nhrm.get("related_persons") or [],
        "recoup": nhrm.get("recoup") or [],
        "documents": nhrm.get("documents") or [],
    }


# ── 主流程 ────────────────────────────────────────────────────────────────────

def load_llm_patch() -> dict[int, dict]:
    """讀取 Gemini geocoding patch，回傳 {nhrm_id: {lat, lng, location_raw}}。"""
    patch_path = REPO / "data/processed/nhrm_llm_patch.jsonl"
    patch: dict[int, dict] = {}
    if not patch_path.exists():
        return patch
    with open(patch_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                nid = obj["nhrm_id"]
                if obj.get("lat") is not None:
                    patch[nid] = obj
    print(f"  LLM patch 有座標：{len(patch)} 筆", file=sys.stderr)
    return patch


def load_audit_summaries() -> dict[int, str]:
    """讀取 nhrm_audit.jsonl，回傳 {nhrm_id: summary}（只取有摘要的記錄）。"""
    audit_path = REPO / "data/processed/nhrm_audit.jsonl"
    summaries: dict[int, str] = {}
    if not audit_path.exists():
        return summaries
    with open(audit_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    if obj.get("summary"):
                        summaries[obj["nhrm_id"]] = obj["summary"]
                except (json.JSONDecodeError, KeyError):
                    pass
    print(f"  audit 摘要：{len(summaries)} 筆", file=sys.stderr)
    return summaries


def main(nhrm_path: Path, output_path: Path) -> None:
    print("載入 twtjdb...", file=sys.stderr)
    twtjdb = load_twtjdb()
    print(f"  {len(twtjdb)} 筆", file=sys.stderr)

    print(f"載入 NHRM ({nhrm_path.name})...", file=sys.stderr)
    nhrm_records = load_nhrm(nhrm_path)
    valid = [r for r in nhrm_records if not r.get("error")]
    print(f"  {len(nhrm_records)} 筆（有效 {len(valid)} 筆）", file=sys.stderr)

    print("載入 LLM geocoding patch...", file=sys.stderr)
    llm_patch = load_llm_patch()

    print("載入 audit 摘要...", file=sys.stderr)
    audit_summaries = load_audit_summaries()

    persons = []
    stats: dict[str, int] = {
        "with_coords": 0,
        "no_coords": 0,
        "source_twtjdb": 0,
        "source_nhrm_city": 0,
        "source_nhrm_place": 0,
        "source_nhrm_intro": 0,
        "source_native": 0,
        "source_llm": 0,
        "has_twtjdb_match": 0,
        "no_twtjdb_match": 0,
    }

    for rec in valid:
        merged = merge_one(rec, twtjdb)

        # 6a. force patch（覆蓋自動 geocoding，source != twtjdb 時才生效）
        nid = rec["nhrm_id"]
        if nid in llm_patch and llm_patch[nid].get("force") and merged.get("location_source") != "twtjdb":
            p = llm_patch[nid]
            merged["lat"] = p["lat"]
            merged["lng"] = p["lng"]
            merged["location_raw"] = p["location_raw"]
            merged["location_source"] = "llm"

        # 6b. LLM geocoding patch（最後手段，只補無座標記錄）
        if merged["lat"] is None and nid in llm_patch:
            p = llm_patch[nid]
            merged["lat"] = p["lat"]
            merged["lng"] = p["lng"]
            merged["location_raw"] = p["location_raw"]
            merged["location_source"] = "llm"

        # 7. 注入 audit 摘要（若有）
        if nid in audit_summaries:
            merged["summary"] = audit_summaries[nid]

        persons.append(merged)

        if merged["lat"] is not None:
            stats["with_coords"] += 1
            stats[f"source_{merged['location_source']}"] += 1
        else:
            stats["no_coords"] += 1

        if merged["twtjdb_id"]:
            stats["has_twtjdb_match"] += 1
        else:
            stats["no_twtjdb_match"] += 1

    meta = {"nhrm_total": len(nhrm_records), "valid": len(valid), **stats}
    output = {"_meta": meta, "persons": persons}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 讀取 audit 中有確認案發地點的 nhrm_id 集合，以及 audit 提供的精確座標
    audit_path = REPO / "data/processed/nhrm_audit.jsonl"
    audit_confirmed: set[int] = set()
    audit_coords: dict[int, tuple[float, float]] = {}  # nhrm_id → (lat, lng)
    audit_locations: dict[int, str] = {}              # nhrm_id → arrest_location 文字
    if audit_path.exists():
        with open(audit_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        nid = obj["nhrm_id"]
                        if obj.get("arrest_location"):
                            audit_confirmed.add(nid)
                            audit_locations[nid] = obj["arrest_location"]
                            if obj.get("arrest_lat") and obj.get("arrest_lng"):
                                audit_coords[nid] = (obj["arrest_lat"], obj["arrest_lng"])
                    except (json.JSONDecodeError, KeyError):
                        pass
    print(f"  audit 確認案發地點：{len(audit_confirmed)} 筆（含座標：{len(audit_coords)} 筆）", file=sys.stderr)

    # 供網頁使用：
    #   - twtjdb 來源（被捕前居住地）：直接上圖
    #   - llm/其他來源：只有 audit 確認案發地點者才上圖，其餘移入待補清單
    public_path = REPO / "public" / "data" / "nhrm_map_ready.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    map_ready = []
    pending_no_coord = []
    _JITTER_SOURCES = {"twtjdb", "nhrm_city", "nhrm_place", "nhrm_intro", "native"}
    for p in persons:
        src = p.get("location_source")
        nid = p["nhrm_id"]
        # 判斷是否允許上地圖
        if p["lat"] is None:
            pending_no_coord.append(p)
            continue
        if src == "twtjdb":
            pass  # 被捕前居住地，最可靠，直接上圖
        else:
            # llm / nhrm_city / nhrm_place / nhrm_intro / native：
            # 統一要求 audit 確認案發地點，避免模糊 geocoding 誤置
            if nid not in audit_confirmed:
                pending_no_coord.append(p)
                continue
        rec = dict(p)
        # audit 提供的精確案發座標優先於原始 geocoded 座標
        if nid in audit_coords:
            rec["lat"], rec["lng"] = audit_coords[nid]
            rec["location_source"] = "audit"
        if nid in audit_locations:
            rec["arrest_location"] = audit_locations[nid]
        elif rec.get("location_source") in _JITTER_SOURCES:
            rng = random.Random(rec["nhrm_id"])
            rec["lat"] = round(rec["lat"] + rng.uniform(-0.06, 0.06), 6)
            rec["lng"] = round(rec["lng"] + rng.uniform(-0.05, 0.05), 6)
        map_ready.append(rec)

    # 對完全重疊座標做圓形排列（spiderfly 靜態預計算）
    from collections import defaultdict
    _coord_groups: dict[tuple[float, float], list[int]] = defaultdict(list)
    for _i, _rec in enumerate(map_ready):
        _coord_groups[(_rec["lat"], _rec["lng"])].append(_i)
    _SPIRAL_FOOT_M = 28.0  # 每個標記間距（公尺），對應 Leaflet 預設值
    for (_lat0, _lng0), _idxs in _coord_groups.items():
        _n = len(_idxs)
        if _n < 2:
            continue
        _radius_m = max(15.0, _n * _SPIRAL_FOOT_M / (2 * math.pi))
        _lat_per_m = 1.0 / 111111.0
        _lng_per_m = 1.0 / (111111.0 * math.cos(math.radians(_lat0)))
        for _j, _idx in enumerate(_idxs):
            _angle = 2 * math.pi * _j / _n
            map_ready[_idx]["lat"] = round(_lat0 + _radius_m * _lat_per_m * math.cos(_angle), 6)
            map_ready[_idx]["lng"] = round(_lng0 + _radius_m * _lng_per_m * math.sin(_angle), 6)

    with open(public_path, "w", encoding="utf-8") as f:
        json.dump({"_meta": {**meta, "map_ready": len(map_ready)}, "persons": map_ready},
                  f, ensure_ascii=False)  # 不縮排，節省檔案大小

    no_coord_path = REPO / "public" / "data" / "nhrm_no_coord.json"
    with open(no_coord_path, "w", encoding="utf-8") as f:
        json.dump(pending_no_coord, f, ensure_ascii=False)

    print(f"\n完成 → {output_path}", file=sys.stderr)
    print(f"       → {public_path} ({len(map_ready)} 筆)", file=sys.stderr)
    print(f"  有座標：{stats['with_coords']} 筆", file=sys.stderr)
    print(f"    來源 twtjdb：{stats['source_twtjdb']}", file=sys.stderr)
    print(f"    來源 NHRM city：{stats['source_nhrm_city']}", file=sys.stderr)
    print(f"    來源 NHRM place：{stats['source_nhrm_place']}", file=sys.stderr)
    print(f"    來源 introduction：{stats['source_nhrm_intro']}", file=sys.stderr)
    print(f"    來源 native：{stats['source_native']}", file=sys.stderr)
    print(f"    來源 LLM (Gemini)：{stats['source_llm']}", file=sys.stderr)
    print(f"  無座標：{stats['no_coords']} 筆", file=sys.stderr)
    print(f"  有 twtjdb 對應：{stats['has_twtjdb_match']} 筆", file=sys.stderr)
    print(f"  無 twtjdb 對應：{stats['no_twtjdb_match']} 筆", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nhrm",
        default=str(REPO / "data/raw/nhrm_all.jsonl"),
        help="NHRM 爬蟲輸出 JSONL（預設：data/raw/nhrm_all.jsonl）",
    )
    parser.add_argument(
        "--out",
        default=str(REPO / "data/processed/nhrm_merged.json"),
        help="輸出 JSON（預設：data/processed/nhrm_merged.json）",
    )
    args = parser.parse_args()
    main(Path(args.nhrm), Path(args.out))
