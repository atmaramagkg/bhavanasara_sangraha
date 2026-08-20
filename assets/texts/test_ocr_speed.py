import os, time, subprocess

img_dir = r'C:\Users\austr\png_hi'
test_images = ['PART1_1.png', 'PART1_50.png', 'PART1_100.png', 'PART1_200.png', 'PART2_50.png', 'PART2_150.png', 'PART2_300.png']

for img_name in test_images:
    path = os.path.join(img_dir, img_name)
    if not os.path.exists(path):
        continue
    t0 = time.time()
    result = subprocess.run(
        ['tesseract', path, 'stdout', '-l', 'hin+san', '--psm', '6'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    elapsed = time.time() - t0
    lines = result.stdout.strip().split('\n')
    print(f"{img_name}: {elapsed:.1f}s, {len(lines)} lines")
    # Show first 3 lines
    for line in lines[:3]:
        print(f"  {line[:100]}")
    print()
