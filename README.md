journal2ebook
=============

![A screenshot of journal2ebook in action](./img/screenshot.png)

Graphical application to convert academic pdfs to epub format for e-readers using
k2pdfopt as a backend.

The GUI allows you to visualize your PDF and draw appropriate margins that will be
passed to k2pdfopt. The resulting pdf file is output to the folder of your choice. There
is also functionality to save and recall journal profiles that store margin values.

This program should work cross-platform (Linux, Mac, and Windows) though it has
been most extensively tested with Linux. The Windows executable is usually behind in
features, but is the most recent version that has been tested in Windows. We do not
currently test on Mac.

The dependencies listed in the following sections must also be met.

Requirements
------------
* Python 3.9 or higher
* `k2pdfopt` to convert pdf to epub
* `tkinter`

`k2pdfopt` must be in your system's search PATH (or installed to the journal2ebook directory).

You can check if `tkinter` is properly installed by running `python -m tkinter`. This
command should spawn a smaller window with tkinter's version. If this is not the case,
you might not have tkinter installed and you probably have to run something like
```
sudo apt install python3-tk
```

Installation
------------

1. clone git repository
2. run `pip install .` from the root directory
3. run `journal2ebook` to run

Development
----------

For the development of `journal2ebook`, we use `pre-commit` to lint the project and enforce a consistent code style.

To get started, install the project in development mode
```bash
pip install -e ".[develop]"
```
and, afterwards, install the pre-commit hooks via
```bash
pre-commit install
```
Now, every time you try to commit a change, the pre-commit hooks run and tell you any issues the linters found.
You can also run them manually via
```bash
pre-commit run --all
```

Finally, if your IDE supports lsp-servers and is configured properly, you should see all linter errors in your IDE. Happy coding!
