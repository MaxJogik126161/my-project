import socket
import threading
import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime

import config

class ChatHistory:
    def __init__(self, username):
        self.username = username
        self.filepath = f"history_{username}.json"
        self.messages = []
        self._lock    = threading.Lock()
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            self.messages = []
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.messages = data.get("messages", [])
        except Exception:
            self.messages = []

    def _save(self):
        data = {
            "username": self.username,
            "saved":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total":    len(self.messages),
            "messages": self.messages
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_message(self, pkt):
        entry = {
            "type":     "message",
            "username": pkt.get("username", "?"),
            "text":     pkt.get("text", ""),
            "time":     pkt.get("time", ""),
            "date":     datetime.now().strftime("%Y-%m-%d")
        }
        with self._lock:
            self.messages.append(entry)
            self._save()

    def add_private(self, pkt):
        entry = {
            "type": "private",
            "from": pkt.get("from", "?"),
            "to":   pkt.get("to", "?"),
            "text": pkt.get("text", ""),
            "time": pkt.get("time", ""),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        with self._lock:
            self.messages.append(entry)
            self._save()

    def add_system(self, text):
        entry = {
            "type": "system",
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        with self._lock:
            self.messages.append(entry)
            self._save()

    def get_all(self):
        with self._lock:
            return list(self.messages)

    def get_count(self):
        with self._lock:
            return len(self.messages)

    def clear(self):
        with self._lock:
            self.messages = []
            self._save()

    def get_filepath(self):
        return os.path.abspath(self.filepath)

class HistoryWindow:
    def __init__(self, parent, history: ChatHistory, username: str):
        self.history  = history
        self.username = username

        self.win = tk.Toplevel(parent)
        self.win.title("📜 История чата — Nexus")
        self.win.geometry("680x520")
        self.win.configure(bg=config.BG_DARK)
        self.win.resizable(True, True)
        self.win.grab_set()

        self._build()
        self._load_messages()

    def _build(self):
        hdr = tk.Frame(self.win, bg=config.BG_LIGHT, pady=8)
        hdr.pack(fill=tk.X)

        tk.Label(
            hdr, text="📜 ИСТОРИЯ ЧАТА",
            bg=config.BG_LIGHT, fg=config.ACCENT,
            font=("Consolas", 13, "bold")
        ).pack(side=tk.LEFT, padx=15)

        self.count_lbl = tk.Label(
            hdr, text="",
            bg=config.BG_LIGHT, fg=config.TEXT_MUTED,
            font=("Consolas", 9)
        )
        self.count_lbl.pack(side=tk.RIGHT, padx=15)

        filter_frame = tk.Frame(
            self.win, bg=config.BG_MEDIUM, pady=6
        )
        filter_frame.pack(fill=tk.X, padx=8, pady=(6, 0))

        tk.Label(
            filter_frame, text="🔍",
            bg=config.BG_MEDIUM, fg=config.TEXT_MUTED,
            font=("Consolas", 11)
        ).pack(side=tk.LEFT, padx=(6, 2))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_filter)
        tk.Entry(
            filter_frame,
            textvariable=self.search_var,
            bg=config.INPUT_BG, fg=config.TEXT_PRIMARY,
            insertbackground=config.TEXT_PRIMARY,
            font=("Consolas", 11),
            relief=tk.FLAT, bd=4, width=22
        ).pack(side=tk.LEFT, padx=4)

        tk.Label(
            filter_frame, text="Тип:",
            bg=config.BG_MEDIUM, fg=config.TEXT_SECONDARY,
            font=("Consolas", 9)
        ).pack(side=tk.LEFT, padx=(12, 2))

        self.type_var = tk.StringVar(value="Все")
        opt = tk.OptionMenu(
            filter_frame, self.type_var,
            "Все", "Сообщения", "Личные", "Системные",
            command=lambda _: self._on_filter()
        )
        opt.config(
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 9), relief=tk.FLAT, bd=0,
            activebackground=config.ACCENT,
            highlightthickness=0
        )
        opt["menu"].config(
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 9)
        )
        opt.pack(side=tk.LEFT, padx=4)

        tk.Button(
            filter_frame, text="✕ Сброс",
            bg=config.BG_LIGHT, fg=config.TEXT_MUTED,
            font=("Consolas", 9),
            relief=tk.FLAT, padx=8,
            command=self._reset_filter
        ).pack(side=tk.LEFT, padx=4)

        text_frame = tk.Frame(self.win, bg=config.BG_DARK)
        text_frame.pack(
            fill=tk.BOTH, expand=True, padx=8, pady=6
        )

        self.text_box = tk.Text(
            text_frame,
            bg=config.BG_DARK, fg=config.TEXT_PRIMARY,
            font=("Consolas", 10),
            relief=tk.FLAT, state=tk.DISABLED,
            wrap=tk.WORD, padx=10, pady=6
        )
        self.text_box.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True
        )

        sb = tk.Scrollbar(
            text_frame,
            command=self.text_box.yview,
            bg=config.SCROLLBAR_BG
        )
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_box.configure(yscrollcommand=sb.set)

        self.text_box.tag_configure(
            "date_sep", foreground=config.TEXT_MUTED,
            font=("Consolas", 9, "italic"), justify="center"
        )
        self.text_box.tag_configure(
            "own_name", foreground=config.ACCENT,
            font=("Consolas", 10, "bold")
        )
        self.text_box.tag_configure(
            "other_name", foreground="#64b5f6",
            font=("Consolas", 10, "bold")
        )
        self.text_box.tag_configure(
            "system", foreground="#9c88ff",
            font=("Consolas", 9, "italic")
        )
        self.text_box.tag_configure(
            "time", foreground=config.TEXT_MUTED,
            font=("Consolas", 8)
        )
        self.text_box.tag_configure(
            "msg_text", foreground=config.TEXT_PRIMARY,
            font=("Consolas", 10)
        )
        self.text_box.tag_configure(
            "private_label", foreground="#ffd700",
            font=("Consolas", 9, "bold")
        )
        self.text_box.tag_configure(
            "private_text", foreground="#ffd700",
            font=("Consolas", 10)
        )
        self.text_box.tag_configure(
            "highlight", background="#2a3a1a",
            foreground="#b8ff80"
        )
        self.text_box.tag_configure(
            "empty", foreground=config.TEXT_MUTED,
            font=("Consolas", 11, "italic"), justify="center"
        )

        btn_frame = tk.Frame(
            self.win, bg=config.BG_DARK, pady=6
        )
        btn_frame.pack(fill=tk.X, padx=8)

        tk.Button(
            btn_frame, text="📂 Открыть файл",
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 9),
            relief=tk.FLAT, padx=10, pady=5,
            command=self._open_file
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_frame, text="💾 Экспорт в TXT",
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 9),
            relief=tk.FLAT, padx=10, pady=5,
            command=self._export_txt
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_frame, text="🗑 Очистить историю",
            bg=config.OFFLINE_RED, fg="white",
            font=("Consolas", 9),
            relief=tk.FLAT, padx=10, pady=5,
            command=self._clear_history
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_frame, text="✕ Закрыть",
            bg=config.BG_MEDIUM, fg=config.TEXT_MUTED,
            font=("Consolas", 9),
            relief=tk.FLAT, padx=10, pady=5,
            command=self.win.destroy
        ).pack(side=tk.RIGHT, padx=4)

        tk.Label(
            self.win,
            text=f"📁 {self.history.get_filepath()}",
            bg=config.BG_DARK, fg=config.TEXT_MUTED,
            font=("Consolas", 8), anchor=tk.W
        ).pack(fill=tk.X, padx=10, pady=(0, 4))

    def _load_messages(self, search="", msg_type="Все"):
        messages = self.history.get_all()
        filtered = []
        for m in messages:
            t = m.get("type", "")
            if msg_type == "Сообщения" and t != "message":
                continue
            if msg_type == "Личные"    and t != "private":
                continue
            if msg_type == "Системные" and t != "system":
                continue
            if search:
                text  = m.get("text", "").lower()
                uname = m.get(
                    "username", m.get("from", "")
                ).lower()
                if search.lower() not in text and \
                   search.lower() not in uname:
                    continue
            filtered.append(m)

        self._render(filtered, search)
        total = self.history.get_count()
        shown = len(filtered)
        self.count_lbl.config(
            text=f"Показано: {shown} / Всего: {total}"
        )

    def _render(self, messages, highlight=""):
        self.text_box.config(state=tk.NORMAL)
        self.text_box.delete("1.0", tk.END)

        if not messages:
            self.text_box.insert(
                tk.END,
                "\n\n    История пуста или ничего не найдено\n",
                "empty"
            )
            self.text_box.config(state=tk.DISABLED)
            return

        prev_date = None
        for m in messages:
            date  = m.get("date", "")
            time  = m.get("time", "")
            mtype = m.get("type", "message")

            if date and date != prev_date:
                self.text_box.insert(
                    tk.END,
                    f"\n  ── {date} ──────────────────────\n",
                    "date_sep"
                )
                prev_date = date

            if mtype == "message":
                uname = m.get("username", "?")
                text  = m.get("text", "")
                tag   = "own_name" \
                    if uname == self.username else "other_name"
                self.text_box.insert(
                    tk.END, f"  {uname}", tag
                )
                self.text_box.insert(
                    tk.END, f"  {time}\n", "time"
                )
                self._insert_highlighted(
                    f"  {text}\n", "msg_text", highlight
                )

            elif mtype == "private":
                frm  = m.get("from", "?")
                to   = m.get("to", "?")
                text = m.get("text", "")
                direction = f"ЛС от {frm}" \
                    if frm != self.username else f"ЛС → {to}"
                self.text_box.insert(
                    tk.END,
                    f"  🔒 {direction}  {time}\n",
                    "private_label"
                )
                self._insert_highlighted(
                    f"  {text}\n", "private_text", highlight
                )

            elif mtype == "system":
                text = m.get("text", "")
                self.text_box.insert(
                    tk.END,
                    f"  ─── {text} ───  {time}\n",
                    "system"
                )

        self.text_box.config(state=tk.DISABLED)
        self.text_box.see(tk.END)

    def _insert_highlighted(self, text, base_tag, keyword):
        if not keyword:
            self.text_box.insert(tk.END, text, base_tag)
            return
        lower_text = text.lower()
        lower_kw   = keyword.lower()
        start = 0
        while True:
            idx = lower_text.find(lower_kw, start)
            if idx == -1:
                self.text_box.insert(
                    tk.END, text[start:], base_tag
                )
                break
            self.text_box.insert(
                tk.END, text[start:idx], base_tag
            )
            self.text_box.insert(
                tk.END,
                text[idx:idx + len(keyword)],
                "highlight"
            )
            start = idx + len(keyword)

    def _on_filter(self, *args):
        self._load_messages(
            search   = self.search_var.get().strip(),
            msg_type = self.type_var.get()
        )

    def _reset_filter(self):
        self.search_var.set("")
        self.type_var.set("Все")
        self._load_messages()

    def _open_file(self):
        path = self.history.get_filepath()
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showinfo(
                "Файл не найден", "История ещё не сохранена"
            )

    def _export_txt(self):
        path = filedialog.asksaveasfilename(
            parent=self.win,
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"), ("All", "*.*")
            ],
            initialfile=f"nexus_history_{self.username}.txt"
        )
        if not path:
            return
        try:
            messages = self.history.get_all()
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    f"Nexus Messenger — история чата\n"
                    f"Пользователь: {self.username}\n"
                    f"Экспорт: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"{'─' * 50}\n\n"
                )
                prev_date = None
                for m in messages:
                    date  = m.get("date", "")
                    time  = m.get("time", "")
                    mtype = m.get("type", "")
                    if date != prev_date:
                        f.write(f"\n── {date} ──\n")
                        prev_date = date
                    if mtype == "message":
                        f.write(
                            f"[{time}] "
                            f"{m.get('username','?')}: "
                            f"{m.get('text','')}\n"
                        )
                    elif mtype == "private":
                        f.write(
                            f"[{time}] 🔒 "
                            f"{m.get('from','?')} → "
                            f"{m.get('to','?')}: "
                            f"{m.get('text','')}\n"
                        )
                    elif mtype == "system":
                        f.write(
                            f"[{time}] *** "
                            f"{m.get('text','')} ***\n"
                        )
            messagebox.showinfo(
                "Экспорт завершён",
                f"Файл сохранён:\n{path}"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _clear_history(self):
        if messagebox.askyesno(
            "Очистить историю",
            "Удалить всю историю сообщений?\n"
            "Это действие нельзя отменить.",
            parent=self.win
        ):
            self.history.clear()
            self._load_messages()
            messagebox.showinfo(
                "Готово", "История очищена", parent=self.win
            )

class NexusClient:
    def __init__(self, on_message, on_system, on_userlist,
                 on_connect, on_disconnect, on_error,
                 on_private, on_typing):
        self.on_message    = on_message
        self.on_system     = on_system
        self.on_userlist   = on_userlist
        self.on_connect    = on_connect
        self.on_disconnect = on_disconnect
        self.on_error      = on_error
        self.on_private    = on_private
        self.on_typing     = on_typing

        self.sock      = None
        self.username  = None
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
            raise ConnectionError(
                data.get("message", "Ошибка сервера")
            )
        if data.get("type") != "welcome":
            raise ConnectionError("Неверный ответ сервера")

        self.connected = True
        threading.Thread(
            target=self._recv_loop, daemon=True
        ).start()
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
        elif t == "typing":
            self.on_typing(pkt)

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

    def send_typing(self, is_typing: bool):
        self._send({"type": "typing", "is_typing": is_typing})

    def disconnect(self):
        self.connected = False
        try:
            self.sock.close()
        except Exception:
            pass

class TitleNotifier:
    BLINK_INTERVAL = 600

    def __init__(self, root, base_title):
        self.root         = root
        self.base_title   = base_title
        self._blinking    = False
        self._blink_job   = None
        self._blink_state = False
        self._pending     = 0
        self._focused     = True

        self.root.bind("<FocusIn>",  self._on_focus_in)
        self.root.bind("<FocusOut>", self._on_focus_out)

    def notify(self, text="💬 Новое сообщение"):
        if self._focused:
            return
        self._pending += 1
        self._alt_title = f"({self._pending}) {text}"
        if not self._blinking:
            self._blinking    = True
            self._blink_state = False
            self._do_blink()

    def notify_pm(self, sender):
        self.notify(f"🔒 ЛС от {sender}")

    def stop(self):
        self._stop_blink()

    def update_base_title(self, title):
        self.base_title = title
        if not self._blinking:
            self.root.title(title)

    def _do_blink(self):
        if not self._blinking:
            return
        self.root.title(
            self.base_title
            if self._blink_state
            else self._alt_title
        )
        self._blink_state = not self._blink_state
        self._blink_job = self.root.after(
            self.BLINK_INTERVAL, self._do_blink
        )

    def _stop_blink(self):
        self._blinking    = False
        self._blink_state = False
        self._pending     = 0
        if self._blink_job is not None:
            try:
                self.root.after_cancel(self._blink_job)
            except Exception:
                pass
            self._blink_job = None
        self.root.title(self.base_title)

    def _on_focus_in(self, event):
        self._focused = True
        self._stop_blink()

    def _on_focus_out(self, event):
        self._focused = False

class TypingIndicator:
    TIMEOUT = 4000

    def __init__(self, label: tk.Label):
        self.label    = label
        self._users   = {}
        self._root    = label.winfo_toplevel()

    def set_typing(self, username: bool, is_typing: bool):
        if is_typing:
            self._add(username)
        else:
            self._remove(username)

    def remove_user(self, username):
        self._remove(username)

    def clear(self):
        for job in self._users.values():
            try:
                self._root.after_cancel(job)
            except Exception:
                pass
        self._users.clear()
        self._update_label()

    def _add(self, username):
        if username in self._users:
            try:
                self._root.after_cancel(self._users[username])
            except Exception:
                pass

        job = self._root.after(
            self.TIMEOUT,
            lambda u=username: self._remove(u)
        )
        self._users[username] = job
        self._update_label()

    def _remove(self, username):
        if username in self._users:
            try:
                self._root.after_cancel(self._users[username])
            except Exception:
                pass
            del self._users[username]
        self._update_label()

    def _update_label(self):
        users = list(self._users.keys())

        if not users:
            self.label.config(text="")
            return

        if len(users) == 1:
            text = f"✏ {users[0]} печатает..."
        elif len(users) == 2:
            text = f"✏ {users[0]} и {users[1]} печатают..."
        else:
            rest = len(users) - 2
            text = (
                f"✏ {users[0]}, {users[1]} "
                f"и ещё {rest} печатают..."
            )

        self.label.config(text=text)

class EmojiPicker:
    EMOJIS = [
        "😀","😁","😂","🤣","😃","😄","😅","😆",
        "😇","😈","😉","😊","😋","😌","😍","😎",
        "😏","😐","😑","😒","😓","😔","😕","😖",
        "😗","😘","😙","😚","😛","😜","😝","😞",
        "😟","😠","😡","😢","😣","😤","😥","😦",
        "😧","😨","😩","😪","😫","😬","😭","😮",
        "😯","😰","😱","😲","😳","😴","😵","😶",
        "😷","🤒","🤓","🤔","🤕","🤗","🤠","🤡",
        "🤢","🤣","🤤","🤥","🤧","🤨","🤩","🤪",
        "🤫","🤬","🤭","🤮","🤯","🥰","🥱","🥲",
        "🥳","🥴","🥵","🥶","🥸","🧐","🫠","🫡",
        "👋","🤚","🖐","✋","🖖","👌","🤌","🤏",
        "✌","🤞","🤟","🤘","🤙","👈","👉","👆",
        "🖕","👇","☝","👍","👎","✊","👊","🤛",
        "🤜","👏","🙌","👐","🤲","🤝","🙏","💪",
        "🦾","🦿","🦵","🦶","👂","🦻","👃","🫀",
        "❤","🧡","💛","💚","💙","💜","🖤","🤍",
        "🤎","💔","❣","💕","💞","💓","💗","💖",
        "💘","💝","💟","☮","✝","☪","🕉","✡",
        "🔯","🕎","☯","☦","🛐","⛎","♈","♉",
        "🌸","🌺","🌻","🌹","🥀","🌷","🌱","🌿",
        "☘","🍀","🎋","🎍","🍃","🍂","🍁","🍄",
        "🌾","💐","🌵","🎄","🌲","🌳","🌴","🌞",
        "🌝","🌛","🌜","🌚","🌕","🌖","🌗","🌘",
        "🌑","🌒","🌓","🌔","🌙","🌟","⭐","🌠",
        "☁","⛅","🌤","🌥","🌦","🌧","⛈","🌩",
        "🌨","❄","☃","⛄","🌬","💨","🌪","🌫",
        "🌈","☔","⚡","❄","🔥","💧","🌊","🌀",
        "🍎","🍊","🍋","🍇","🍓","🍒","🍑","🥭",
        "🍍","🥥","🥝","🍅","🫑","🥦","🥬","🥒",
        "🌶","🫒","🧄","🧅","🥔","🍠","🥐","🥖",
        "🍞","🥨","🧀","🥚","🍳","🥞","🧇","🥓",
        "🍔","🍟","🌭","🌮","🌯","🥙","🧆","🥚",
        "🍕","🥗","🥘","🫕","🍝","🍜","🍲","🍛",
        "🍣","🍱","🥟","🦪","🍤","🍙","🍚","🍘",
        "🍥","🥮","🍡","🧁","🎂","🍰","🍮","🍭",
        "🍬","🍫","🍿","🍩","🍪","🌰","🥜","🍯",
        "🧃","🥤","🧋","☕","🫖","🍵","🧉","🍺",
        "🍻","🥂","🍷","🥃","🍸","🍹","🍾","🫗",
        "⚽","🏀","🏈","⚾","🥎","🏐","🏉","🥏",
        "🎾","🏸","🏒","🏑","🥍","🏏","🪃","🥅",
        "⛳","🪁","🏹","🎣","🤿","🥊","🥋","🎽",
        "🛹","🛼","🛷","⛸","🥌","🎿","⛷","🏂",
        "🪂","🏋","🤼","🤸","🤺","🏇","⛹","🤾",
        "🏌","🏄","🚣","🧘","🧗","🚵","🚴","🏆",
        "🥇","🥈","🥉","🏅","🎖","🎗","🎫","🎟",
        "🎪","🤹","🎭","🩰","🎨","🎬","🎤","🎧",
        "🎼","🎹","🥁","🪘","🎷","🎺","🎸","🪕",
        "🎻","🎲","♟","🎯","🎳","🎮","🎰","🧩",
        "🚗","🚕","🚙","🚌","🚎","🏎","🚓","🚑",
        "🚒","🚐","🛻","🚚","🚛","🚜","🏍","🛵",
        "🛺","🚲","🛴","🛹","🛼","🚏","🛣","🛤",
        "⛽","🚨","🚥","🚦","🛑","🚧","⚓","🛟",
        "⛵","🚤","🛥","🛳","⛴","🚢","✈","🛩",
        "🛫","🛬","🪂","💺","🚁","🚟","🚠","🚡",
        "🛰","🚀","🛸","🪐","🌍","🌎","🌏","🗺",
        "💡","🔦","🕯","🪔","💰","💴","💵","💶",
        "💷","💸","💳","🪙","💹","📈","📉","📊",
        "📋","📌","📍","✂","🗃","🗄","🗑","🔒",
        "🔓","🔏","🔐","🔑","🗝","🔨","🪓","⛏",
        "⚒","🛠","🗡","⚔","🛡","🪚","🔧","🪛",
        "🔩","⚙","🗜","⚖","🦯","🔗","⛓","🪝",
        "🧲","🪜","⚗","🧪","🧫","🧬","🔬","🔭",
        "📡","💉","🩸","💊","🩹","🩺","🩻","🚪",
        "🛏","🛋","🪑","🚽","🪠","🚿","🛁","🪤",
        "✅","❎","🔴","🟠","🟡","🟢","🔵","🟣",
        "⚫","⚪","🟤","🔶","🔷","🔸","🔹","🔺",
        "🔻","💠","🔘","🔲","🔳","▪","▫","◾",
        "◽","◼","◻","🟥","🟧","🟨","🟩","🟦",
        "🟪","⬛","⬜","🟫","🔈","🔉","🔊","📢",
        "📣","📯","🔔","🔕","🎵","🎶","💬","💭",
        "🗯","♠","♥","♦","♣","🃏","🀄","🎴",
    ]

    CATEGORIES = [
        ("😀 Смайлы",     0,   88),
        ("👋 Жесты",      88,  120),
        ("❤ Сердца",     120, 144),
        ("🌸 Природа",    144, 216),
        ("🍎 Еда",        216, 312),
        ("⚽ Активность", 312, 392),
        ("🚗 Транспорт",  392, 440),
        ("💡 Объекты",    440, 512),
        ("✅ Символы",    512, 999),
    ]

    def __init__(self, parent, on_select):
        self.on_select        = on_select
        self.win              = None
        self.parent           = parent
        self.current_category = 0
        self.search_var       = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

    def toggle(self, anchor_widget):
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None
            return
        self._show(anchor_widget)

    def _show(self, anchor):
        self.win = tk.Toplevel()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=config.BG_MEDIUM)

        anchor.update_idletasks()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() - 370
        if x < 0:
            x = 0
        self.win.geometry(f"420x360+{x}+{y}")
        self._build_picker()
        self.win.bind("<FocusOut>", self._on_focus_out)
        self.win.focus_set()

    def _build_picker(self):
        hdr = tk.Frame(self.win, bg=config.BG_LIGHT, pady=4)
        hdr.pack(fill=tk.X)

        tk.Label(
            hdr, text="😊 Выбор эмодзи",
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Consolas", 10, "bold")
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            hdr, text="✕",
            bg=config.BG_LIGHT, fg=config.TEXT_MUTED,
            font=("Consolas", 10),
            relief=tk.FLAT, padx=6,
            command=self._close
        ).pack(side=tk.RIGHT, padx=4)

        sf = tk.Frame(self.win, bg=config.BG_MEDIUM, pady=4)
        sf.pack(fill=tk.X, padx=6)

        tk.Label(
            sf, text="🔍",
            bg=config.BG_MEDIUM, fg=config.TEXT_MUTED,
            font=("Consolas", 11)
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.search_entry = tk.Entry(
            sf,
            textvariable=self.search_var,
            bg=config.INPUT_BG, fg=config.TEXT_PRIMARY,
            insertbackground=config.TEXT_PRIMARY,
            font=("Consolas", 11),
            relief=tk.FLAT, bd=4
        )
        self.search_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        self.search_entry.focus()

        self.cat_frame = tk.Frame(self.win, bg=config.BG_DARK)
        self.cat_frame.pack(fill=tk.X)

        self.cat_buttons = []
        for i, (name, _, __) in enumerate(self.CATEGORIES):
            icon = name.split()[0]
            btn = tk.Button(
                self.cat_frame, text=icon,
                bg=config.BG_DARK, fg=config.TEXT_PRIMARY,
                font=("Segoe UI Emoji", 13),
                relief=tk.FLAT, padx=4, pady=2,
                command=lambda idx=i: self._select_category(idx)
            )
            btn.pack(side=tk.LEFT, padx=1, pady=2)
            self.cat_buttons.append(btn)

        grid_outer = tk.Frame(self.win, bg=config.BG_MEDIUM)
        grid_outer.pack(
            fill=tk.BOTH, expand=True, padx=4, pady=4
        )

        canvas = tk.Canvas(
            grid_outer, bg=config.BG_MEDIUM,
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            grid_outer, orient=tk.VERTICAL,
            command=canvas.yview,
            bg=config.SCROLLBAR_BG
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.grid_frame  = tk.Frame(canvas, bg=config.BG_MEDIUM)
        self.grid_window = canvas.create_window(
            (0, 0), window=self.grid_frame, anchor=tk.NW
        )

        self.grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(
                self.grid_window, width=e.width
            )
        )
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            )
        )

        self.canvas = canvas
        self._select_category(0)

    def _select_category(self, idx):
        self.current_category = idx
        for i, btn in enumerate(self.cat_buttons):
            btn.config(
                bg=config.BG_LIGHT if i == idx
                else config.BG_DARK
            )
        self.search_var.set("")
        _, start, end = self.CATEGORIES[idx]
        self._fill_grid(self.EMOJIS[start:end])

    def _on_search(self, *args):
        query = self.search_var.get().strip()
        if not query:
            self._select_category(self.current_category)
            return
        filtered = [e for e in self.EMOJIS if query in e]
        self._fill_grid(filtered if filtered else self.EMOJIS)

    def _fill_grid(self, emojis):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        cols = 10
        for i, emoji in enumerate(emojis):
            btn = tk.Button(
                self.grid_frame, text=emoji,
                bg=config.BG_MEDIUM,
                activebackground=config.BG_LIGHT,
                relief=tk.FLAT,
                font=("Segoe UI Emoji", 15),
                width=2, pady=2,
                command=lambda e=emoji: self._pick(e)
            )
            btn.grid(
                row=i // cols, column=i % cols,
                padx=1, pady=1
            )
            btn.bind(
                "<Enter>",
                lambda ev, b=btn: b.config(bg=config.BG_LIGHT)
            )
            btn.bind(
                "<Leave>",
                lambda ev, b=btn: b.config(bg=config.BG_MEDIUM)
            )

        self.canvas.yview_moveto(0)

    def _pick(self, emoji):
        self.on_select(emoji)

    def _close(self):
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def _on_focus_out(self, event):
        if self.win:
            self.win.after(150, self._check_focus)

    def _check_focus(self):
        try:
            if self.win and self.win.winfo_exists():
                if self.win.focus_get() is None:
                    self._close()
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
            self.win, text="Messenger v0.5",
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
            relief=tk.FLAT, width=24, bd=6
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
    TYPING_SEND_DELAY  = 300
    TYPING_STOP_DELAY  = 2000

    def __init__(self, root, username, client):
        self.root           = root
        self.username       = username
        self.client         = client
        self.private_target = None
        self.message_count  = 0
        self.emoji_picker   = None

        self._is_typing      = False
        self._typing_job     = None

        self._base_title = f"Nexus Messenger — {username}"
        self.root.title(self._base_title)
        self.root.geometry("900x620")
        self.root.configure(bg=config.BG_DARK)
        self.root.minsize(700, 450)

        self.history = ChatHistory(username)

        self._build_ui()

        self.notifier = TitleNotifier(self.root, self._base_title)
        self.typing   = TypingIndicator(self.typing_label)

        self._sys_msg(f"✅ Подключён как {username}")
        count = self.history.get_count()
        if count > 0:
            self._sys_msg(
                f"📜 Загружена история: {count} сообщений"
            )

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

        tk.Button(
            hdr, text="📜 История",
            bg=config.BG_MEDIUM, fg=config.TEXT_PRIMARY,
            font=("Consolas", 9),
            relief=tk.FLAT, padx=10, pady=4,
            activebackground=config.ACCENT,
            command=self._open_history
        ).pack(side=tk.RIGHT, padx=6)

        main = tk.Frame(self.root, bg=config.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)

        users_frame = tk.Frame(
            main, bg=config.BG_MEDIUM, width=180
        )
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
            relief=tk.FLAT, border=0,
            activestyle="none"
        )
        self.users_list.pack(
            fill=tk.BOTH, expand=True, padx=8, pady=4
        )
        self.users_list.bind(
            "<Double-Button-1>", self._on_user_click
        )

        tk.Label(
            users_frame,
            text="2×ЛКМ — личное сообщение",
            bg=config.BG_MEDIUM, fg=config.TEXT_MUTED,
            font=("Consolas", 7), wraplength=160
        ).pack(pady=(0, 8), padx=5)

        chat_frame = tk.Frame(main, bg=config.BG_DARK)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_box = tk.Text(
            chat_frame,
            bg=config.BG_DARK, fg=config.TEXT_PRIMARY,
            font=("Consolas", 11),
            relief=tk.FLAT, state=tk.DISABLED,
            wrap=tk.WORD, padx=10, pady=8,
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

        self.typing_label = tk.Label(
            self.root, text="",
            bg=config.BG_DARK, fg="#9c88ff",
            font=("Consolas", 9, "italic"),
            anchor=tk.W
        )
        self.typing_label.pack(
            fill=tk.X, padx=16, pady=(2, 0)
        )

        input_frame = tk.Frame(
            self.root, bg=config.BG_MEDIUM, pady=8
        )
        input_frame.pack(fill=tk.X, padx=10, pady=(2, 6))

        self.pm_indicator = tk.Label(
            input_frame, text="",
            bg=config.BG_MEDIUM, fg="#ffd700",
            font=("Consolas", 9)
        )
        self.pm_indicator.pack(anchor=tk.W, padx=5)

        inp_row = tk.Frame(input_frame, bg=config.BG_MEDIUM)
        inp_row.pack(fill=tk.X)

        self.emoji_btn = tk.Button(
            inp_row, text="😊",
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY,
            font=("Segoe UI Emoji", 14),
            relief=tk.FLAT, padx=6, pady=4,
            activebackground=config.ACCENT,
            command=self._toggle_emoji
        )
        self.emoji_btn.pack(side=tk.LEFT, padx=(5, 4))

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            inp_row,
            textvariable=self.input_var,
            bg=config.INPUT_BG, fg=config.TEXT_PRIMARY,
            insertbackground=config.TEXT_PRIMARY,
            font=("Consolas", 12),
            relief=tk.FLAT, bd=8
        )
        self.input_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        self.input_entry.bind("<Return>", lambda e: self._send())
        self.input_entry.bind(
            "<Escape>", lambda e: self._cancel_pm()
        )
        self.input_entry.bind(
            "<KeyRelease>", self._on_key_release
        )
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

        self.emoji_picker = EmojiPicker(
            parent=self.input_entry,
            on_select=self._insert_emoji
        )

    def _on_key_release(self, event):
        if event.keysym in (
            "Return", "Escape", "Tab",
            "Up", "Down", "Left", "Right"
        ):
            return

        text = self.input_var.get().strip()

        if text:
            self._start_typing()
        else:
            self._stop_typing()

    def _start_typing(self):
        if not self._is_typing:
            self._is_typing = True
            self.client.send_typing(True)

        if self._typing_job is not None:
            try:
                self.root.after_cancel(self._typing_job)
            except Exception:
                pass

        self._typing_job = self.root.after(
            self.TYPING_STOP_DELAY,
            self._stop_typing
        )

    def _stop_typing(self):
        if self._typing_job is not None:
            try:
                self.root.after_cancel(self._typing_job)
            except Exception:
                pass
            self._typing_job = None

        if self._is_typing:
            self._is_typing = False
            self.client.send_typing(False)

    def _open_history(self):
        HistoryWindow(self.root, self.history, self.username)

    def _toggle_emoji(self):
        self.emoji_picker.toggle(self.emoji_btn)

    def _insert_emoji(self, emoji):
        pos = self.input_entry.index(tk.INSERT)
        cur = self.input_var.get()
        self.input_var.set(cur[:pos] + emoji + cur[pos:])
        self.input_entry.icursor(pos + len(emoji))
        self.input_entry.focus()

    def add_message(self, pkt):
        uname  = pkt.get("username", "?")
        text   = pkt.get("text", "")
        ts     = pkt.get("time", "")
        is_own = (uname == self.username)

        self.typing.remove_user(uname)

        self.history.add_message(pkt)

        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, "\n")

        if is_own:
            self.chat_box.insert(
                tk.END, f"  {uname}", "own_name"
            )
        else:
            self.chat_box.insert(
                tk.END, f"  {uname}", "other_name"
            )

        self.chat_box.insert(tk.END, f"  {ts}\n", "time")

        tag = "msg_own" if is_own else "msg_other"
        self.chat_box.insert(tk.END, f"  {text}\n", tag)

        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)
        self.message_count += 1
        self.status_var.set(
            f"Сообщений: {self.message_count}  "
            f"│  История: {self.history.get_count()}"
        )

        if not is_own:
            self.notifier.notify(f"💬 {uname}: {text[:30]}")

    def add_private(self, pkt):
        frm  = pkt.get("from", "?")
        to   = pkt.get("to", "?")
        text = pkt.get("text", "")
        ts   = pkt.get("time", "")

        self.history.add_private(pkt)

        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, "\n")

        direction = (
            f"ЛС от {frm}"
            if frm != self.username else f"ЛС → {to}"
        )
        self.chat_box.insert(
            tk.END,
            f"  🔒 {direction}  {ts}\n",
            "private_label"
        )
        self.chat_box.insert(
            tk.END, f"  {text}\n", "private_msg"
        )
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

        if frm != self.username:
            self.notifier.notify_pm(frm)

    def on_typing_received(self, pkt):
        uname     = pkt.get("username", "")
        is_typing = pkt.get("is_typing", False)
        if uname and uname != self.username:
            self.typing.set_typing(uname, is_typing)

    def _sys_msg(self, text):
        self.history.add_system(text)
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(
            tk.END, f"\n  ─── {text} ───\n", "system"
        )
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
            self.status_var.set(
                "Слишком длинное сообщение (макс. 500)"
            )
            return

        self._stop_typing()

        if self.private_target:
            self.client.send_private(self.private_target, text)
        else:
            self.client.send_message(text)

        self.input_var.set("")

    def _on_user_click(self, event):
        sel = self.users_list.curselection()
        if not sel:
            return
        item = (
            self.users_list.get(sel[0])
            .strip().lstrip("★").strip()
        )
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
        self.notifier.stop()
        self.typing.clear()

    def _on_close(self):
        self._stop_typing()
        self.notifier.stop()
        self.typing.clear()
        if self.emoji_picker:
            self.emoji_picker._close()
        self.client.disconnect()
        self.root.destroy()

class NexusApp:
    def __init__(self):
        self.root     = tk.Tk()
        self.root.withdraw()
        self.client   = None
        self.chat_win = None
        self._show_login()
        self.root.mainloop()

    def _show_login(self):
        login = LoginWindow(self.root, self._on_login)
        self.root.wait_window(login.win)

    def _on_login(self, username):
        self.client = NexusClient(
            on_message    = self._on_message,
            on_system     = self._on_system,
            on_userlist   = self._on_userlist,
            on_connect    = self._on_connect,
            on_disconnect = self._on_disconnect,
            on_error      = self._on_error,
            on_private    = self._on_private,
            on_typing     = self._on_typing
        )
        try:
            self.client.connect(username)
        except Exception as e:
            messagebox.showerror(
                "Ошибка подключения",
                f"Не удалось подключиться к серверу:\n{e}\n\n"
                f"Убедитесь, что сервер запущен "
                f"({config.HOST}:{config.PORT})"
            )
            self._show_login()

    def _on_connect(self, data):
        def _do():
            self.root.deiconify()
            self.chat_win = ChatWindow(
                self.root, self.client.username, self.client
            )
            self.chat_win.update_users(data.get("users", []))
        self.root.after(0, _do)

    def _on_message(self, pkt):
        if self.chat_win:
            self.root.after(
                0, lambda: self.chat_win.add_message(pkt)
            )

    def _on_system(self, pkt):
        if self.chat_win:
            msg = pkt.get("message", "")
            self.root.after(
                0, lambda: self.chat_win._sys_msg(msg)
            )

    def _on_userlist(self, users):
        if self.chat_win:
            self.root.after(
                0, lambda: self.chat_win.update_users(users)
            )

    def _on_private(self, pkt):
        if self.chat_win:
            self.root.after(
                0, lambda: self.chat_win.add_private(pkt)
            )

    def _on_typing(self, pkt):
        if self.chat_win:
            self.root.after(
                0,
                lambda: self.chat_win.on_typing_received(pkt)
            )

    def _on_disconnect(self):
        if self.chat_win:
            self.root.after(0, self.chat_win.set_disconnected)

    def _on_error(self, msg):
        self.root.after(
            0, lambda: messagebox.showerror("Ошибка", msg)
        )

if __name__ == "__main__":
    NexusApp()
