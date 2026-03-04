"""
Nymo Relay Server
Запускается на Railway. Соединяет двух клиентов через сервер.
"""

import socket
import threading
import os

PORT = int(os.environ.get("PORT", 5051))
rooms = {}  # room_id -> [conn1, conn2]
rooms_lock = threading.Lock()


def pipe(src, dst, label):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass


def handle_client(conn, addr):
    try:
        # Первое что клиент шлёт — room_id (64 байта, дополненные пробелами)
        room_id = b""
        while len(room_id) < 64:
            chunk = conn.recv(64 - len(room_id))
            if not chunk:
                conn.close()
                return
            room_id += chunk
        room_id = room_id.decode("utf-8").strip()

        print(f"[+] {addr} -> room '{room_id}'")

        with rooms_lock:
            if room_id not in rooms:
                rooms[room_id] = [conn]
                conn.sendall(b"WAIT    ")  # ждём второго
                print(f"    room '{room_id}' создана, ждём второго")
            else:
                waiting = rooms[room_id][0]
                del rooms[room_id]
                # Сообщаем обоим что соединение установлено
                waiting.sendall(b"CONNECT ")
                conn.sendall(b"CONNECT ")
                print(f"    room '{room_id}' — оба подключены, пайп запущен")
                # Запускаем двусторонний пайп
                t1 = threading.Thread(target=pipe, args=(waiting, conn, "A->B"), daemon=True)
                t2 = threading.Thread(target=pipe, args=(conn, waiting, "B->A"), daemon=True)
                t1.start()
                t2.start()

    except Exception as e:
        print(f"[-] Ошибка {addr}: {e}")
        try: conn.close()
        except: pass


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(10)
    print(f"Nymo Relay запущен на порту {PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
