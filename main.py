
import os
import hashlib
import threading
from tkinter import *
from tkinter import filedialog, messagebox
from send2trash import send2trash

duplicates = []
scan_thread = None

# ---------- HASH ----------
def get_hash(path):
    h = hashlib.md5()

    try:
        with open(path, 'rb') as f:
            while chunk := f.read(4096):
                h.update(chunk)

        return h.hexdigest()

    except:
        return None


# ---------- STATUS ----------
def set_busy(busy):
    status_var.set("Scanning..." if busy else "Ready")
    state = DISABLED if busy else NORMAL

    scan_btn.config(state=state)
    delete_btn.config(state=state)


# ---------- SHOW RESULTS ----------
def show_results():

    result_box.delete(0, END)

    if not duplicates:
        result_box.insert(END, "No duplicates found")
        return

    for group in duplicates:

        result_box.insert(END, "---- Duplicate Group ----")
        result_box.insert(END, f"✔ KEEP: {group[0]}")
        result_box.insert(END, "❌ DUPLICATES:")

        for file in group[1:]:

            try:
                size = os.path.getsize(file) // 1024
                result_box.insert(END, f"{file} ({size} KB)")

            except:
                result_box.insert(END, file)

        result_box.insert(END, "")


# ---------- SCAN ----------
def scan_folder(folder):

    global duplicates

    root.after(0, lambda: set_busy(True))
    size_map = {}
    duplicates = []

    # group by size
    for root_dir, _, files in os.walk(folder):

        for name in files:

            if ext := file_type.get().lower().strip():
                if not name.lower().endswith(ext):
                    continue

            path = os.path.join(root_dir, name)

            try:
                size_map.setdefault(os.path.getsize(path), []).append(path)

            except:
                pass

    # compare hash
    for files in size_map.values():

        if len(files) < 2:
            continue

        hash_map = {}

        for path in files:

            h = get_hash(path)

            if h:
                hash_map.setdefault(h, []).append(path)

        for group in hash_map.values():

            if len(group) > 1:

                # keep original file first
                group.sort(
                    key=lambda x: (
                        "copy" in os.path.basename(x).lower(),
                        "(" in os.path.basename(x)
                    )
                )

                duplicates.append(group)

    root.after(0, show_results)
    root.after(0, lambda: set_busy(False))


# ---------- START SCAN ----------
def start_scan():

    global scan_thread

    folder = filedialog.askdirectory()

    if not folder:
        return

    if scan_thread and scan_thread.is_alive():
        return

    scan_thread = threading.Thread(
        target=scan_folder,
        args=(folder,),
        daemon=True
    )

    scan_thread.start()


# ---------- DELETE ----------
def delete_duplicates():

    global duplicates

    if not duplicates:
        messagebox.showinfo("Info", "No duplicates found")
        return

    if not messagebox.askyesno(
        "Confirm",
        "Delete duplicate files?"
    ):
        return

    deleted = 0

    for group in duplicates:

        for file in group[1:]:

            try:
                send2trash(os.path.normpath(file))
                deleted += 1

            except Exception as e:
                print("Error:", e)

    if deleted > 0:

        messagebox.showinfo(
            "Done",
            f"{deleted} duplicate files moved to Recycle Bin"
        )

        duplicates.clear()
        result_box.delete(0, END)

    else:

        messagebox.showerror(
            "Error",
            "Unable to delete duplicate files"
        )

# ---------- GUI ----------
root = Tk()

root.title("Duplicate File Detector")
root.geometry("700x500")
root.configure(bg="white")

# header
top = Frame(root, bg="white")
top.pack(fill=X, padx=15, pady=10)

Label(
    top,
    text="Duplicate File Detector",
    font=("Arial", 20, "bold"),
    bg="white"
).pack(anchor=W)

Label(
    top,
    text="File type (e.g. .jpg, .pdf). Leave empty for all:",
    bg="white"
).pack(anchor=W, pady=(10, 5))

file_type = Entry(top, font=("Arial", 11))
file_type.pack(fill=X)

# buttons
btn_frame = Frame(root, bg="white")
btn_frame.pack(fill=X, padx=15, pady=10)

scan_btn = Button(
    btn_frame,
    text="Select Folder & Scan",
    command=start_scan
)

scan_btn.pack(side=LEFT, padx=(0, 10))

delete_btn = Button(
    btn_frame,
    text="Delete Duplicates",
    command=delete_duplicates
)

delete_btn.pack(side=LEFT)

# status
status_var = StringVar(value="Ready")

Label(
    root,
    textvariable=status_var,
    bg="white",
    fg="#444"
).pack(anchor=W, padx=15)

# results
frame = Frame(root)
frame.pack(fill=BOTH, expand=True, padx=15, pady=10)

scroll = Scrollbar(frame)
scroll.pack(side=RIGHT, fill=Y)

result_box = Listbox(
    frame,
    width=100,
    height=20,
    font=("Consolas", 10),
    yscrollcommand=scroll.set
)

result_box.pack(side=LEFT, fill=BOTH, expand=True)
scroll.config(command=result_box.yview)

root.mainloop()

