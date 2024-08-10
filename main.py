import psutil
import tkinter as tk
from tkinter import ttk, Menu
import subprocess
import os
import sys

# Determine the directory where the script or executable is located
if getattr(sys, 'frozen', False):
    # If the script is compiled to an EXE, use the location of the EXE
    base_dir = sys._MEIPASS
else:
    # Otherwise, use the location of the script
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Path to PsSuspend.exe (automatically determined based on the script's directory)
pssuspend_path = os.path.join(base_dir, "pssuspend.exe")

# Global variable to control auto-refresh
auto_refresh = False  # Default to not auto-refresh

# Function to reset progress labels to default text
def reset_progress_label(label, default_text):
    label.config(text=default_text)

def suspend_process(pid, label):
    try:
        label.config(text="Suspending...")
        subprocess.run([pssuspend_path, str(pid)], check=True)
        label.config(text="Suspend: 100%")
        label.after(2000, reset_progress_label, label, "Suspend: 0%")
    except subprocess.CalledProcessError as e:
        print(f"Error suspending process {pid}: {e}")
        label.config(text="Error")
        label.after(2000, reset_progress_label, label, "Suspend: 0%")

def resume_process(pid, label):
    try:
        label.config(text="Resuming...")
        subprocess.run([pssuspend_path, "-r", str(pid)], check=True)
        label.config(text="Resume: 100%")
        label.after(2000, reset_progress_label, label, "Resume: 0%")
    except subprocess.CalledProcessError as e:
        print(f"Error resuming process {pid}: {e}")
        label.config(text="Error")
        label.after(2000, reset_progress_label, label, "Resume: 0%")

def update_tree(tree):
    # Clear the tree
    for item in tree.get_children():
        tree.delete(item)

    # A dictionary to store processes by PID
    processes = {p.info['pid']: p.info for p in psutil.process_iter(['pid', 'name', 'ppid'])}

    # A dictionary to store tree items by PID
    tree_items = {}

    # A list of processes that could not be added on the first pass
    unplaced_processes = []

    # First pass: Attempt to add all processes
    for pid, proc in processes.items():
        name = proc['name'].replace('{', '').replace('}', '')  # Ensure no curly braces
        ppid = proc['ppid']

        # Create the tree item
        values = (pid,)
        if ppid == 0 or ppid not in processes:
            # Top-level process (orphan process)
            tree_items[pid] = tree.insert('', 'end', text=name, values=values)
        elif ppid in tree_items:
            # Parent is already in the tree
            tree_items[pid] = tree.insert(tree_items[ppid], 'end', text=name, values=values)
        else:
            # Parent isn't in the tree yet; add this process to unplaced
            unplaced_processes.append((pid, proc))

    # Second pass: Try to place remaining processes
    for pid, proc in unplaced_processes:
        ppid = proc['ppid']
        if ppid in tree_items:
            # Now the parent should be in the tree
            tree_items[pid] = tree.insert(tree_items[ppid], 'end', text=proc['name'], values=(pid,))

    # Expand only the first tier of nodes
    for item in tree.get_children():
        tree.item(item, open=True)

    # Schedule the next update if auto-refresh is enabled
    if auto_refresh:
        tree.after(1000, update_tree, tree)

def toggle_auto_refresh(tree):
    global auto_refresh
    auto_refresh = not auto_refresh
    if auto_refresh:
        update_tree(tree)

def manual_refresh(tree):
    update_tree(tree)

def on_right_click(event, tree):
    iid = tree.identify_row(event.y)
    if iid:
        tree.selection_set(iid)
        popup_menu = Menu(tree, tearoff=0)
        popup_menu.add_command(label="Suspend", command=lambda: suspend_selected_process(tree))
        popup_menu.add_command(label="Resume", command=lambda: resume_selected_process(tree))
        popup_menu.add_separator()
        popup_menu.add_command(label="Suspend This Only", command=lambda: suspend_this_only(tree))
        popup_menu.add_command(label="Resume This Only", command=lambda: resume_this_only(tree))
        popup_menu.post(event.x_root, event.y_root)

def suspend_selected_process(tree):
    selected_item = tree.selection()[0]
    pid = int(tree.item(selected_item)['values'][0])
    suspend_process(pid, suspend_progress_label)
    tree.item(selected_item, tags=('suspended',))
    tree.tag_configure('suspended', background='red')

def resume_selected_process(tree):
    selected_item = tree.selection()[0]
    pid = int(tree.item(selected_item)['values'][0])
    resume_process(pid, resume_progress_label)
    tree.item(selected_item, tags=('running',))
    tree.tag_configure('running', background='white')

def suspend_this_only(tree):
    selected_item = tree.selection()[0]
    pid = int(tree.item(selected_item)['values'][0])
    suspend_process(pid, suspend_progress_label)
    tree.item(selected_item, tags=('suspended',))
    tree.tag_configure('suspended', background='red')

def resume_this_only(tree):
    selected_item = tree.selection()[0]
    pid = int(tree.item(selected_item)['values'][0])
    resume_process(pid, resume_progress_label)
    tree.item(selected_item, tags=('running',))
    tree.tag_configure('running', background='white')

def create_process_monitor():
    root = tk.Tk()
    root.title("AppFreeze Control - jeffreygu0109@gmail.com")
    root.geometry("600x600")

    # Frame for buttons and progress labels
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)

    # Toggle Auto-Refresh Button
    toggle_button = tk.Button(button_frame, text="Toggle Auto Refresh", command=lambda: toggle_auto_refresh(tree))
    toggle_button.pack(side=tk.LEFT, padx=5)

    # Manual Refresh Button
    refresh_button = tk.Button(button_frame, text="Manual Refresh", command=lambda: manual_refresh(tree))
    refresh_button.pack(side=tk.LEFT, padx=5)

    # Suspend Progress Label
    global suspend_progress_label
    suspend_progress_label = tk.Label(button_frame, text="Suspend: 0%")
    suspend_progress_label.pack(side=tk.LEFT, padx=10)

    # Resume Progress Label
    global resume_progress_label
    resume_progress_label = tk.Label(button_frame, text="Resume: 0%")
    resume_progress_label.pack(side=tk.LEFT, padx=10)

    # Columns for the Treeview
    columns = ("PID",)

    tree = ttk.Treeview(root, columns=columns, show="tree headings")
    tree.pack(fill=tk.BOTH, expand=True)

    # Define column headings
    tree.heading("#0", text="Process Name", anchor=tk.W)
    tree.column("#0", width=250)
    tree.heading("PID", text="PID")
    tree.column("PID", anchor=tk.W, width=100)

    # Bind right-click event
    tree.bind("<Button-3>", lambda event: on_right_click(event, tree))

    # Initial update without auto-refresh
    update_tree(tree)

    root.mainloop()

if __name__ == "__main__":
    create_process_monitor()
