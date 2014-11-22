from tkinter import * # ui library
from tkinter import ttk # themed ui components that match the OS
import math

import tkinter_png as png # png library for TKinter

class Item:
    "An item on the panel."
    __slots__ = ('name', 'shortName', 'longName', 'icon', 'desc', 'author', 'button', 'win')
    def __init__(
            self,
            name, 
            shortName, 
            longName = None,
            icon = '_blank', 
            author = '',
            desc = ""):
        self.name = name
        self.shortName = shortName
        self.longName = shortName if longName is None else longName
        self.icon = png.loadIcon(icon)
        self.desc = desc
        self.author = author


class selWin: 
    "The selection window for skyboxes, music, goo and voice packs."
    def __init__(self, tk, lst, has_none=True, none_desc='Do not add anything.', title='BEE2'):
        self.noneItem = Item('NONE', '', desc=none_desc)
        self.noneItem.icon = png.loadPng('none')
        self.disp_label = StringVar()
        self.chosen_id = ''
        self.suggested = None
        if has_none:
            self.item_list = [self.noneItem] + lst
        else:
            self.item_list = lst
        self.selected = self.item_list[0]
        self.orig_selected = self.selected
        self.parent = tk
        
        self.win=Toplevel(tk)
        self.win.withdraw()
        self.win.title("BEE2 - " + title)
        self.win.transient(master=tk)
        self.win.resizable(True, True)
        self.win.iconbitmap('BEE2.ico')
        self.win.protocol("WM_DELETE_WINDOW", lambda s=self: s.exit())
        self.win.bind("<Escape>",lambda e, s=self: s.exit())
        
        self.wid = {}
        shim = ttk.Frame(self.win, relief="sunken")
        shim.grid(row=0, column=0, sticky="NSEW")
        self.win.rowconfigure(0, weight=1)
        self.win.columnconfigure(0, weight=1)
        shim.rowconfigure(0, weight=1)
        shim.columnconfigure(0, weight=1)
        
        self.wid_canvas = Canvas(shim, highlightthickness=0)
        self.wid_canvas.grid(row=0, column=0, sticky="NSEW") # need to use a canvas to allow scrolling

        self.pal_frame=ttk.Frame(self.wid_canvas) # add another frame inside to place labels on
        self.wid_canvas.create_window(1, 1, window=self.pal_frame, anchor="nw")
        
        self.wid_scroll = ttk.Scrollbar(shim, orient=VERTICAL, command=self.wid_canvas.yview)
        self.wid_scroll.grid(row=0, column=1, sticky="NS")
        self.wid_canvas['yscrollcommand'] = self.wid_scroll.set
        
        self.sugg_lbl = ttk.LabelFrame(self.pal_frame, text="Suggested", labelanchor=N, height=50)
        
        self.prop_frm = ttk.Frame(self.win, borderwidth=4, relief='raised')
        self.prop_frm.grid(row=0, column=1, sticky="NSEW")
        
        self.prop_icon_frm = ttk.Frame(self.prop_frm, borderwidth=4, relief='raised', width=64, height=64)
        self.prop_icon_frm.grid(row=0, column=0, columnspan=4)
        
        self.prop_icon = ttk.Label(self.prop_icon_frm)
        self.prop_icon.img = png.loadIcon('faithplate_128')
        self.prop_icon['image'] = self.prop_icon.img
        self.prop_icon.grid(row=0, column = 0)
        
        self.prop_name = ttk.Label(self.prop_frm, text="Item", justify=CENTER, font=("Helvetica", 12, "bold"))
        self.prop_name.grid(row=1, column = 0, columnspan=4)
        self.prop_author = ttk.Label(self.prop_frm, text="Author")
        self.prop_author.grid(row=2, column = 0, columnspan=4)
        
        self.prop_desc_frm = ttk.Frame(self.prop_frm, relief="sunken")
        self.prop_desc_frm.grid(row=4, column=0, columnspan=4, sticky="NSEW")
        self.prop_desc_frm.rowconfigure(0, weight=1)
        self.prop_desc_frm.columnconfigure(0, weight=1)
        self.prop_frm.rowconfigure(4, weight=1)
        
        self.prop_desc = Text(self.prop_desc_frm, width=19, height=8, wrap="word", font="TkSmallCaptionFont")
        self.prop_desc.grid(row=0, column=0, padx=(2,0), pady=2, sticky="NSEW")
        self.prop_desc['state']="disabled"
        
        self.prop_scroll = ttk.Scrollbar(self.prop_desc_frm, orient=VERTICAL, command=self.prop_desc.yview)
        self.prop_scroll.grid(row=0, column=1, sticky="NS", padx=(0,2), pady=2)
        self.prop_desc['yscrollcommand'] = self.prop_scroll.set
        
        self.prop_reset = ttk.Button(self.prop_frm, text = "Reset to Default", command = lambda obj=self: obj.reset_sel())
        self.prop_reset.grid(row=5, column=0, columnspan=4, sticky = "EW", padx=8, pady=(8,1))
        
        self.prop_ok = ttk.Button(self.prop_frm, text = "OK", command = lambda obj=self: obj.save())
        self.prop_cancel = ttk.Button(self.prop_frm, text = "Cancel", command = lambda obj=self: obj.exit())
        
        self.prop_ok.grid(row=6, column=0, padx=(8,16))
        self.prop_cancel.grid(row=6, column=2, padx=(16,8))
        ttk.Sizegrip(self.prop_frm).grid(row=6, column=3, sticky="SE")
        
        for item in self.item_list:
            if item==self.noneItem:
                item.button = ttk.Button(self.pal_frame, image=item.icon)
            else:
                item.button = ttk.Button(self.pal_frame, text=item.shortName, image=item.icon, compound='top')
            item.win = self.win
            item.button.bind("<Button-1>",lambda e, s=self, i=item: s.sel_item(i))
            item.button.bind("<Double-Button-1>",lambda e, s=self: s.save())
        self.flow_items(None)
        self.wid_canvas.bind("<Configure>",lambda e, s=self: s.flow_items(e))
        
    def init_display(self, frame, row=0, column=0, colspan=1, rowspan=1):
        '''Create and grid() the label used to open the selector window.'''
        self.display = ttk.Label(frame, textvariable=self.disp_label, width=10, relief="sunken")
        self.display.grid(row=row, column=column, columnspan=colspan, rowspan=rowspan, sticky="EW")
        self.display.bind("<Button-1>", lambda e, s=self: s.open_win())
        self.save()
        
    def exit(self):
        "Quit and cancel."
        self.sel_item(self.orig_selected)
        self.save()
        
    def save(self):
        "Save the selected item into the textbox."
        self.win.grab_release()
        self.win.withdraw()
        if self.selected == self.noneItem:
            self.disp_label.set("<None>")
            self.chosen_id = None
        else:
            self.disp_label.set(self.selected.shortName)
            self.chosen_id = self.selected.name
            
    def open_win(self):
        self.win.deiconify()
        self.win.lift(self.parent)
        self.win.grab_set()
        self.win.geometry('+'+str(self.parent.winfo_rootx()+30)+'+'+str(self.parent.winfo_rooty()+30))
        self.sel_item(self.selected)
        
    def reset_sel(self):
        if self.suggested is not None:
            self.sel_item(self.suggested)
        
    def sel_item(self, item):
        self.prop_name['text'] = item.longName
        if item.author == '':
            self.prop_author['text'] = ''
        elif ',' in item.author:
            self.prop_author['text'] = 'Authors: ' + item.author
        else:
            self.prop_author['text'] = 'Author: ' + item.author
        self.prop_icon['image'] = item.icon
        
        self.prop_desc['state']="normal"
        self.prop_desc.delete(1.0, END)
        self.prop_desc.insert("end", item.desc) 
        self.prop_desc['state']="disabled"
        
        self.selected.button.state(('!alternate',))
        self.selected = item
        item.button.state(('alternate',))
        
        if self.suggested is None or self.selected == self.suggested:
            self.prop_reset.state(('disabled',))
        else:
            self.prop_reset.state(('!disabled',))
    
    def flow_items(self, e):
        self.pal_frame.update_idletasks()
        self.pal_frame['width']=self.wid_canvas.winfo_width()
        self.prop_name['wraplength'] = self.prop_desc.winfo_width()
        width=(self.wid_canvas.winfo_width()-10) // 80
        if width <1:
            width=1 # we got way too small, prevent division by zero
        itemNum=len(self.item_list)
        self.wid_canvas['scrollregion'] = (0, 0, width*80, math.ceil(itemNum/width)*115+20)
        self.pal_frame['height']=(math.ceil(itemNum/width)*115+20)
        for i,item in enumerate(self.item_list):
            if item == self.suggested:
                self.sugg_lbl.place(x=((i%width) *80+1),y=((i//width)*115))
                self.sugg_lbl['width'] = item.button.winfo_width()
            item.button.place(x=((i%width) *80+1),y=((i//width)*115+20))
            item.button.lift()
            
        
    def set_suggested(self, suggested):
        for item in self.item_list:
            if item.name == suggested:
                self.suggested=item

if __name__ == '__main__': # test the window if directly executing this file
    root=Tk()
    lbl = ttk.Label(root, text="I am a demo window.")
    lbl.grid()
    png.img_error=png.loadIcon('_error') # If image is not readable, use this instead
    root.geometry("+500+500")
    lst = [
        Item(
            "SKY_BLACK", 
            "Black", 
            longName = "Darkness", 
            icon = "faithplate_128",
            author = "Valve",
            desc = 'Pure black darkness. Nothing to see here.'),
        Item(
            "SKY_BTS", 
            "BTS", 
            longName = "Behind The Scenes - Factory", 
            icon = "faithplate_128",
            author = "TeamSpen210",
            desc = 'The dark constuction and office areas of Aperture. Catwalks '
                   'extend between different buildings, with vactubes and cranes '
                   'carrying objects throughout the facility. Abandoned offices can '
                   'often be found here.')
          ]
        
    def done(x):
        print(x)
        root.withdraw()
    window = selWin(root, lst, has_none=True, none_desc='Pure blackness. Nothing to see here.')
    window.init_display(root, 1, 0)
    window.set_suggested("SKY_BLACK")