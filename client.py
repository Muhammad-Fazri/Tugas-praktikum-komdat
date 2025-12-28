import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import queue

SERVER_IP = "192.168.1.1"
SERVER_PORT = 12345

class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")

        self.sock = None
        self.running = False
        self.buffer = ""
        self.msg_queue = queue.Queue()

        tk.Label(root, text="ID:").pack()
        self.id_entry = tk.Entry(root)
        self.id_entry.pack()

        self.connect_btn = tk.Button(root, text="Connect", command=self.connect)
        self.connect_btn.pack(pady=5)

        self.chat_area = scrolledtext.ScrolledText(
            root, width=70, height=20, state="disabled"
        )
        self.chat_area.pack(padx=10, pady=10)

        self.msg_entry = tk.Entry(root, width=60)
        self.msg_entry.pack(side="left", padx=5)

        self.send_btn = tk.Button(root, text="pesan", command=self.send)
        self.send_btn.pack(side="left")
        self.root.after(50, self.process_queue)

    
    def connect(self):
        name = self.id_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "ID kosong")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, SERVER_PORT))
            self.sock.send((name + "\n").encode())

            resp = self.sock.recv(1024).decode()
            if "CONNECTED" not in resp:
                messagebox.showerror("Error", resp)
                return

            self.running = True
            self.connect_btn.config(state="disabled")

            threading.Thread(target=self.receive, daemon=True).start()
            self.msg_queue.put("Terhubung ke server")

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def receive(self):
        try:
            while self.running:
                data = self.sock.recv(1024)
                if not data:
                    break

                self.buffer += data.decode()
                while "\n" in self.buffer:
                    msg, self.buffer = self.buffer.split("\n", 1)
                    self.msg_queue.put(msg)

        except Exception as e:
            self.msg_queue.put(f"ERROR: {e}")
        finally:
            self.running = False
            self.msg_queue.put("Koneksi terputus")

    
    def process_queue(self):
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self.chat_area.config(state="normal")
            self.chat_area.insert(tk.END, msg + "\n")
            self.chat_area.see(tk.END)
            self.chat_area.config(state="disabled")

        self.root.after(50, self.process_queue)

   
    def send(self):
        msg = self.msg_entry.get().strip()
        if msg and self.sock:
            try:
                self.sock.send((msg + "\n").encode())
                if msg.startswith("TO:"):
                    try:
                        _, target, text = msg.split(":", 2)
                        display_msg = f"[Privat] → {target}:{text}"
                    except:
                        display_msg = f"[ME]:{msg}"
                elif msg.startswith("ALL:"):
                    display_msg = f"[ALL]:{msg[4:]}"
                else:
                    display_msg = f"[ME]:{msg}"

                self.chat_area.config(state="normal")
                self.chat_area.insert(tk.END, display_msg + "\n")
                self.chat_area.see(tk.END)
                self.chat_area.config(state="disabled")

                self.msg_entry.delete(0, tk.END)

            except:
                messagebox.showerror("Error", "Gagal kirim pesan")

if __name__ == "__main__":
    root = tk.Tk()
    ClientGUI(root)
    root.mainloop()
