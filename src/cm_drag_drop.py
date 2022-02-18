#!/usr/bin/python

# dragdrop.py

import wx
import ast
import cm_app as cm
import string
from cm_Defines import *

class mylog():
    def WriteText(self, text):
        print text

        
        
        
    

       

class loadcell(wx.Panel):
    def __init__(self, parent, winId, ps=(0,0), dct={'weight':1,'hub_info':1,}, log= None):             

        #The dct is strng that is converted back to dict.
        #expected format :dct  {'hub_id': 1, 'load_cell': u'load-cell:7', 'cell_id': 7, 'hub_name': u'hub_1'}
        self.log = mylog()
        
        if type(dct) == type(""):
            dct = ast.literal_eval(dct)

        self.dctHub = dct
        #print "ps ",ps
        #print "dct ",dct
        
        self.x_cord, self.y_cord = ps
        
        #print "loadcell dctHub",self.dctHub
        
        wx.Panel.__init__(self, parent, winId,ps,(100,-1))
        vrtSizer = wx.BoxSizer(wx.VERTICAL)

        #Create new btn
        
        if 0:                
            txt = "HubName:%s, \n CellId:%s" % (dct["hub_name"],dct["cell_id"])
            
#            btnBar = [(wx.NewId(),"Save","cir_black.png",txt)]
            btnBar = [(wx.NewId(),"Save","motion_2.bmp",txt)]
            
            btn_id,txt,pic,toolTip = btnBar[0]
#            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_BMP)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            self.newBtn = wx.BitmapButton(self, btn_id, bmp, (10, 10),
                           (bmp.GetWidth()+10, bmp.GetHeight()+10))
        else:
            self.newBtn = BackGroundPanel(self,wx.NewId(),"motion_1.bmp")
            self.newBtn.SetSize((20,10))

            #self.newBtn.Bind(wx.EVT_LEFT_UP, self.OnClick)
            
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.newBtn.Bind(wx.EVT_LEFT_UP, self.OnClick)    
#        self.newBtn.SetToolTipString(toolTip)


        vrtSizer.Add(self.newBtn)

        self.save()
        self.SetSizer(vrtSizer)
        vrtSizer.Fit(self)
        
    def OnClick(self, evt):
        print "newBtn OnClick"
        self.log.WriteText("OnClick: load cell text"% (self.dctHub))
        self.dctHub["win_id"] = self.Id
        
        hub  = cm.CHubsObj()

        hub.hbs_RemoveHubCellCord(self.dctHub["hub_id"], self.dctHub["cell_id"])
        
        self.Parent.RemoveLoadCellFromGraphic(self.dctHub)
        self.Destroy()
        
        
    # save the loadcells x,y coordinates
    def save(self):
        hub  = cm.CHubsObj()
        #{'hub_id': 'hub_id:8', 'load_cell': u'load-cell 1', 'hub_name': u'ML##Speakers'}
        hub.hbs_AddHubCellCord(self.dctHub["hub_id"], self.dctHub["cell_id"], 
                               self.x_cord, self.y_cord)   #Add a single cell pos to hub
        
        
        

        
        
#This is the text that appears on the bitmap, to    
 
################################
class MyTextDropTarget(wx.TextDropTarget):
    def __init__(self, object):
        wx.TextDropTarget.__init__(self)
        self.object = object

    def OnDropText(self, x, y, data):
        self.object.InsertStringItem(0, data)
########################################
class DoodleDropTarget(wx.PyDropTarget):
    def __init__(self, window, log=mylog()):
        wx.PyDropTarget.__init__(self)
        self.log = log
        self.dv = window

        # specify the type of data we will accept
        self.df = wx.CustomDataFormat("DoodleLines")
        self.data = wx.CustomDataObject(self.df)
        self.SetDataObject(self.data)

        # some virtual methods that track the progress of the drag
    def OnEnter(self, x, y, d):
        self.log.WriteText("OnEnter: %d, %d, %d\n" % (x, y, d))
        return d

    def OnLeave(self):
        self.log.WriteText("OnLeave\n")

    def OnDrop(self, x, y):
        self.log.WriteText("OnDrop: %d %d\n" % (x, y))
        return True


    def OnDragOver(self, x, y, d):
    #self.log.WriteText("OnDragOver: %d, %d, %d\n" % (x, y, d))
    # The value returned here tells the source what kind of visual
    # feedback to give.  For example, if wxDragCopy is returned then
    # only the copy cursor will be shown, even if the source allows
    # moves.  You can use the passed in (x,y) to determine what kind
    # of feedback to give.  In this case we return the suggested value
    # which is based on whether the Ctrl key is pressed.
        return d

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):
        self.log.WriteText("OnData: %d, %d, %d\n" % (x, y, d))
        txt_id = wx.NewId()

        
    # copy the data from the drag source to our data object
        if self.GetData():
        # convert it back to a list of lines and give it to the viewer
            data = self.data.GetData()
#            print "OnDragOver data:%s" % data
#            print "type data",type(data)
            data = ast.literal_eval(data)

            #format data into dictionary
            #The data is strng that is converted back to dict.
            #expected format :{'hub_id': 'hub_id:8', 'load_cell': u'load-cell 1', 'hub_name': u'ML##Speakers'}
            
            hubID = string.split(data["hub_id"], ":")       

            #expected return ['hub_id', '8']
            data['hub_id'] = int(hubID[1])
        
            cellID = string.split(data["load_cell"], ":") 

            #expected return cellID is ['cell_id', '8']
            data['cell_id'] = int(cellID[1])


            data = str(data)
            text = loadcell(self.dv, txt_id, (x,y), data)
            #text = loadcell(self.dv, txt_id, (x,y) , data )
 #           lines = wx.InputStream(cPickle.loads(linesdata))
 #           self.dv.SetLines(lines)
 
            
