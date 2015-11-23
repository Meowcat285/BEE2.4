from tkinter import simpledialog
import tk_tools


class StringDialog(simpledialog._QueryString):
    def body(self, master):
        super().body(master)
        tk_tools.set_icon(self)


def ask_string(title, prompt, **kargs):
    d = StringDialog(title, prompt, **kargs)
    return d.result

ask_string.__doc__ = simpledialog.askstring.__doc__