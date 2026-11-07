from __future__ import annotations

import argparse
import importlib
import json
import os
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import ttk
from collections.abc import Callable


DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
SYSTEM_MESSAGE = (
    "Kamu adalah Stars, asisten AI pribadi yang ramah, cerdas, dan praktis. "
    "Jawab dalam bahasa yang digunakan pengguna. Jangan mengaku bisa melakukan "
    "aksi di komputer atau mengakses informasi langsung jika kamu tidak benar-benar bisa."
)


class StarsApp:
    def __init__(self, root: tk.Tk, start_listening: bool = False) -> None:
        self.root = root
        self.root.title("Stars - Personal AI")
        self.root.geometry("860x640")
        self.root.minsize(600, 460)
        self.root.configure(bg="#0b1020")

        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.api_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_API_URL).strip()
        self.model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip()
        self.messages: list[dict[str, str]] = []
        self.busy = False
        self.listening = False
        self.closing = False
        self.stop_event = threading.Event()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._append_message(
            "Stars",
            "Halo! Aku Stars, asisten AI kamu. Tanyakan apa saja untuk memulai.",
            "assistant",
        )
        if not self.api_key:
            self._set_status("Atur OPENAI_API_KEY di terminal sebelum menjalankan Stars.")
        else:
            self._set_status(f"Model: {self.model} | Pesan dikirim ke API yang dikonfigurasi.")
        if start_listening:
            self.root.after(300, self._toggle_listening)

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Stars.TButton",
            background="#6366f1",
            foreground="#ffffff",
            padding=(18, 10),
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Stars.TButton", background=[("active", "#818cf8"), ("disabled", "#3b3f63")])

        header = tk.Frame(self.root, bg="#111831", padx=22, pady=16)
        header.pack(fill="x")
        tk.Label(
            header,
            text="✦  STARS",
            bg="#111831",
            fg="#e0e7ff",
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text="PERSONAL AI",
            bg="#111831",
            fg="#8b9bbd",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        self.chat = tk.Text(
            self.root,
            bg="#0b1020",
            fg="#e5e7eb",
            insertbackground="#ffffff",
            wrap="word",
            padx=24,
            pady=20,
            font=("Segoe UI", 11),
            relief="flat",
            state="disabled",
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure("assistant_name", foreground="#a5b4fc", font=("Segoe UI", 10, "bold"))
        self.chat.tag_configure("user_name", foreground="#5eead4", font=("Segoe UI", 10, "bold"))
        self.chat.tag_configure("message", foreground="#e5e7eb", spacing1=4, spacing3=16)
        self.chat.tag_configure("error", foreground="#fca5a5", spacing1=4, spacing3=16)

        composer = tk.Frame(self.root, bg="#111831", padx=18, pady=14)
        composer.pack(fill="x")
        self.input = tk.Text(
            composer,
            height=3,
            bg="#1a2340",
            fg="#f3f4f6",
            insertbackground="#ffffff",
            wrap="word",
            padx=12,
            pady=10,
            font=("Segoe UI", 10),
            relief="flat",
        )
        self.input.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.input.bind("<Control-Return>", self._send_from_event)
        self.root.bind_all("<Control-Shift-s>", self._toggle_listening_from_event)
        self.send_button = ttk.Button(
            composer,
            text="Kirim  ➤",
            style="Stars.TButton",
            command=self._send_message,
        )
        self.send_button.pack(side="right", anchor="s")
        self.mic_button = ttk.Button(
            composer,
            text="🎙 Mulai bicara",
            style="Stars.TButton",
            command=self._toggle_listening,
        )
        self.mic_button.pack(side="right", anchor="s", padx=(0, 8))

        footer = tk.Frame(self.root, bg="#111831", padx=20, pady=(0, 12))
        footer.pack(fill="x")
        self.status = tk.Label(
            footer,
            text="Ctrl+Enter: kirim  |  Ctrl+Shift+S: nyalakan/matikan mikrofon",
            bg="#111831",
            fg="#8491ad",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.status.pack(fill="x")

    def _send_from_event(self, event: tk.Event) -> str:
        if event.widget is self.input:
            self._send_message()
        return "break"

    def _toggle_listening_from_event(self, event: tk.Event) -> str:
        if event.widget.winfo_toplevel() is self.root:
            self._toggle_listening()
        return "break"

    def _send_message(self) -> None:
        text = self.input.get("1.0", "end").strip()
        if not text:
            return
        self._submit_message(text)

    def _submit_message(self, text: str) -> None:
        if self.busy:
            return
        if not self.api_key:
            self._append_message(
                "Stars",
                "API key belum diatur. Ikuti langkah konfigurasi di README.md, lalu buka ulang aplikasi.",
                "error",
            )
            self._set_status("OPENAI_API_KEY belum diatur.")
            return

        self.input.delete("1.0", "end")
        self._append_message("Kamu", text, "user")
        self.messages.append({"role": "user", "content": text})
        self.busy = True
        self.send_button.configure(state="disabled")
        self._set_status("Stars sedang berpikir...")
        threading.Thread(target=self._request_reply, daemon=True).start()

    def _toggle_listening(self) -> None:
        if self.listening:
            self.listening = False
            self.mic_button.configure(text="Menutup mikrofon...", state="disabled")
            self._set_status("Mikrofon dimatikan.")
            return

        self.listening = True
        self.mic_button.configure(text="⏹ Matikan mikrofon")
        self._set_status("Memulai mikrofon...")
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self) -> None:
        try:
            sr = importlib.import_module("speech_recognition")
        except ImportError:
            self._schedule_ui(self._voice_setup_error)
            return

        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self._schedule_ui(self._set_status, "Mikrofon aktif. Silakan bicara.")
                while self.listening and not self.stop_event.is_set():
                    try:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=12)
                    except sr.WaitTimeoutError:
                        continue

                    try:
                        transcript = recognizer.recognize_google(audio, language="id-ID")
                    except sr.UnknownValueError:
                        self._schedule_ui(self._set_status, "Ucapan belum terdengar jelas. Silakan coba lagi.")
                        continue
                    except sr.RequestError as error:
                        self._schedule_ui(
                            self._set_status,
                            f"Layanan pengenal suara tidak tersedia: {error}",
                        )
                        continue

                    self._schedule_ui(self._handle_voice_text, transcript)
        except (OSError, AttributeError) as error:
            self._schedule_ui(self._voice_device_error, str(error))
        finally:
            self.listening = False
            if not self.closing:
                self._schedule_ui(self._on_listening_stopped)

    def _handle_voice_text(self, text: str) -> None:
        if self.busy:
            self._set_status("Stars masih menjawab. Ucapkan pesan lagi setelah selesai.")
            return
        self.input.delete("1.0", "end")
        self.input.insert("1.0", text)
        self._submit_message(text)

    def _voice_setup_error(self) -> None:
        self.listening = False
        self.mic_button.configure(text="🎙 Mulai bicara")
        self._append_message(
            "Stars",
            "Fitur mikrofon belum terpasang. Buka terminal di folder proyek dan jalankan: "
            "python -m pip install -r requirements.txt",
            "error",
        )
        self._set_status("Paket pengenalan suara belum terpasang.")

    def _voice_device_error(self, detail: str) -> None:
        self.listening = False
        self.mic_button.configure(text="🎙 Mulai bicara")
        self._append_message("Stars", f"Tidak dapat membuka mikrofon: {detail}", "error")
        self._set_status("Periksa mikrofon dan izin akses mikrofon Windows.")

    def _on_listening_stopped(self) -> None:
        self.mic_button.configure(text="🎙 Mulai bicara", state="normal")

    def _schedule_ui(self, callback: Callable[..., object], *args: object) -> None:
        if self.closing:
            return
        try:
            self.root.after(0, callback, *args)
        except tk.TclError:
            if not self.closing:
                raise

    def _close(self) -> None:
        self.closing = True
        self.listening = False
        self.stop_event.set()
        self.root.destroy()

    def _request_reply(self) -> None:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_MESSAGE}, *self.messages],
        }
        try:
            request = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Format respons API tidak dikenali.")
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise ValueError("Respons API tidak berisi pilihan jawaban.")
            message = choices[0].get("message")
            if not isinstance(message, dict):
                raise ValueError("Format jawaban API tidak dikenali.")
            answer = message.get("content")
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Jawaban dari API kosong atau tidak didukung.")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            self.root.after(0, self._finish_error, f"API mengembalikan HTTP {error.code}: {detail[:500]}")
            return
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            self.root.after(0, self._finish_error, f"Tidak dapat memperoleh jawaban: {error}")
            return

        self.root.after(0, self._finish_reply, answer.strip())

    def _finish_reply(self, answer: str) -> None:
        self.messages.append({"role": "assistant", "content": answer})
        self._append_message("Stars", answer, "assistant")
        self._set_status(f"Model: {self.model} | Siap")
        self._set_idle()

    def _finish_error(self, detail: str) -> None:
        self._append_message("Stars", detail, "error")
        self._set_status("Terjadi kesalahan. Periksa koneksi, API key, dan konfigurasi endpoint.")
        self._set_idle()

    def _set_idle(self) -> None:
        self.busy = False
        self.send_button.configure(state="normal")
        self.input.focus_set()

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _append_message(self, name: str, text: str, kind: str) -> None:
        self.chat.configure(state="normal")
        name_tag = "user_name" if kind == "user" else "assistant_name"
        body_tag = "error" if kind == "error" else "message"
        self.chat.insert("end", f"{name}\n", name_tag)
        self.chat.insert("end", f"{text}\n\n", body_tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stars desktop AI")
    parser.add_argument(
        "--listen",
        action="store_true",
        help="mulai mendengarkan mikrofon saat aplikasi dibuka",
    )
    args = parser.parse_args()
    root = tk.Tk()
    StarsApp(root, start_listening=args.listen)
    root.mainloop()


if __name__ == "__main__":
    main()