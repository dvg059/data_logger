#!/usr/bin/env python
# -*- coding: cp1252 -*-

import  wx
#import  wx.grid     as  gridlib
import  wx.lib.agw.peakmeter as PM

import wx.grid  as  gridlib
import time
import cm_app as CM
from  cm_Defines import *

#import  wx.lib.scrolledpanel as scrolled

#ids for windows
WinGroups_ids = wx.NewId()  # id of window that has all the groups.

#ids for btns at top of panel
BtnConnect_Id = wx.NewId() #Try to connect to hub using connect parms
BtnDisable_Id = wx.NewId() #Disable hub communications.
BtnSave_Id    = wx.NewId() #Save current hub Settngs, hub_name,conenction etc
BtnCancel_Id  = wx.NewId() #Discard current hub parametes and reload the orignals

#ids for constants and Max Values

MAX_AVG_READS   = 5     #Nbr of readings before taking an avg
PEAK_METER_FULL_SCALE = 20
METER_GREEN = 12 
METER_YELLOW = 16
METER_RED  = PEAK_METER_FULL_SCALE-1
NUM_METER_BARS = 1

def GetPeakMeter(parent):
        full_scale =  PEAK_METER_FULL_SCALE
        green    =  METER_GREEN
        yellow   =  METER_YELLOW
        red      =  METER_RED
        
        meter = PM.PeakMeterCtrl(parent, -1, style=wx.SIMPLE_BORDER, agwStyle=PM.PM_VERTICAL)
        meter.SetMeterBands(NUM_METER_BARS, PEAK_METER_FULL_SCALE  )

        meter.SetRangeValue(METER_GREEN  , METER_YELLOW , METER_RED )
        return meter


## General purpose math, for use with map functions (see python list doc)9999
def sub(x,y):
    return x-y

def add(x,y):
    return x+y

#add seq without a for loop
def sum(seq):
    def add(x,y): return x+y
    return reduce(add, seq, 0)

BtnBar = [(BtnConnect_Id,"Connect","connect_1.png","Connect to Hub"),
          (BtnDisable_Id,"Disable","disconnect_1.png","Disconnect from Hub")]

#,
#          (BtnSave_Id,"Save","save_1.png","Save Changes"),
#          (BtnCancel_Id,"Cancel","cancel_1.png","Cancel Changes")]
##DV--------------------------------------
##DV Mar 20: 2012: Add Freature to Connect and Disconnect a hub,
##                 Add Feature to change and save hub n cell parameters(name, connection(.
##                 Add Feature to Add and Remove Hubs.
##                 Add Feature to name and save cells
##
##DV Mar 09 2012: The panel meeter is displaying correctly for a
##      all colors (grn,yel,red). The led readout text is now
##      working correctly. It streches and keeps the text center.
##      The font forecolour should change ot match the grap.
##      I wanna put 8 of these things up before going further.
##DV Mar 08 2012: The meter shows up and displays a single bar.
##      SetMeterBands was changed to 1 for number of loadcells
##      and 10(nbr of bargraphs). 
##      SetRangeValues sets the colors <=6 green, >=8 yel, >8 = red.
##      The grid wasnt working correctly till SetRangeValue was called.
##      the default values were probably much higher then 10

#---------------------------
log = CM.CLog(4)
#---------------------------
class CGroupMngr:
    ''' Manage the modles group windows.
        caller will request window for a given group id.
        if the window is already displayed return a pointer to it
        else create the window and return a pointer to it
        '''
    def __init__(self,log):
        self.group_dct={"group_id":-1, "window_id":-1, "window":None}
        self.group_windows = []
        self.log = log
        self.group_windows.append(self.group_dct)
        #self.log.write("CGroupMngr__init__")
        
    def grp_mgr_CreateWindow(self, grp_id = -1, name = None):
        #Create a window for the requested id
        #Added to my internal list for next time

        dct={'group_id':grp_id, 'window_id':wx.NewId()}

        grp_win =  CWinGroup(self, dct['name'], "Group %s" % (name),
                                       {'group_id':grp_id,'group_name':name},
                                       self.log)
        dct['window']=grp_win
        self.group_windows.append(dct)
        return dct

    def grp_mgr_GetWindow(self, grp_id = -1):
        found = False
        ret_win = None  #assume we cant find the grp_id

        for grp_win in self.group_windows:
            #Search thru the list of group windows,
            #If we already have a window up for the req grp_id just return it
            
            if (grp_win['group_id'] == grp_id):
                win = wx.FindWindowById(grp_win['window_id'])
                self.log.write("CGroupMngr:grp_mgr_GetWindow  %s" % win)

                if win:
                    return grp_win['window']
                
            
        #the requested group window was not found, create a window,
        group  = CM.CHubGroupObj()
        ids_names = group.gp_GetGroups()
        # exptd_lst = [(2, 'group_2'), (1, 'grp1'), (0, 'group_0')]

        found = False
        #find the group name id from the group obj
        for id_name in ids_names:
            id,name = id_name

            self.log.write("CGroupMngr:grp_mgr_GetWindow %s %s" % (id,grp_id))
            if int(id) == int(grp_id):
                found = True
                break
            
        if found == True:
            #found a group id and name, now create a window for it
            dct = self.grp_mgr_CreateWindow(grp_id,name)

            self.log.write("CGroupMngr.grp_mgr_GetWindow: New window for group GroupId:%s" % grp_id)
            return dct['window']
            
        else:
            self.log.write("CGroupMngr.grp_mgr_GetWindow: Unknown GroupId:%s" % grp_id)
            return None
#---------------------------------------------
GrpMngr= CGroupMngr(CM.CLog())

# -------------------------------------------
class dlgUserEntry(wx.Dialog):
    def __init__(
            self, parent, ID, title, strs = ["string 1","string 2"," string 3","string 4"], listbox=[],
            size=wx.DefaultSize, pos=wx.DefaultPosition, 
            style=wx.DEFAULT_DIALOG_STYLE
            ):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI object using the Create
        # method.

        self.userTexts = []
        
        
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.PostCreate(pre)


        # Now continue with the normal construction of the dialog
        # contents
        vrtSz = wx.BoxSizer(wx.VERTICAL)
        # This label This a caption at the top of the dialog
        # Theres no text box assoc with this label
        label = wx.StaticText(self, -1, strs[0])
        label.SetHelpText("This is the help text for the label")
        
        vrtSz.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        rows = len(strs) -1
        cols = 2
        grdSz = wx.GridSizer(rows, cols, vgap=5, hgap=5)

        #exptd format [(string, [])]
        self.cbs = []  #used by calling routine to get user selection

        for str_lst in listbox:
            str,lst = str_lst
            #print "str_ls %s, lst %s" % (str, lst) #expt str_ls Select Group, lst ['0, group_0']
            label = wx.StaticText(self, -1, str)
            grdSz.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            cb = wx.ComboBox(self, 501, lst[0], (90, 80), (160, -1), [], wx.CB_DROPDOWN)
            grdSz.Add(cb, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            for item in lst:
                cb.Append(item, item.upper())

            self.cbs.append(cb)

            
        for str in strs[1:]:
            #Create a label and assoc text
            #Labels on the left, userText cntrls on the right
            label = wx.StaticText(self, -1, str)
            label.SetHelpText("help text for label:%s" % str)

            grdSz.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            text = wx.TextCtrl(self, -1, "", size=(80,-1))
            text.SetHelpText("text feils for user entry ")
            self.userTexts.append(text) #save text controls for calling routine

            grdSz.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            
        vrtSz.Add(grdSz, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        vrtSz.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnSz = wx.StdDialogButtonSizer()
        
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnSz.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
        btnSz.AddButton(btn)
        btnSz.Realize()

        vrtSz.Add(btnSz, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(vrtSz)
        vrtSz.Fit(self)

#--------------------------------        
class frame_parser:
    '''
        Prarse a raw data buffer into cell weight
        Each hub will have one frame parser.
        The raw string is verified and parsed into
        cell_id(0-70), weight, display_text and weight value
    '''
    
    def __init__(self, log=None):
        self.buf = []
        self.log = log
        
    def ParseData(self, raw_buf = []):
        '''parse raw frame into format
            70 16 39 2 25 1 16 39 2 25 1
            weight = b[1] + b[2]*256
            cell_id = b[3, bargraph=b[4], status = b[5]]
            '''
        self.buf = self.buf + raw_buf
        
        i = 0
        for ch in range(len(self.buf)):
            if self.buf[i] == 70:
                break
            i = i + 1
        self.buf = self.buf[i:]
        
            
        dct={"cell_id":0, "weight":0, "overload":0,"valid":False, "units":"?"}
        #print"self.buf",self.buf
        if (len(self.buf) > 10):   
            if (    (self.buf[1] == self.buf[6]) and (self.buf[2] == self.buf[7]) \
                and (self.buf[3] == self.buf[8])  and (self.buf[4] == self.buf[9]) \
                and (self.buf[5] == self.buf[10]) and (self.buf[0] == 70) ):
                self.log.write( "ParseData  valid packet")
                
                dct["cell_id"] = self.buf[3]
                dct["weight"] = self.buf[1] + self.buf[2]*256
                dct["overload"] = self.buf[4]

                dct["units"] = "???"
                
                if int(self.buf[5] == 1):
                    dct["units"] = "lbs"
                    
                elif int(self.buf[5] == 2):
                    dct["units"] = "kg"
                
                dct["valid"] = True
               # print "ParseRawData: valid packRecv", dct

            self.buf = self.buf[1:]
        return dct

 
#--------------------------     
class cell_reading:
    ''' used to track and avg cell Readdings.
    '''
    def __init__(self, cell_id = -1, max_reads = MAX_AVG_READS, unit = LBS, max_value = NO_CONNECT_VALUE_2_TON):
        self.cell_id = cell_id  #unique identifer, same as the owner.
        self.readings = []         #array of readings
        self.max_reads = max_reads  #max number of reads
        self.max_value = max_value  # values >= to max are invalid cause a reset of readings
        self.Reset()
        
        for i in xrange(self.max_reads):
            self.readings.append(0)        
        
    def Reset(self):
        '''reinit internal vars '''
        # subtract array from itself
        self.readings = map(sub,self.readings,self.readings)

        self.count = 0
        self.highest_read = 0
        self.is_valid = False       #used to inidcate a read is valid

    def AddRead(self, new_read):
        '''Add new read to array of reading
        ensure a box car avg of reads are keep'''

        #ensure a full set of reads           
        if new_read < self.max_value:
            if (self.count >= self.max_reads):
                self.is_valid = True

            self.count = self.count % self.max_reads

            self.readings[self.count] = new_read
            self.count = self.count + 1                
            
        else:
            #values > max cause a reset of values
            self.Reset()
            
        return self.count 
    
        
    def GetAvg(self):
        '''Calc and return the average readding'''
        avg = sum(self.readings)
        avg = avg / self.max_reads

        if avg > self.highest_read:
            self.highest_read = avg
            
        dct = {"avg":avg, "is_valid":self.is_valid,"max":self.highest_read} 
        return dct

#--------------------------------
class CMy_Meter(PM.PeakMeterCtrl):
    '''
        This meter obj is used when showing all hubs or groups.
        The meter obj has the hub and cell id that it represents
        The meter obj has a text obj thats the readout value for the meters.
        When the meter obj is disabled it setes the text background and foreground
        to gray.
        The user can toggle the enable or disable state by clicking on the meter bar.
        The default state is diabled on creation.
        The user can disable or enable the meter by clicking on
        the meter bar.
        The actual handler is set to the parent
    '''
    def __init__(self, parent, id, name,cell_id, hub_id, txt_obj, log = None):
        
        PM.PeakMeterCtrl.__init__(self, parent, id, style=wx.SIMPLE_BORDER, agwStyle=PM.PM_HORIZONTAL)
        self.SetMeterBands(NUM_METER_BARS, PEAK_METER_FULL_SCALE )
        self.SetRangeValue(METER_GREEN ,METER_YELLOW  ,METER_RED)
        
        self.Bind(wx.EVT_LEFT_DCLICK,   parent.OnMeterClick)
        
        self.parent = parent
        self.id = id
        self.name = name
        self.cell_id = cell_id
        self.hub_id = hub_id
        self.txt_obj = txt_obj
        self.mtr_SetState(DISABLED)
        
        self.meterTimer = wx.Timer(self)
        self.meterTimeout = 30
        self.Bind(wx.EVT_TIMER, self.OnMeterTimer, self.meterTimer)
        self.meterTimer.Start(250)


    def OnMeterTimer(self,evt):
        if (self.meterTimeout > 0):
            self.meterTimeout = self.meterTimeout -1

            if self.meterTimeout <= 0:
                self.mtr_CellDisplayUpdate({"text":"","overload":0})


        
    def mtr_SetState(self, state = DISABLED):
        if state == DISABLED:
            self.state = DISABLED
            self.txt_obj.SetForegroundColour(GREY)
            self.txt_obj.SetBackgroundColour(GREY)
            self.mtr_CellDisplayUpdate({"text":"","overload":0})
        else:
            self.state = ENABLED
            self.txt_obj.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
            self.txt_obj.SetForegroundColour(wx.WHITE)
            self.txt_obj.SetBackgroundColour(wx.BLACK)

    def mtr_ToggleState(self):
        if self.state == DISABLED:
            self.mtr_SetState(ENABLED)
        else:
            self.mtr_SetState(DISABLED)
            
    def mtr_CellDisplayUpdate(self,dct={"text":"","overload":0}):
        bar_value = int(dct["overload"])
        self.meterTimeout = 30
        
        self.txt_obj.SetValue(dct["text"])
        #log.write("mtr_CellDisplayUpdate %s" % bar_value)
        
        self.SetData([bar_value],0, NUM_METER_BARS)
        

    def OnMeterClick(self, evt):
        log.write("CMy_Meter:CMy_Meter %s" % evt.GetId())

#------------------------------
class CPnlGroup(wx.Panel):
    '''
      Pnl of user defined cells.
      
    '''
    def __init__(self, parent, id, name, dct={}, log = None): 
        wx.Panel.__init__(self, parent, id, style = wx.BORDER_DOUBLE)
        self.log = log
        #self.scroll = wx.ScrolledWindow(self, -1)
        self.dct = dct #This should be a dict of ids and names

        self.group_parent = parent

        #hubs and cells are ordered dont change the order
        self.txt_names = []
        self.txt_values = []
        self.meters = []
        self.pnl_grpDoLayout()

        #self.scroll.SetVirtualSize((600, 400))
    def pnl_grpUpdateLoadCell(self,dct):
        #iterate thru the list of meters and cells
        total_weight = 0
        cells_offline = 0
        total_cells = 0
        
        for cell in self.meters:
            if (cell.state == ENABLED):
                total_cells = total_cells + 1
                if cell.txt_obj.GetValue().isdigit():
                    total_weight = total_weight + int(cell.txt_obj.GetValue() )
                else:
                    cells_offline = cells_offline + 1

        dct_grp_data = {"nbr_cells":total_cells, 
                        "total_weight":total_weight, 
                        "units":dct["units"]}
        
        self.group_parent.UpdateGroupDataGrid(dct_grp_data)
                
        for cell in self.meters:
            if ( (cell.cell_id == dct['cell_id']) and (cell.hub_id == dct['hub_id']) and (cell.state == ENABLED) ):
                cell.mtr_CellDisplayUpdate(dct)
                
                    
#            self.mtr_CellDisplayUpdate({"text":"","bar":0})

        
    def pnl_grpFilterHubs(self,ids_names = []):
        '''
            Given  a list of hubs that are enabled 
            Admin level users see all the hubs.
            User level users only see hubs assigned to the group
        '''
        
        #If admin user then return list all hub and ids
        usr_obj = CM.CUserObj()
        filtered_ids_hubs = [] # [(hub_id,hub_nm),]
        filtered_hubs =[]
        
        #Test default setting of user obj
        if usr_obj.usr_GetUserLevel() == ADMIN_LEVEL:
            return ids_names
        else:
            for hub_id_nm in ids_names:
                hub_id, hub_nm = hub_id_nm
                group  = CM.CHubGroupObj()

                if (group.gp_IsHubInGroup( self.dct['group_id'], hub_id) == True) and ( (hub_id in filtered_hubs) == False):
                    
                    filtered_hubs.append(hub_id)
                    filtered_ids_hubs.append((hub_id,hub_nm))

#            log.write( "pnl_grpFilterHubs",filtered_ids_hubs,4)

            return filtered_ids_hubs
                

    
    def pnl_grpDoLayout(self):

        self.log.write("pnl_grpDoLayout:")


        #self.cells.append( meter(self,self.log,x,("cell %s" % x)))
        self.log.write("pnl_grpDoLayout:  cells")

        self.led_timeout  = 0
        
#        grdSizer = wx.GridSizer(rows=2, cols=16, vgap=1, hgap=1)
        hub = CM.CHubsObj()
        cb_list_hubs = []            
        ids_names = []
        #Get the total number of user hubs
        nbr_hubs = hub.hbs_GetHubIdsNames(ids_names)
        
        ids_names = self.pnl_grpFilterHubs(ids_names)
        nbr_hubs = len(ids_names)
        self.hubs_ids_names = ids_names
        
        rows = 5
        cols = 3
            
        if nbr_hubs < 2:
            rows = 1
            cols = 1

        elif nbr_hubs < 3:
            rows = 1
            cols = 2
            
        elif nbr_hubs < 5:
            rows = 2
            cols = 2

        elif nbr_hubs < 12:
            rows = 5
            cols = 3

        elif nbr_hubs > 12:
            rows = 5
            cols = 4
            
#        print "rows%s, cols:%s" % (rows, cols)    
        grdSzr_grp = wx.GridSizer(rows = rows, cols=cols, vgap=2, hgap=2)
        
        #iterate the list of hub ids and names
        for id_name in ids_names:
            hub_id,hub_name = id_name

            vertSzr_txt_hub = wx.BoxSizer(wx.VERTICAL)

            txt_name = wx.TextCtrl(self,-1, hub_name, wx.Point(0, 0), wx.Size(100, 15),
                                     (wx.NO_BORDER | wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )
            
            txt_name.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
            txt_name.SetForegroundColour(wx.WHITE)
            txt_name.SetBackgroundColour(wx.BLACK)
            self.txt_names.append(txt_name)


            grdSzr_hub = wx.GridSizer(rows = 2, cols=4, vgap=0, hgap=0)
            #make the loadcells for the group, theres alwoys 7 load cells
            for cell_id in range(MAX_CELLS):
                vertSzr_val_meter = wx.BoxSizer(wx.VERTICAL)
                idx = len(self.meters)

                                
                #text control to display meter value
                txt_value = wx.TextCtrl(self, idx, "cell_value", wx.Point(0, 0), wx.Size(100, 30),
                                     (wx.NO_BORDER | wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )
                txt_value.SetSize((30,20))
                #Meter obj, will set events to so user can enable or disable
                meter = CMy_Meter(self,idx, hub_name, cell_id, hub_id, txt_value,self.log)
#                meter.SetMeterBands(NUM_METER_BARS, PEAK_METER_FULL_SCALE )

#                meter.SetRangeValue(METER_GREEN ,METER_YELLOW  ,METER_RED)
                meter.SetData([0], 0, NUM_METER_BARS)

                #this is the mete for the group, it replicate
                meter.SetSize((62,45))
                self.pnl_grpInitMeterState(meter)

                self.meters.append(meter)
                self.txt_values.append(txt_value)
                
                #Add the meter and the text assoc with the meter readout
                vertSzr_val_meter.Add(meter, 0, wx.FIXED_MINSIZE|wx.CENTER)
                vertSzr_val_meter.Add(txt_value, 0,  wx.FIXED_MINSIZE|wx.CENTER)
                                  
                grdSzr_hub.Add(vertSzr_val_meter, 0, wx.FIXED_MINSIZE | wx.CENTER,2)

            #this text is the hub name, the meter and readout value are added bleow
#            vertSzr_txt_hub.Add(txt_name, 0, wx.EXPAND|wx.FIXED_MINSIZE)
            vertSzr_txt_hub.Add(txt_name)
            
            vertSzr_txt_hub.Add(grdSzr_hub, 0, wx.EXPAND|wx.FIXED_MINSIZE)
#            vertSzr_txt_hub.Add(grdSzr_hub)
                                  
            grdSzr_grp.Add(vertSzr_txt_hub,0,wx.FIXED_MINSIZE)
                                  
            self.SetSizer(grdSzr_grp)
                                                                    
        self.log.write("pnl_grpDoLayout: ")


    def pnl_grpInitMeterState(self, meter):
        group  = CM.CHubGroupObj()
        self.log.write("pnl_grpInitMeterState: Enable this cell/meter is in this group")
        if group.gp_IsCellInGroup( self.dct['group_id'], meter.hub_id, meter.cell_id) == True:
            meter.mtr_SetState(ENABLED)
        else:
            meter.mtr_SetState(DISABLED)
            

    def pnl_grpUpdateHubCellState(self, meter):
        group  = CM.CHubGroupObj()
        self.log.write('CPnlGroup pnl_grpUpdateHubCellState group_id %s, group_name: %s' %
                       (self.dct['group_id'], self.dct['group_name']))
        

        if meter.state == ENABLED:
            #Add the hub_id n cell_id to enabled hub
            group.gp_AddHubCell(self.dct['group_id'], meter.hub_id, meter.cell_id)
            self.log.write('CPnlGroup gp_AddHubCell grp(%s), hub(%s), cell(%s)' %
                           (int(self.dct['group_id']), int( meter.hub_id), int(meter.cell_id)) )
        else:
            #Disabled hub,cell remove the hub,cell
            group.gp_RemoveCellInGroup(self.dct['group_id'], meter.hub_id, meter.cell_id)

            self.log.write('CPnlGroup gp_RemoveHubCell grp(%s), hub(%s), cell(%s)' %
                           (self.dct['group_id'], meter.hub_id, meter.cell_id))
        
        self.Refresh()


    def OnMeterClick(self,evt):
        meter = evt.GetEventObject()
        meter.mtr_ToggleState()
        self.log.write("OnMeterClick CPnlGroup(%s) : Cell:%s Hub:%s" % (self.dct, meter.cell_id,meter.hub_id))
        self.pnl_grpUpdateHubCellState(meter)
#------------------------------
class CGroupGridPanel(wx.Panel):

    '''
        This panel is used by group windows to show the total weight
        Number of cells and other data about a group.
        The calling routine should pass in a dict of nbr rows and nbr cols.
        And labels. 
        dct['rows'] = nbr rows: 
        dct['cols'] = nbr cols:
        dct['row_labels'] =list of string row labels, len should match nbr rows
        dct['col_labels'] = list of string col labels, len should match col labels
    '''                 
    def __init__(self, parent, winId, dct={'rows':1,'cols':1, 'row_labels':['row1'], 'col_labels':['col1']},log = None):
        wx.Panel.__init__(self, parent, winId,  style = wx.BORDER_DOUBLE)
        
        self.dct_parms = dct
        self.parent = parent
        self.winId = winId
        self.log = log
            
        self.grd_group_details = gridlib.Grid(self)
        self.grd_group_details.CreateGrid(dct['rows'], dct['cols'])      #CreateGrid(rows,cols)
        self.InitGroupDetailsGrid(self.grd_group_details)
        
        grdSzr = wx.GridSizer(rows = 1, cols=3, vgap=2, hgap=1)

        #grdSzr.Add((0,0), 0)       
        grdSzr.Add(self.grd_group_details, 5, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL,1) #wx.ALIGN_CENTER_VERTICAL|wx.ALL
        #grdSzr.Add((0,0), 0)  
         
        sz = self.grd_group_details.Size
        grdSzr.SetMinSize(sz)  
        
        self.SetSizer(grdSzr)


        
    def InitGroupDetailsGrid(self, grd):
        attr = gridlib.GridCellAttr()
        attr.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

        grd.SetRowAttr(0,attr)
        
        grd.SetDefaultCellAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER) 

        grd.SetRowLabelSize(0)
        grd.SetColLabelSize(15)
        grd.SetDefaultCellTextColour(wx.WHITE)
        grd.SetLabelTextColour(wx.WHITE)
        
        grd.DisableCellEditControl()
        grd.SetLabelBackgroundColour( wx.BLACK)
        grd.SetDefaultCellBackgroundColour(wx.BLACK)
        grd.DisableDragGridSize()
        grd.EnableEditing(False)
        
        for col in range( len(self.dct_parms['col_labels']) ):
            grd.SetColLabelValue(col, self.dct_parms['col_labels'][col])
        
        
        for col in range(grd.GetNumberCols()):
            #bar.SetColAttr(col, attr)
            grd.SetColMinimalWidth(col,10)
            grd.SetColSize(col,150)

    def UpdateGroupGrid(self, dct_grp_data={}):
        '''       dct_grp_data = {"nbr_cells":len(self.meters), 
                        "total_weight":total_weight, 
                        "cells_offline":cells_offline}
        '''
        self.grd_group_details.SetCellValue(0, 2, str( dct_grp_data["nbr_cells"]) )
        self.grd_group_details.SetCellValue(0, 0, str( dct_grp_data["total_weight"]) )
        self.grd_group_details.SetCellValue(0, 1, str( dct_grp_data["units"]) )
        
      
#------------------------------
class CPnlStatus(wx.Panel):

    '''
        Generic Status Panel
    '''
    def __init__(self, parent, id, strs=['label'],log = None):
        wx.Panel.__init__(self, parent, id,  style = wx.BORDER_DOUBLE)
        
        
        #self.label = wx.StaticText(self, -1, strs[0])
        self.label = wx.TextCtrl(self,-1, strs[0], wx.Point(0, 0), wx.Size(100, 30),
                                 (wx.NO_BORDER | wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )

        #self.label.SetHelpText("This is the help text for the label")
        #self.text1 = wx.TextCtrl(self,-1, "text", wx.Point(0, 0), wx.Size(100, 30),
        #                         (wx.NO_BORDER | wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )

        self.label.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        self.label.SetForegroundColour(wx.WHITE)
        self.label.SetBackgroundColour(wx.BLACK)
        self.log = log

        hrSizer = wx.BoxSizer(wx.VERTICAL) ### Horizontal sizer for buttons(Top of hubPage

        hrSizer.Add(self.label,0,wx.EXPAND)
        self.SetSizer(hrSizer)

#------------------------------
class CWinGroup(wx.Frame):
    '''
        This Group. Acts like a modless dialog box.
        it group objects
        the notebook
    '''
    def __init__(
            self, parent, ID,  title, dct={'group_id':-1, 'group_name':'name'},
            log=None,
            pos=wx.DefaultPosition,
            size=(625,550), style=wx.DEFAULT_FRAME_STYLE): #sets the size of the group window
                
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)

        self.id = ID
        self.log = log
        #CPnlStatus has the group name
        self.status_pnl = CPnlStatus(self,-1, [dct['group_name']],self.log)
        #CGroupGridPanel has the grid with data about the grid
        self.data_pnl = CGroupGridPanel(self,-1, 
                                        dct={'rows':1,
                                             'cols':3, 
                                            'row_labels':[], 
                                            'col_labels':['Total Weight','Units','Nbr Load Cells']},
                                        log = self.log)
        #This has the loadcells in the group
        self.grp_pnl = CPnlGroup(self,
                                 id = int(dct['group_id']),
                                 name = dct['group_name'],
                                 dct = dct,
                                 log = self.log)
         
        #if (len(self.grp_pnl.hubs_ids_names) > 9):
        #    self.SetSize((900,1000))

        #elif (len(self.grp_pnl.hubs_ids_names) > 6):
        #    self.SetSize((900,750))
        
        if (len(self.grp_pnl.hubs_ids_names) > 12):
            self.SetSize((2000,1000))
                
        elif (len(self.grp_pnl.hubs_ids_names) > 9):
            self.SetSize((900,1000))
        
        elif (len(self.grp_pnl.hubs_ids_names) >= 7): #nbr hubs 7-9
            width = 700
            length = 900
            self.SetSize((length,width))
        
        elif (len(self.grp_pnl.hubs_ids_names) >= 5): #nbr hubs 6
            width = 500
            length = 900
            
            self.SetSize((length,width))

        elif (len(self.grp_pnl.hubs_ids_names) >= 3): #nbr hubs 3 to 4
            width =  500
            length = 600
            
            self.SetSize((length,width))
        else:
            self.SetSize((625,325)) # 1-2 hubs in group


        self.log.write( "CWinGroup:__init__ %s" % (dct) )
        

        vrtSzr = wx.BoxSizer(wx.VERTICAL)
        vrtSzr.Add(self.status_pnl, 0, wx.EXPAND)
        vrtSzr.Add(self.data_pnl)
        vrtSzr.Add(self.grp_pnl, 1, wx.EXPAND)
        self.SetSizer(vrtSzr)
        
    def UpdateGroupDataGrid(self, dct):
        '''       dct_grp_data = {"nbr_cells":len(self.meters), 
                        "total_weight":total_weight, 
                        "cells_offline":cells_offline}
        '''
        self.data_pnl.UpdateGroupGrid(dct)
#---------------------------
class hub(wx.Panel):
    def __init__(self, parent, log, hub_id, parms=[]):
        wx.Panel.__init__(self, parent, -1, style = wx.BORDER_DOUBLE)
        self.log    = log
        self.hub_id     = hub_id
        
        self.no_connect_value = NO_CONNECT_VALUE_2_TON
        self.max_weight = LOADCELL_TON_2
        
        self.units      = "?"
        #self.parent = parent
        self.HubNB = parent
        
        self.SetParams(parms)
        self.buf = []

        self.parser = frame_parser(log)
        self.name = "hub%s" % hub_id  #default name.
        self.cells = []
        self.log.write("hub:__init___ parms: %s" % parms,6 )
                

            
        self.frmHub_id = wx.NewId()
        self.dirty_grid = False
        
        self.text1  = LabelBorder(self, wx.NewId(),"Hub Setup","motion_2.bmp", font=18)

                
        #---- Create a progress bar to show hub connections status
        #self.cnxt_bar =  gridlib.Grid(self)
        self.col_cell = 0
        #self.InitConnectBar(self.cnxt_bar)
        
        #---------------------------------
        #This grid shows details about the hub.
        #Total weight of the hub, units
        self.grd_hub_details = gridlib.Grid(self)
        self.grd_hub_details.CreateGrid(1, 4)      #CreateGrid(rows,cols)
        self.InitHubDetailsGrid(self.grd_hub_details)
 
        #Bind Grid Events-----------------

        self.btns=[]
 
        #Create Hub Button Bar---------------------
        #create 4btns and arannge them in horiz line,
        #assign each btn text and mapp it to the OnClick Event handler
        for b in range(len(BtnBar)):
            btn_id,txt,pic,toolTip = BtnBar[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(self, btn_id, bmp, (20, 20),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)


            self.btns.append(newBtn)
            # wx.ALL,5 this keeps a space bettween buttons

        #----------------
        for x in  xrange(MAX_CELLS):
            self.cells.append( meter(self,log,x,("cell %s" % x), self.no_connect_value))

        self.DoControlLayoutAndSizers()

        #Create a general purpose timer for the hub
        self.hubTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnHubTimer, self.hubTimer)
        wx.CallLater(500, self.StartHub)

    #----------- Set Hub Parameters -----------------------
    def SetParams(self, parms):   
        self.parms = parms
         
    #----------- End Hub __init___--------------------------
    def DoControlLayoutAndSizers(self):
        '''Size and layout the controls for a hub.
        Admin users can see all controls.
        Reg users can only see conxt and disconnect buttons
        ''' 
        vhubSizer = wx.BoxSizer(wx.VERTICAL)  ### sizer for grid and btns(Top of hubPage
        vertSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL) ### Horizontal sizer for buttons(Top of hubPage
        grdSizer = wx.GridSizer(rows=4, cols=4, vgap=15, hgap=15)

        for btn in  self.btns:
            btnSizer.Add(btn,0,wx.EXPAND|wx.ALL, 5)

        #add connection bar/ to left of buttons
        #btnSizer.Add(self.cnxt_bar,0,wx.ALL, 10)
        btnSizer.Add(self.grd_hub_details,0, wx.ALL,5)
                     
    
        #the line of btns(btnSizer) on top, then grid
            
        vhubSizer.Add(btnSizer,0,wx.EXPAND)
            
        vertSizer.Add(vhubSizer, 0,wx.EXPAND|wx.TOP, 5)
        #---------------
   
        vertSizer.Add(self.text1, 0,wx.EXPAND|wx.ALL,5)
        

        for cell in  self.cells:
            grdSizer.Add(cell,0,wx.EXPAND)

        vertSizer.Add(grdSizer,0,wx.EXPAND|wx.ALL,5)
        self.SetSizer(vertSizer)
        
 
    #----------- Start Hub --------
    def StartHub(self):
        ''' Start the Hub code'''
        self.hubCommTimeoutCount = 0
        self.hubTimer.Start(250)
        self.DisableHub()
        #INIT any controls that need parms values
        for parm in self.parms:
            option,val = parm
            if option == 'name':
                self.text1.SetLabel(val)


            
            if option == 'max_weight':
                self.max_weight = val       # val = "2 Ton" or "5 Ton"
                
    #Communications Timer Event.
        
    def OnHubTimer(self,evt):
        if (self.hubCommTimeoutCount > 0):
            self.hubCommTimeoutCount = self.hubCommTimeoutCount -1

            if self.hubCommTimeoutCount <= 0:
                self.DisableHub()
                self.grd_hub_details.SetCellValue(0,2,"")
                self.grd_hub_details.SetCellValue(0,0,"")
#                for col in range(self.cnxt_bar.GetNumberCols()):
#                    self.cnxt_bar.SetCellBackgroundColour(0, col, wx.BLACK)
#                    self.cnxt_bar.SetCellValue(0, col," ")

    #-----------------------------------   
    def	OnCellLeftClick(self,evt):
        self.dirty_grid = True
       
        self.grid.SetCellAlignment(evt.GetRow(), evt.GetCol(),wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grid.SetCellFont(evt.GetRow(), evt.GetCol(),wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.grid.SetCellTextColour(evt.GetRow(),evt.GetCol(), YELLOW)
        #print "GetCellValue", self.grid.GetCellValue(evt.GetRow(),evt.GetCol())

        evt.Skip()
 
    #- Button bar event handlers -
    def OnClick(self, evt):
        ''''Btn Bar event handler '''
        if (evt.GetId() == BtnConnect_Id):
            self.ConnectHub()

        elif (evt.GetId() == BtnDisable_Id):
            self.DisableHub()

        elif (evt.GetId() == BtnSave_Id):
            self.SaveHubParam()
    
        elif (evt.GetId() == BtnCancel_Id):
            self.CancelHubParam()

    #- Connect to the hub         
    def ConnectHub(self):
        self.HubNB.DoHubConnect(self.hub_id,self.parms)
        self.hubCommTimeoutCount = 30
        # self.UpdateDataGUI(True)

    def DisableHub(self):
        ##print "DisableHub----"
        self.buf = []
        self.HubNB.DoHubDisable(self.hub_id,self.parms)
        # self.UpdateDataGUI(False)

        #Disable all loadcells
        for cell in self.cells:
            dctDisp = {}
            dctDisp["text"] = "EEEE"
         #   dctDisp["bar"]  = 0
            dctDisp['units'] = ""
            dctDisp['overload'] = "0"
            cell.CellDisplayUpdate(dctDisp)
            cell.reads.Reset()


    #---------------------------
    def InitHubDetailsGrid(self, grd):
        attr = gridlib.GridCellAttr()
        attr.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

        grd.SetRowAttr(0,attr)
        
        grd.SetDefaultCellAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER) 

        grd.SetRowLabelSize(0)
        grd.SetColLabelSize(15)
        grd.SetDefaultCellTextColour(wx.WHITE)
        grd.SetLabelTextColour(wx.WHITE)
        
        grd.DisableCellEditControl()
        grd.SetLabelBackgroundColour( wx.BLACK)
        grd.SetDefaultCellBackgroundColour(wx.BLACK)
        grd.DisableDragGridSize()
        grd.EnableEditing(False)
        
        grd.SetColLabelValue(0,"Total Weight")
        grd.SetColLabelValue(1,"Units")
        grd.SetColLabelValue(2,"Communications")
        grd.SetColLabelValue(3,"Cell Max Weight")
        grd.SetCellTextColour(0,2,wx.GREEN)
        
        
        for col in range(grd.GetNumberCols()):
            #bar.SetColAttr(col, attr)
            grd.SetColMinimalWidth(col,10)
            grd.SetColSize(col,100)

 
    #---------------------------
    def InitConnectBar(self, bar):
        bar.CreateGrid(1, 5)      #CreateGrid(rows,cols)
        attr = gridlib.GridCellAttr()
        
        
        attr.SetFont(wx.Font(6, wx.SWISS, wx.NORMAL, wx.BOLD))
            
        bar.SetDefaultCellTextColour(wx.WHITE)
        bar.SetLabelTextColour(wx.WHITE)
        #attr.SetColSize(2)
        bar.SetRowLabelSize(0)
        bar.SetColLabelSize(0)
        
        bar.DisableCellEditControl()
        bar.SetLabelBackgroundColour( wx.BLACK)
        bar.SetDefaultCellBackgroundColour(wx.BLACK)
        bar.DisableDragGridSize()
        bar.EnableEditing(False)
        bar.SetRowAttr(0,attr)
        for col in range(bar.GetNumberCols()):
            #bar.SetColAttr(col, attr)
            bar.SetColMinimalWidth(col,0)
            bar.SetColSize(col,20)

        
                
    def HubUpdateCells(self, buf = []):
        ''' write new values to load cells'''
        dct = self.parser.ParseData(buf)
        self.log.write(("HubUpdateCells %s" % dct),3)
        
        while dct["valid"] == True:
            cell_id = dct["cell_id"]
            self.UpdateConnectBar()
            self.units = dct["units"]

            #put the new weight data in cell text box
            dctDisp={}
            dctDisp["text"] = "---"  # --- is the disconnect value the cell is disconnected.
           # dctDisp["bar"]  = 0
            dctDisp["units"]  = dct['units']
            dctDisp["overload"]  = 0    
            
            if dct["weight"] < self.no_connect_value:    #NO_CONNECT_VALUE:
                dctDisp["text"] = str( dct["weight"])
               # dctDisp["bar"]  = (dct["weight"]*10 / self.max_weight_value)
                dctDisp["overload"]  = dct['overload']    
#                print "dctDisp:%s" % dctDisp 
                
            self.log.write("HubUpdateCells dctDisp %s" % dctDisp,5)
            self.cells[cell_id].CellDisplayUpdate(dctDisp)
            
            
            #Add new reading to cells read history, for data logger
            self.cells[cell_id].reads.AddRead(dct["weight"])
                        
            #reset timout, to show connectiong
            self.cells[cell_id].led_timeout = 10
            #get another dctionary.
            dct = self.parser.ParseData()

    def hubGetCellAvg(self):
        
        lst_cell_data = []
        
        for cell in self.cells:
            dctDisp = {}
            dctDisp['hub_name'] = self.name
            dctDisp['cell_id'] = cell.id

            dctDisp['time']    = time.time()
            avg_reads  = cell.reads.GetAvg()
            self.log.write("hubGetCellAvg readings %s" % cell.reads.readings,3)
            #Append valid avgerages to the dictionary
            self.log.write("hubGetCellAvg avg_reads %s" % avg_reads,3)

            if avg_reads["is_valid"]:
                dctDisp["value"] = avg_reads["avg"]
                dctDisp["max"]   = avg_reads["max"]
                lst_cell_data.append(dctDisp)

                dct_grp_grid = {}
                dct_grp_grid['hub_name'] = self.name
                dct_grp_grid['cell_id'] = cell.id
                dct_grp_grid['hub_id']  = self.hub_id
                dct_grp_grid['text']   = str( avg_reads["avg"])
#                dct_grp_grid["bar"]  = ( int (avg_reads["avg"]*10) / self.max_weight_value)

                
                #This is where I want to send to the groups or store the dctDisp For alter use
                #self.HubNB.UpdateGroupsHubData(dct_grp_grid)

            
        self.log.write("hubGetCellAvg lst_cell_data %s" % lst_cell_data,3)
        return lst_cell_data
        
    def UpdateData(self, buf):
        self.log.write("UpdateData",7)
        self.hubCommTimeoutCount = 20
##        self.buf = self.buf + buf
        self.HubUpdateCells(buf)
        
    def UpdateConnectBar(self):
        self.col_cell = (self.col_cell + 1)
        self.col_cell = self.col_cell % 6
#        self.col_cell = self.col_cell % self.cnxt_bar.GetNumberCols()
            
        s = '*****' * self.col_cell   
        self.grd_hub_details.SetCellValue(0,2,s)        #grid comm indicator
                #hubGetCellAvg
        lstAvg = self.hubGetCellAvg()
        log.write("lstAvg: %s" % lstAvg, 2)
        avg_val = 0
        for cell_avg in lstAvg:
            avg_val = int(cell_avg['value']) + avg_val
            
        self.grd_hub_details.SetCellValue(0, 0, str(avg_val)) #sets avg value in grid
        self.grd_hub_details.SetCellValue(0, 1, self.units) #sets units in the grid
        self.grd_hub_details.SetCellValue(0, 3, self.max_weight) #sets max weight in the grid
        
        #Assume 2 ton load cell
        self.no_connect_value = NO_CONNECT_VALUE_2_TON
        self.max_weight_value = MAX_2_TON_VALUE

        if self.max_weight == LOADCELL_TON_5:
            #2 ton loadcells send values > 20000 to indicate no connection
            self.no_connect_value = NO_CONNECT_VALUE_5_TON
            self.max_weight_value = MAX_5_TON_VALUE
            
        


#-------------------------------------------------        
class meter(wx.Panel):
    def __init__(self, parent, log,id=-1, name = "cell", no_connect_value = NO_CONNECT_VALUE_2_TON):
        wx.Panel.__init__(self, parent, -1, style = wx.SIMPLE_BORDER)
        self.parent = parent
        self.hub = parent
        self.log = log
        self.id  = id                   #assign each cell a unique nbr and name
        self.name = name                #assign each cell a name for display.
        #self.log.write( ("cell id: %s, name: %s") % (self.id, self.name) )


            
        self.reads = cell_reading(self.id, MAX_AVG_READS, LBS, no_connect_value)
        
        
        # Initialize Peak Meter control 1
        #self.vertPeak = PM.PeakMeterCtrl(self, -1, style=wx.SIMPLE_BORDER, agwStyle=PM.PM_VERTICAL)
        self.vertPeak = GetPeakMeter(self)

        #---------------------------
        # Create the LED display
        #self.led_value = gizmos.LEDNumberCtrl(self, -1, (25,175), (280, 50),
        #per vinnys request cell ids start at 1 not zero
        self.led_value = wx.TextCtrl(self,-1, "text", wx.Point(0, 0), wx.Size(100, 30),(wx.NO_BORDER | wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )
        self.led_id_txt = wx.TextCtrl(self,-1, "cell %s" % str(self.id+1), wx.Point(0, 0), wx.Size(100, 30),(wx.NO_BORDER | wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )

        self.led_id_txt.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        self.led_id_txt.SetForegroundColour(wx.WHITE)
        self.led_id_txt.SetBackgroundColour(wx.BLACK)
        #self.led_id_txt.SetSize((20,100))
        
        self.led_value.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        self.led_value.SetForegroundColour(wx.WHITE)
        self.led_value.SetBackgroundColour(wx.BLACK)

        # sets length,height
        self.led_value.SetSize((50,100))
        
        # Layout the two PeakMeterCtrl
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.vertPeak.SetSize((70,145))  #sets the size of meters for hub  (x,y)
        # but not the panel below it. This way I can keep them tight
        mainSizer.Add(self.led_id_txt,0, wx.EXPAND|wx.CENTER)
        mainSizer.Add(self.vertPeak, 0, wx.FIXED_MINSIZE|wx.CENTER,10)
        mainSizer.Add(self.led_value,0, wx.EXPAND|wx.LEFT|wx.RIGHT, 7)
        self.SetSizer(mainSizer)
        mainSizer.Layout()
        wx.CallLater(500, self.Start)

#        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)

    def Start(self):
        ''' Starts the PeakMeterCtrl. '''
        #self.vertPeak.Start(PEAK_METER_FULL_SCALLE)        # 18 fps
        self.log.write("hub:Start", 4)

    def CellDisplayUpdate(self,dct={"text":"","bar":0, 'units':'?',"overload":0}):
        #the 
        #dct["bar"] = int(dct["bar"]) * 280
        bar_value = int(dct["overload"])
        
        self.led_value.SetValue(dct["text"])

        self.log.write("dct[overload]%s" % (dct["overload"]), 5)

        self.vertPeak.SetData([bar_value],0, NUM_METER_BARS)
        
        #Update the groups cell value
        dctDisp={}
        dctDisp['hub_name'] = self.hub.name
        dctDisp['cell_id'] = self.id
        dctDisp['hub_id']  = self.hub.hub_id
        dctDisp['text']    = dct['text']
 #       dctDisp['bar']    =  dct['bar']
        dctDisp['units']  =  dct['units']
        dctDisp["overload"] = dct["overload"]
        #This is where I want to send to the groups or store the dctDisp For alter use
        self.hub.HubNB.UpdateGroupsHubData(dctDisp)






        
