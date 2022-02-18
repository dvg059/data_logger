
import  wx
from wxPython.wx import *
from wxPython.grid import *
import  wx.grid as gridlib
from cm_Defines import *
import  ConfigParser as CP
import cm_app as CM 
import string
#---------------------------------------------------------------------------
#Custom Grid prames,
LOGGER_GRID_TYPE = 0    #Custom Grid will use logger params
HUB_GRID_TYPE    = 1    #Custom Grid will use Hub params
GROUP_GRID_TYPE  = 2    #Custom 
#---------------------------------------------------------------------------
class CustomDataTable(wxPyGridTableBase):
    def __init__(self,data, gridType):
        self.data= data
        wxPyGridTableBase.__init__(self)
        
        if gridType == HUB_GRID_TYPE:
            self.colLabels = ['Hub Name', 'IP Addr', "IP Port", "Serial", "Cell Max Weight"]
            
            self.dataTypes = [wxGRID_VALUE_STRING, wxGRID_VALUE_STRING, wxGRID_VALUE_STRING, 
                              wxGRID_VALUE_STRING, wxGRID_VALUE_CHOICE + ":2 Ton, 5 Ton",]


        elif gridType == LOGGER_GRID_TYPE:
            self.colLabels = ['Logger Update Time Sec', 'Logger Base File Name']
            
            self.dataTypes = [wxGRID_VALUE_STRING, wxGRID_VALUE_STRING]

            
        elif gridType == GROUP_GRID_TYPE:
            self.colLabels = ['GroupName']
            
            self.dataTypes = [wxGRID_VALUE_STRING]
            
                          
    def GetNumberRows(self):
        return len(self.data) + 1
    def GetNumberCols(self):
        return len(self.data[0])
    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return true
    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''
    def SetValue(self, row, col, value):
        try:
            self.data[row][col] = value
        except IndexError:
            self.data.append([''] * self.GetNumberCols())
            self.SetValue(row, col, value)
            msg = wxGridTableMessage(self,                             # The table
                                     wxGRIDTABLE_NOTIFY_ROWS_APPENDED, # what we did to it
                                     1)                                # how many
            self.GetView().ProcessTableMessage(msg)
    def GetColLabelValue(self, col):
        return self.colLabels[col]
    def GetTypeName(self, row, col):
        return self.dataTypes[col]
    def CanGetValueAs(self, row, col, typeName):
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return true
        else:
            return False
    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)
#---------------------------------------------------------------------------
class CustTableGrid(wxGrid):
    def __init__(self, parent, data , gridType):
        wxGrid.__init__(self, parent, -1)
        self.table = CustomDataTable(data,gridType)
        self.SetTable(self.table, true)
        self.SetRowLabelSize(0)
        self.SetMargins(0,0)
        self.AutoSizeColumns(False)
        EVT_GRID_CELL_LEFT_DCLICK(self, self.OnLeftDClick)
        
    def OnLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
class SetupWindow(wxFrame):
    '''
        This setupWindow. Acts like a modless dialog box.
        it displays hub parameters (Connection, Name) For each page inthe
        the notebook
    '''
    def __init__(
            self, parent, ID, title,log, pos=wx.DefaultPosition,
            size=(500,650), style=wx.DEFAULT_FRAME_STYLE
            ):
        self.parent = parent
        self.log = log
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        
        
        self.BtnSave_Id = wx.NewId()
        self.BtnCancel_Id = wx.NewId()
        self.BtnExit_Id = wx.NewId()

        self.AddHub_Id = wx.NewId()
        self.RemoveHub_Id = wx.NewId()

        self.AddGroup_Id = wx.NewId()
        self.RemoveGroup_Id = wx.NewId()

        self.AddCellToGroup_Id = wx.NewId()
        self.RemoveCellFromGroup_Id = wx.NewId()


        
        self.dataGroupParms  = [['Group']]
        
        # default data for HubGridParmetes,
        #HubName, ipAddr, ipPort, Serial Port, MaxWeight
        self.data = [
            ["HubName", "192.200.100.50", "4001", ' ', LOADCELL_TON_2],
            ["HubName", "192.200.100.50", "4001", ' ', LOADCELL_TON_5],
            ["HubName", "192.200.100.50", "4001", ' ', LOADCELL_TON_5],
            ["HubName", "192.200.100.50", "4001", ' ', LOADCELL_TON_2],
            ]

        self.initwin()

        
    def initwin(self):
        self.panel = wxPanel(self, -1, style=0)
        
        self.ref= None
        
        #init grid1 with hub data
        self.data = []

        self.initHubData()   
        

        
        #------------- Label for Hub Setup Grid     
        #default data for dataLoggerParms
        #
        self.dataLoggerParms = [['500',"MotionLabs"]]

        lbl_hub_grid = LabelBorder(self.panel, wx.NewId(),"Hub Setup","motion_2.bmp")


        #--------------------------------------------
        grdSz = wx.GridSizer(rows=2, cols=3, vgap=3, hgap=3)
        vrtSz = wx.BoxSizer(wx.VERTICAL)
        #grid sizer for hub buttons
        grdSzHubBtn = wx.GridSizer(rows=2, cols=2, vgap=3, hgap=3)
        grdSzGrpBtn = wx.GridSizer(rows=2, cols=2, vgap=3, hgap=3)


        #Create Hub Button Bar---------------------
        #create btns and arannge them in horiz line,
        #assign each btn text and mapp it to the OnClick Event handler
        btnBar = [(self.BtnSave_Id,"Save","save_1.png","Save Changes"),
          (self.BtnCancel_Id,"Cancel","cancel_1.png","Cancel Changes"),
          (self.BtnExit_Id,"Exit","exit_1.png","Exit")]

        for b in range(len(btnBar)):
            btn_id,txt,pic,toolTip = btnBar[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(self.panel, btn_id, bmp, (15, 15),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)
            grdSz.Add(newBtn, 0, wx.EXPAND|wx.ALL, 5)

        #Create buttons to add and remove hubs
        #--------------------------------------
        btnBarHubs = [(self.AddHub_Id,"Add New Hub","add.png","Add Hub"),
          (self.RemoveHub_Id,"Remove Selected Hub","remove.png","Remove Hub")]
        
        #Hub buttons create btns and arannge them in horiz line,
        #assign each btn text and mapp it to the OnClick Event handler
        
        for b in range(len(btnBarHubs)):
            btn_id, txt, pic,toolTip = btnBarHubs[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(self.panel, btn_id, bmp, (15, 15),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)
            grdSzHubBtn.Add(newBtn, 0, wx.EXPAND | wx.ALL, 5)
        

        #Hub Add and Remove buttons should appear bettween label and grid
        
        vrtSz.Add(grdSz)            #Add,Cancel, Exit buttons
                                    #Lable that says logger Setup
                                    
        #----------------------------------------
        #Creates the grid for data logger parms
        lbl_logger_grid = LabelBorder(self.panel, wx.NewId(),"Data Logger Setup","motion_2.bmp")

        #self.gridLoggerSetup = CustTableGrid(self.panel,self.dataLoggerParms,LOGGER_GRID_TYPE)
        self.gridLoggerSetup = gridlib.Grid(self.panel)
        self.gridLoggerSetup.CreateGrid(1, 2)      #CreateGrid(rows,cols)
        self.gridLoggerSetup.SetColLabelValue(0,"Update Time Sec")
        self.gridLoggerSetup.SetColLabelValue(1,'Base File Name')

        self.gridLoggerSetup.SetColSize(0,175) #Logger update time
        self.gridLoggerSetup.SetColSize(1,150) #Logger update time
        self.gridLoggerSetup.SetSize((100,600))
        self.gridLoggerSetup.SetDefaultCellTextColour(wx.WHITE)
        self.gridLoggerSetup.SetDefaultCellBackgroundColour(wx.BLACK)
        self.gridLoggerSetup.SetDefaultCellFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
                
        self.gridLoggerSetup.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        
        #put values from ini file in the grid
        #get n show current update time 
        dl = CM.CDataLogParms()
        cur_update_time = str( dl.dlp_GetUpdateTime() )
        csv_file_name = dl.dlp_GetCSVFileName()
        csv_file_name = string.split(csv_file_name,"_")[0]        
        
        self.gridLoggerSetup.SetCellValue(0,0, cur_update_time )
        self.gridLoggerSetup.SetCellValue(0,1, csv_file_name)


        
        #Add label logger setup and add logger grid
        vrtSz.Add(lbl_logger_grid,0, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)       
                                     
        vrtSz.Add(self.gridLoggerSetup)   
        
        vrtSz.Add((60, 20), 0, wx.EXPAND)   # spacer bettween logger and hub gui                              
        

        #------------------------------------------

        #This creates the grid for the hub parms
        self.gridHubSetup = CustTableGrid(self.panel,self.data,HUB_GRID_TYPE)
        self.gridHubSetup.SetColSize(0,120) #hub name
        self.gridHubSetup.SetColSize(1,110)  #ip addr
        self.gridHubSetup.SetColSize(2,50) #ip port
        
        self.gridHubSetup.SetDefaultCellTextColour(wx.WHITE)
        self.gridHubSetup.SetDefaultCellBackgroundColour(wx.BLACK)
        self.gridHubSetup.SetDefaultCellFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
                
        self.gridHubSetup.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        vrtSz.Add(lbl_hub_grid,0, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)
      
        vrtSz.Add(grdSzHubBtn)      #Add Remove
        
        vrtSz.Add(self.gridHubSetup, 1, wxGROW|wxALL, 5)

 

        
        #------------------------------------------------------------
        #Add GroupHub label, buttons and grid ui controls
        #----------------------------------------
        #------------- Label for Hub Setup Grid     

        lbl_group_grid = LabelBorder(self.panel, wx.NewId(),"Group Setup","motion_2.bmp")
        
        
        #Creates the grid for data logger parms
        btnBarGroups = [(self.AddGroup_Id,"Add Group","add.png","Add New Group"),
          (self.RemoveGroup_Id,"Remove Group","remove.png","Remove Selected From Group")]

        for b in range(len(btnBarGroups)):
            btn_id, txt, pic,toolTip = btnBarGroups[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(self.panel, btn_id, bmp, (15, 15),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)
            grdSzGrpBtn.Add(newBtn, 0, wx.EXPAND|wx.ALL, 5)



#        self.gridGroupSetup = CustTableGrid(self.panel,self.dataGroupParms,GROUP_GRID_TYPE)
        self.gridGroupSetup = gridlib.Grid(self.panel)
        self.gridGroupSetup.CreateGrid(0, 3)      #CreateGrid(rows,cols)
        self.sw_InitGroupGrid(self.gridGroupSetup)


        
        #Add label logger setup and add logger grid
        vrtSz.Add(lbl_group_grid,0, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)  
        
        vrtSz.Add(grdSzGrpBtn)     
                                     
        vrtSz.Add(self.gridGroupSetup)

        
        self.panel.SetSizer(vrtSz)

    #------------------------------------
    def sw_SaveLogUpdateTime(self):
        '''Save user value, for time bettween log file updates'''
        
        time = self.gridLoggerSetup.GetCellValue(0,0)  
        csvFileName = self.gridLoggerSetup.GetCellValue(0,1)

        self.log.write( "sw_SaveLogUpdateTime1: time %s, %s" % (time,csvFileName))
        if time == "" or time == None:
            time = 5
        else:
            time = int(eval(time))
        
        if (time < 0):
            time = 5
        elif (time > 10000):
            time = 10000
        
        self.log.write( "sw_SaveLogUpdateTime: time %s" % time)
        dl = CM.CDataLogParms()
        
        dl.dlp_SetUpdateTime(time)

        csvFileName = self.gridLoggerSetup.GetCellValue(0,1)
        dl.dlp_SetCSVFileName(csvFileName)

        #self.gridLoggerSetup.SetCellValue( 0, 0, str(time) )
        #self.userTexts[0].SetValue(str(time))
        self.parent.HubNB.cm_Timer.Start(time * 1000)

    #----------------------------------------------------
    #-----------------------------------
    def sw_InitGroupGrid(self, grid):
        attr = gridlib.GridCellAttr()
        attr.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        attr.SetBackgroundColour(wx.BLACK)
        attr.SetTextColour(wx.WHITE)
        self.grp_rows_ids = []
        
        grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        #Group Name, HubName, Cell
        if grid.GetNumberRows() > 0:
            grid.DeleteRows(0, grid.GetNumberRows())

        groupObj  = CM.CHubGroupObj()
        group_ids_names = groupObj.gp_GetGroups()

        
        grid.SetColLabelValue(0,"Group Name")
        grid.SetColLabelValue(1,"Hub Name")
        grid.SetColLabelValue(2,"Cell")
        
        #get list of group ids and names
        for group in group_ids_names:
            grp_id, grp_name = group
            

            grid.AppendRows(1)
            cur_row = grid.GetNumberRows() -1


            grid.SetRowAttr(cur_row, attr)

            hub_ids = groupObj.gp_GetHubsForGroup(grp_id)
            cell_ids = groupObj.gp_GetCellsForGroup(grp_id)

            grid.SetCellValue(cur_row,0,grp_name)

            #Keeps track of what group vs rows.
            #User selects a row, I can look up the grp id
            self.grp_rows_ids.append( (cur_row,grp_id) )
        
            for hub_id in hub_ids:
                self.log.write( "hubObj:hbsGetHubIdName:%s" % hub_id)

    #-----------------------------------------------------    
    def initHubData(self):
        ''' Were initializing the gird control for hub data 
        in the setup window. 
        Iterate the the hub pages and get the parameters (name, conxt string
        and put them in the grid
        '''

        for page_nbr in xrange(self.parent.HubNB.GetPageCount()):
            hub_page = self.parent.HubNB.GetPage(page_nbr)
            self.log.write("page name %s, params %s" % (hub_page.name,hub_page.parms),5)
            
            #default values, for hub record
            hub_name = "HubName"
            ip_addr = "192.200.100.50"
            ip_port = "4001"
            serial_port = " "
            max_weight = LOADCELL_TON_2
            row =  [hub_name, ip_addr, ip_port ,serial_port,max_weight ]
        
            #exptd param key,value parms format is
            #   [('name', 'hub1FFFFF'), ('connect', '192.200.100.50,4001')]
            #iterate thru each hubpage and grab its paramters
            #print hub_page.parms
            
            for ky, val in hub_page.parms:
                if ky == "name":
                    #print "new hubname", val
                    row[0] = string.strip(val)   ##name 
                    
                elif ky == "connect":
                    #connect parameter: ('connect', '192.200.100.51,40001')
                    cnxt = val.split(",")

                    if (len(cnxt) > 1):            
                        row[1] = cnxt[0]  ##ipaddr
                        row[2]= cnxt[1]  ##port to listen

                elif ky == "serial":
                    row[3] = val   
                
                elif ky == "max_weight":
                    row[4] = val
                    
            self.data.append(row)
    #------------------------------------
    def SaveHubParam(self):
        '''Extract grid values and save them to ini file'''
        hub  = CM.CHubsObj()
        
        for row in range(self.gridHubSetup.GetNumberRows()-1):
            newparms = []
           # print "self.parent.HubNB.%s" % dir(self.parent.HubNB)
            hub_page = self.parent.HubNB.GetPage(row)

            #retrive, save and update new hub_page name
            val = string.strip(self.gridHubSetup.GetCellValue(row,0))
            newparms = [("name",val)]
            hub_page.name = val
            hub_page.text1.SetLabel(hub_page.name)
            hub.hbs_UpdateHub(hub_page.hub_id, 'name', val)

            self.parent.HubNB.SetPageText(row,val)

            #reteive and save hub_page connect string
            ipadr_port = string.strip(self.gridHubSetup.GetCellValue(row,1)) \
                         +"," + string.strip(self.gridHubSetup.GetCellValue(row,2))
            
            newparms.append( ("connect", ipadr_port))
            hub.hbs_UpdateHub(hub_page.hub_id, 'connect', ipadr_port)

            #retrieve and save hub_page serial string
            serial = string.strip(self.gridHubSetup.GetCellValue(row,3))
            newparms.append( ("serial", serial))
            hub.hbs_UpdateHub(hub_page.hub_id, 'serial', serial)
            
            #retrieve and save the max weight values
            max_weight = string.strip(self.gridHubSetup.GetCellValue(row,4))
            newparms.append(('max_weight', max_weight))
            hub.hbs_UpdateHub(hub_page.hub_id,'max_weight', max_weight)
            
            hub_page.SetParams(newparms)

        self.initwin()

    def sw_UpdateHubData(self):     
        sz= self.panel.GetSize()    #resets the grid with new hub data
        self.panel.Destroy()
        self.initwin()          # the grid window now displays it
        self.panel.SetSize(sz)
        
        
    def sw_SaveGroupParam(self):
        '''Cycle thru the group grid and settings '''
        groupObj  = CM.CHubGroupObj()
        for row_grpId in self.grp_rows_ids:
            row, grpId = row_grpId
            
            grp_nm = string.strip(self.gridGroupSetup.GetCellValue(row,0))
            self.log.write("sw_SaveGroupParam, grpId(%s),grp_nm(%s)" % (grpId,grp_nm),6)

            if len(grp_nm) > 0 and grpId >= 0:
                groupObj.gp_SetGroupName(grpId, grp_nm)
           
    def OnClick(self, evt):
        if evt.GetId() == self.BtnExit_Id:
            '''Close window via exit button'''
            self.Destroy()
                    
        elif evt.GetId() == self.BtnSave_Id:
            self.sw_SaveLogUpdateTime()
            self.sw_SaveGroupParam()
            self.SaveHubParam()
            #self.initwin()

            
        #-------------------------------------
        elif evt.GetId() == self.BtnCancel_Id:
            #Cancel
            self.sw_UpdateHubData()  #Init Penel
            
        #-------------------------------------
        elif evt.GetId() == self.AddHub_Id:
            self.parent.OnAddHub()  #adds a hub tab to note book
            self.sw_UpdateHubData() #tell the grid that hub data has changed
            
        #-------------------------------------
        elif evt.GetId() == self.RemoveHub_Id:
            cur_row = self.gridHubSetup.GetGridCursorRow()
                        
            hub_name = self.gridHubSetup.GetCellValue(cur_row, 0)
            
            self.log.write("cur_row:%s, RemoveHub:%s" % (cur_row, hub_name),5)
            question = "Are you sure you want to delete Hub: %s" % hub_name
            
            yes_no = CM.YesNo(self,question, caption = 'Delete?')
            if yes_no == True:
                self.parent.HubNB.DoDeletePage(cur_row)

            self.sw_UpdateHubData() #tell the grid that hub data has changed
        #----------------------------------------------
        elif evt.GetId() == self.AddGroup_Id:
            group  = CM.CHubGroupObj()
            new_grp_id = group.gp_AddGroup()
            self.log.write( "AddGroup:%s, newGroupId %s " % (group.gp_GetGroups(),new_grp_id), 5)
            self.sw_InitGroupGrid(self.gridGroupSetup)

        #evt.GetID------------------------------------
        elif evt.GetId() == self.RemoveGroup_Id:
            group  = CM.CHubGroupObj()
            cur_row = self.gridGroupSetup.GetGridCursorRow()
            group_name =  self.gridGroupSetup.GetCellValue(cur_row, 0)
            
            question = "Are you sure you want to delete Group: %s" % group_name
            
            yes_no = CM.YesNo(self,question, caption = 'Delete?')

            
            if yes_no == True:
                grp_id = -1
                for row_id in self.grp_rows_ids:
                    row, grp_id = row_id
                    if row == cur_row:
                        grp_id = grp_id
                        break
                self.log.write("OnClick:RemoveGroup_Id id=%s, name=%s" % (grp_id, group_name),5)
                
                group.gp_RemoveGroup(grp_id)
                self.sw_InitGroupGrid(self.gridGroupSetup)

    #---------------------------------------------------    
    def sw_UpdateGrid(self):
        print "self.InitGrid(self.gridHubSetup)"
        print "self.sw_SaveLogUpdateTime() dont forget this, you need to save"

#---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    app = wx.PySimpleApp()
    frame = TestFrame(None, sys.stdout)
    frame.Show(True)
    app.MainLoop()


#---------------------------------------------------------------------------
