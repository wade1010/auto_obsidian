import sys
print("Python:", sys.version)
print("Path:", sys.executable)

try:
    from PyQt5.QtWidgets import QApplication
    print("PyQt5: OK")
    import PyQt5
    print("PyQt5 path:", PyQt5.__file__)
except Exception as e:
    print("PyQt5 Error:", e)

try:
    from PyQt6.QtWidgets import QApplication
    print("PyQt6: OK")
except Exception as e:
    print("PyQt6 Error:", e)
