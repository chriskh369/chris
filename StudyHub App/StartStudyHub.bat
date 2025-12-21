@echo off
cd /d "c:\Users\Chris\OneDrive\מסמכים\GitHub\chris"
start http://localhost:8080/index.html
python -m http.server 8080
