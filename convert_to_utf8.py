import os
import chardet

folder = "./Structured_Data"   # your source folder

for file in os.listdir(folder):
    if file.endswith(".txt"):
        path = os.path.join(folder, file)
        
        # Detect encoding
        with open(path, "rb") as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            enc = detected["encoding"]

        print(f"Converting {file} (detected: {enc}) → UTF-8")

        # Read using detected encoding
        try:
            text = raw_data.decode(enc)
        except Exception:
            print(f"⚠️ Failed with {enc}, using cp1252 fallback")
            text = raw_data.decode("cp1252", errors="ignore")

        # Write back as UTF-8
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

print("\n🎉 All files converted to clean UTF-8 successfully!")
