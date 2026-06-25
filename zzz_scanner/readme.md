pyinstaller --noconfirm --name GenshinArtifactScanner --console --uac-admin --collect-all rapidocr_onnxruntime --collect-all onnxruntime --collect-data customtkinter main.py

for onedir build

pyinstaller --noconfirm --name GenshinArtifactScanner --console --uac-admin --onefile --collect-all rapidocr_onnxruntime --collect-all onnxruntime --collect-data customtkinter main.py

for one single exe file