import enum
import subprocess
import tkinter as tk
import tkinter.filedialog
from pathlib import Path
from tkinter import ttk
from typing import Any, Optional

import click
import pdf2image

try:
    import ImageTk
except ImportError:
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
        # self.master = master
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

        # self.bind("<ButtonRelease-1>", lambda _: self.draw(self.canvas))

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
            self._item_id = self.canvas.create_line(*coords, tags=("scale"))
        else:
            self.canvas.coords(self._item_id, *coords)


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
        _path: str | None = tk.filedialog.askopenfilename(
            parent=self, initialdir=init_dir, filetypes=[("pdf", "*.pdf")]
        )

        if _path is None and self.path is not None:
            return self.path
        elif _path is None:
            raise NoPdfSelectedError

        path = Path(_path)

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
        name = tk.StringVar()
        profiles = tk.Variable(master, [p.name for p in self._config["profiles"]])

        self.profiles = tk.Listbox(master, listvariable=profiles)
        self.profiles.grid(row=3, column=0, sticky=tk.SW)
        self.profiles.bind("<<ListboxSelect>>", lambda _: self.apply_profile(name))
        self.profiles.selection_set(self._config["last_profile"])
        self.profiles.activate(self._config["last_profile"])

        button_new = ttk.Button(master, text="New profile")
        button_new.grid(row=4, column=0, sticky=tk.E + tk.W)
        button_new.bind("<Button-1>", lambda _: self.add_new_profile())
        button_new.bind("<Return>", lambda _: self.add_new_profile())

        entry_rename = ttk.Entry(master, textvariable=name, width=4)
        entry_rename.grid(row=5, column=0, sticky=tk.E + tk.W)
        entry_rename.bind("<Return>", lambda _: self.rename_profile(name))

        button_rename = ttk.Button(master, text="Rename profile")
        button_rename.grid(row=6, column=0, sticky=tk.E + tk.W)
        button_rename.bind("<Button-1>", lambda _: self.rename_profile(name))
        button_rename.bind("<Return>", lambda _: self.rename_profile(name))

        button_save = ttk.Button(master, text="Save profile")
        button_save.grid(row=7, column=0, sticky=tk.E + tk.W)
        button_save.bind("<Button-1>", lambda _: self.save_profile())
        button_save.bind("<Return>", lambda _: self.save_profile())

        button_delete = ttk.Button(master, text="Delete profile")
        button_delete.grid(row=8, column=0, sticky=tk.E + tk.W)
        button_delete.bind("<Button-1>", lambda _: self.delete_profile())
        button_delete.bind("<Return>", lambda _: self.delete_profile())

        self.apply_profile(name)

    def apply_profile(self, name: tk.StringVar):
        selection = self.profiles.curselection()
        if len(selection) == 0:
            return

        idx = selection[0]
        self._config["last_profile"] = idx

        profile = self._config["profiles"][idx]

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

        name.set(profile.name)

    def add_new_profile(self):
        profile = Profile("<new>")
        self.profiles.insert(tk.END, profile)
        self._config["profiles"].append(profile)

        self._config.save()

    def delete_profile(self):
        selection = self.profiles.curselection()
        if len(selection) == 0:
            return

        idx = selection[0]
        del self._config["profiles"][idx]
        self.profiles.delete(idx)

        self._config.save()

    def rename_profile(self, name: tk.StringVar):
        _name = name.get()
        if _name == "":
            return

        selection = self.profiles.curselection()
        if len(selection) == 0:
            return

        idx = selection[0]
        self._config["profiles"][idx].name = _name
        self.profiles.delete(idx)
        self.profiles.insert(idx, self._config["profiles"][idx])

        self._config.save()

    def save_profile(self):
        selection = self.profiles.curselection()
        if len(selection) == 0:
            return

        idx = selection[0]
        profile = self._config["profiles"][idx]

        profile.skip_first_page = self.skip_first_page.get()
        profile.many_cols = self.many_cols.get()
        profile.color = self.color.get()

        profile.leftmargin = self.scale_left.get()
        profile.rightmargin = self.scale_right.get()
        profile.topmargin = self.scale_top.get()
        profile.bottommargin = self.scale_bottom.get()

        self._config.save()

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
        return
    myapp.mainloop()
