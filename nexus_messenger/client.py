import socket
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import sys

import config

class NexusClient:
    def __init__(self, on_message, on_system, on_userlist,
                 on_connect, on_disconnect, on_error, on_private):
        self.on_message = on_message
        self.on_system = on_system
        self.on_userlist = on_userlist
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error
        self.on_private = on_private

        self.sock = None
        self.username = None
        self.connected = False

    def connect(self, username):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((config.HOST, config.PORT))
        self.sock.settimeout(None)
        self.username = username

        self._send({"type": "join", "username": username})

        line = self._recv_line()
        if not line:
            raise ConnectionError("Нет ответа от сервера")

        data = json.loads(line)

        if data.get("type") == "error":
            raise ConnectionError(data.get("message", "Ошибка сервера"))

        if data.get("type") != "welcome":
            raise ConnectionError("Неверный ответ сервера")

        self.connected = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        self.on_connect(data)

    def _recv_line(self):
        buf = b""
        while True:
            chunk = self.sock.recv(1)
            if not chunk:
                return None
            if chunk == b"\n":
                return buf.decode("utf-8", errors="replace")
            buf += chunk

    def _recv_loop(self):
        while self.connected:
            try:
                line = self._recv_line()
                if not line:
                    break
                pkt = json.loads(line)
                self._dispatch(pkt)
            except Exception:
                break
        self.connected = False
        self.on_disconnect()

    def _dispatch(self, pkt):
        t = pkt.get("type")
        if t == "message":
            self.on_message(pkt)
        elif t == "system":
            self.on_system(pkt)
        elif t == "userlist":
            self.on_userlist(pkt.get("users", []))
        elif t == "private":
            self.on_private(pkt)

    def _send(self, data):
        try:
            msg = json.dumps(data, ensure_ascii=False) + "\n"
            self.sock.sendall(msg.encode("utf-8"))
        except Exception:
            pass

    def send_message(self, text):
        self._send({"type": "message", "text": text})

    def send_private(self, to, text):
        self._send({"type": "private", "to": to, "text": text})

    def disconnect(self):
        self.connected = False
        try:
            self.sock.close()
        except Exception:
            pass

class LoginWindow:
    def __init__(self, parent, on_login):
        self.on_login = on_login
        self.win = tk.Toplevel(parent)
        self.win.title("Nexus — Вход")
        self.win.geometry("380x260")
        self.win.configure(bg=config.BG_DARK)
        self.win.resizable(False, False)
        self.win.grab_set()
        self._build()

    def _build(self):
        tk.Label(
            self.win, text="⚡ NEXUS",
            bg=config.BG_DARK, fg=config.ACCENT,
            font=("Consolas", 28, "bold")
        ).pack(pady=(25, 0))

        tk.Label(
            self.win, text="Messenger v0.1",
            bg=config.BG_DARK, fg=config.TEXT_MUTED,
            font=("Consolas", 10)
        ).pack()

        tk.Label(
            self.win, text="Имя пользователя:",
            bg=config.BG_DARK, fg=config.TEXT_SECONDARY,
            font=("Consolas", 10)
        ).pack(pady=(20, 4))

        self.name_var = tk.StringVar()
        entry = tk.Entry(
            self.win,
            textvariable=self.name_var,
            bg=config.INPUT_BG, fg=config.TEXT_PRIMARY,
            insertbackground=config.TEXT_PRIMARY,
            font=("Consolas", 12),
            relief=tk.FLAT,
            width=24,
            bd=6
        )
        entry.pack()
        entry.focus()
        entry.bind("<Return>", lambda e: self._do_login())

        self.err_lbl = tk.Label(
            self.win, text="",
            bg=config.BG_DARK, fg=config.OFFLINE_RED,
            font=("Consolas", 9)
        )
        self.err_lbl.pack(pady=4)

        tk.Button(
            self.win, text="ВОЙТИ →",
            bg=config.ACCENT, fg="white",
            font=("Consolas", 11, "bold"),
            relief=tk.FLAT, padx=20, pady=8,
            activebackground=config.ACCENT_HOVER,
            command=self._do_login
        ).pack(pady=8)

    def _do_login(self):
        name = self.name_var.get().strip()
        if not name:
            self.err_lbl.config(text="Введите имя пользователя")
            return
        if len(name) < 2:
            self.err_lbl.config(text="Минимум 2 символа")
            return
        if len(name) > 20:
            self.err_lbl.config(text="Максимум 20 символов")
            return
        if " " in name:
            self.err_lbl.config(text="Пробелы не допускаются")
            return
        self.win.destroy()
        self.on_login(name)

    def show_error(self, msg):
        self.err_lbl.config(text=msg)

class ChatWindow:
    def __init__(self, root, username, client):
        self.root = root
        self.username = username
        self.client = client
        self.private_target = None
        self.message_count = 0

        self.root.title(f"Nexus Messenger — {username}")
        self.root.geometry("900x620")
        self.root.configure(bg=config.BG_DARK)
        self.root.minsize(700, 450)

        self._build_ui()
        self._sys_msg(f"✅ Подключён как {username}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=config.BG_LIGHT, pady=8)
        hdr.pack(fill=tk.X)

        tk.Label(
            hdr, text="⚡ NEXUS",
            bg=config.BG_LIGHT, fg=config.ACCENT,
            font=("Consolas", 15, "bold")
        ).pack(side=tk.LEFT, padx=15)

        self.conn_dot = tk.Label(
            hdr, text="●",
            bg=config.BG_LIGHT, fg=config.ONLINE_GREEN,
            font=("Consolas", 12)
        )
        self.conn_dot.pack(side=tk.LEFT)

        self.conn_lbl = tk.Label(
            hdr, text=" В сети",
            bg=config.BG_LIGHT, fg=config.TEXT_SECONDARY,
            font=("Consolas", 10)
        )
        self.conn_lbl.pack(side=tk.LEFT)

        self.mode_lbl = tk.Label(
            hdr, text="[ ОБЩИЙ ЧАТ ]",
            bg=config.BG_LIGHT, fg=config.TEXT_MUTED,
            font=("Consolas", 9)
        )
        self.mode_lbl.pack(side=tk.LEFT, padx=20)

        tk.Label(
            hdr, text=f"👤 {self.username}",
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 10)
        ).pack(side=tk.RIGHT, padx=15)

        main = tk.Frame(self.root, bg=config.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)

        users_frame = tk.Frame(main, bg=config.BG_MEDIUM, width=180)
        users_frame.pack(side=tk.RIGHT, fill=tk.Y)
        users_frame.pack_propagate(False)

        tk.Label(
            users_frame, text="УЧАСТНИКИ",
            bg=config.BG_MEDIUM, fg=config.TEXT_MUTED,
            font=("Consolas", 9, "bold")
        ).pack(pady=(10, 4))

        self.users_list = tk.Listbox(
            users_frame,
            bg=config.BG_MEDIUM, fg=config.TEXT_PRIMARY,
            selectbackground=config.ACCENT,
            selectforeground="white",
            font=("Consolas", 10),
            relief=tk.FLAT,
            border=0,
            activestyle="none"
        )
        self.users_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.users_list.bind("<Double-Button-1>", self._on_user_click)

        tk.Label(
            users_frame,
            text="2×ЛКМ — личное сообщение",
            bg=config.BG_MEDIUM, fg=config.TEXT_MUTED,
            font=("Consolas", 7),
            wraplength=160
        ).pack(pady=(0, 8), padx=5)

        chat_frame = tk.Frame(main, bg=config.BG_DARK)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_box = tk.Text(
            chat_frame,
            bg=config.BG_DARK, fg=config.TEXT_PRIMARY,
            font=("Consolas", 11),
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD,
            padx=10, pady=8,
            cursor="arrow"
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)

        self.chat_box.tag_configure(
            "own_name", foreground=config.ACCENT,
            font=("Consolas", 11, "bold")
        )
        self.chat_box.tag_configure(
            "other_name", foreground="#64b5f6",
            font=("Consolas", 11, "bold")
        )
        self.chat_box.tag_configure(
            "system", foreground="#9c88ff",
            font=("Consolas", 10, "italic")
        )
        self.chat_box.tag_configure(
            "time", foreground=config.TEXT_MUTED,
            font=("Consolas", 9)
        )
        self.chat_box.tag_configure(
            "msg_own", foreground=config.TEXT_PRIMARY,
            font=("Consolas", 11)
        )
        self.chat_box.tag_configure(
            "msg_other", foreground=config.TEXT_PRIMARY,
            font=("Consolas", 11)
        )
        self.chat_box.tag_configure(
            "private_label", foreground="#ffd700",
            font=("Consolas", 10, "bold")
        )
        self.chat_box.tag_configure(
            "private_msg", foreground="#ffd700",
            font=("Consolas", 11)
        )

        sb = tk.Scrollbar(
            chat_frame, command=self.chat_box.yview,
            bg=config.SCROLLBAR_BG
        )
        self.chat_box.configure(yscrollcommand=sb.set)

        input_frame = tk.Frame(self.root, bg=config.BG_MEDIUM, pady=8)
        input_frame.pack(fill=tk.X, padx=10, pady=6)

        self.pm_indicator = tk.Label(
            input_frame, text="",
            bg=config.BG_MEDIUM, fg="#ffd700",
            font=("Consolas", 9)
        )
        self.pm_indicator.pack(anchor=tk.W, padx=5)

        inp_row = tk.Frame(input_frame, bg=config.BG_MEDIUM)
        inp_row.pack(fill=tk.X)

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            inp_row,
            textvariable=self.input_var,
            bg=config.INPUT_BG, fg=config.TEXT_PRIMARY,
            insertbackground=config.TEXT_PRIMARY,
            font=("Consolas", 12),
            relief=tk.FLAT,
            bd=8
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 8))
        self.input_entry.bind("<Return>", lambda e: self._send())
        self.input_entry.bind("<Escape>", lambda e: self._cancel_pm())
        self.input_entry.focus()

        tk.Button(
            inp_row, text="ОТПРАВИТЬ",
            bg=config.ACCENT, fg="white",
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT, padx=14, pady=6,
            activebackground=config.ACCENT_HOVER,
            command=self._send
        ).pack(side=tk.LEFT, padx=(0, 5))

        status = tk.Frame(self.root, bg=config.BG_LIGHT, pady=3)
        status.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Готов")
        tk.Label(
            status, textvariable=self.status_var,
            bg=config.BG_LIGHT, fg=config.TEXT_MUTED,
            font=("Consolas", 8)
        ).pack(side=tk.LEFT, padx=10)

        self.online_count = tk.Label(
            status, text="0 онлайн",
            bg=config.BG_LIGHT, fg=config.ONLINE_GREEN,
            font=("Consolas", 8)
        )
        self.online_count.pack(side=tk.RIGHT, padx=10)

    def add_message(self, pkt):
        uname = pkt.get("username", "?")
        text = pkt.get("text", "")
        ts = pkt.get("time", "")
        is_own = (uname == self.username)

        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, "\n")

        if is_own:
            self.chat_box.insert(tk.END, f"  {uname}", "own_name")
        else:
            self.chat_box.insert(tk.END, f"  {uname}", "other_name")

        self.chat_box.insert(tk.END, f"  {ts}\n", "time")

        if is_own:
            self.chat_box.insert(tk.END, f"  {text}\n", "msg_own")
        else:
            self.chat_box.insert(tk.END, f"  {text}\n", "msg_other")

        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)
        self.message_count += 1
        self.status_var.set(f"Сообщений получено: {self.message_count}")

    def add_private(self, pkt):
        frm = pkt.get("from", "?")
        to = pkt.get("to", "?")
        text = pkt.get("text", "")
        ts = pkt.get("time", "")

        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, "\n")

        direction = f"ЛС от {frm}" if frm != self.username else f"ЛС → {to}"
        self.chat_box.insert(
            tk.END, f"  🔒 {direction}  {ts}\n", "private_label"
        )
        self.chat_box.insert(tk.END, f"  {text}\n", "private_msg")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def _sys_msg(self, text):
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"\n  ─── {text} ───\n", "system")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def update_users(self, users):
        self.users_list.delete(0, tk.END)
        for u in sorted(users):
            prefix = "★ " if u == self.username else "  "
            self.users_list.insert(tk.END, f"{prefix}{u}")
        self.online_count.config(text=f"{len(users)} онлайн")

    def _send(self):
        text = self.input_var.get().strip()
        if not text:
            return
        if len(text) > 500:
            self.status_var.set("Слишком длинное сообщение (макс. 500)")
            return

        if self.private_target:
            self.client.send_private(self.private_target, text)
        else:
            self.client.send_message(text)

        self.input_var.set("")

    def _on_user_click(self, event):
        sel = self.users_list.curselection()
        if not sel:
            return
        item = self.users_list.get(sel[0]).strip().lstrip("★").strip()
        if item == self.username:
            return
        self.private_target = item
        self.pm_indicator.config(
            text=f"🔒 Личное сообщение → {item}  (ESC — отмена)"
        )
        self.mode_lbl.config(
            text=f"[ ЛС → {item} ]", fg="#ffd700"
        )
        self.input_entry.focus()

    def _cancel_pm(self):
        self.private_target = None
        self.pm_indicator.config(text="")
        self.mode_lbl.config(
            text="[ ОБЩИЙ ЧАТ ]", fg=config.TEXT_MUTED
        )

    def set_disconnected(self):
        self.conn_dot.config(fg=config.OFFLINE_RED)
        self.conn_lbl.config(text=" Отключён")
        self.status_var.set("Соединение потеряно")
        self.input_entry.config(state=tk.DISABLED)

    def _on_close(self):
        self.client.disconnect()
        self.root.destroy()

class NexusApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.client = None
        self.chat_win = None
        self._show_login()
        self.root.mainloop()

    def _show_login(self):
        login = LoginWindow(self.root, self._on_login)
        self.root.wait_window(login.win)

    def _on_login(self, username):
        self.client = NexusClient(
            on_message=self._on_message,
            on_system=self._on_system,
            on_userlist=self._on_userlist,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
            on_error=self._on_error,
            on_private=self._on_private
        )

        try:
            self.client.connect(username)
        except Exception as e:
            messagebox.showerror(
                "Ошибка подключения",
                f"Не удалось подключиться к серверу:\n{e}\n\n"
                f"Убедитесь, что сервер запущен ({config.HOST}:{config.PORT})"
            )
            self._show_login()

    def _on_connect(self, data):
        def _do():
            self.root.deiconify()
            self.chat_win = ChatWindow(self.root, self.client.username, self.client)
            users = data.get("users", [])
            self.chat_win.update_users(users)
        self.root.after(0, _do)

    def _on_message(self, pkt):
        if self.chat_win:
            self.root.after(0, lambda: self.chat_win.add_message(pkt))

    def _on_system(self, pkt):
        if self.chat_win:
            msg = pkt.get("message", "")
            self.root.after(0, lambda: self.chat_win._sys_msg(msg))

    def _on_userlist(self, users):
        if self.chat_win:
            self.root.after(0, lambda: self.chat_win.update_users(users))

    def _on_private(self, pkt):
        if self.chat_win:
            self.root.after(0, lambda: self.chat_win.add_private(pkt))

    def _on_disconnect(self):
        if self.chat_win:
            self.root.after(0, self.chat_win.set_disconnected)

    def _on_error(self, msg):
        self.root.after(0, lambda: messagebox.showerror("Ошибка", msg))

if __name__ == "__main__":
    NexusApp()
