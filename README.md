

# hướng dẫn run source

1. cài đặt các thư viện trong requirements.txt
pip install -r requirements.txt

2. Cài đặt môi trường ảo và kích hoạt nó
py -m venv .venv
.venv\Scripts\activate

3. Tạo 2 Terminal (Lưu ý : cả hai đều phải cài môi trường .venv)
Chạy api: 
- cd API
- pip install -r requirements.txt
- uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4

Chạy gui:
- cd src
- streamlit run gui.py

