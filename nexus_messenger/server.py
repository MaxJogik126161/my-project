import socket
import threading
import json
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

import config

class NexusServer:
    def __init__(self):
        self.clients       = {}
        self.usernames     = {}
        self.lock          = threading.Lock()
        self.server_socket = None
        self.running       = False
        self.message_count = 0
        self.start_time    = None

    def start(self, log_callback=None):
        self.log = log_callback or print
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        self.server_socket.bind((config.HOST, config.PORT))
        self.server_socket.listen(config.MAX_CLIENTS)
        self.running    = True
        self.start_time = datetime.now()
        self.log(
            f"[SERVER] Nexus Server запущен "
            f"на {config.HOST}:{config.PORT}"
        )
        threading.Thread(
            target=self._accept_loop, daemon=True
        ).start()

    def _accept_loop(self):
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _send_json(self, sock, data):
        try:
            msg = json.dumps(data, ensure_ascii=False) + "\n"
            sock.sendall(msg.encode("utf-8"))
            return True
        except OSError as e:
            if hasattr(e, "winerror") and e.winerror == 10054:
                return False
            return False
        except Exception:
            return False

    def _recv_line(self, sock):
        buf = b""
        while True:
            chunk = sock.recv(1)
            if not chunk:
                return None
            if chunk == b"\n":
                return buf.decode("utf-8", errors="replace")
            buf += chunk

    def _handle_client(self, conn, addr):
        username = None
        try:
            line = self._recv_line(conn)
            if not line:
                conn.close()
                return

            data = json.loads(line)
            if data.get("type") != "join":
                conn.close()
                return

            username = data.get("username", "").strip()

            with self.lock:
                if not username or username in self.usernames:
                    self._send_json(conn, {
                        "type":    "error",
                        "message": "Имя занято или недопустимо"
                    })
                    conn.close()
                    return

                self.clients[conn]       = username
                self.usernames[username] = conn
                user_list = list(self.usernames.keys())

            self._send_json(conn, {
                "type":     "welcome",
                "username": username,
                "users":    user_list,
                "message":  f"Добро пожаловать в Nexus, {username}!"
            })

            self._broadcast({
                "type":    "system",
                "message": f"🟢 {username} подключился к чату",
                "time":    self._now()
            }, exclude=conn)

            self._broadcast_user_list()
            self.log(f"[+] {username} подключился с {addr[0]}")

            while self.running:
                line = self._recv_line(conn)
                if not line:
                    break
                try:
                    pkt = json.loads(line)
                    self._process_packet(pkt, conn, username)
                except json.JSONDecodeError:
                    pass

        except OSError as e:
            if hasattr(e, "winerror") and e.winerror == 10054:
                pass
            else:
                self.log(f"[!] Ошибка клиента {addr}: {e}")
        except Exception as e:
            self.log(f"[!] Ошибка клиента {addr}: {e}")
        finally:
            self._disconnect(conn, username)

    def _process_packet(self, pkt, conn, username):
        ptype = pkt.get("type")

        if ptype == "message":
            text = pkt.get("text", "").strip()
            if not text:
                return
            self.message_count += 1
            out = {
                "type":     "message",
                "username": username,
                "text":     text,
                "time":     self._now(),
                "id":       self.message_count
            }
            self._broadcast(out)
            self.log(f"[MSG] {username}: {text[:60]}")

        elif ptype == "private":
            target = pkt.get("to")
            text   = pkt.get("text", "").strip()
            with self.lock:
                target_sock = self.usernames.get(target)
            if target_sock and text:
                pm = {
                    "type": "private",
                    "from": username,
                    "to":   target,
                    "text": text,
                    "time": self._now()
                }
                self._send_json(target_sock, pm)
                self._send_json(conn, pm)

        elif ptype == "typing":
            self._broadcast({
                "type":     "typing",
                "username": username,
                "is_typing": pkt.get("is_typing", False)
            }, exclude=conn)

        elif ptype == "ping":
            self._send_json(conn, {"type": "pong"})

    def _broadcast(self, data, exclude=None):
        with self.lock:
            targets = list(self.clients.keys())
        dead = []
        for sock in targets:
            if sock is exclude:
                continue
            if not self._send_json(sock, data):
                dead.append(sock)
        for sock in dead:
            self._disconnect(sock, self.clients.get(sock))

    def _broadcast_user_list(self):
        with self.lock:
            users = list(self.usernames.keys())
        self._broadcast({"type": "userlist", "users": users})

    def _disconnect(self, conn, username):
        with self.lock:
            if conn in self.clients:
                del self.clients[conn]
            if username and username in self.usernames:
                del self.usernames[username]
        try:
            conn.close()
        except Exception:
            pass

        if username:
            self._broadcast({
                "type":    "system",
                "message": f"🔴 {username} покинул чат",
                "time":    self._now()
            })
            self._broadcast_user_list()
            self.log(f"[-] {username} отключился")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    def _now(self):
        return datetime.now().strftime("%H:%M:%S")

    def get_stats(self):
        uptime = ""
        if self.start_time:
            delta = datetime.now() - self.start_time
            h = int(delta.total_seconds() // 3600)
            m = int((delta.total_seconds() % 3600) // 60)
            s = int(delta.total_seconds() % 60)
            uptime = f"{h:02d}:{m:02d}:{s:02d}"
        return {
            "clients":  len(self.clients),
            "messages": self.message_count,
            "uptime":   uptime
        }

class ServerGUI:
    def __init__(self):
        self.server = NexusServer()
        self.root   = tk.Tk()
        self.root.title("Nexus Server — Control Panel")
        self.root.geometry("700x500")
        self.root.configure(bg=config.BG_DARK)
        self.root.resizable(True, True)
        self._build_ui()
        self._auto_start()
        self._update_stats()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=config.BG_LIGHT, pady=10)
        hdr.pack(fill=tk.X)

        tk.Label(
            hdr, text="⚡ NEXUS SERVER",
            bg=config.BG_LIGHT, fg=config.ACCENT,
            font=("Consolas", 18, "bold")
        ).pack(side=tk.LEFT, padx=20)

        self.status_lbl = tk.Label(
            hdr, text="● ОСТАНОВЛЕН",
            bg=config.BG_LIGHT, fg=config.OFFLINE_RED,
            font=("Consolas", 11, "bold")
        )
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

        stats_frame = tk.Frame(
            self.root, bg=config.BG_MEDIUM, pady=8
        )
        stats_frame.pack(fill=tk.X)

        self.stat_clients  = self._stat_box(
            stats_frame, "КЛИЕНТОВ", "0"
        )
        self.stat_messages = self._stat_box(
            stats_frame, "СООБЩЕНИЙ", "0"
        )
        self.stat_uptime   = self._stat_box(
            stats_frame, "АПТАЙМ", "00:00:00"
        )

        log_frame = tk.Frame(self.root, bg=config.BG_DARK)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(
            log_frame, text="[ SERVER LOG ]",
            bg=config.BG_DARK, fg=config.TEXT_SECONDARY,
            font=("Consolas", 9)
        ).pack(anchor=tk.W)

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            bg=config.INPUT_BG, fg=config.ONLINE_GREEN,
            font=("Consolas", 10),
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.log_box.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(
            self.root, bg=config.BG_DARK, pady=8
        )
        btn_frame.pack(fill=tk.X, padx=10)

        self.start_btn = tk.Button(
            btn_frame, text="▶ ЗАПУСТИТЬ",
            bg=config.ONLINE_GREEN, fg="white",
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT, padx=15, pady=6,
            command=self._start_server
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            btn_frame, text="■ ОСТАНОВИТЬ",
            bg=config.OFFLINE_RED, fg="white",
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT, padx=15, pady=6,
            state=tk.DISABLED,
            command=self._stop_server
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="🗑 ОЧИСТИТЬ ЛОГ",
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 10),
            relief=tk.FLAT, padx=15, pady=6,
            command=self._clear_log
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            btn_frame,
            text=f"{config.HOST}:{config.PORT}",
            bg=config.BG_DARK, fg=config.TEXT_MUTED,
            font=("Consolas", 9)
        ).pack(side=tk.RIGHT, padx=10)

    def _stat_box(self, parent, label, value):
        frame = tk.Frame(
            parent, bg=config.BG_LIGHT, padx=20, pady=5
        )
        frame.pack(side=tk.LEFT, padx=10, pady=5, ipadx=10)
        tk.Label(
            frame, text=label,
            bg=config.BG_LIGHT, fg=config.TEXT_SECONDARY,
            font=("Consolas", 8)
        ).pack()
        lbl = tk.Label(
            frame, text=value,
            bg=config.BG_LIGHT, fg=config.ACCENT,
            font=("Consolas", 16, "bold")
        )
        lbl.pack()
        return lbl

    def _auto_start(self):
        self._start_server()

    def _start_server(self):
        try:
            self.server.start(log_callback=self._log)
            self.status_lbl.config(
                text="● РАБОТАЕТ", fg=config.ONLINE_GREEN
            )
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        except Exception as e:
            self._log(f"[ERROR] Не удалось запустить: {e}")

    def _stop_server(self):
        self.server.stop()
        self.status_lbl.config(
            text="● ОСТАНОВЛЕН", fg=config.OFFLINE_RED
        )
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._log("[SERVER] Сервер остановлен")

    def _log(self, text):
        def _do():
            self.log_box.config(state=tk.NORMAL)
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_box.insert(tk.END, f"[{ts}] {text}\n")
            self.log_box.see(tk.END)
            self.log_box.config(state=tk.DISABLED)
        self.root.after(0, _do)

    def _clear_log(self):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state=tk.DISABLED)

    def _update_stats(self):
        stats = self.server.get_stats()
        self.stat_clients.config(text=str(stats["clients"]))
        self.stat_messages.config(text=str(stats["messages"]))
        self.stat_uptime.config(
            text=stats["uptime"] or "00:00:00"
        )
        self.root.after(1000, self._update_stats)

    def _on_close(self):
        self.server.stop()
        self.root.destroy()

if __name__ == "__main__":
    ServerGUI()
