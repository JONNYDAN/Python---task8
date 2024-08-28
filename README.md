

# hướng dẫn run source

1. Cài đặt môi trường ảo và kích hoạt nó
py -m venv .venv
.venv\Scripts\activate

2. cài đặt các thư viện trong requirements.txt
pip install -r requirements.txt


3. Tạo 1 Terminal để chạy API (Lưu ý : active .venv ở terminal này)
- cd API
- uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
- API sẽ run ở port 8000


4. Tạo 1 Terminal để chạy GUI (Lưu ý : active .venv ở terminal này)
- cd UI
- streamlit run gui.py
- UI sẽ run ở port 8501


# MULTIPROCESS
Trong code này a sử dụng multi process bằng uvicorn, e có thể tăng hoặc giảm số process bằng cách update số worker tương ứng, hiện tại a để --workers 4 nghĩa là 4 process

