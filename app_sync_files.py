import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
import re
import os
import shutil
import hashlib

# ============================================================
# CONFIG
# ============================================================

STAGES = [
    "VC",
    "PT1",
    "PTB1",
    "PTB2",
    "VP",
    "M1"
]

DATE_PATTERN = re.compile(r"(\d{2}\.\d{2}\.\d{4})")

vehicles_db = {}

# ============================================================
# HELPERS
# ============================================================

def log(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    root.update_idletasks()


def clear_log():
    log_box.delete("1.0", tk.END)


# ============================================================
# BROWSE
# ============================================================

def browse_source():
    folder = filedialog.askdirectory()

    if folder:
        source_var.set(folder)


def browse_destination():
    folder = filedialog.askdirectory()

    if folder:
        destination_var.set(folder)


# ============================================================
# VEHICLE PARSER
# ============================================================

def extract_vehicle_info(folder_name):

    normalized = (
        folder_name.upper()
        .replace("_", " ")
        .replace("-", " ")
    )

    parts = normalized.upper().split()

    body = None
    stage = None
    sv = None

    for item in parts:

        if item in STAGES:
            stage = item
            break

    if not stage:
        return None

    stage_index = parts.index(stage)

    if stage_index > 0:
        body = parts[0]

    for item in parts[stage_index + 1:]:


        if item.isdigit():

            sv = item
            break

    if not body:
        return None

    if not stage:
        return None

    if not sv:
        return None

    return body, stage, sv


# ============================================================
# POWERTRAIN
# ============================================================

def classify_powertrain(folder_name):

    name = folder_name.upper()

    if "HR16" in name:
        return "HEV"

    if "HR18" in name:
        return "HEV"

    return "ICE"


# ============================================================
# LPG
# ============================================================

def classify_lpg(folder_name):

    name = folder_name.upper()

    if "LPG" in name:
        return "LPG"

    return "NON_LPG"


# ============================================================
# DATE
# ============================================================

def extract_date(full_path):

    match = DATE_PATTERN.search(full_path)

    if match:
        return match.group(1)

    return None


# ============================================================
# SCAN
# ============================================================

def scan_folders():

    global vehicles_db

    vehicles_db = {}

    source = source_var.get().strip()

    if not source:

        messagebox.showerror(
            "Error",
            "Select source folder first"
        )

        return

    clear_log()

    root_folder = Path(source)

    folders_scanned = 0
    vehicle_matches = 0

    hev_count = 0
    ice_count = 0

    lpg_count = 0
    non_lpg_count = 0

    log("Starting scan...\n")

    for folder in root_folder.rglob("*"):

        if not folder.is_dir():
            continue

        folders_scanned += 1

        vehicle_info = extract_vehicle_info(folder.name)

        if not vehicle_info:
            continue

        date_found = extract_date(str(folder))

        if not date_found:
            continue

        body, stage, sv = vehicle_info

        powertrain = classify_powertrain(folder.name)

        lpg_type = classify_lpg(folder.name)

        if powertrain == "HEV":
            hev_count += 1
        else:
            ice_count += 1

        if lpg_type == "LPG":
            lpg_count += 1
        else:
            non_lpg_count += 1

        vehicle_key = (
            body,
            stage,
            sv
        )

        if vehicle_key not in vehicles_db:

            vehicles_db[vehicle_key] = {
                "powertrain": powertrain,
                "lpg": lpg_type,
                "dates": [],
                "folders": []
            }

        else:

            if lpg_type == "LPG":
                vehicles_db[vehicle_key]["lpg"] = "LPG"

        vehicles_db[vehicle_key]["dates"].append(
            date_found
        )

        vehicles_db[vehicle_key]["folders"].append(
            str(folder)
        )

        vehicle_matches += 1

    unique_vehicles = len(vehicles_db)

    log("========== SCAN RESULT ==========\n")

    log(
        f"Folders scanned : {folders_scanned}"
    )

    log(
        f"Vehicle folders : {vehicle_matches}"
    )

    log(
        f"Unique vehicles : {unique_vehicles}"
    )

    log("")

    log(f"HEV : {hev_count}")
    log(f"ICE : {ice_count}")

    log("")

    log(f"LPG     : {lpg_count}")
    log(f"NON LPG : {non_lpg_count}")

    log("\n========== VEHICLES ==========\n")

    for key, value in sorted(vehicles_db.items()):

        body, stage, sv = key

        log(
            f"{body} | "
            f"{stage} | "
            f"{sv} | "
            f"{value['powertrain']} | "
            f"{value['lpg']} | "
            f"Interventions: "
            f"{len(value['dates'])}"
        )

# ============================================================
# PLACEHOLDER SYNC
# ============================================================

def sync_folders():

    messagebox.showinfo(
        "Info",
        "SYNC logic will be added in Part 2"
    )

import shutil
import hashlib

# ============================================================
# HASH
# ============================================================

def get_file_hash(filepath):

    sha = hashlib.sha256()

    try:

        with open(filepath, "rb") as f:

            while True:

                chunk = f.read(8192)

                if not chunk:
                    break

                sha.update(chunk)

        return sha.hexdigest()

    except:
        return None

# ============================================================
# COPY
# ============================================================

def copy_folder_content(src_folder, dst_folder):

    copied = 0
    skipped = 0

    src_folder = Path(src_folder)
    dst_folder = Path(dst_folder)

    for item in src_folder.iterdir():

        target = dst_folder / item.name

        if item.is_dir():

            shutil.copytree(
                item,
                target,
                dirs_exist_ok=True
            )

        else:

            if target.exists():

                src_hash = get_file_hash(item)
                dst_hash = get_file_hash(target)

                if src_hash and dst_hash:

                    if src_hash == dst_hash:

                        skipped += 1
                        continue

            shutil.copy2(
                item,
                target
            )

            copied += 1

    return copied, skipped

# ============================================================
# DATE SORT
# ============================================================

def sort_dates(date_list):

    parsed = []

    for d in date_list:

        try:

            parsed.append(
                datetime.strptime(
                    d,
                    "%d.%m.%Y"
                )
            )

        except:
            pass

    parsed.sort()

    return parsed

# ============================================================
# SYNC
# ============================================================

def sync_folders():

    global vehicles_db

    destination = destination_var.get().strip()

    if not destination:

        messagebox.showerror(
            "Error",
            "Select destination folder"
        )

        return

    if not vehicles_db:

        messagebox.showerror(
            "Error",
            "Run SCAN first"
        )

        return

    copied_files = 0
    skipped_files = 0

    log("\n")
    log("========== SYNC START ==========\n")

    destination_root = Path(destination)

    for vehicle_key, vehicle_data in vehicles_db.items():

        body, stage, sv = vehicle_key

        powertrain = vehicle_data["powertrain"]
        lpg = vehicle_data["lpg"]

        if powertrain == "HEV":

            vehicle_root = (
                destination_root
                / "HEV"
                / body
                / stage
                / sv
            )

        else:

            vehicle_root = (
                destination_root
                / "ICE"
                / lpg
                / body
                / stage
                / sv
            )

        vehicle_root.mkdir(
            parents=True,
            exist_ok=True
        )

        interventions = []

        for index, date_string in enumerate(vehicle_data["dates"]):

            folder_source = vehicle_data["folders"][index]

            try:

                date_obj = datetime.strptime(
                    date_string,
                    "%d.%m.%Y"
                )

                interventions.append(
                    (
                        date_obj,
                        folder_source,
                        date_string
                    )
                )

            except:
                pass

        interventions.sort(
            key=lambda x: x[0]
        )

        for idx, entry in enumerate(interventions):

            date_obj, source_folder, date_string = entry

            intervention_name = (
                f"{idx:02d}. "
                f"{date_string}"
            )

            intervention_folder = (
                vehicle_root /
                intervention_name
            )

            intervention_folder.mkdir(
                exist_ok=True
            )

            copied, skipped = copy_folder_content(
                source_folder,
                intervention_folder
            )

            copied_files += copied
            skipped_files += skipped

        log(
            f"[SYNC] "
            f"{body} -> "
            f"{stage} -> "
            f"{sv}"
        )

    log("")
    log("=" * 50)
    log(
        f"Files copied : "
        f"{copied_files}"
    )

    log(
        f"Files skipped : "
        f"{skipped_files}"
    )

    log("=" * 50)

    messagebox.showinfo(
        "Finished",
        "Synchronization completed"
    )

# ============================================================
# GUI
# ============================================================

root = tk.Tk()

root.title(
    "Vehicle Sync Tool"
)

root.geometry(
    "1100x700"
)

source_var = tk.StringVar()
destination_var = tk.StringVar()

title = tk.Label(
    root,
    text="Vehicle Sync Tool",
    font=(
        "Segoe UI",
        18,
        "bold"
    )
)

title.pack(
    pady=10
)

# SOURCE

frame_source = tk.Frame(root)

frame_source.pack(
    fill="x",
    padx=10,
    pady=5
)

tk.Label(
    frame_source,
    text="Source Folder:"
).pack(
    side="left"
)

tk.Entry(
    frame_source,
    textvariable=source_var
).pack(
    side="left",
    fill="x",
    expand=True,
    padx=5
)

tk.Button(
    frame_source,
    text="Browse",
    command=browse_source
).pack(
    side="left"
)

# DEST

frame_dest = tk.Frame(root)

frame_dest.pack(
    fill="x",
    padx=10,
    pady=5
)

tk.Label(
    frame_dest,
    text="Destination Folder:"
).pack(
    side="left"
)

tk.Entry(
    frame_dest,
    textvariable=destination_var
).pack(
    side="left",
    fill="x",
    expand=True,
    padx=5
)

tk.Button(
    frame_dest,
    text="Browse",
    command=browse_destination
).pack(
    side="left"
)

# BUTTONS

buttons_frame = tk.Frame(root)

buttons_frame.pack(
    pady=10
)

scan_button = tk.Button(
    buttons_frame,
    text="SCAN",
    width=20,
    bg="#2196F3",
    fg="white",
    command=scan_folders
)

scan_button.pack(
    side="left",
    padx=10
)

sync_button = tk.Button(
    buttons_frame,
    text="SYNC",
    width=20,
    bg="#4CAF50",
    fg="white",
    command=sync_folders
)

sync_button.pack(
    side="left",
    padx=10
)

# LOG

log_box = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD
)

log_box.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

root.mainloop()