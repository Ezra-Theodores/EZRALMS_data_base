@echo off
echo Starting test at %time%
C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe -c "from sentence_transformers import SentenceTransformer; import numpy as np; import time; print('Loading...'); model = SentenceTransformer('all-MiniLM-L6-v2'); print('Model ready'); print('Encoding...'); start = time.time(); emb = model.encode('test'); print(f'Done in {time.time()-start:.2f}s, len={len(emb)}'); print('OK')"
echo Finished at %time%
pause
