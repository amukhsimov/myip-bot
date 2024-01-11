import requests
import time
from dotenv import load_dotenv
import os
import re

current_ip = None


def send_ip():
    base_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}"

    # send message
    tg_msg = {
        "chat_id": os.getenv('TELEGRAM_CHAT_ID'),
        "text": f"🐳 Привет 👋\nТекущий IP адрес: *{current_ip}*",
        "parse_mode": "Markdown",
    }
    response = requests.post(f"{base_url}/sendMessage", json=tg_msg, timeout=5)
    if response.status_code != 200:
        raise RuntimeError(f"Error while posting a message: {response.text}")

    # send file
    response = requests.post(f"{base_url}/sendDocument",
                             data={"chat_id": os.getenv('TELEGRAM_CHAT_ID')},
                             files={"document": open(os.getenv('OVPN_FILE'), 'rb')},
                             timeout=5)
    if response.status_code != 200:
        raise RuntimeError(f"Error while posting a document: {response.text}")


def ip_has_changed():
    with open(os.getenv('OVPN_FILE'), 'rt') as fp:
        text = fp.read()
    old_ip = text.split('\n')[0].split()[1]
    return old_ip != current_ip


def update_file():
    with open(os.getenv('OVPN_FILE'), 'rt') as fp:
        text = fp.read()
    lines = text.split('\n')
    line_0 = lines[0].split()
    line_0[1] = current_ip
    lines[0] = ' '.join(line_0)

    with open(os.getenv('OVPN_FILE'), 'wt') as fp:
        fp.write('\n'.join(lines))


def check():
    global current_ip

    load_dotenv(dotenv_path='./.env', override=True)

    new_ip = requests.get('https://ident.me').content.decode('utf-8')
    if not re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', new_ip):
        raise ValueError(f"Got invalid IP from ident.me: {new_ip}")

    current_ip = new_ip

    if ip_has_changed():
        update_file()
        send_ip()


def run():
    while True:
        try:
            check()
            time.sleep(int(os.getenv('SYNC_PERIOD_SECONDS')))
        except Exception as ex:
            print(f"Error: {ex}")


if __name__ == '__main__':
    run()
