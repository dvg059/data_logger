#!/usr/bin/python

# myscrolledwindow.py
## this is a scrolled window for 

import wx
image_file = "truss_page.jpeg"
DRAG_SOURCE    = wx.NewId()


import wx

def SetDcContext( memDC, font=None, color=None ):
    if font:
        memDC.SetFont( font )
    else:
        memDC.SetFont( wx.NullFont )

    if color:
        memDC.SetTextForeground( color )



def WriteTextOnBitmap( text, bitmap, pos=(0, 0), font=None, color=None) :
    """
    Simple write into a bitmap doesn't do any checking.
    """
    memDC = wx.MemoryDC()
    SetDcContext( memDC, font, color )
    memDC.SelectObject( bitmap )
    try:
        memDC.DrawText( text, pos[0], pos[1])
    except :
        pass

    memDC.SelectObject( wx.NullBitmap )

    return bitmap



class TextDropTarget(wx.TextDropTarget):
    """ This object implements Drop Target functionality for Text """
    def __init__(self, obj):
        """ Initialize the Drop Target, passing in the Object Reference to
          indicate what should receive the dropped text """
        # Initialize the wx.TextDropTarget Object
        wx.TextDropTarget.__init__(self)
        # Store the Object Reference for dropped text
        self.obj = obj

    def OnDropText(self, x, y, data):
        """ Implement Text Drop """
        # When text is dropped, write it into the object specified
        self.obj.WriteText(data + '\n\n')

class MyScrolledWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(500, 400))

        sw = wx.ScrolledWindow(self)
        bmp = wx.Image(image_file,wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        wx.StaticBitmap(sw, -1, bmp)
        sw.SetScrollbars(20,20,55,40)
        

class MyApp(wx.App):
   def OnInit(self):
       frame = MyScrolledWindow(None, -1, image_file)
       frame.Show(True)
       frame.Centre()
       return True

#app = MyApp(0)
#app.MainLoop()
