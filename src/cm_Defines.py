#!/usr/bin/env python

import wx
APP_NAME = "CELLMATE"
COMP_NAME = "Motion Labratories"
APP_VERSION = "1.00"

##----------------------------------------
APP_DEBUG_FILE = "CMDBG.txt"
##----------------------------------------
LOADCELL_TON_2 = "2 Ton"
LOADCELL_TON_5 = "5 Ton"
NO_CONNECT_VALUE_2_TON = 10000
NO_CONNECT_VALUE_5_TON = 20000
MAX_2_TON_VALUE = 2000
MAX_5_TON_VALUE = 5000


USER_LEVEL = 0
ADMIN_LEVEL = 1
MAX_CELLS = 8   #max cells per hub
MAX_HUBS = 16

AllHubs_Id = wx.NewId()     #used win creating a window that shows all hubs


DEFAULT_LOG_LEVEL = 4
RELEASE_LOG_LEVEL = 10
#------
ENABLED = True
DISABLED = False
#----- New event messages

#---- Units --------
LBS     = wx.NewId() #pounds units
KG      = wx.NewId() #KG units

AddGroup_Id = wx.NewId()
RemoveGroup_Id = wx.NewId()

AddCellToGroup_Id = wx.NewId()
RemoveCellFromGroup_Id = wx.NewId()

BtnSave_Id = wx.NewId()
BtnCancel_Id = wx.NewId()
BtnExit_Id = wx.NewId()
#---------------------------

STATE_DISCONNECTED = wx.NewId()      #load cell is not connected or responding  
STATE_NO_COMMUNICATIONS = wx.NewId() #load cell is connceted but has no weight 
STATE_LESS_80 =     wx.NewId()
STATE_LESS_100 =    wx.NewId()       #load cell is bettween 80 and 100% of load
STATE_LESS_110 =    wx.NewId()       #load cell is bettween 100 and 110% of load


#---------------------------
#---- colors
GREEN =     wx.Colour(0,255,0)
GREEN1 =     wx.Colour(0,180,20)

RED =       wx.Colour(255,0,0)
RED1 =      wx.Colour(200,20,20)

BLUE =      wx.Colour(0,0,255)

YELLOW =    wx.Colour(255,255,0)

GREY  =     wx.Colour(135,135,135)
#----------------------------------------------

class ImagePanel(wx.Panel):
    def __init__(self, parent, win_id, image_file = 'motion.bmp'):
        # create the panel
        wx.Panel.__init__(self, parent, win_id)
        png = wx.Image(image_file, wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        #self.bitmap1 = wx.StaticBitmap(self, -1, img2, (0, 0))

        
        

 
class BackGroundPanel(wx.Panel):
    """class Panel1 creates a panel with an image on it, inherits wx.Panel
    sample use to put a bitmap on center panel
        pnl = BackGroundPanel(self.panel,wx.NewId(),"motion_2.bmp")
        pnl.SetSize((30,20))
        vrtSz.Add(pnl,0, wx.ALIGN_CENTER)   # spacer bettween logger and hub gui                              

    
    """
    def __init__(self, parent, win_id, image_file = 'motion.bmp', type=wx.BITMAP_TYPE_ANY):
        # create the panel
        wx.Panel.__init__(self, parent, win_id)
        try:
            # pick an image file you have in the working folder
            # you can load .jpg  .png  .bmp  or .gif files
            
            bmp1 = wx.Image(image_file, type).ConvertToBitmap()
            # image's upper left corner anchors at panel coordinates (0, 0)
            self.bitmap1 = wx.StaticBitmap(self, -1, bmp1, (0, 0))
            # show some image details
            str1 = "%s  %dx%d" % (image_file, bmp1.GetWidth(), bmp1.GetHeight()) 
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftDown)

            #parent.SetTitle(str1)
        except IOError:
            print "Image file %s not found" % image_file
            raise SystemExit
 
        # button goes on the image --> self.bitmap1 is the parent
        #self.button1 = wx.Button(self.bitmap1, id=-1, label='Button1', pos=(8, 8))

    def OnLeftDown(self, evt):
        print "----- OnLeftDown -----"
        
class LabelBorder(wx.Panel):
    def __init__(self, parent, win_id, label="Some Text",image_file = 'motion.bmp', font = 10):
        # create the panel
        wx.Panel.__init__(self, parent, win_id)
        bmp1 = wx.Image(image_file, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        # image's upper left corner anchors at panel coordinates (0, 0)
        self.bitmap1 = wx.StaticBitmap(self, -1, bmp1, (0, 0))

        bmp1 = wx.Image(image_file, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        # image's upper left corner anchors at panel coordinates (0, 0)
        self.bitmap2 = wx.StaticBitmap(self, -1, bmp1, (0, 0))

        self.bitmap1.SetSize((20,30))
        self.bitmap2.SetSize((20,30))
            # button goes on the image --> self.bitmap1 is the parent
   
        self.label = wx.TextCtrl(self,-1, label, wx.Point(0, 0), wx.Size(200, 30),
                                     (wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )
            
        self.label.SetFont(wx.Font(font, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        self.label.SetForegroundColour(wx.WHITE)
        self.label.SetBackgroundColour(wx.BLACK)
            
        vrtSz = wx.BoxSizer(wx.HORIZONTAL)

        vrtSz.Add(self.bitmap1)
        vrtSz.Add(self.label,1,wx.EXPAND|wx.ALIGN_CENTER|wx.ALL,1)
        vrtSz.Add(self.bitmap2)
        self.SetSizer(vrtSz)

    def SetLabel(self, text):
        self.label.SetLabel(text)
