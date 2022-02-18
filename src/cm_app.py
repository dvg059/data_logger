import  sys
import  wx
import  wx.lib.newevent
import  string
import  os
import  frmCMCell as CMCell
import  socket
import  thread
import  ast

##ConfigParser Reads and Writes INI settings
import  ConfigParser as CP
import  traceback as TB
import wx.grid  as  gridlib
import time
import datetime
import copy
import pprint

from  cm_Defines import *
from frmSetupWindow import  *

import hub_tree as HT



color =wx.Colour(80,10,10)
##DV--------------------------------------
##DV April 13 Adding UserLogin levels (USER,Admin)
##DV Mar 22 2012: Added Menu. Users can now add hubs,via a menu option
##  AddHub adds a page by adding the next available hubId section to the
##  to the ini file. Then reload the ini file.
##DV Mar 16 2012: Adding the and INI file section hubx (x = 0 - 9)
##   will generate a new hub page the default name is the same as the
##   the section name. INI sections :[hub3], [hub1], [hub0] will create
##  three hub pages. With the default hub names matching the sections.
##DV Mar 13 2012: Adding INI file settings for hub and cell.
##   If no ini file exists create one. Default one page 8 loadcells

##DV Mar 07 2012: Adding dialog message box
##DV Mar 07 2012: Adding splash screen.
YELLOW =    wx.Colour(255,255,0)

ID_SETUP_WINDOW = wx.NewId()

##----------------------------------------
APP_DEBUG_FILE = "CMDBG.txt"

##----------------------------------------
#INI file sections and format
#[hubXX]  where XX is the hub id 0 to 15
#name     name of the hub, displayed on tab
#YY       YY is cell id 0 to 7, name, comm_property.
#
APP_INI_FILE = os.getcwd() + "cm_file.ini"
INI_HUB_SECTION = "hub0"
LOGGER_INI_FILE = "logger.ini"
# default cell values from ini file , cell name, ip_addr
INI_DEFAULT_CELL_OPTION = "cell_nm_0"
INI_DEFALUT_CONNECT_OPTION = "192.200.100.51,40001"

# default hub values from ini file , hub  name, ip_addr
INI_DEFAULT_HUB_OPTION  = "hub_nm_0,192.200.100.51"

# default socket port
INI_DEFAULT_SOCKET_PORT = 40001

#Ini data logger variables
INI_LOG_SECTION = "logger"          #section for datalogger
INI_LOG_COUNT_OPTION = "count"      #number part of counter file
INI_LOG_NAME_OPTION = "name"        #name of datalog file
MAX_LOG_COUNT_NBR   = 99
INI_LOG_TIME = "logtime"            #time bettween log file updates

#--------------------------


#---------------------------
dctHubTbl={"name":"hub","section":"hub0","connect":"192.200.100.50, 4001"}
#sample use and invocation
#ld={0:dctHubTbl}
#ld[0]["name"]
#---------------------------
#---------------------- Socket Data Structs
# This creates a new Event class and a EVT binder function
(UpdateSocketEvent, EVT_UPDATE_SOCKETDATA) = wx.lib.newevent.NewEvent()

(UpdateLoggerEvent,  EVT_UPDATE_LOGGER_EVENT) = wx.lib.newevent.NewEvent()
(AddRemoveCellEvent, EVT_ADD_REMOVE_CELL_EVENT) =  wx.lib.newevent.NewEvent()

class CLog():
    def __init__(self,dbgLevel=0):
        self.debug_level = dbgLevel
        #self.write( "Clog __init__ %s" % self.debug_level)
        
    def write(self,text, level=5):
        pp = pprint.PrettyPrinter(indent=4)

        if (level >= self.debug_level):
            s = "Clog:write\t %s" % text
            pp.pprint(s)
            
#---------------------------

#log = CLog(DEFAULT_LOG_LEVEL)
log = CLog(RELEASE_LOG_LEVEL)

#-----------------------------
def YesNo(parent, question, caption = 'Yes or no?'):
    dlg = wx.MessageDialog(parent, question, caption, wx.YES_NO | wx.ICON_QUESTION)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result

#------------------------------        
class CHubsObj():
    '''
        defines hub names, cell names, connection params
    '''
    def __init__(self, hub_file = "hub_file.ini",
                 max_hubs = MAX_HUBS,
                 max_cells = 8,
                 section_name = "hub_",
                 log_level=0):
        
        self.config_file = hub_file
        
        self.max_hubs = max_hubs
        self.max_cells = max_cells
        self.log_level = log_level
        self.section_name = string.strip(section_name)

        # ensure name is terminated with '_', use for spliting section names and ids
        if self.section_name[-1] != '_':
            self.section_name = self.section_name + '_'

    #------------------------------        
    def log(self, text, level = 5):
        if self.log_level > level:
            print text
    #------------------------------  
    def hbs_GetHubCellCord(self,hub_id):
        items = self.hbs_GetHubIdName(hub_id)
        
        #print "hbs_GetHubCellCord", hub_id, items
        if items != None:
            for item in items:
                item_name, item_value = item
                if item_name == "hub_cell_xy":
                    return ast.literal_eval(item_value)         
                    #Convert string to dict and return, item_value
                    # each cell has xy, coordin and a cell id 
                    # [{'y': 116, 'hub_id': 1, 'cell_id': 4, 'x': 233}, 
                    # {'y': 134, 'hub_id': 1, 'cell_id': 6, 'x': 112}]

              
    def hbs_GetHubIdName(self, id):
        '''
        If hub id exist return parms for requested hub id.
        else return None
        '''
        cp_obj = CP.ConfigParser()
        cp_obj.read(self.config_file)
        section = "%s%s" %(self.section_name,id)
        
        if cp_obj.has_section(section):
            return cp_obj.items(section)
            #return (id, cp_obj.get(section,'name'),cp_obj.get(section,'connect'),cp_obj.get(section,'serial'))
        else:
            return None
    #------------------------------        
    def hbs_GetHubIdsNames(self, ids_names= []):
        cp_obj = CP.ConfigParser()
        cp_obj.read(self.config_file)
 
        for section in cp_obj.sections():
            
            self.log("hbs_GetHubIdsNames: section:%s" % section)
            #section_name is the base for all sections
            # i.e section name is hub_xx, where hub_ = section_name, xx is the id
            
            if self.section_name in section:
                nm, id = string.split(section, self.section_name)
                ids_names.append( ( int(id), cp_obj.get(section,"name")))                
            #len of ids and names shld match
        return len(ids_names)
    #------------------------------        
    def hbs_AddHub(self, name = None):
        cp_obj = CP.ConfigParser()
        cp_obj.read(self.config_file)

        hub_added_success = False
        ids = range(1,self.max_hubs)
        ids.sort()
        #print "hbs_AddHub ids: %s" % (ids)
        for id in ids:
            section = self.section_name + str(id)
            
            if (section  in cp_obj.sections()) == False:
                # this id and section is available, add it
                cp_obj.add_section(section)
                
                if (name == None):
                    #create a default name if none given, Users dont like to see 0
                    #so instead of just name = section(hub_0 to hub_xx), its now hub_1 to xx
                    name = "hub_" + str(int(id))
                    
                cp_obj.set(section, 'name', name)

                cp_obj.set(section, "connect", ",")

                cp_obj.set(section, "serial","")
                
                cp_obj.set(section, 'max_weight', LOADCELL_TON_2)
                
                lst = range(0,self.max_cells)
                lst.sort()
                lst = map(str,lst)
                cp_obj.set(section,'cells',lst)
                
                lst=[]
                #stored (hubId,cellId,(X,Y))pos of loadcell on the graphic, format [(hubID, loadcellID, (x,y) ), ...] 
                cp_obj.set(section,"hub_cell_xy",lst)    
                            
                hub_added_success = True    
                self.gp_WriteFile(cp_obj)
                break
            
        if hub_added_success == True:
            return id
        else:
            id = None
        
    #------------------------------        
    def hbs_UpdateHub(self, id, option, val):
            '''
                if option = name, val = 'name'
                if option = connect, val 'XXXX,YYYY',
                         XXXX=ipadd=192.200.100.50,
                         yyy = 001
                         
                if option == max_weight, value = "2 Ton" or "5 Ton"
            '''
            cp_obj = CP.ConfigParser()
            cp_obj.read(self.config_file)
            section = '%s%s' % (self.section_name, id)

            if cp_obj.has_section(section):
                cp_obj.set(section,option, val)
                self.gp_WriteFile(cp_obj)
                
                

    # hbs_RemoveHubCellCord, remove a cell and assoc coords frrom the object
    def hbs_RemoveHubCellCord(self,hub_id,cell_id):
            cp_obj = CP.ConfigParser()                          
            #check if the hub section is defined
            cp_obj.read(self.config_file)
            
            section = '%s%s' % (self.section_name, hub_id)   
            
                   
            if cp_obj.has_section(section):
                #the hub_id section should be defined
                #the the cell xy coordinates
                
                cell_cords = cp_obj.get(section, "hub_cell_xy")
#                print "hub_cell_xy",cell_cords
                
                cell_cords = ast.literal_eval(cell_cords)
#                print "cell_cords",cell_cords
                #exptd format for cell_cords
                #cell_cords [{'y': 1000, 'hub_id': 1, 'cell_id': 0, 'x': 100}]
                found = False
                
                for ii in range(len(cell_cords)):
                    if ((cell_cords[ii]['hub_id'] == hub_id) and (cell_cords[ii]['cell_id'] == cell_id)):
                        
                        found = True
                        break

                if found == True:
                    #delete requsted enry and save itt
                    print "hbs_RemoveHubCellCord 0 ",hub_id,cell_id, ii

                    print "hbs_RemoveHubCellCord 1 ",cell_cords
                    del(cell_cords[ii])
                    cp_obj.set(section, 'hub_cell_xy', cell_cords)
                    print "hbs_RemoveHubCellCord 2 ",cell_cords
                
                    self.gp_WriteFile(cp_obj)   #sccuessfull removal rex`turn true
                    return True
                else:
#                print "hbs_AddHubCellCord_exit",section
                    return False    #cell id not found return fasle

            return False  #hub id was not found, could not remove  return fasle
                       
                        
    #hbs_AddHubCellCord Add a new cell pos to given hub
    def hbs_AddHubCellCord(self,hub_id,cell_id,xpos,ypos):
            cp_obj = CP.ConfigParser()                          #check if the hub section is defined
            cp_obj.read(self.config_file)
            
            section = '%s%s' % (self.section_name, hub_id)   
            
                   
            if cp_obj.has_section(section):
                #the hub_id section should be defined
                #the the cell xy coordinates
                
                cell_cords = cp_obj.get(section, "hub_cell_xy")
#                print "hub_cell_xy",cell_cords
                
                cell_cords = ast.literal_eval(cell_cords)
#                print "cell_cords",cell_cords
                #exptd format for cell_cords
                #cell_cords [{'y': 1000, 'hub_id': 1, 'cell_id': 0, 'x': 100}]
                found = False
                
                for ii in range(len(cell_cords)):
                    if ((cell_cords[ii]['hub_id'] == hub_id) and (cell_cords[ii]['cell_id'] == cell_id)):
                        cell_cords[ii]['x'] = xpos
                        cell_cords[ii]['y'] = ypos
                        
                        #the cell was found so update its x,y cords an leave
                        found = True
                        
                        
                if found == False:
                    #The cell wasnt found so add the new cell and its x,y cords to the list
                    d = {"hub_id":hub_id, "cell_id":cell_id, "x":xpos, "y":ypos}
                    cell_cords.append(d)
                
                cp_obj.set(section, 'hub_cell_xy', cell_cords)
                
                self.gp_WriteFile(cp_obj)
                return True
            else:
#                print "hbs_AddHubCellCord_exit",section
                return False
    #------------------------------        
    def hbs_RemoveHub(self, id = -1):
        cp_obj = CP.ConfigParser()
        cp_obj.read(self.config_file)
        success = False
        
        section = "%s%s" % (self.section_name, id)
        if cp_obj.has_section(section):
            cp_obj.remove_section(section)
            success = True
            self.gp_WriteFile(cp_obj)
 
        return success
    #------------------------------        
    def gp_WriteFile(self, cp_obj):        
        fp = open(self.config_file,"w+")
        cp_obj.write(fp)
        fp.close()

#------------------------------------
class CUserObj:
        def __init__(self,user_file =  "user_file.ini"):
            self.config_file = user_file
            
        def usr_SetUser(self, user_level = USER_LEVEL):
            '''
            Open the user ini file and set the level option.
            [user]
            level = ADMIN
            '''
            # Return the list of cells for the requested grp
            ini_obj = CP.ConfigParser()
            ini_obj.read(self.config_file)
            section = 'user'
                
            if (ini_obj.has_section(section) == False):
                ini_obj.add_section(section)
    
            ini_obj.set(section, 'level', user_level)
            
            self.usr_WriteFile(ini_obj)
        
        def usr_GetUserLevel(self):
            '''
            Return the current user level,
            If no user level is defined set a default user level
            '''
            ini_obj = CP.ConfigParser()
            ini_obj.read(self.config_file)
            section = 'user'
                
            if (ini_obj.has_section(section) == False):
                self.usr_SetUser()
                
            return int( ini_obj.get(section,"level") )               

        def usr_GetImageFile(self):             #Retrieves the name of the image file for dragNdrop
            ini_obj = CP.ConfigParser()
            ini_obj.read(self.config_file)
            section = 'image_file'
            
            if (ini_obj.has_section(section) == False):
                return ''
            else:
                return ini_obj.get(section,'name')
            
        def usr_SetImageFile(self, file_nm):             #Saves the name of the image file for dragNdrop
            if len(file_nm) <= 0:
                return False
            
            ini_obj = CP.ConfigParser()
            ini_obj.read(self.config_file)
            section = "image_file"
            
            if (ini_obj.has_section(section) == False):
                ini_obj.add_section(section)            

            ini_obj.set(section, 'name', file_nm)
            
            self.usr_WriteFile(ini_obj)
            return True
            
            
            

        def usr_WriteFile(self, ini_obj):        
            cp_fp = open(self.config_file,"w+")
            ini_obj.write(cp_fp)
            cp_fp.close()
            

class CHubGroupObj():
    '''
        cells of cells from user selected hubs
        user can add or remove cells from a group
    '''
    def __init__(self,group_file = os.getcwd()+"\\group.ini", max_groups = 10):
        #the init files checks if a group file exists
        #if a group file exist read and parse it into a list of dictionarys
        #the dictionary keys are id, name, cells, hubs
        # where id = group id, name = hub name, hubs =  hub ids, cells = cell ids
        #
        self.group_file = group_file
        
        self.max_groups = max_groups
        self.groups = []

    def gp_ConvertStringToArray(self,str=''):
        # sample parm str = '[1,2,4,5,10,15]'
        # sample return = [1,2,4,5,10,15]
        if len(str) > 2:
            str = string.split(str[1:-1],',')
            #sample  str = ['1', '2', '4', '5', '10', '15']
            #convert the list of string to integers and return
            str = map(int,str)
        else:
            str = []
            
        return str
    
    def gp_AddHubCell(self,  grp_id, hub_id, cell_id):
        # if cell n hub are not in the given grp_id then add them
        # return True if the hub,cell pair is added
        # return False if the hub,cell pair not added/already in group
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)

        hub_cell_added_group = False
        
        log.write("gp_AddHubCell:Start grp_id:%s, hub:%s, cell:%s" % (grp_id, hub_id,cell_id),6)

        for section in grp_obj.sections():
            #split a section into its string and id params
            #check if the id matches the one requested from caller
            name,id = string.split(section,'_')

            if int(id) == int(grp_id):

                # requested grp found
                # convert the list of cell and hub ids to integer
                cells = self.gp_ConvertStringToArray( grp_obj.get(section,'cells') )
                hubs  = self.gp_ConvertStringToArray( grp_obj.get(section,'hubs') )

                log.write("gp_AddHubCell:Found grp_id:%s, hubs(%s), cells(%s)" % (id, hubs, cells),5)
                log.write("gp_AddHubCell:Found hub_id in hubs:%s)" % ( (hub_id in hubs)),5)

                found = False
                #Check if the hub,cell pair already in the list
                for ii in range(len(hubs)):
                    if hubs[ii] == hub_id and cells[ii] == cell_id:
                        found = True
                        break
                    
                if  found == False:
                    #hub, cell pair not in the group, add them
                    log.write("gp_AddHubCell: Adding to Group:%s, hub_id:%s, cell_id:%s" % (grp_id, hub_id,cell_id))
                    hubs.append(hub_id)
                    grp_obj.set(section,'hubs', hubs)
                    
                    cells.append(cell_id)
                    grp_obj.set(section,'cells',cells)
                
                    self.gp_WriteFile(grp_obj)
                    hub_cell_added_group = True
                else:
                    log.write("cell(%s) and hub(%s) already in group:%s" % (cell_id, hub_id, grp_id),6)
                    hub_cell_added_group = False

                break

        return hub_cell_added_group
    
    def gp_GetIdFromSectionName(self, name):
        str,id = string.split(name,"group_")
        return int(id)
    
    def gp_GetGroups(self):
        # Return the list of cells for the requested grp
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)
        ids = map(self.gp_GetIdFromSectionName, grp_obj.sections())
        ids_names = []

        for section in grp_obj.sections():
            
            ids_names.append((self.gp_GetIdFromSectionName(section), grp_obj.get(section,'name')))

        return ids_names
        


    def gp_GetCellsForGroup(self, grp_id):
        # Return the list of cells for the requested grp
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)
        
        section = 'group_%s' % grp_id
        
        if grp_obj.has_section(section):
            if grp_obj.has_option(section, "cells"):
                return self.gp_ConvertStringToArray( grp_obj.get(section,'cells') )
        else:
            return []
        
    def gp_GetHubsForGroup(self, grp_id):
        # Return the list of cells for the requested grp
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)
        section = 'group_%s' % grp_id

        hubs = []
        if grp_obj.has_section(section):
            if grp_obj.has_option(section, "hubs"):
                hubs = self.gp_ConvertStringToArray( grp_obj.get(section,'hubs') )
                if hubs == None:
                    hubs=[]
        return hubs
        
    def gp_RemoveGroup(self,grp_id):
        # remove/delete the group with the given id
        # return true if section was found and deleted,
        # return false is section not found

        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)
        sec_to_del = 'group_%s' % grp_id
        
        if grp_obj.has_section(sec_to_del):
            grp_obj.remove_section(sec_to_del)
            self.gp_WriteFile(grp_obj)
            return True

        else:
            return False

    def gp_RemoveCellInGroup(self, grp_id, hub_id,cell_id):
        ''' remove given hub cell the group
            return true
        '''
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)

        sections = grp_obj.sections()
        found = False
        
        section = ('group_%s' % grp_id)
            
        if ( section in grp_obj.sections()) == False:
            log.write("gp_RemoveCellInGroup: GroupId invalid:%s)" % ( section),6)
            return found
        
        cells = self.gp_ConvertStringToArray( grp_obj.get(section,'cells') )
        hubs  = self.gp_ConvertStringToArray( grp_obj.get(section,'hubs') )
       
        #Check if the hub,cell pair already in the list
        for ii in range(len(hubs)):
            if hubs[ii] == hub_id and cells[ii] == cell_id:
                hubs.pop(ii)
                cells.pop(ii)
                grp_obj.set(section,'hubs', hubs)
                    
                grp_obj.set(section,'cells',cells)

                self.gp_WriteFile(grp_obj)

                log.write("gp_RemoveCellInGroup:Found hub_id:%s, cell_id:%s)" % ( hub_id,cell_id),4)
                found = True
                break
            
        return found        

    def gp_IsHubInGroup(self, grp_id,hub_id):
        '''
             If the given hub_id is in the 
            group return true.
            1: Get the section name append the grpId to word group_
            2: Get the name and  list of all hubs for this section
            3: Is the req hub_id in the list of hubs
        '''
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)

        found = False
        #Get the section for this group
        section = ('group_%s' % grp_id)
        
        #If the sections is not valid return false    
        if ( section in grp_obj.sections()) == False:
            log.write("gp_IsHubInGroup: GroupId invalid:%s)" % ( section),6)
            found = False
        else:
            # The section is found, Get the list of hubs for this group.
            hubs  = self.gp_ConvertStringToArray( grp_obj.get(section,'hubs') )
            grp_name = grp_obj.get(section,'name')
          
            if int(hub_id) in hubs:
                log.write("gp_IsHubInGroup hub_id(%s) in group(%s)" % (hub_id,grp_name) )
                found = True
                
            return found        

        

    def gp_IsCellInGroup(self, grp_id, hub_id,cell_id):
        ''' if the given hub cell is part of the group
            return true
        '''
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)

        sections = grp_obj.sections()
        found = False
        
        section = ('group_%s' % grp_id)
            
        if ( section in grp_obj.sections()) == False:
            log.write("gp_IsCellInGroup: GroupId invalid:%s)" % ( section),6)
            return found
        else:
            cells = self.gp_ConvertStringToArray( grp_obj.get(section,'cells') )
            hubs  = self.gp_ConvertStringToArray( grp_obj.get(section,'hubs') )

            #log.write("gp_IsCellInGroup:Found grp_id:%s, hubs(%s), cells(%s)" % (id, hubs, cells),6)
            #log.write("gp_IsCellInGroup:Found hub_id in hubs:%s)" % ( (hub_id in hubs)),6)
            
            #Check if the hub,cell pair already in the list
            for ii in range(len(hubs)):
                if hubs[ii] == hub_id and cells[ii] == cell_id:
                    log.write("gp_IsCellInGroup:Found hub_id:%s, cell_id:%s)" % ( hub_id,cell_id),6)
                    found = True
                    break
                
            return found        

    def gp_SetGroupName(self, grp_id,grp_name):  
        ''' Set/change the name  of group id'''
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)
        
        if (grp_id < 0) or (grp_name == None):
            log.write("gp_SetGroupName: Error Setting Name:grp_id(%s), name(%s)" % (grp_id,grp_name), 6)
            
            return False
        
        section = ('group_%s' % grp_id)
        if ( section in grp_obj.sections() ):
            grp_obj.set(section,'name', grp_name)

        self.gp_WriteFile(grp_obj)
        return True
          
    def gp_AddGroup(self,  name = None, hub_id = [], cell_id = []):
        #add a cell to the given grp, 
        grp_obj = CP.ConfigParser()
        grp_obj.read(self.group_file)

        sections = grp_obj.sections()
        success = False

        # iterate thru the sections, find first available grp_id
        # sections have the formate group_##,
        # where, group is the default name and ## is the group id
        for id in range(0, self.max_groups):
            section = ('group_%s' % id)
            
            if ( section in grp_obj.sections()) == False:
                grp_obj.add_section(section)
                
                if (name == None):
                    name = 'group_%s' % id

                grp_obj.set(section,'name', name)

                if (hub_id  != []):
                    hub_id = [hub_id]
                grp_obj.set(section,'hubs', hub_id)

                if (cell_id != []):
                    cell_id = [cell_id]
                grp_obj.set(section,'cells', cell_id)

                self.gp_WriteFile(grp_obj)
                
                break
        if (id >= self.max_groups):
            id = -1
        
        return id

    def gp_WriteFile(self, grp_obj):        
        grp_fp = open(self.group_file,"w+")
        grp_obj.write(grp_fp)
        grp_fp.close()
#-------------------------------------        
class CDataLogParms:
    ''' DataLogParms: User definable parameters for datalogger
        time bettween updates ect
    '''
    def __init__(self, ini_file = LOGGER_INI_FILE, log = None):
        self.ini_file = ini_file
        self.default_update_time = '300'
        self.default_file_name  = "CellMateLogFile_"
        self.log = None
        self.enabled = False
        

    def dlp_Log(self, text):
        if self.log == None:
            return
        else:
            log.write("DataLogParms:%s" % text)
            
            
    def dlp_IsEnabled(self):
        ini_obj = CP.ConfigParser()
        ini_obj.read(self.ini_file)

        if (ini_obj.has_section(INI_LOG_SECTION) == False):
            self.dlp_EnableDataLogging(False)
            ini_obj.read(self.ini_file)


       # if (ini_obj.has_option(INI_LOG_SECTION, INI_LOG_ENABLE_OPTION) == False):
        #OVER HErer    ini_obj.set(INI_LOG_SECTION, INI_LOG_ENABLE_OPTION, "0" )
                
    def dlp_GetCSVFileName(self):
        '''
            Return the amt of time bettween data log upsates
        '''
        ini_obj = CP.ConfigParser()
        ini_obj.read(self.ini_file)

        if (ini_obj.has_section(INI_LOG_SECTION) == False):
            self.dlp_SetCSVFileName(self.default_file_name)
            ini_obj.read(self.ini_file)
            
        if (ini_obj.has_option(INI_LOG_SECTION, INI_LOG_NAME_OPTION) == False):
            ini_obj.set(INI_LOG_SECTION, INI_LOG_NAME_OPTION, "CellMateLog_" )

        filename = ini_obj.get(INI_LOG_SECTION, INI_LOG_NAME_OPTION)
        dt = datetime.date.today()
        filename = filename + str(dt.year)+str(dt.month)+str(dt.day)+"_"
        
        return filename
    
    def dlp_GetUpdateTime(self):
        '''
            Return the amt of time bettween data log upsates
        '''
        ini_obj = CP.ConfigParser()
        ini_obj.read(self.ini_file)

        if (ini_obj.has_section(INI_LOG_SECTION) == False):
            self.dlp_SetUpdateTime(self.default_update_time)            
            ini_obj.read(self.ini_file)
            
        if ini_obj.has_option(INI_LOG_SECTION,INI_LOG_TIME) == False:
            self.dlp_SetUpdateTime(self.default_update_time)            
            ini_obj.read(self.ini_file)
            
        time = ini_obj.get(INI_LOG_SECTION, INI_LOG_TIME)
        time = int(time)   #wxTimers are in milliseconds convert to sec

        return time
    
    def dlp_SetCSVFileName(self,fileName):
        ini_obj = CP.ConfigParser()
        ini_obj.read(self.ini_file)

        if (ini_obj.has_section(INI_LOG_SECTION) == False):
            ini_obj.add_section(INI_LOG_SECTION)
            
        if fileName[-1] != '_':
            fileName = fileName + '_'
            
        ini_obj.set(INI_LOG_SECTION, INI_LOG_NAME_OPTION, fileName)
        
        self.dlp_WriteFile(ini_obj)
    
    def dlp_SetUpdateTime(self,time):
        ini_obj = CP.ConfigParser()
        ini_obj.read(self.ini_file)

        if (ini_obj.has_section(INI_LOG_SECTION) == False):
            ini_obj.add_section(INI_LOG_SECTION)

        ini_obj.set(INI_LOG_SECTION, INI_LOG_TIME, time)
        
        self.dlp_WriteFile(ini_obj)
    
    def dlp_WriteFile(self, cp_obj):        
        cp_fp = open(self.ini_file,"w+")
        cp_obj.write(cp_fp)
        cp_fp.close()

        
#---------------------------
def MsgDlg(window, string, caption='wxProject', style=wx.YES_NO|wx.CANCEL):
    """Common MessageDialog."""
    dlg = wx.MessageDialog(window, string, caption, style)
    result = dlg.ShowModal()
    dlg.Destroy()
    return result


#-------------------------------------
class XSetupWindow(wx.Frame):
    '''
        This setupWindow. Acts like a modless dialog box.
        it displays hub parameters (Connection, Name) For each page inthe
        the notebook
    '''
    def __init__(
            self, parent, ID, title, pos=wx.DefaultPosition,
            size=(400,650), style=wx.DEFAULT_FRAME_STYLE
            ):
                
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        panel = wx.Panel(self)

        self.parent = parent
        self.BtnSave_Id = wx.NewId()
        self.BtnCancel_Id = wx.NewId()
        self.BtnExit_Id = wx.NewId()

        self.AddHub_Id = wx.NewId()
        self.RemoveHub_Id = wx.NewId()

        self.AddGroup_Id = wx.NewId()
        self.RemoveGroup_Id = wx.NewId()

        self.AddCellToGroup_Id = wx.NewId()
        self.RemoveCellFromGroup_Id = wx.NewId()
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
                
        btnBar = [(self.BtnSave_Id,"Save","save_1.png","Save Changes"),
          (self.BtnCancel_Id,"Cancel","cancel_1.png","Cancel Changes"),
          (self.BtnExit_Id,"Exit","exit_1.png","Exit")]

        btnBarHubs = [(self.AddHub_Id,"Add New Hub","add.png","Add Hub"),
          (self.RemoveHub_Id,"Remove Selected Hub","remove.png","Remove Hub")]
        
        btnBarGroups = [(self.AddGroup_Id,"Add Group","add.png","Add New Group"),
          (self.RemoveGroup_Id,"Remove Group","remove.png","Remove Selected From Group")]

        self.grid = gridlib.Grid(panel)
        self.grid.CreateGrid(0, 4)      #CreateGrid(rows,cols)

        self.InitGrid(self.grid)  #pop grid with INI values
        self.grid.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)

        self.grd_group_parms = gridlib.Grid(panel)
        self.grd_group_parms.CreateGrid(0, 3)      #CreateGrid(rows,cols)
        self.sw_InitGroupGrid(self.grd_group_parms)
        self.grd_group_parms.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClickGridGroup)
        self.grd_group_parms.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClickGridGroup)


        lbl_hub_grid = wx.TextCtrl(panel,-1, "Hub Setup", wx.Point(0, 0), wx.Size(100, 30),
                                 (wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )
        lbl_hub_grid.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        lbl_hub_grid.SetForegroundColour(wx.WHITE)
        lbl_hub_grid.SetBackgroundColour(wx.BLACK)


        lbl_group_grid = wx.TextCtrl(panel,-1, "Group Setup", wx.Point(0, 0), wx.Size(100, 30),
                                 (wx.TE_READONLY | wx.TE_CENTRE |wx.TE_RICH) )
        lbl_group_grid.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, 0, ""))
        lbl_group_grid.SetForegroundColour(wx.WHITE)
        lbl_group_grid.SetBackgroundColour(wx.BLACK)



        grdSz = wx.GridSizer(rows=2, cols=3, vgap=3, hgap=3)

        vrtSz = wx.BoxSizer(wx.VERTICAL)
        #grid sizer for hub buttons
        grdSzHubBtn = wx.GridSizer(rows=2, cols=2, vgap=3, hgap=3)
        grdSzGrpBtn = wx.GridSizer(rows=2, cols=2, vgap=3, hgap=3)

        #Create Hub Button Bar---------------------
        #create btns and arannge them in horiz line,
        #assign each btn text and mapp it to the OnClick Event handler
        for b in range(len(btnBar)):
            btn_id,txt,pic,toolTip = btnBar[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(panel, btn_id, bmp, (20, 20),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)
            grdSz.Add(newBtn, 0, wx.EXPAND|wx.ALL, 5)

        
            
        #Create labels and text controls for log file entries

        #grid for labels and user text, log time, log fileName
        grdSz_txt = wx.GridSizer(rows=2, cols=2, vgap=1, hgap=1)
        self.userTexts=[]    
        for str in ["LogFile Update Time Seconds", "LogFile Name"]:
            #Create a label and assoc text
            #Labels on the left, userText cntrls on the right
            label = wx.StaticText(panel, -1, str)
            label.SetHelpText("help text for label:%s" % str)

            grdSz_txt.Add(label, 0, wx.EXPAND|wx.ALL, 5)

            text = wx.TextCtrl(panel, -1, "", size=(80,20))
            text.SetHelpText("text feils for user entry ")
            self.userTexts.append(text) #save text controls for calling routine
            grdSz_txt.Add(text,  1,wx.ALL, 5)

        #get n show current update time 
        dl = CDataLogParms()
        cur_update_time = dl.dlp_GetUpdateTime()
        csv_file_name = dl.dlp_GetCSVFileName()
        csv_file_name = string.split(csv_file_name,"_")[0]        
        
        self.userTexts[0].SetValue( "%s" %(cur_update_time) )
        self.userTexts[1].SetValue(csv_file_name)
        
        vrtSz.Add(grdSz)
        vrtSz.Add(grdSz_txt) #user log file time and filename labels and text
        #Do layout and grid Sizers

        vrtSz.Add(lbl_hub_grid,0, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)

        #Hub buttons create btns and arannge them in horiz line,
        #assign each btn text and mapp it to the OnClick Event handler
        for b in range(len(btnBarHubs)):
            btn_id, txt, pic,toolTip = btnBarHubs[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(panel, btn_id, bmp, (20, 20),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)
            grdSzHubBtn.Add(newBtn, 0, wx.EXPAND | wx.ALL, 5)
        
        #Hub Add and Remove buttons should appear bettween label and grid
        vrtSz.Add(grdSzHubBtn)
        
        for b in range(len(btnBarGroups)):
            btn_id, txt, pic,toolTip = btnBarGroups[b]
            bmp = wx.Bitmap(pic, wx.BITMAP_TYPE_PNG)
            mask = wx.Mask(bmp, wx.BLUE)
            bmp.SetMask(mask)
            newBtn = wx.BitmapButton(panel, btn_id, bmp, (20, 20),
                       (bmp.GetWidth()+10, bmp.GetHeight()+10))
            self.Bind(wx.EVT_BUTTON, self.OnClick,newBtn)
            newBtn.SetToolTipString(toolTip)
            grdSzGrpBtn.Add(newBtn, 0, wx.EXPAND|wx.ALL, 5)

        vrtSz.Add(self.grid, 1, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)

        vrtSz.Add(lbl_group_grid,0,     wx.ALIGN_CENTRE|wx.EXPAND|wx.NORTH, 15)
        vrtSz.Add(grdSzGrpBtn)
        vrtSz.Add(self.grd_group_parms, 1, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)
        panel.SetSizer(vrtSz)
        panel.Layout()
        
        #Setup window accessed by user admin level
        usr_obj = CUserObj()
        usr_obj.usr_SetUser(ADMIN_LEVEL)

    def OnCloseWindow(self,evt):
        ''' close window via system menu'''
#        print "OnCloseWindow()"
#        usr_obj = CUserObj()
#        usr_obj.usr_SetUser(USER_LEVEL)
        self.Destroy()
        

    def OnClick(self, evt):
        ''' Handler for save and cancel button clicks
        on user setup window
        '''
        
        if evt.GetId() == self.BtnExit_Id:
            '''Close window via exit button'''
#            print "BtnExit_Id()"
#            usr_obj = CUserObj()
#            usr_obj.usr_SetUser(USER_LEVEL)
            self.Destroy()
                    
        if evt.GetId() == self.BtnSave_Id:
            self.SaveHubParam()
            self.sw_SaveGroupParam()
            
        #-------------------------------------
        elif evt.GetId() == self.BtnCancel_Id:
            #Cancel
            self.InitGrid(self.grid)  #Init grid with INI values
            
        #-------------------------------------
        elif evt.GetId() == self.AddHub_Id:
            self.parent.OnAddHub()
        
        #-------------------------------------
        elif evt.GetId() == self.RemoveHub_Id:
            cur_row = self.grid.GetGridCursorRow()
                        
            hub_name = self.grid.GetCellValue(cur_row, 0)
            
            log.write("cur_row:%s, RemoveHub:%s" % (cur_row, hub_name),5)
            question = "Are you sure you want to delete Hub: %s" % hub_name
            
            yes_no = YesNo(self,question, caption = 'Delete?')
            if yes_no == True:
                self.parent.HubNB.DoDeletePage(cur_row)
            
        #evt.GetID------------------------------------
        elif evt.GetId() == self.RemoveGroup_Id:
            group  = CHubGroupObj()
            cur_row = self.grd_group_parms.GetGridCursorRow()
            group_name =  self.grd_group_parms.GetCellValue(cur_row, 0)
            
            question = "Are you sure you want to delete Group: %s" % group_name
            
            yes_no = YesNo(self,question, caption = 'Delete?')

            
            if yes_no == True:
                grp_id = -1
                for row_id in self.grp_rows_ids:
                    row,id = row_id
                    if row == cur_row:
                        grp_id = id
                        break
                log.write("OnClick:RemoveGroup_Id id=%s, name=%s" % (grp_id, group_name),5)
                
                group.gp_RemoveGroup(grp_id)
                self.sw_InitGroupGrid(self.grd_group_parms)

        #-------------------------------------
        elif evt.GetId() == self.AddGroup_Id:
            group  = CHubGroupObj()
            id = group.gp_AddGroup()
            log.write( "AddGroup:%s, newGroupId %s " % (group.gp_GetGroups(),id), 5)
            self.sw_InitGroupGrid(self.grd_group_parms)


        #-------------------------------------
        elif evt.GetId() == self.AddCellToGroup_Id:
            pass

        #-------------------------------------
        elif evt.GetId() == self.RemoveCellFromGroup_Id:
            pass
        
    #------------------------------------
    def sw_SaveLogUpdateTime(self):
        '''Save user value, for time bettween log file updates'''
        
        time = self.userTexts[0].GetValue()
        if time == "" or time == None:
            time = 5
        else:
            time = int(eval(time))
        
        if (time < 0):
            time = 5
        elif (time > 10000):
            time = 10000
        
        log.write( "sw_SaveLogUpdateTime: time %s" % time)
        dl = CDataLogParms()
        
        dl.dlp_SetUpdateTime(time)

        csvFileName = self.userTexts[1].GetValue()
        dl.dlp_SetCSVFileName(csvFileName)

        self.userTexts[0].SetValue(str(time))
        self.parent.HubNB.cm_Timer.Start(time * 1000)
    #------------------------------------
    def sw_SaveGroupParam(self):
        '''Cycle thru the group grid and settings '''
        groupObj  = CHubGroupObj()
        for row_grpId in self.grp_rows_ids:
            row, grpId = row_grpId
            
            grp_nm = string.strip(self.grd_group_parms.GetCellValue(row,0))
            log.write("sw_SaveGroupParam, grpId(%s),grp_nm(%s)" % (grpId,grp_nm),6)

            if len(grp_nm) > 0 and grpId >= 0:
                groupObj.gp_SetGroupName(grpId, grp_nm)
            
           
#self.grp_rows_ids.append( (cur_row,grp_id) )
# for row in range(self.grd_group_parms.GetNumberRows()):

           
            

    #------------------------------------
    def SaveHubParam(self):
        '''Extract grid values and save them to ini file'''
        hub  = CHubsObj()
        for row in range(self.grid.GetNumberRows()):
            newparms = []
            hub_page = self.parent.HubNB.GetPage(row)

            #retrive, save and update new hub_page name
            val = string.strip(self.grid.GetCellValue(row,0))
            newparms = [("name",val)]
            hub_page.name = val
            hub_page.text1.SetLabel(hub_page.name)
            hub.hbs_UpdateHub(hub_page.hub_id, 'name', val)

            self.parent.HubNB.SetPageText(row,val)

            #reteive and save hub_page connect string
            ipadr_port = string.strip(self.grid.GetCellValue(row,1)) \
                         +"," + string.strip(self.grid.GetCellValue(row,2))
            
            newparms.append( ("connect", ipadr_port))
            hub.hbs_UpdateHub(hub_page.hub_id, 'connect', ipadr_port)

            #retrieve and save hub_page serial string
            serial = string.strip(self.grid.GetCellValue(row,3))
            newparms.append( ("serial", serial))
            hub.hbs_UpdateHub(hub_page.hub_id, 'serial', serial)
            
            hub_page.parms = newparms

        self.sw_UpdateGrid()

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

        groupObj  = CHubGroupObj()
        group_ids_names = groupObj.gp_GetGroups()

        hubObj = CHubsObj()
        
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
                log.write( "hubObj:hbsGetHubIdName:%s" % hub_id)
                                                         

    #-----------------------------------
    def sw_UpdateGrid(self):
        self.InitGrid(self.grid)
        self.sw_SaveLogUpdateTime()
        
    #-----------------------------------
    def InitGrid(self, grid):
        '''
            InitGrid: assumes all HubPages are being displayed
            It goes thru each page gets the params and displays the name and connect
            info for each page in the grid.
            The Grid will show the hubs name, and connect info
        '''
        #grid attributes
        
        attr = gridlib.GridCellAttr()
        attr.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        attr.SetBackgroundColour(wx.BLACK)
        attr.SetTextColour(wx.WHITE)
        
        grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        #name, ip_addr, port, serial
        if grid.GetNumberRows() > 0:
            grid.DeleteRows(0, grid.GetNumberRows())
            
        for page_nbr in xrange(self.parent.HubNB.GetPageCount()):
            hub_page = self.parent.HubNB.GetPage(page_nbr)
            log.write("page name %s, params %s" % (hub_page.name,hub_page.parms),5)

            grid.AppendRows(1)
            cur_row = grid.GetNumberRows() -1
            grid.SetRowAttr(cur_row, attr)
            
            #exptd param key,value parms format is
            #   [('name', 'hub1FFFFF'), ('connect', '192.200.100.50,4001')]
            #iterate thru each hubpage and grab its paramters
            for ky, val in hub_page.parms:
                if ky == "name":
                    grid.SetColLabelValue(0,"Name")
                    grid.SetCellValue( cur_row, 0, string.strip(val) )  ##name 
                    
                elif ky == "connect":
                    #connect parameter: ('connect', '192.200.100.51,40001')
                    cnxt = val.split(",")
                    grid.SetColLabelValue(1,"IP Address")
                    grid.SetColLabelValue(2,"IP Port")

                    if (len(cnxt) > 1):            
                        grid.SetCellValue(cur_row,1,cnxt[0])  ##ipaddr
                        grid.SetCellValue(cur_row,2,cnxt[1])  ##port to listen

                elif ky == "serial":
                    grid.SetColLabelValue(3,"Comm Port")
                    grid.SetCellValue(cur_row,3,val)    
 



    #-----------------------------------   
    def	OnCellLeftClick(self,evt):
        self.dirty_grid = True
       
        self.grid.SetCellAlignment(evt.GetRow(), evt.GetCol(),wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grid.SetCellFont(evt.GetRow(), evt.GetCol(),wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.grid.SetCellTextColour(evt.GetRow(),evt.GetCol(), YELLOW)
        #print "GetCellValue", self.grid.GetCellValue(evt.GetRow(),evt.GetCol())

        evt.Skip()
 
    def	OnCellLeftClickGridGroup(self,evt):
        self.grd_group_parms.SetCellAlignment(evt.GetRow(), evt.GetCol(),wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grd_group_parms.SetCellFont(evt.GetRow(), evt.GetCol(),wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.grd_group_parms.SetCellTextColour(evt.GetRow(),evt.GetCol(), YELLOW)
        
        evt.Skip()
    #----------------------------------
    def OnCellRightClickGridGroup(self,evt):
        self.sw_DoAddCellToGroup()
    #-----------------------------------
    def sw_DoAddCellToGroup(self):
        '''
            Display a dialog box, allow users to add hub to currently selected up
            User needs to click on group name (i.e row 0) 
        '''
        cur_row = self.grd_group_parms.GetGridCursorRow()
        grp_name = ""        
        log.write("grp_name %s, cur_row %s" % (grp_name, cur_row))

 
        group  = CHubGroupObj()
        lst = group.gp_GetGroups() #exptd_lst = [(2, 'group_2'), (1, 'grp1'), (0, 'group_0')]
        cb_list_group = []
        for id_name in lst:
            id,name = id_name
            cb_list_group.append( ("%s, " % id) + name )
            
        groups = ("Groups", cb_list_group)


        hub = CHubsObj()
        cb_list_hubs = []            
        ids_names = []
        nbr = hub.hbs_GetHubIdsNames(ids_names)
        for id_name in ids_names:
            id,name = id_name
            cb_list_hubs.append(  ("%s, " % id) + name)

        hubs = ("Hubs", cb_list_hubs)

        cells = ("Cells", map(str,range(0,8)))
        strTitle = "Add Cell to Group"
        label = " Select Hub and Cell "

        log.write("%s, %s, %s" % (groups,hubs,cells))
        dlg = CMCell.dlgUserEntry(self, -1, (strTitle), [label], [groups,hubs,cells],
                         size=(550, 400),
                         #style=wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME,
                         style=wx.DEFAULT_DIALOG_STYLE
                         )
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            log.write("group %s" % dlg.cbs[0].GetSelection())
            log.write("hub %s" % dlg.cbs[1].GetSelection())
            log.write("cell %s" % dlg.cbs[1].GetSelection())
        dlg.Destroy()  
#        if val == wx.ID_OK:


        log.write("sw_DoAddCellToGroup: GroupName found")

        
#----------------------------------
# control panel buttons, check boxes for user control'
#    DataLog on off
class ControlPanel(wx.Panel):
    def __init__(self, parent, winID=-1, parms=[]):
        wx.Panel.__init__(self, parent, winID, style = wx.BORDER_DOUBLE)

        #
        self.DataLogger_id = wx.NewId()
        self.cb_DataLogger = wx.CheckBox(self, self.DataLogger_id, "Data Log OFF ")
        self.cb_DataLogger.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox, self.cb_DataLogger)
        self.SetBackgroundColour(wx.RED)

    #On Check Box for controlling datalogger
    def OnCheckBox(self,evt):
        if evt.GetId() == self.DataLogger_id:
            #Toggle the state of the check box, set panel background to match logging state
            if self.cb_DataLogger.IsChecked():
                self.SetBackgroundColour(wx.GREEN)
                self.cb_DataLogger.SetLabel("Data Log ON ")
            else:
                self.SetBackgroundColour(wx.RED)
                self.cb_DataLogger.SetLabel("Data Log OFF ")
                
            self.Refresh()
            
    def IsDataLogEnabled(self):
        return self.cb_DataLogger.IsChecked()
                
#--------------------------
class MySplashScreen(wx.SplashScreen):
    def __init__(self):
        log.write("splash screen")
        bmp = wx.Image('splash.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        wx.SplashScreen.__init__(self, bmp,
                                 wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                 3000, None, -1)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.fc = wx.FutureCall(2000, self.ShowMain)

    #---------------------------------------------------------------------
    def OnClose(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()
        
        # if the timer is still running then go ahead and show the
        # main frame now
        if self.fc.IsRunning():
            self.fc.Stop()
            self.ShowMain()


    def ShowMain(self):
        frame = MyFrame(None, -1,COMP_NAME +" "+ APP_NAME + " " + APP_VERSION)
        frame.OnLogIn(None)
        
        frame.Show(True)

        # Tell wxWindows that this is our main window
        # Return a success flag,  daily totip code goes here
        return True

#---------------------------
class CMNoteBook(wx.Notebook):
    def __init__(self, parent, id, log):
#       try:
        self.log = log    
        style = wx.NB_TOP
        self.buf = []
        self.lstHubPages = []   #lst of HubPages
        self.logHubPage = 0  #current hubpage being logged

        self.parent = parent

        
        wx.Notebook.__init__(self, parent, id, style=style)

        ## tracks which hub_id is on which page.
        self.dctHubs = {}
        self.dctSocketThreads={}
        self.Bind(EVT_UPDATE_SOCKETDATA, self.OnSocketUpdate)

        self.cm_DoLogFileSettings()

        self.log.write("start")
        self.DoAddPage()
        
        self.cm_Timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.cm_OnTimer, self.cm_Timer)
        wx.CallLater(500, self.cm_OnStart)

    
    #---- Update the log file setting in the ini
    def cm_DoLogFileSettings(self, option=None, value=None):
        ''' '''
        ini_obj = CP.ConfigParser()
        ini_obj.read(APP_INI_FILE)
        
        if (ini_obj.has_section(INI_LOG_SECTION) == False):
            ini_obj.add_section(INI_LOG_SECTION)

        #write new value to section
        if (option != None) and (value != None):
            ini_obj.set(INI_LOG_SECTION, option, value)

        if (ini_obj.has_option(INI_LOG_SECTION, INI_LOG_COUNT_OPTION) == False):
            ini_obj.set(INI_LOG_SECTION, INI_LOG_COUNT_OPTION, str(00) )
            
        
      

        #update the data logger file counter 
        self.log_count = ini_obj.get(INI_LOG_SECTION, INI_LOG_COUNT_OPTION)
        tmp = (int(self.log_count) + 1) % MAX_LOG_COUNT_NBR
        
        ini_obj.set(INI_LOG_SECTION, INI_LOG_COUNT_OPTION, tmp)

        dl = CDataLogParms()
        self.log_filename = "log\\" + dl.dlp_GetCSVFileName()

        ini_fp = open(APP_INI_FILE,"w+")
        ini_obj.write(ini_fp)
        ini_fp.close()

    def cm_Close(self):
        ''' closing the app. do cleanup'''
        

        
    def cm_OnStart(self):
        '''
        cm_Start
        '''
        dl = CDataLogParms()
        self.cm_Timer.Start(dl.dlp_GetUpdateTime() * 1000)

    def cm_OnTimer(self,evt):
        """ Iterate thru the hub pages,
        Get next page for logging"""
        # get next page to update
        lst_cell_data = []
        #cycle thru all the hubpages and process the
        # cell data for each page
        if self.parent.statusbar.IsDataLogEnabled() == False:
            return
        
        
        for page_nbr in xrange(self.GetPageCount()):
            hub_page = self.GetPage(page_nbr)
            self.log.write("cm_OnTimer testing name %s" % hub_page.name,3)
            
            lst_cell_data = lst_cell_data + hub_page.hubGetCellAvg()

        self.log.write("cm_OnTimer %s" % len(lst_cell_data), 2)
        
        if len(lst_cell_data) > 0:
            dctLoggerData = {}
            log_fname = self.log_filename + str(self.log_count) + ".csv"
            dctLoggerData["FileName"] = os.getcwd() +'\\' + log_fname
            
            dctLoggerData['data'] = lst_cell_data
            self.log.write("dctLoggerData[FileName]:%s" % (dctLoggerData["FileName"]),8)
            
            self.cm_loggerThread = DataLogThread(self, dctLoggerData)
            self.cm_loggerThread.Start()

            ##Reset the hubs list, after sending it to logger        

    def UpdateLoggerEvent(self,evt):
        self.log.write("UpdateLoggerEvent",7)
        
    def UpdateGroupsHubData(self, dctHubCell): 
        ''' 
            Update the Group windows with data for hubs and cells.
            Iterate thru all the group windows call their update functio
        '''
        self.log.write("UpdateGroupsHubData:, %s" % (dctHubCell),6 )   
        for win_id in self.parent.group_windows_id:
            self.log.write("UpdateGroupsHubData:group_windows_id, %s" % (win_id),6 )   
            
            win = wx.FindWindowById(win_id)
            if win == None:
                self.parent.group_windows_id.remove(win_id)
            else:
                win.grp_pnl.pnl_grpUpdateLoadCell(dctHubCell)
                log.write("UpdateGroupsHubData:grp_pnls:%s" % (win.grp_pnl),6)
                
            
        
    def DoAddPage(self, id = -1):   
        ''' Read the ini file, each section gets a note book page.id
        the section format is hubXX, Where XX is a hubid number 0 to MAX_HUBS
        the dctHubIds uses these numbers as keys.'''
        hub  = CHubsObj()
        id_name_lst = []

        hub.hbs_GetHubIdsNames(id_name_lst)

        #if no hubs are currently defined then add one
        if ( len(id_name_lst) <= 0):
            hub.hbs_AddHub()
            hub.hbs_GetHubIdsNames(id_name_lst)
            
        #sample id_name_connect_serial_lst=
        #          
        for id_name in id_name_lst:
            hub_id, hub_name = id_name
            
            
            self.log.write("hubnm %s" % (hub_name),7)

            #sample lstOptions list of tuple
            #[('0', 'cell_nm_0'), ('connect', '192.200.100.51,40001'),
            #('name', 'hub0'), ('port', '40001')]

            if id == -1:
                # calling func passed -1 add everything
                parms = hub.hbs_GetHubIdName(hub_id)
            
                win = CMCell.hub(self, log, hub_id, parms )
                self.AddPageToNB(win, "    %s        " % hub_name)

                log.write("CMNoteBook:AddPage:%s, name: %s" % (hub_id, hub_name))

            elif (id == hub_id):
                #calling func passed valid id, only add the valid id
                parms = hub.hbs_GetHubIdName(hub_id)
            
                win = CMCell.hub(self, log, hub_id, parms )
                self.AddPageToNB(win, "    %s        " % hub_name)

                log.write("CMNoteBook:AddPage:%s, name: %s" % (hub_id, hub_name))

      
    def AddPageToNB(self, page, name):
        self.AddPage(page, name)
        self.dctHubs[page.hub_id] = self.GetPageCount() - 1
        self.parent.PageAdded()     # Tell parent we added a page
        
        
    def DoDeletePage(self, del_page = None):
        #If no page is given, delete the currently selected page
        #GetSelection ruturns the a nbr 0 to total nbr pages
        if del_page == None:
            curPage =  self.GetSelection()
        else:
            curPage = del_page
        
        if curPage > -1:
            hub_page = self.GetPage(curPage)
            
            log.write( "DoDeletePage: self.dctHubs.%s" %  self.dctHubs, 5)
            
            for ky in self.dctHubs.keys():
                if (self.dctHubs[ky] == curPage):

                    "Remove Page and assoc section from ini file"
                    hub = CHubsObj()
                    hub.hbs_RemoveHub(hub_page.hub_id)

                    self.dctHubs.pop(ky)
                    self.DeletePage(curPage)
                    self.log.write("DoDeletePage page%s" % ky)
                    break


            self.dctHubs={}
            #Redo the dict {hub_id: page_nbr},after deleting a page
            #page_nbr = 0 to total nbr of pages in hub note book
            for page_nbr in range(self.GetPageCount()):
                hub_page = self.GetPage(page_nbr)
                self.dctHubs[hub_page.hub_id] = page_nbr

            log.write( "DoDeletePage: self.dctHubs.%s" %  self.dctHubs,5)
    
            self.parent.PageDeleted()     # Tell parent we added a page
        
    #-----------------------------------
    def CreateDctFromParms(self,parms):
        '''Create a hub dct from a parmater list'''
        dct = {'name':'','connect':'', 'id':'', 'serial':'' }
        #print "CreateDctFromParms",parms
        for optn, val in parms:
            if optn == "name":
                dct["name"]=val
                
            if optn == "connect":
                dct['connect'] =  val

            if optn == "serial":
                dct['serial'] = val

            if optn == "id":
                dct['id'] = val

            dct["DataThreadRunning"]=False

        return dct
    #-----------------------------------
    def DoHubConnect(self, id, parms):
        if self.dctSocketThreads.has_key(id) == False:
            dct= self.CreateDctFromParms(parms)
            dct['id'] = id
            if (dct["connect"] == "0000,0001") and ( "ML##" in dct["name"] ):
                self.log.write("DoHubConnect Test Connect Found", 6)
                self.dctSocketThreads[id] = mock_SocketDataThread(self, dct)
            else:
                self.dctSocketThreads[id] = SocketDataThread(self, dct)
                
            self.dctSocketThreads[id].Start()
            
    def DoHubDisable(self, id, parms):
        ''' Disable button selected by user'''
        self.log.write("DoHubDisable")
        
        if self.dctSocketThreads.has_key(id) == True:
            self.dctSocketThreads[id].Stop()
            
            # wait for thread to die.
            # if the thread dosent die within 10 secs
            #   just declare it dead and move on.
            
            st_time = time.time()
            while self.dctSocketThreads[id].IsRunning():
                time.sleep(0.1)
                if ( (time.time() - st_time) > 10.0):
                    self.log.write("Wait on thread time out:")
                    break
                
            self.dctSocketThreads.pop(id)
            self.log.write("DoHubDisable: Removed Thread %s" % id)
    #self.parent.DoHubDisable(self.id,self.parms)

    def OnSocketUpdate(self,evt):
        '''new data from socket, 
        Find the hub page for the data and call its Update Data func
        '''
        id = evt.dct["id"]

        if (self.dctSocketThreads.has_key(id)):
            if (self.dctSocketThreads[id].IsRunning()):
                
                for page_nbr in xrange(self.GetPageCount()):
                    hubPage = self.GetPage(page_nbr)
                    
                    if hubPage.hub_id == id:
                        self.log.write( ("OnSocketUpdate ----found hubPage.name---- %s" % hubPage.name), 5)
                        hubPage.UpdateData(evt.data)


            else:
                self.log.write("OnSocketUpdate  Died")
            

    def AddRemoveCell(self, evt):
        '''
            OnAddRemoveCell: 
        '''
        self.log.write("OnAddRemoveCell: %s" % evt)
    #-----------------------------------
class SocketDataThread:
    def __init__(self, win, dct):
        try:
            self.win = win
            self.dctHubs = dct
                    
            cnxt = dct['connect'].split(",")
            log.write("connect - ",10)

            self.ip_addr = cnxt[0]
            self.ip_port = cnxt[1]
            
            print "self.ip_port", self.ip_port
            print "self.ip_addr", self.ip_addr
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            #self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.connect((self.ip_addr, int(self.ip_port)) )
            
        except:
            log.write( "Thread Failed to start Exception %s" % (self.dctHubs),10)
            print "thread ended", self.dctHubs

            self.running = False
            dct["DataThreadRunning"]=self.running
            evt = UpdateSocketEvent(dct = self.dctHubs, data = [])
            wx.PostEvent(self.win, evt)
        
    
    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())
        print "Thread Socket Starting: %s" % self.dctHubs



    def Stop(self):
        self.keepGoing = False
        log.write("Thread Stopping",5)

    def IsRunning(self):
        return self.running

    def Run(self):
        log.write("Run from thread",5)
        print "Run", self.dctHubs
        self.dctHubs['DataThreadRunning']=True
        self.keepGoing = True
            
        try:
            while self.keepGoing:
                buf = self.client_socket.recv(12)
                buf = map(ord,buf)
                
                #dct = self.dctHubs dctHubs
                evt = UpdateSocketEvent(dct = self.dctHubs, data = buf)
                wx.PostEvent(self.win, evt)
                print "got data", buf

            self.client_socket.close()
            self.running = False
            log.write("Thread has ended  ",10)
            print "thread ended"

        except:
            log.write("SocketDataThread has ended  Exception",5) 
            self.running = False
            self.dctHubs["DataThreadRunning"]=self.running
            #evt = UpdateSocketEvent(dct = self.dctHubs, data = [])
            #wx.PostEvent(self.win, evt)

#------------------------------------------
#mock_SocketDataThread for testing only
'''
Data Format 70, 16, 39, 2, 25, 1, 16, 39, 2, 25, 1
70 = startChar
dct["weight"] = self.buf[1] + self.buf[2]*256
dct["cell_id"] = self.buf[3]

dct["overload"] = self.buf[4]
dct["status"] = self.buf[5]
'''
class mock_SocketDataThread:
    def __init__(self, win, dct):
        try:
            self.win = win
            self.dctHubs = dct
                    
            cnxt = dct['connect'].split(",")

            self.ip_addr = cnxt[0]
            self.ip_port = cnxt[1]
            log.write("mock_SocketDataThread: End of init")

        except:
            log.wrtie("Thread Failed to start Exception: %s" % self.dctHubs)

            self.running = False
            dct["DataThreadRunning"]=self.running
            #evt = UpdateSocketEvent(dct = self.dctHubs, data = [])
            #wx.PostEvent(self.win, evt)

    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False
        log.write("mock_SocketDataThread: Stoped")

    def IsRunning(self):
        return self.running

    def Run(self):
        try:
            cell_id = 3
            while self.keepGoing:
                cell_id = cell_id % 8
                units = 1   #lbs = 1,  kg =3
    
                weight = 1000
                
                
                time.sleep(.1)
                
                if cell_id == 7:
                    weight = 4500
    
                if cell_id == 6:
                    weight = 3800
    
                if cell_id == 5:
                    weight = 3200
                        
                if cell_id == 4:
                    weight = 2800
    
                if cell_id == 3:
                    weight = 2400
    
                if cell_id == 2:
                    weight = 2200
    
                if cell_id == 1:
                    weight = 2000
                    
                overload = weight/200
                low_byte_weight = weight & 0x00ff
                high_byte_weight = weight >> 8
                
                buf = [33, 2,1,70, low_byte_weight, high_byte_weight, cell_id, overload, units, 
                                   low_byte_weight, high_byte_weight, cell_id, overload, units,]
                cell_id = cell_id + 1
                #dct = self.dctHubs
                evt = UpdateSocketEvent(dct = self.dctHubs, data = buf)
                wx.PostEvent(self.win, evt)
         
            self.running = False
            self.client_socket.close()
            log.write("Thread has ended %" % self.dctHubs)
        except:
            log.write("MockSocket exception")
#---------------------------
class DataLogThread:
    def __init__(self, win, dct):
        self.win = win
        self.dctLogData = dct

    def Start(self):
        log.write("DataLogThread - Start", 5)

        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False
        log.write( "DataLogThread - Stop" )

    def IsRunning(self):
        return self.running

    def Run(self):
        log.write("******DataLogThread - Run",7)
        #fill in file name if we dont have one
        if self.dctLogData.has_key('FileName') == False:
            self.dctLogData['FileName'] = 'CellMateLogger_00'
            
        log.write("********DataLogThread - Run Path 11 %s" % self.dctLogData,7)

        if self.dctLogData.has_key('Path') == False:
            self.dctLogData['Path'] = os.getcwd() + 'logger'
            
        log.write( "********DataLogThread - Run Path 22 %s" % self.dctLogData)

#        pp = pprint.PrettyPrinter(indent=4)
#        pp.pprint(self.dctLogData)

        pth,fn = os.path.split(self.dctLogData['FileName'])
        if pth != "":
            if (os.path.exists(pth) != True):
                os.makedirs(pth)
                
        fh = open(self.dctLogData['FileName'],'a')
        for x in (self.dctLogData['data']):
            x['cell_id'] = int(x['cell_id']) + 1
            fh.write (time.ctime(x['time']) + ','  + str(x['cell_id']) + ', ' +  str(x['hub_name'])
                                            + ',' + str(x['value']) + ','   +  str( x['max']) + '\n')
        fh.close()
        
        #os.chdir(self.dctLogData['Path'])

        evt = UpdateLoggerEvent(dct={"status":"done"})
        wx.PostEvent(self.win,evt)

        log.write("DataLogThread is done",7)
        
#        pp.pprint(self.dctLogData)
        
        self.running = False
#---------------------------										  
class CustomStatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has three fields
        self.SetFieldsCount(3)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-2, -1, -2])
        #self.log = log
        self.sizeChanged = False
        self.Bind(wx.EVT_SIZE, self.OnSize)
        #self.Bind(wx.EVT_IDLE, self.OnIdle)

        # Field 0 ... just text
        self.SetStatusText("A Custom StatusBar...", 0)

        # This will fall into field 1 (the second field)
        self.cb = wx.CheckBox(self, 1001, "toggle clock")
        #self.Bind(wx.EVT_CHECKBOX, self.OnToggleClock, self.cb)
        self.cb.SetValue(True)

        # set the initial position of the checkbox
        self.Reposition()

    def OnSize(self, evt):
        self.Reposition()  # for normal size events

        # Set a flag so the idle time handler will also do the repositioning.
        # It is done this way to get around a buglet where GetFieldRect is not
        # accurate during the EVT_SIZE resulting from a frame maximize.
        self.sizeChanged = True
    # reposition the checkbox

    def Reposition(self):
        rect = self.GetFieldRect(1)
        self.cb.SetPosition((rect.x+2, rect.y+2))
        self.cb.SetSize((rect.width-4, rect.height-4))
        self.sizeChanged = False


#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(
            self, parent, ID, title, pos=wx.DefaultPosition,
            size=(650,650), style=wx.DEFAULT_FRAME_STYLE
            ):
        
        ID_FILE_SEL = wx.NewId()
        
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        #panel = wx.Panel(self, -1)
        #panel = MyPanel(self)

        #--- Create menu bar
        mb = wx.MenuBar()
        
        #---- Create File Menu items, Quit, about
        file_menu = wx.Menu()

        #allow user to select logon Level
        item = wx.MenuItem(file_menu, wx.NewId(), "&Logon")
        self.Bind(wx.EVT_MENU, self.OnLogIn, item)
        file_menu.AppendItem(item)

        file_menu.AppendSeparator()

        #allow user to select location of log file dir
        item = wx.MenuItem(file_menu, wx.ID_ANY, "&About")
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        file_menu.AppendItem(item)

        file_menu.AppendSeparator()


        item = wx.MenuItem(file_menu, wx.ID_ANY, "&Quit")
        self.Bind(wx.EVT_MENU, self.OnClose, item)
        file_menu.AppendItem(item)
        
        self.OnAddHub_Id = wx.NewId()
        self.OnRemoveHub_Id = wx.NewId()

        self.OnShowAllHubs = wx.NewId()
        self.OnShowGroup   = wx.NewId()
        self.OnChoseGraphic = wx.NewId()
        self.OnHubTree      = wx.NewId()
        

        #---- Create Hub Menu items, add, remove
        hub_menu = wx.Menu()
        
        item = wx.MenuItem(hub_menu, self.OnAddHub_Id, "Add&Hub")
        hub_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnClick, item)
        
        hub_menu.AppendSeparator()   

        item = wx.MenuItem(hub_menu, self.OnRemoveHub_Id, "&RemoveHub")
        hub_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnClick, item)

        item = wx.MenuItem(hub_menu, self.OnShowGroup, "Show Group")
        hub_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnClick, item)
        
        item = wx.MenuItem(hub_menu, self.OnChoseGraphic, "Chose &Graphic")
        hub_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnClick, item)
        
        item = wx.MenuItem(hub_menu, self.OnHubTree, "Show Hub&Tree")
        hub_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnClick, item)
        
        #Add Menu bars 
        mb.Append(file_menu, "&File")
        mb.Append(hub_menu, "&Hubs")

        self.SetMenuBar(mb)
        #Tool Bar:
        vbox = wx.BoxSizer(wx.VERTICAL)
            
        self.group_windows_id = []
        self.image_file = None
        
        self.statusbar = ControlPanel(self)    
        vbox.Add(self.statusbar, 0, wx.EXPAND|wx.EAST)

        self.HubNB = CMNoteBook(self,-1, log)

        vbox.Add(self.HubNB, 1, wx.EXPAND|wx.ALL|wx.NORTH,2)

        if 0:
            self.statusbar = self.CreateStatusBar()
            self.statusbar.SetFieldsCount(3)
            # Sets the three fields to be relative widths to each other.
            self.statusbar.SetStatusWidths([-2, -1, -2])
            self.DataLogging_id = wx.NewId()
            self.cb = wx.CheckBox(self.statusbar, self.DataLogging_id , "Enable DataLogging")
            self.Bind(wx.EVT_CHECKBOX, self.OnClick, self.cb)
            self.cb.SetValue(False)


        self.SetSizer(vbox)

        #---- Create NoteBook of hubs
        self.Centre()

    def  PageDeleted(self):
        '''
            Notebook deleted a page
        '''
        frmSetup = self.FindWindowById(ID_SETUP_WINDOW)
        if frmSetup != None:
            frmSetup.sw_UpdateHubData()
            #frmSetup.sw_UpdateGrid()

    def  PageAdded(self):
        '''
            Notebook added a page
        '''
        frmSetup = self.FindWindowById(ID_SETUP_WINDOW)
        if frmSetup != None:
            frmSetup.sw_UpdateHubData()
            #frmSetup.sw_UpdateGrid()
        
        #---- Create Menu handlers
    def OnLogIn(self, evt):
        '''Change in login level force pages to resize and redraw controls'''

        strTitle = "User Logon"

        dlg = CMCell.dlgUserEntry(self, -1, (strTitle), ["CellMate", "User Name", "Password"],
                         size=(550, 400),
                         #style=wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME,
                         style=wx.DEFAULT_DIALOG_STYLE
                         )
        dlg.CenterOnScreen()

        # this does not return until the dialog is closed.
        val = dlg.ShowModal()
    
        if val == wx.ID_OK:
            userLevel = dlg.userTexts[1].GetValue()
            
            if userLevel == "cell*mate":
                #Setup window accessed by user admin level
                usr_obj = CUserObj()
                usr_obj.usr_SetUser(ADMIN_LEVEL)

                frame = SetupWindow(self,ID_SETUP_WINDOW, "CelllMate SetupWindow",log)
                frame.Show(True)

            else:
                usr_obj = CUserObj()
                usr_obj.usr_SetUser(USER_LEVEL)
                
                
        #Cycle Thru all hub pages so they can adj to current level
        for page in xrange(self.HubNB.GetPageCount()):
            hub_page = self.HubNB.GetPage(page)
            hub_page.DoControlLayoutAndSizers()


        #---- Create Menu handlers
    def OnClose(self,evt):
        self.HubNB.cm_Close()
        log.write("OnClose")
        self.Close()

    def OnLogFileSel(self, evt):
        #update log file dir location
        dlg = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # Show the dialog and retrieve the user response.
        # If it is the OK response, update logfile path
        # .
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            new_path = dlg.GetPath()
            pth, fn = os.path.split(self.HubNB.log_filename)
            newNm = os.path.join(new_path,fn)
            self.HubNB.cm_DoLogFileSettings(INI_LOG_NAME_OPTION, newNm)
            log.write('%s\n' % newNm)

        # Compare this with the debug above; did we change working dirs?
        log.write("CWD: %s\n" % os.getcwd())

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()


    def OnFile(self, evt):
        log.write("OnFile:",3)
        
    def OnClick(self, evt):
        if evt.GetId() == self.OnAddHub_Id:
            self.OnAddHub()
            
        elif evt.GetId() == self.OnRemoveHub_Id:
            self.OnRemoveHub()

        elif evt.GetId() == self.OnShowAllHubs:
            log.write("OnShowAllHubs")
            
            dct = {"group_id":-1, "group_name":'Hubs'}
            grp = CMCell.CWinGroup(self, AllHubs_Id,'All Hubs',dct, log)
            grp.Show(True)
            
        elif evt.GetId() == self.OnChoseGraphic:
            """ 
            User selects the image_file for use in hubTree, 
            DragNDrop
            """
            fileTypes = 'All image files (tif, bmp, jpg, gif, png...)| *.tif;*.bmp;*.jpg;*.png;*.pcx;*.gif;*.pnm' 
            dlg = wxFileDialog(self, "Open Image", "", "", fileTypes, wxOPEN) 

            if dlg.ShowModal() == wx.ID_OK:
                self.image_file =dlg.GetPath()
                print self.image_file
            dlg.Destroy()

        elif evt.GetId() == self.OnHubTree:
            """ 
                Bring up hub_tree and graphic window
            """
            HT.HubTree(self.image_file)

        elif evt.GetId() == self.OnShowGroup:
            #User wants to show a group.
            #Show the user a list of groups, then display the selected group
            log.write("OnShowGroup")

            group  = CHubGroupObj()
            lst = group.gp_GetGroups() #exptd_lst = [(2, 'group_2'), (1, 'grp1'), (0, 'group_0')]
            cb_list_group = []
            
            if len(lst) <= 0:       #no groups defined use a default group name
                group.gp_AddGroup('group0')
                lst = group.gp_GetGroups() #exptd_lst = [(2, 'group_2'), (1, 'grp1'), (0, 'group_0')]

                
            for id_name in lst:
                id,name = id_name
                cb_list_group.append( ("%s, " % id) + name )
                
            
            groups = ("Groups", cb_list_group)
            label = "Select Group To Show "
            
            #Show user list of available groups to chose from
            strTitle = "Select Group"
            dlg = CMCell.dlgUserEntry(self, -1, (strTitle), [label], [groups],
                         size=(550, 400),
                         #style=wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME,
                         style=wx.DEFAULT_DIALOG_STYLE
                         )
            
            dlg.CenterOnScreen()
            val = dlg.ShowModal()
            
            if val == wx.ID_OK:
                id_name =  string.split(dlg.cbs[0].GetValue(),',')
                if id_name != "":
                    grp_id,name = id_name
                    #log.write("User selected group id %s" % dlg.cbs[0].GetSelection())
                    dct = {"group_id": grp_id, "group_name":name}
                    win_id = wx.NewId()
                    grp = CMCell.CWinGroup(self, win_id, name,dct, log)
                    self.group_windows_id.append(win_id)    #list of windows ids that have groups, use find window
                    grp.Show(True)

            dlg.Destroy()  
            
            
    def OnAddHub(self):
        hub = CHubsObj()
        new_hub_id = hub.hbs_AddHub()
        self.HubNB.DoAddPage(new_hub_id) # cause hub to add the given id
            
        log.write( "OnAddHub %s" % self.HubNB.dctHubs.keys(),3)

                
    def OnRemoveHub(self):
        self.HubNB.DoDeletePage()
        
        

    def OnAbout(self, evt):
        self.Exit()    
#---------------------------------------------------------------------------
# Socket Threads
# pass in ipaddr,port, hubdct

#---------------------------------------------------------------------------
# Every wxWindows application must have a class derived from wxApp
class MyApp(wx.App):

    # wxWindows calls this method to initialize the application
    def OnInit(self):
        log.write("starting")
        # Create an instance of our customized Frame class

        splash = MySplashScreen()

        return True
    
    def OnExit(self):
        ''' close window via system menu'''
        log.write("ExitAPP",7) #XXChange debug level 
        usr_obj = CUserObj()
        usr_obj.usr_SetUser(USER_LEVEL)
        self.Destroy()

        


if __name__ == "__main__":

    app = MyApp(0)     # Create an instance of the application class
    app.MainLoop()     # Tell it to start processing events


