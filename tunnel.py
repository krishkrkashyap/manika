import subprocess
import re
import time

# Start the SSH tunnel in background
proc = subprocess.Popen(
    ['ssh', '-o', 'StrictHostKeyChecking=no', '-R', '80:localhost:8503', 'serveo.net'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print("Creating tunnel...")
url = None
for line in proc.stdout:
    print(line, end='')
    match = re.search(r'https://[a-zA-Z0-9.-]+serveousercontent\.com', line)
    if match:
        url = match.group(0)
        print(f"\n{'='*50}")
        print(f"YOUR PUBLIC URL:")
        print(f"{url}")
        print(f"{'='*50}")
        break

if url:
    print("\nShare this URL with your client!")
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTunnel closed.")
