import socket

urls = [
    "vvqbtimkusvbujuocgbg.supabase.co",
    "pbbaowiskhztxzzzflyc.supabase.co",
    "toknroutertybot.tybotflow.com"
]

print("--- DNS DIAGNOSTICS ---")
for url in urls:
    try:
        ip = socket.gethostbyname(url)
        print(f"SUCCESS: {url} -> {ip}")
    except socket.gaierror as e:
        print(f"FAILURE: {url} -> FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {url} -> {e}")
