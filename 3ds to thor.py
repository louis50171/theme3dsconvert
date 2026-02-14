import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import zipfile
import tempfile

# Résolutions corrigées
TOP_RESOLUTION = (1920, 1080)     # écran 6"
BOTTOM_RESOLUTION = (1240, 1080)  # écran 3,92"


def resize_and_crop(image_path, target_size):
    target_width, target_height = target_size
    img = Image.open(image_path)

    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return img.crop((left, top, right, bottom))


def truncate_path(path, max_len=50):
    if not path or len(path) <= max_len:
        return path
    return "..." + path[-(max_len - 3):]


def extract_3ds_theme(zip_path):
    """Extrait pt_top et pt_bottom depuis un ZIP de thème 3DS (ThemePlaza)."""
    top_path = None
    bottom_path = None
    tmp_dir = tempfile.mkdtemp(prefix="3ds_theme_")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        for name in names:
            basename = os.path.basename(name).lower()
            if basename.startswith("pt_top") and basename.endswith(".png"):
                zf.extract(name, tmp_dir)
                top_path = os.path.join(tmp_dir, name)
            elif basename.startswith("pt_bottom") and basename.endswith(".png"):
                zf.extract(name, tmp_dir)
                bottom_path = os.path.join(tmp_dir, name)

    return top_path, bottom_path


class AynThorWallpaperTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Ayn Thor Wallpaper Adapter")
        self.root.geometry("500x560")
        self.root.resizable(False, False)

        BG_COLOR = "#2b2b2b"
        FG_COLOR = "#e0e0e0"
        ACCENT = "#5c9eed"
        FRAME_BG = "#353535"
        PATH_FG = "#a0a0a0"
        IMPORT_COLOR = "#e8a035"

        self.root.configure(bg=BG_COLOR)

        self.top_image_path = None
        self.bottom_image_path = None
        self.output_folder = None
        self.imported_zip_name = None

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 16, "bold"))
        style.configure("Path.TLabel", background=FRAME_BG, foreground=PATH_FG, font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabelframe", background=FRAME_BG, foreground=FG_COLOR, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=BG_COLOR, foreground=ACCENT, font=("Segoe UI", 10, "bold"))
        style.configure("Generate.TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.map("Generate.TButton",
                  background=[("active", "#4a8bd4"), ("!active", ACCENT)],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("Import.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("Import.TButton",
                  background=[("active", "#c4882a"), ("!active", IMPORT_COLOR)],
                  foreground=[("active", "white"), ("!active", "white")])

        main_frame = ttk.Frame(root, padding=15)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Ayn Thor Wallpaper Adapter", style="Title.TLabel").pack(pady=(0, 10))

        # --- Import 3DS ---
        ttk.Button(
            main_frame,
            text="Importer un thème 3DS (.zip)",
            command=self.import_3ds_theme,
            style="Import.TButton"
        ).pack(fill="x", pady=(0, 4))
        self.zip_path_label = ttk.Label(main_frame, text="", style="Path.TLabel")
        self.zip_path_label.pack(anchor="w", fill="x", pady=(0, 10))

        sep = ttk.Separator(main_frame, orient="horizontal")
        sep.pack(fill="x", pady=(0, 10))

        # --- Écran Haut ---
        top_frame = ttk.LabelFrame(main_frame, text='Écran 6" (Haut) — 1920×1080', padding=10)
        top_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(top_frame, text="Parcourir...", command=self.load_top).pack(anchor="w")
        self.top_path_label = ttk.Label(top_frame, text="Aucun fichier sélectionné", style="Path.TLabel")
        self.top_path_label.pack(anchor="w", pady=(4, 0), fill="x")

        # --- Écran Bas ---
        bottom_frame = ttk.LabelFrame(main_frame, text='Écran 3.92" (Bas) — 1240×1080', padding=10)
        bottom_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(bottom_frame, text="Parcourir...", command=self.load_bottom).pack(anchor="w")
        self.bottom_path_label = ttk.Label(bottom_frame, text="Aucun fichier sélectionné", style="Path.TLabel")
        self.bottom_path_label.pack(anchor="w", pady=(4, 0), fill="x")

        # --- Dossier de sortie ---
        output_frame = ttk.LabelFrame(main_frame, text="Dossier de sortie", padding=10)
        output_frame.pack(fill="x", pady=(0, 15))

        ttk.Button(output_frame, text="Parcourir...", command=self.choose_output).pack(anchor="w")
        self.output_path_label = ttk.Label(output_frame, text="Aucun dossier sélectionné", style="Path.TLabel")
        self.output_path_label.pack(anchor="w", pady=(4, 0), fill="x")

        # --- Bouton Générer ---
        ttk.Button(
            main_frame,
            text="Générer les wallpapers",
            command=self.process_images,
            style="Generate.TButton"
        ).pack(pady=(5, 0), ipadx=20)

    def import_3ds_theme(self):
        zip_path = filedialog.askopenfilename(
            filetypes=[("Thème 3DS (ZIP)", "*.zip")]
        )
        if not zip_path:
            return

        try:
            top, bottom = extract_3ds_theme(zip_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le ZIP :\n{e}")
            return

        found = []
        if top:
            self.top_image_path = top
            self.top_path_label.configure(text=truncate_path(top))
            found.append("haut (pt_top)")
        if bottom:
            self.bottom_image_path = bottom
            self.bottom_path_label.configure(text=truncate_path(bottom))
            found.append("bas (pt_bottom)")

        zip_name = os.path.basename(zip_path)
        self.imported_zip_name = os.path.splitext(zip_name)[0]
        self.zip_path_label.configure(text=truncate_path(zip_path))

        if not found:
            messagebox.showwarning(
                "Import partiel",
                f"Aucune image pt_top/pt_bottom trouvée dans :\n{zip_name}"
            )
        elif len(found) == 2:
            messagebox.showinfo("Import réussi", f"Images détectées depuis :\n{zip_name}\n\n  - {found[0]}\n  - {found[1]}")
        else:
            messagebox.showwarning(
                "Import partiel",
                f"Seule l'image {found[0]} a été trouvée dans :\n{zip_name}"
            )

    def load_top(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.top_image_path = path
            self.top_path_label.configure(text=truncate_path(path))

    def load_bottom(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.bottom_image_path = path
            self.bottom_path_label.configure(text=truncate_path(path))

    def choose_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_folder = path
            self.output_path_label.configure(text=truncate_path(path))

    def process_images(self):
        if not self.top_image_path or not self.bottom_image_path or not self.output_folder:
            messagebox.showerror("Erreur", "Merci de sélectionner toutes les images et le dossier.")
            return

        try:
            output_dir = self.output_folder
            if self.imported_zip_name:
                output_dir = os.path.join(self.output_folder, self.imported_zip_name)
                os.makedirs(output_dir, exist_ok=True)

            top_wallpaper = resize_and_crop(self.top_image_path, TOP_RESOLUTION)
            bottom_wallpaper = resize_and_crop(self.bottom_image_path, BOTTOM_RESOLUTION)

            top_output = os.path.join(output_dir, "ayn_thor_top_1920x1080.png")
            bottom_output = os.path.join(output_dir, "ayn_thor_bottom_1240x1080.png")

            top_wallpaper.save(top_output)
            bottom_wallpaper.save(bottom_output)

            messagebox.showinfo("Succès", "Wallpapers générés avec succès !")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AynThorWallpaperTool(root)
    root.mainloop()
