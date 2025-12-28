import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import datetime

HOST = "0.0.0.0"
PORT = 12345

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Server")

        self.text = scrolledtext.ScrolledText(root, width=90, height=22)
        self.text.pack(padx=10, pady=10)

        self.start_btn = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_btn.pack(pady=5)

        self.server = None
        self.clients = {}
        self.lock = threading.Lock()

    def log(self, msg):
        time = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.text.insert(tk.END, f"{time} {msg}\n")
        self.text.see(tk.END)

    def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen()
        self.log(f"SERVER Berjalan DI HOST:{HOST}  Dan DI PORT:{PORT}")
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.accept_client, daemon=True).start()

    def accept_client(self):
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        name = None
        buffer = ""
        try:
            name = conn.recv(1024).decode().strip()
            with self.lock:
                if name in self.clients:
                    conn.send(b"ID sudah dipakai\n")
                    conn.close()
                    return
                self.clients[name] = conn

            conn.send(b"CONNECTED\n")
            self.log(f"{name} TERHUBUNG  KE SERVER")

            while True:
                data = conn.recv(1024)
                if not data:
                    break

                buffer += data.decode()
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    self.process_message(name, msg.strip())

        except Exception as e:
            self.log(f"ERROR {name}: {e}")
        finally:
            if name:
                with self.lock:
                    self.clients.pop(name, None)
            conn.close()
            self.log(f"{name} TERPUTUS")

    def process_message(self, name, msg):
        ts = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.log(f"{name} >> {msg}")

        if msg.startswith("TO:"):
            try:
                _, target, text = msg.split(":", 2)
                with self.lock:
                    if target in self.clients:
                        self.clients[target].send(
                            f"{ts} [PRIVATE from:{name}] {text}\n".encode()
                        )
                    else:
                        self.clients[name].send(
                            f"{ts} Client tujuan tidak diketahui\n".encode()
                        )
            except:
                self.clients[name].send(
                    f"{ts} Format salah! TO:id:pesan\n".encode()
                )

        elif msg.startswith("ALL:"):
            text = msg.split(":", 1)[1]
            with self.lock:
                for cname, csock in self.clients.items():
                    if cname != name:
                        csock.send(
                            f"{ts} [BROADCAST from:{name}] {text}\n".encode()
                        )
        else:
            self.clients[name].send(
                f"{ts} Format tidak dikenali\n".encode()
            )

if __name__ == "__main__":
    root = tk.Tk()
    ServerGUI(root)
    root.mainloop()