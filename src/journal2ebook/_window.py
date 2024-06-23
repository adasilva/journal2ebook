import enum
import subprocess
import tkinter as tk
import tkinter.filedialog
from pathlib import Path
from tkinter import ttk
from typing import Any, Optional

import click
import pdf2image
from PIL import ImageTk

from ._config import Config, Profile
from ._exceptions import NoPdfSelectedError

PADDING_BETWEEN_SLIDERS = 10
SLIDERLENGTH = 14
WINDOW_TITLE = "journal2ebook"


class Position(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()
    TOP = enum.auto()
    BOTTOM = enum.auto()


class Scale(tk.Scale):
    def __init__(self, master, *, position: Position):
        self.position = position

        if self.position in (Position.LEFT, Position.RIGHT):
            length = master.canvas.winfo_width()
            orient: Any = tk.HORIZONTAL
        else:
            length = master.canvas.winfo_height()
            orient = tk.VERTICAL

        if self.position in (Position.LEFT, Position.TOP):
            from_ = 0
            to = 0.5 - 0.5 * (PADDING_BETWEEN_SLIDERS + SLIDERLENGTH) / length
        else:
            from_ = 0.5 + 0.5 * (PADDING_BETWEEN_SLIDERS + SLIDERLENGTH) / length
            to = 1

        super().__init__(
            master,
            from_=from_,
            to=to,
            orient=orient,
            resolution=0.01,
            sliderlength=SLIDERLENGTH,
            length=length / 2.0,
            showvalue=False,
            command=lambda _: self.draw(),
        )

        self._item_id: Optional[int] = None

        if self.position == Position.LEFT:
            self.grid(row=0, column=1, sticky=tk.W)
            self.set(0.0)
        elif self.position == Position.RIGHT:
            self.grid(row=0, column=2, sticky=tk.E)
            self.set(1.0)
        elif self.position == Position.TOP:
            self.grid(row=1, column=0, sticky=tk.N)
            self.set(0.0)
        else:
            self.grid(row=2, column=0, sticky=tk.S)
            self.set(1.0)

    @property
    def canvas(self):
        return self.master.canvas  # type: ignore[attr-defined]

    def draw(self):
        if self.position in (Position.LEFT, Position.RIGHT):
            x_pos = self.get() * self.canvas.winfo_width()
            coords = (x_pos, 0, x_pos, self.canvas.winfo_height())
        else:
            y_pos = self.get() * self.canvas.winfo_height()
            coords = (0, y_pos, self.canvas.winfo_width(), y_pos)

        if self._item_id is None or self._item_id not in self.canvas.find_all():
            self._item_id = self.canvas.create_line(*coords, fill="red", tags=("scale"))
        else:
            self.canvas.coords(self._item_id, *coords)
            self.canvas.itemconfig(self._item_id, fill="red")


class App(ttk.Frame):
    canvas: Any
    page: tk.IntVar
    _max_pages: int
    path: Path

    scale_left: Scale
    scale_right: Scale
    scale_top: Scale
    scale_bottom: Scale

    profiles: Any

    _images: list[Any]

    width: int
    height: int

    def __init__(self, master, path: Path):
        super().__init__(master, padding=10)

        self._config = Config()

        self.current_profile_index = self._config["last_profile"]
        self.profile_name = tk.StringVar()
        self.is_editing_name = False  

        self.path = self.require_path(path)
        self.load_pdf()

        self.page = tk.IntVar(self, value=1)
        self.page.trace_add("write", self.draw_image)

        self.grid()
        self.init_menu()

        self.set_width_height()
        self.canvas = tk.Canvas(self, width=self.width, height=self.height)
        self.canvas.grid(
            row=1, column=1, columnspan=2, rowspan=2, sticky=tk.NW, padx=7, pady=7
        )
        self.draw_image()

        self.scale_left = Scale(self, position=Position.LEFT)
        self.scale_right = Scale(self, position=Position.RIGHT)
        self.scale_top = Scale(self, position=Position.TOP)
        self.scale_bottom = Scale(self, position=Position.BOTTOM)

        self.init_page_counter()

        self.skip_first_page = tk.BooleanVar(value=False)
        self.many_cols = tk.BooleanVar(value=False)
        self.color = tk.BooleanVar(value=False)
        self.init_extras()


    @property
    def num_pages(self) -> int:
        return len(self._images)

    def require_path(self, path: Path | None) -> Path:
        if path is not None:
            return path

        init_dir = self._config["last_dir"]
        maybe_path: str | tuple = tk.filedialog.askopenfilename(
            parent=self, initialdir=init_dir, filetypes=[("pdf", "*.pdf")]
        )

        if isinstance(maybe_path, tuple):
            if hasattr(self, "path"):
                return self.path
            raise NoPdfSelectedError

        path = Path(maybe_path)

        self._config["last_dir"] = path.parent.absolute()
        return path

    def load_pdf(self):
        self._images = pdf2image.convert_from_path(self.path)

    def set_width_height(self, height=600):
        img = self._images[self.page.get() - 1]
        aspect = img.size[0] / img.size[1]

        self.height = height
        self.width = int(height * aspect)

    def draw_image(self, *args):
        img = self._images[self.page.get() - 1]
        img = img.resize((self.width, self.height))

        self.img = ImageTk.PhotoImage(img)
        self.canvas.create_image(self.width / 2.0, self.height / 2.0, image=self.img)

        for _id in self.canvas.find_withtag("scale"):
            self.canvas.delete(_id)
        self.canvas.update()

    def open_pdf(self):
        self.path = self.require_path(None)
        self.load_pdf()
        self.set_width_height()
        self.page.set(1)
        self.draw_image()

        self.scale_left.draw()
        self.scale_right.draw()
        self.scale_top.draw()
        self.scale_bottom.draw()

    def init_menu(self):
        menu = tk.Menu(self)
        self.master.config(menu=menu)  # type: ignore[attr-defined]

        file_menu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF", command=self.open_pdf)
        file_menu.add_command(label="Convert PDF", command=self.convert)
        file_menu.add_command(label="Exit", command=self.master.destroy)

        about_menu = tk.Menu(menu)
        menu.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About journal2ebook")
        about_menu.add_command(label="About k2pdfopt")
        about_menu.add_command(label="Show config path")

    def init_page_counter(self):
        frame_page = ttk.Frame(self)
        frame_page.grid(row=3, column=1, columnspan=2)

        button_decrease = ttk.Button(frame_page)
        button_decrease.configure(text="<")
        button_decrease.grid(row=0, column=0, sticky=tk.W)
        button_decrease.bind("<Button-1>", self._decrease_page)

        button_increase = ttk.Button(frame_page)
        button_increase.configure(text=">")
        button_increase.grid(row=0, column=2, sticky=tk.E)
        button_increase.bind("<Button-1>", self._increase_page)

        entry_page = ttk.Entry(frame_page, textvariable=self.page, width=4)
        entry_page.grid(row=0, column=1)
        entry_page.bind("<Return>", lambda _: self.update())

    def init_extras(self):
        extras = ttk.Frame(self)
        extras.grid(row=1, column=3, rowspan=2, sticky=tk.N + tk.S)

        checkmark_skip_first = tk.Checkbutton(
            extras, text="Skip first page", variable=self.skip_first_page
        )
        checkmark_skip_first.grid(row=0, column=0, sticky=tk.NW)

        checkmark_extra_cols = tk.Checkbutton(
            extras, text="3 or 4 columns", variable=self.many_cols
        )
        checkmark_extra_cols.grid(row=1, column=0, sticky=tk.NW)

        checkmark_color = tk.Checkbutton(
            extras, text="color output", variable=self.color
        )
        checkmark_color.grid(row=2, column=0, sticky=tk.NW)

        # Profiles list box
        self.init_profiles(extras)

        # Quit and save buttons on the side
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=3, sticky=tk.S)

        button_new_file = ttk.Button(frame_buttons, text="Open file")
        button_new_file.grid(row=0, column=0, sticky=tk.E + tk.W)
        button_new_file.bind("<Button-1>", lambda _: self.open_pdf())
        button_new_file.bind("<Return>", lambda _: self.open_pdf())

        button_convert = ttk.Button(frame_buttons, text="Convert PDF")
        button_convert.grid(row=1, column=0, sticky=tk.E + tk.W)
        button_convert.focus_force()
        button_convert.bind("<Button-1>", lambda _: self.convert())
        button_convert.bind("<Return>", lambda _: self.convert())

        button_quit = ttk.Button(frame_buttons)
        button_quit.configure(text="Quit")
        button_quit.grid(row=2, column=0, sticky=tk.E + tk.W)
        button_quit.bind("<Button-1>", lambda _: self.master.destroy())
        button_quit.bind("<Return>", lambda _: self.master.destroy())

    def init_profiles(self, master):
        profiles = tk.Variable(master, [p.name for p in self._config["profiles"]])

        self.profiles = tk.Listbox(master, listvariable=profiles)
        self.profiles.grid(row=3, column=0, sticky=tk.SW)
        self.profiles.bind("<<ListboxSelect>>", self.on_profile_select)
        self.profiles.selection_set(self._config["last_profile"])
        self.profiles.activate(self._config["last_profile"])

        button_new = ttk.Button(master, text="New profile")
        button_new.grid(row=4, column=0, sticky=tk.E + tk.W)
        button_new.bind("<Button-1>", lambda _: self.add_new_profile())
        button_new.bind("<Return>", lambda _: self.add_new_profile())

        self.entry_rename = ttk.Entry(master, textvariable=self.profile_name)
        self.entry_rename.grid(row=5, column=0, sticky=tk.E + tk.W)
        self.entry_rename.bind("<FocusIn>", self.on_entry_focus_in)
        self.entry_rename.bind("<FocusOut>", self.on_entry_focus_out)

        button_rename = ttk.Button(master, text="Rename profile")
        button_rename.grid(row=6, column=0, sticky=tk.E + tk.W)
        button_rename.bind("<Button-1>", lambda _: self.rename_profile())
        button_rename.bind("<Return>", lambda _: self.rename_profile())

        button_save = ttk.Button(master, text="Save profile")
        button_save.grid(row=7, column=0, sticky=tk.E + tk.W)
        button_save.bind("<Button-1>", lambda _: self.save_profile())
        button_save.bind("<Return>", lambda _: self.save_profile())

        button_delete = ttk.Button(master, text="Delete profile")
        button_delete.grid(row=8, column=0, sticky=tk.E + tk.W)
        button_delete.bind("<Button-1>", lambda _: self.delete_profile())
        button_delete.bind("<Return>", lambda _: self.delete_profile())

        self.apply_profile(self._config["last_profile"])

    def add_new_profile(self):
        new_profile = Profile(f"New Profile {len(self._config['profiles']) + 1}")
        self._config["profiles"].append(new_profile)
        self.profiles.insert(tk.END, new_profile.name)
        new_index = len(self._config["profiles"]) - 1
        self.profiles.selection_clear(0, tk.END)
        self.profiles.selection_set(new_index)
        self.profiles.activate(new_index)
        self.current_profile_index = new_index
        self._config["last_profile"] = new_index
        self.apply_profile(new_index)
        self._config.save()
        print(f"Added new profile: {new_profile.name}, index: {new_index}")

    def delete_profile(self):
        if self.current_profile_index is None:
            print("No profile selected. Aborting delete.")
            return

        if len(self._config["profiles"]) <= 1:
            print("Cannot delete the last remaining profile.")
            return

        deleted_profile = self._config["profiles"].pop(self.current_profile_index)
        print(f"Deleted profile: {deleted_profile.name}")

        # Update the listbox
        self.profiles.delete(self.current_profile_index)

        # Adjust the current_profile_index
        if self.current_profile_index >= len(self._config["profiles"]):
            self.current_profile_index = len(self._config["profiles"]) - 1

        # Select the next available profile
        self.profiles.selection_clear(0, tk.END)
        self.profiles.selection_set(self.current_profile_index)
        self.profiles.activate(self.current_profile_index)

        # Apply the newly selected profile
        self.apply_profile(self.current_profile_index)

        # Update last_profile after deletion
        self._config["last_profile"] = self.current_profile_index
        self._config.save()
        print(f"Profile deleted. Current index: {self.current_profile_index}")

    def on_entry_focus_in(self, event):
        self.is_editing_name = True

    def on_entry_focus_out(self, event):
        self.is_editing_name = False

    def on_profile_select(self, event):
        selection = self.profiles.curselection()
        if selection:
            self.current_profile_index = selection[0]
            self._config["last_profile"] = self.current_profile_index
            self.apply_profile(self.current_profile_index)
            self._config.save()

    def apply_profile(self, index):
        if index is None:
            return

        self.current_profile_index = index
        self._config["last_profile"] = index
        profile = self._config["profiles"][index]

        self.skip_first_page.set(profile.skip_first_page)
        self.many_cols.set(profile.many_cols)
        self.color.set(profile.color)

        self.scale_left.set(profile.leftmargin)
        self.scale_right.set(profile.rightmargin)
        self.scale_top.set(profile.topmargin)
        self.scale_bottom.set(profile.bottommargin)

        self.scale_left.draw()
        self.scale_right.draw()
        self.scale_top.draw()
        self.scale_bottom.draw()

        if not self.is_editing_name:
            self.profile_name.set(profile.name)

        print(f"Applied profile: {profile.name}")  # Debug output
        print(f"Checkbox states: skip_first_page={profile.skip_first_page}, many_cols={profile.many_cols}, color={profile.color}")  # Debug output

        self._config.save()


    def save_profile(self):
        if self.current_profile_index is None:
            print("No profile selected. Aborting save.")
            return

        profile = self._config["profiles"][self.current_profile_index]

        # Update profile with current UI values
        profile.name = self.profile_name.get()
        profile.skip_first_page = self.skip_first_page.get()
        profile.many_cols = self.many_cols.get()
        profile.color = self.color.get()

        profile.leftmargin = self.scale_left.get()
        profile.rightmargin = self.scale_right.get()
        profile.topmargin = self.scale_top.get()
        profile.bottommargin = self.scale_bottom.get()

        print(f"Saving profile: {profile.name}")  # Debug output
        print(f"Checkbox states: skip_first_page={profile.skip_first_page}, many_cols={profile.many_cols}, color={profile.color}")  # Debug output
        print(f"Margins: left={profile.leftmargin}, right={profile.rightmargin}, top={profile.topmargin}, bottom={profile.bottommargin}")  # Debug output

        self._config.save()
        self.update_profiles_listbox()

# Ensure the correct profile remains selected
        self.profiles.selection_clear(0, tk.END)
        self.profiles.selection_set(self.current_profile_index)
        self.profiles.activate(self.current_profile_index)
        
        print(f"Profile saved successfully. Current index: {self.current_profile_index}")



    def rename_profile(self):
        new_name = self.profile_name.get()
        if not new_name:
            print("New name is empty. Aborting rename.")
            return

        if self.current_profile_index is None:
            print("No profile selected. Aborting rename.")
            return

        old_name = self._config["profiles"][self.current_profile_index].name
        self._config["profiles"][self.current_profile_index].name = new_name
        self.profiles.delete(self.current_profile_index)
        self.profiles.insert(self.current_profile_index, new_name)
        self.profiles.selection_set(self.current_profile_index)

        print(f"Renamed profile from '{old_name}' to '{new_name}'")  # Debug output
        self._config.save()
        self.update_profiles_listbox()



    def update_profiles_listbox(self):
        self.profiles.delete(0, tk.END)
        for profile in self._config["profiles"]:
            self.profiles.insert(tk.END, profile.name)
        
        # Ensure the current profile remains selected
        if self.current_profile_index is not None and 0 <= self.current_profile_index < self.profiles.size():
            self.profiles.selection_set(self.current_profile_index)
            self.profiles.activate(self.current_profile_index)

        print(f"Updated profiles listbox. Current profiles: {[p.name for p in self._config['profiles']]}")
        print(f"Current profile index: {self.current_profile_index}")

    def _increase_page(self, _):
        self.page.set(min(self.page.get() + 1, self.num_pages))

        self.scale_left.draw()
        self.scale_right.draw()
        self.scale_top.draw()
        self.scale_bottom.draw()

    def _decrease_page(self, _):
        self.page.set(max(1, self.page.get() - 1))

        self.scale_left.draw()
        self.scale_right.draw()
        self.scale_top.draw()
        self.scale_bottom.draw()

    def convert(self):
        args = [
            "k2pdfopt",
            "-x",
            "-c" if self.color.get() else "-c-",
            "-p",
            f"{self.skip_first_page.get() + 1}-{self.num_pages}",
            "-col",
            f"{2 + 2 * int(self.many_cols.get())}",
            "-ml",
            f"{8.5 * self.scale_left.get():.3f}",
            "-mr",
            f"{8.5 * (1 - self.scale_right.get()):.3f}",
            "-mt",
            f"{11 * self.scale_top.get():.3f}",
            "-mb",
            f"{11 * (1 - self.scale_bottom.get()):.3f}",
            "-ui-",
            "-o",
            f"{self.path.with_stem(self.path.stem + '_output')}",
            str(self.path),
        ]
        try:
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError:
            pass


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), required=False)
def main(path: Path):
    root = tk.Tk()
    root.wm_title("journal2ebook")
    try:
        myapp = App(root, path)
    except NoPdfSelectedError:
        msg = "No path to a pdf file was provided. Exiting..."
        raise SystemExit(msg)
    myapp.mainloop()
