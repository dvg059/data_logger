import  wx

import frmCMCell as CMCell
import cm_app as CM
import imageAnButtons as SclWin
import cm_drag_drop as DD
import cm_app as CM
"""
    HubTree
    This is the hub tree object.
    
    Its called from the menu item on the tabbed notebook.
    The hub_tree is displays  a root item and each hub is a tree 
    Off the root item, each hub has 8 loadcells.

    Scrolled Window:
        The scorlled window is implemented in the imageAnButtons file.
        The image is selcected from the hubTree and passed to ImageAnButton
        Window when it is created.
    users can drag and drop loadCell items from the hubTree onto the scrlWindow.
"""
#---------------------------------------------------------------------------
#log = CM.CLog()

class YourDropTarget(wx.PyDropTarget):
    """Implements drop target functionality to receive files, bitmaps and text"""
    def __init__(self):
        wx.PyDropTarget.__init__(self)
        self.do = wx.DataObjectComposite()  # the dataobject that gets filled with the appropriate data
        self.filedo = wx.FileDataObject()
        self.textdo = wx.TextDataObject()
        self.bmpdo = wx.BitmapDataObject()
        self.do.Add(self.filedo)
        self.do.Add(self.bmpdo)
        self.do.Add(self.textdo)
        self.SetDataObject(self.do)


    def OnData(self, x, y, d):
        """
        Handles drag/dropping files/text or a bitmap
        """
        if self.GetData():
            df = self.do.GetReceivedFormat().GetType()

            if df in [wx.DF_UNICODETEXT, wx.DF_TEXT]:
                text = self.textdo.GetText()

            elif df == wx.DF_FILENAME:
                for name in self.filedo.GetFilenames():
                    print name

            elif df == wx.DF_BITMAP:
                bmp = self.bmpdo.GetBitmap()

        return d  # you must return this
    
    
    
# Define Text Drop Target class
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
#------------------------------------------------
# Define Text Drop Target class
class FileDropTarget(wx.FileDropTarget):
   """ This object implements Drop Target functionality for Files """
   def __init__(self, obj):
      """ Initialize the Drop Target, passing in the Object Reference to
          indicate what should receive the dropped files """
      # Initialize the wxFileDropTarget Object
      wx.FileDropTarget.__init__(self)
      # Store the Object Reference for dropped files
      self.obj = obj

   def OnDropFiles(self, x, y, filenames):
      """ Implement File Drop """
      # For Demo purposes, this function appends a list of the files dropped at the end of the widget's text
      # Move Insertion Point to the end of the widget's text
      self.obj.SetInsertionPointEnd()
      # append a list of the file names dropped
      self.obj.WriteText("%d file(s) dropped at %d, %d:\n" % (len(filenames), x, y))
      for file in filenames:
         self.obj.WriteText(file + '\n')
      self.obj.WriteText('\n')

    

class MyTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, style):
        wx.TreeCtrl.__init__(self, parent, id, style=style)

    def OnCompareItems(self, item1, item2):
        t1 = self.GetItemText(item1)
        t2 = self.GetItemText(item2)
        if t1 < t2: return -1
        if t1 == t2: return 0
        return 1

#---------------------------------------------------------------------------

class TestTreeCtrlPanel(wx.Panel):
    def __init__(self, parent, scrolledWindowID ,hub_ini_file = 'hub_file.ini'):
        """
            Read the ini file, create a node for each hub, list 7 load cells f
            for each hub and display it in tree format
        """
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.parent = parent
        self.scrolledWindowID = scrolledWindowID
         
        self.tree = MyTreeCtrl(self, -1, wx.TR_HAS_BUTTONS)
        self.my_name = "tree control"
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        self.fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il

        self.root = self.tree.AddRoot("The Root Item")
        self.tree.SetPyData(self.root, None)
        self.tree.SetItemImage(self.root, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)
        
        self.hub_ini_file = hub_ini_file
        self.hub  = CM.CHubsObj(self.hub_ini_file)
        self.destWindow = None
        
        ids_names = []
        nbr = self.hub.hbs_GetHubIdsNames(ids_names)

        for id_name in ids_names:
            hub_id, name = id_name
            hub_id = "hub_id:%s" % hub_id            
            child = self.tree.AppendItem(self.root, "%s" % name)
            self.tree.SetPyData(child, str(hub_id))
            self.tree.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)

            #each hub has eight load cells
            for ii in range(8):
                last = self.tree.AppendItem(child, "load-cell:%d" % ii )
                self.tree.SetPyData(last, None)
                self.tree.SetItemImage(last, self.fileidx, wx.TreeItemIcon_Normal)

        self.tree.Expand(self.root)
        self.text = "the source of the text from drag and drop"
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)

        #wx.EVT_RIGHT_DOWN(self.text, self.OnDragInit)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG,self.OnDragBegin)
        #self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDragBegin)
        #self.Bind(wx.EVT_TREE_END_DRAG, self.OnDragEnd)
        
        #self.Bind(wx.EVT_TIMER, self.OnTime)


        #1 The source(tree) event OnLeftDown calls self.StartDragOperation and drop.
        #2 StartDragOperation creates a wx.CustomDataObject and a wxDropSource 
        #3 The destination 
        #4         dt = DoodleDropTarget(self, log)
        #5                      self.SetDropTarget(dt)


    def StartDragOperation(self,text_data):
#        tree_data = "hub_name:MyHub, hub_id:7, loadcell:1"
        

        ldata = wx.CustomDataObject(wx.CustomDataFormat("DoodleLines"))
        ldata.SetData(text_data)
        data = wx.DataObjectComposite()
        data.Add(ldata)
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)
        if result == wx.DragMove:
    #        self.lines = []
            self.Refresh()
    
    def OnDragBegin(self, evt):
        self.destWindow = wx.FindWindowById(self.scrolledWindowID)

        item = evt.GetItem()
        parent_item = self.tree.GetItemParent(item)
        hub_id = self.tree.GetPyData(parent_item)
        
        hub_name = "%s" % self.tree.GetItemText(parent_item)
        load_cell = "%s" % self.tree.GetItemText(item)
        dctHubTree={"hub_id":hub_id, "hub_name":hub_name, "load_cell":load_cell}
        
        text = "%s" % (dctHubTree) 
        ##%s, hub_name:%s, load_cell:%s" % (hub_id, hub_name, load_cell)
        #print "OnDragBegin ",text
        
        self.StartDragOperation(str(text))

        
    def OnDragEnd(self, evt):
        target = evt.GetItem()

        if not target.IsOk() or target == self.root:
            return

        text = self.tree.GetItemText(self.dragitem)
        if self.tree.GetItemParent(target) == self.root:
            added = self.tree.AppendItem(target, text)
        else:
            parent = self.tree.GetItemParent(target)
            added = self.tree.InsertItemBefore(parent, self.findItem(target), text)

        self.tree.Delete(self.dragitem)
        self.tree.SetItemImage(added, self.fileidx, wx.TreeItemIcon_Normal)

        self.tree.SelectItem(added)
        self.tree.EnsureVisible(added)

    def OnMouseLeftUp(self, evt):
        self.tree.Unbind(wx.EVT_MOTION)
        self.tree.Unbind(wx.EVT_LEFT_UP)
        evt.Skip()

    def OnMotion(self, evt):
        size = self.tree.GetSize()
        x,y = evt.GetPosition()

        if y < 0 or y > size[1] and not hasattr(self, 'timer'):
            self.timer = wx.Timer(self)
            self.timer.Start(70)
        evt.Skip()

    def OnTime(self, evt):
        x,y = self.tree.ScreenToClient(wx.GetMousePosition())
        size = self.tree.GetSize()

        if y < 0:
            self.ScrollUp()
        elif y > size[1]:
            self.ScrollDown()
        else:
            del self.timer
            return
        self.timer.Start(70)

    def ScrollUp(self):
        if "wxMSW" in wx.PlatformInfo:
            self.tree.ScrollLines(-1)
        else:
            first = self.tree.GetFirstVisibleItem()
            prev = self.tree.GetPrevSibling(first)
            if prev:
                # drill down to find last expanded child
                while self.tree.IsExpanded(prev):
                    prev = self.tree.GetLastChild(prev)
            else:
                # if no previous sub then try the parent
                prev = self.tree.GetItemParent(first)

            if prev:
                self.tree.ScrollTo(prev)
            else:
                self.tree.EnsureVisible(first)

    def ScrollDown(self):
        if "wxMSW" in wx.PlatformInfo:
            self.tree.ScrollLines(1)
        else:
            # first find last visible item by starting with the first
            next = None
            last = None
            item = self.tree.GetFirstVisibleItem()
            while item:
                if not self.tree.IsVisible(item): break
                last = item
                item = self.tree.GetNextVisible(item)

            # figure out what the next visible item should be,
            # either the first child, the next sibling, or the
            # parent's sibling
            if last:
                if self.tree.IsExpanded(last):
                    next = self.tree.GetFirstChild(last)[0]
                else:
                    next = self.tree.GetNextSibling(last)
                    if not next:
                        prnt = self.tree.GetItemParent(last)
                        if prnt:
                            next = self.tree.GetNextSibling(prnt)

            if next:
                self.tree.ScrollTo(next)
            elif last:
                self.tree.EnsureVisible(last)

    def traverse(self, parent=None):
        if parent is None:
            parent = self.root
        nc = self.tree.GetChildrenCount(parent, False)

        def GetFirstChild(parent, cookie):
            return self.tree.GetFirstChild(parent)

        GetChild = GetFirstChild
        cookie = 1
        for i in range(nc):
            child, cookie = GetChild(parent, cookie)
            GetChild = self.tree.GetNextChild
            yield child

    def findItem(self, item):
        parent = self.tree.GetItemParent(item)
        for n,i in enumerate(self.traverse(parent)):
            if item == i:
                return n

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)

    def OnSelChanged(self, event):
        self.item = event.GetItem()
        event.Skip()


#---------------------------------------------------------------------------


class MyFrame(wx.Frame):
    def __init__(
            self, parent, ID, title, pos=wx.DefaultPosition,
            size=(250,400), style=wx.DEFAULT_FRAME_STYLE
            ):
        
        self.scrl_win = None
        ID_FILE_SEL = wx.NewId()

        self.image_file = None
        self.scrolledWindowID = wx.NewId()
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
                    #--- Create menu bar
        mb = wx.MenuBar()
        
        #---- Create File Menu items, Quit, about
        file_menu = wx.Menu()

        #allow user to select logon Level
        item = wx.MenuItem(file_menu, wx.NewId(), "&Select Image")
        self.Bind(wx.EVT_MENU, self.OnImageSelect, item)

        file_menu.AppendItem(item)
        mb.Append(file_menu, "&File")
        
        self.SetMenuBar(mb)
        
        us = CM.CUserObj()                      #check ini file if an image file exists
        self.image_file = us.usr_GetImageFile()
        
        if  self.image_file != "":              #If image file defined bring it up in a window.
            self.scrl_win = SclWin.MyScrolledWindow(None, self.scrolledWindowID, str(self.image_file), self.image_file)
        
            self.scrl_win.Show(True)
            self.scrl_win.Centre()
            self.scrl_win.init_loadcells()
            

    def OnImageSelect(self,evt):

        if  wx.FindWindowById(self.scrolledWindowID) != None:
            return                          #if an image window is already up then return.
                                            #don't allow multiple image windows to be displayed
        
        fileTypes = 'All image files (tif, bmp, jpg, gif, png...)| *.tif;*.bmp;*.jpg;*.png;*.pcx;*.gif;*.pnm;*.jpeg' 
        dlg = wx.FileDialog(self, "Open Image", "", "", fileTypes, wx.OPEN) 

        if dlg.ShowModal() == wx.ID_OK:
            self.image_file =dlg.GetPath()

        dlg.Destroy()

       
        self.scrl_win = SclWin.MyScrolledWindow(None, self.scrolledWindowID, str(self.image_file), self.image_file)
        self.scrl_win.Show(True)
        self.scrl_win.Centre()

        us = CM.CUserObj()                      #save the image file name.
        us.usr_SetImageFile(self.image_file)
        self.scrl_win.init_loadcells()

        
        #---- Create File Menu items, Quit, about



#####################################################
def HubTree(image_file = "truss_page.jpg"):

    class MyApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            self.scrolledWindowID = wx.NewId()

            
            
            # frame = wx.Frame(None, -1, 'HubTree', size=(200,400))
            frame = MyFrame(None,-1, "HubTree")
            
            panel = TestTreeCtrlPanel(frame,self.scrolledWindowID )
            frame.Show()
            

            return True

########################################################            
            
    app = MyApp(0)
    app.MainLoop()

if __name__ == '__main__':
    HubTree()
