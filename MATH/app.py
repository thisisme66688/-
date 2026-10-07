from flask import Flask, request, jsonify, render_template
from app_core import analyze_document
import PyPDF2 # 新增：用來讀取 PDF 的套件

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    question_text = ""

    # 判斷使用者是否有上傳 PDF 檔案
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        try:
            # 使用 PyPDF2 讀取 PDF 內容
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                question_text += page.extract_text() + "\n\n"
        except Exception as e:
            return jsonify({"error": "PDF 讀取失敗，請確認檔案格式。"}), 400
    else:
        # 如果沒有上傳檔案，就抓取文字方塊裡的內容
        question_text = request.form.get('question', '')

    if not question_text.strip():
        return jsonify({"error": "沒有收到任何文字或 PDF 內容"}), 400

    # 丟給核心大腦分析 (不管是手貼的還是 PDF 抽出來的，都一樣處理)
    results = analyze_document(question_text)
    
    # 這次我們多回傳了 extracted_text，讓前端可以看到 PDF 抽出了什麼字
    return jsonify({
        "extracted_text": question_text,
        "results": results
    })

if __name__ == '__main__':
    app.run(debug=True)