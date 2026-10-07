import jieba
import json
import re

# 1. 讀取 JSON 字典
with open('database.json', 'r', encoding='utf-8') as f:
    knowledge_base = json.load(f)

# 強制讓 jieba 認得我們的數學關鍵字
for keyword in knowledge_base.keys():
    jieba.add_word(keyword)

# 2. 定義數學符號規則庫
symbol_patterns = {
    # 1. 三角函數
    r"sin|cos|tan": {"concept": "三角函數", "chapter": "高二上 第1章：三角"},
    
    # 2. 對數運算
    r"log|ln": {"concept": "對數運算", "chapter": "高二上 第2章：指數與對數"},
    
    # 3. 多項式
    r"x\^2|x\*\*2": {"concept": "二次方程式/多項式", "chapter": "高一上 第3章：多項式"},
    
    # 4. 排列組合
    r"C\(\d+,\s*\d+\)|P\(\d+,\s*\d+\)": {"concept": "排列組合", "chapter": "高一下 第2章：排列組合"},
    
    # 5. 極限
    r"lim": {"concept": "數列的極限", "chapter": "高三 微積分"},
    
    # 6. 矩陣基本表示法與乘法 (已將純中括號與 A=, Av 亂碼合併)
    r"\[\s*\d+,\s*\d+\s*\]|A[v]|A\s*=": {"concept": "矩陣與方陣乘法", "chapter": "高二下 第2章：矩陣"},
    
    # 7. 函數基本概念
    r"f\(x\)|g\(x\)": {"concept": "函數的基本概念與運算", "chapter": "高一上 第2章：多項式函數"},
    
    # 8. 高斯符號 (✨ 已將正常版 [a]<=a 與 PDF 亂碼變形版 []a 合併)
    r"\[[a-zA-Z]\]\s*<|\[[a-zA-Z]\]\s*≤|\[\][a-zA-Z]": {"concept": "高斯符號 (最大整數函數)", "chapter": "高一上 第1章：數與式"},
    
    # 9. 直線方程式
    r"[xy]\s*=\s*-?\d+": {"concept": "直線方程式", "chapter": "高一上 第2章：直線與圓"},
    
    # 10. 平面坐標與距離 (✨ 已將正常版 A(2,-2) 與 PDF 變形版 (2,-2)A 合併)
    r"[A-Z]\(\s*-?\d+\s*,\s*-?\d+\s*\)|\(\s*-?\d+\s*,\s*-?\d+\s*\)[A-Za-z]*": {"concept": "平面坐標系與距離公式", "chapter": "高一上 第2章：直線與圓"},
    
    # 11. 不等式特殊字元 ( 和 )
    r"[]": {"concept": "不等式運算", "chapter": "高一上 第1章：數與式"},
    
    # 12. 三角形特殊字元 ()
    r"": {"concept": "三角形的幾何性質", "chapter": "國中幾何 / 高二上 三角"}
}

# 👑 新增：將整份文本切分成一題一題的函式
def split_questions(text):
    # 這個 Regex 尋找像是 "1.", "2、", "(3)", "12." 這類的題號開頭
    # \n? 代表前面可能有一個換行
    # (?=\n?\d+[\.、]|\(\d+\)) 是一個 Lookahead，用來找到下一個題號的位置來作為切割點
    
# 👑 升級版：精準匹配題號，排除選項
    # 規則解析：
    # (?:\n|^) : 確保題號必須出現在一行的開頭 (前面是換行或是文本開頭)
    # (\d+\.)  : 題號必須是「數字加上小數點」(例如 1. , 12.)，不抓頓號、不抓括號
    # \s+      : 題號後面必須接著至少一個空白字元 (空格或 Tab)，避免抓到 3.14 這種小數
    pattern = r'(?:\n|^)(\d+\.)\s+'
    
    # 用題號切割文章
    parts = re.split(pattern, text)
    
    questions = []
    # 如果切割出來只有一段，代表找不到題號，就整段當一題
    if len(parts) == 1:
        return [{"number": "Q", "text": parts[0].strip()}]
        
    # parts 的結構會變成：['前面的廢話', '1.', '題目內容', '2.', '題目內容'...]
    # 如果第一個元素沒有字，代表文章一開頭就是題號
    start_idx = 1 if parts[0].strip() == '' else 0
    
    for i in range(1, len(parts), 2):
        q_num = parts[i].strip() # 抓出題號，例如 "1."
        q_text = parts[i+1].strip() # 抓出題目內容
        if q_text:
            questions.append({
                "number": q_num,
                "text": q_text
            })
            
    # 防呆：如果完全沒切成功，就整段回傳
    if not questions:
        return [{"number": "全文", "text": text}]
    
    return questions

def analyze_single_text(text):
    """分析單一題目的邏輯 (原本的 analyze_question)"""
    matched_results = []
    
    # 引擎 A：中文關鍵字
    words = jieba.lcut(text)
    for word in words:
        if word in knowledge_base:
            matched_results.append({
                "keyword": word,
                "concept": knowledge_base[word]["concept"],
                "chapter": knowledge_base[word]["chapter"]
            })
            
    # 引擎 B：符號掃描
    for pattern, info in symbol_patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            matched_results.append({
                "keyword": match.group(),
                "concept": info["concept"],
                "chapter": info["chapter"]
            })
            
    # 去重複
    unique_results = [dict(t) for t in {tuple(d.items()) for d in matched_results}]
    return unique_results

# 👑 升級版的分析入口
def analyze_document(full_text):
    # 1. 先把長文章切成一題一題
    questions_list = split_questions(full_text)
    
    final_output = []
    # 2. 針對每一題進行分析
    for q in questions_list:
        knowledge_points = analyze_single_text(q["text"])
        final_output.append({
            "question_number": q["number"],
            "question_text": q["text"],
            "knowledge_points": knowledge_points
        })
        
    return final_output