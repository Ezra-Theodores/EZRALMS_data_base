@echo off
C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe test_search.py > test_output.txt 2>&1
echo Done. Checking output...
type test_output.txt
