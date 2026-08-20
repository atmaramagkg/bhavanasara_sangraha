import os, subprocess, re, time, sqlite3

img_dir = r'C:\Users\austr\png_hi'
out_file = r'C:\Users\austr\bss\assets\texts\ocr_full.txt'

# Collect all images in order
parts = []
for p in ['PART1', 'PART2']:
    imgs = []
    for f in os.listdir(img_dir):
        if f.startswith(p + '_') and f.endswith('.png'):
            num = int(f.replace(p+'_','').replace('.png',''))
            imgs.append((num, f))
    imgs.sort(key=lambda x: x[0])
    parts.extend(imgs)

print(f"Total images: {len(parts)}")
print(f"First: {parts[0][1]}, Last: {parts[-1][1]}")

# OCR all images
start = time.time()
with open(out_file, 'w', encoding='utf-8') as out:
    for i, (num, fname) in enumerate(parts):
        path = os.path.join(img_dir, fname)
        result = subprocess.run(
            ['tesseract', path, 'stdout', '-l', 'hin+san', '--psm', '6'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        text = result.stdout.strip()
        out.write(f"===PAGE {fname}===\n")
        out.write(text + '\n')
        
        if (i+1) % 50 == 0:
            elapsed = time.time() - start
            rate = (i+1) / elapsed
            eta = (len(parts) - i - 1) / rate
            print(f"  [{i+1}/{len(parts)}] {elapsed:.0f}s elapsed, {eta:.0f}s remaining")

elapsed = time.time() - start
print(f"\nOCR complete: {len(parts)} images in {elapsed:.0f}s ({elapsed/len(parts):.1f}s/image)")
print(f"Output: {out_file}")

# Count lines
with open(out_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
