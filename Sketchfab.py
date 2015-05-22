#! /usr/bin/env python
# -*- Mode: Python -*-
# -*- coding: ascii -*-

"""    
Sketchfab uploader for Lightwave 
"""


__author__     = "Maxime Rouca, Sketchfab"
__date__       = "May 22 2015"
__copyright__  = "Sketchfab"
__version__    = "1.1"
__maintainer__ = ""
__email__      = ""
__status__     = ""
__lwver__      = "11.5"


try:
    import sys
    import os
    import subprocess
    import gzip
    import struct
    import math
    import zipfile
    import sys
    import platform
    import tempfile
    import shutil

    import webbrowser

    import lwsdk
except:
    print >>sys.stderr, "The LightWave Python module could not be loaded."













# ------------------------------------------------------- LightWave Plugin PART (UI + upload code)

    
#global variables
myui = None
waitPanel = None
msgPanel = None

# DEBUG ?
DEBUG_logDebugInfo = False
DEBUG_logDebugInfoInFile = False
DEBUG_logFilename = ""
url="https://api.sketchfab.com/v1/models"

def initLogForDebug(text):
    if DEBUG_logFilename == "":
        return
    if DEBUG_logDebugInfoInFile:
        if platform.system()=="Darwin":
            DEBUG_logFilename = "/var/tmp/SketchfabLW/log.txt"
        elif platform.system()=="macosx":
            DEBUG_logFilename = "/var/tmp/SketchfabLW/log.txt"
        else:    
            DEBUG_logFilename = os.path.join(tempfile.gettempdir(), "SketchfabLW/log.txt")
        fd = open(DEBUG_logFilename, 'w')
        fd.close()

def logForDebug(text):
    if DEBUG_logDebugInfo: 
        print >>sys.stderr, text
        
        # log in a file:
        if DEBUG_logDebugInfoInFile:
            fd = open(DEBUG_logFilename, 'a')
            fd.write(text + "\n")
            fd.close()



#unzip (for uploader installation)
def unzip(zipFilePath, destDir):
    zfile = zipfile.ZipFile(zipFilePath)
    for name in zfile.namelist():
        (dirName, fileName) = os.path.split(name)
        if fileName == '':
            # directory
            newDir = destDir + '/' + dirName
            if not os.path.exists(newDir):
                os.mkdir(newDir)
        else:
            # file
            fd = open(destDir + '/' + name, 'wb')
            fd.write(zfile.read(name))
            fd.close()
    zfile.close()
    
    
class SketchfabMaster(lwsdk.IMaster):
    def __init__(self, context):
        #print >>sys.stderr, "SketchfabMaster(lwsdk.IMaster)::__init__() !"
        super(SketchfabMaster, self).__init__()
        self._instance_count = 0
        self._panel = None

        #ui variables
        self._title = "Title"
        self._description = ""
        self._tags = ""
        self._APIKey = "set your APIKey here"
        self._private = False
        self._password = ""
        self._rotate = False
        self._freeze = True
        
        # panel items        
        self._ctrl_Title = None
        self._ctrl_Description = None
        self._ctrl_Tags = None
        self._ctrl_APIKey = None
        self._ctrl_Private = None
        self._ctrl_Password = None
        self._ctrl_Upload = None
        self._ctrl_Rotate = None
        #self._ctrl_Freeze = None
        
        #other
        self._SketchFabTempFolder = ""
        self._SketchFabTempDataFolder = ""
        self._SketchFabUploaderAppPath = ""
        self._isMacOSX = False

        self._SceneCounter = 0
        self._ngonCount = 0
        
    #def __del__(self):
    #    #print >>sys.stderr, "SketchfabMaster(lwsdk.IMaster)::__del__() !"
        


    # ---------------- Callbacks ---------------------------------------------
    def panel_close_callback(self, panel, data):
        #print >>sys.stderr, "panel_close_callback()!"
        self._panel = None


    # -------------------- Misc functions ------------------------------        
    def install_uploader(self):
        self.updateTempFolder()

        if os.path.isfile(self._SketchFabUploaderAppPath) == False:
            
            thisScriptFilePath = os.path.realpath(__file__)
            thisScriptFolder = os.path.dirname(thisScriptFilePath)
            logForDebug("thisScriptFolder="+thisScriptFolder)

            if self._isMacOSX:  # on Mac: just copy
                uploaderDirPath = os.path.join(thisScriptFolder, "uploader")
                logForDebug("os.system(" + 'cp -a "'+uploaderDirPath+'" "'+self._SketchFabTempFolder+'/"' + ")" )
                retCode = os.system('cp -a "'+uploaderDirPath+'" "'+self._SketchFabTempFolder+'/"')
                #logForDebug("  => %d"%retCode)
                #os.system("chmod a+x "+self._SketchFabUploaderAppPath)
                #os.system("chmod a+r "+self._SketchFabUploaderAppPath)
            else: # on Windows need to zip/unzip because some dll are perturbating LW
                zipFilePath = os.path.join(thisScriptFolder, "Sketchfab_uploader.zip")
                logForDebug("zipFilePath="+zipFilePath)
                logForDebug("unZipTo:"+self._SketchFabTempFolder)
                unzip(zipFilePath, self._SketchFabTempFolder)

        else:
            logForDebug("install_uploader: "+self._SketchFabUploaderAppPath+" already exist!")

        if (os.path.exists(self._SketchFabUploaderAppPath) == False) and (os.path.isfile(self._SketchFabUploaderAppPath) == False):
            return False
        return True
                    

    def updateTempFolder(self):
        if (self._SketchFabTempFolder == ""):
            logForDebug("Platform = " + platform.system())
            logForDebug("tempfile.gettempdir()="+tempfile.gettempdir())
            #logForDebug("username="+os.getlogin())
            #logForDebug("USER="+os.getenv("USER"))
                
            if (platform.system()=="Darwin") or (platform.system()=="macosx"):
                #self._SketchFabTempFolder = "/var/tmp/SketchfabLW_" + os.getlogin() # on OSX: need to make a specific folder for each user to avoid file right permission issues
                self._SketchFabTempFolder = os.path.join(tempfile.gettempdir(), "SketchfabLW_"+os.getlogin() )
                self._SketchFabUploaderAppPath = os.path.join(self._SketchFabTempFolder, "uploader/sketchfab_uploader")
                self._isMacOSX = True
            else:    
                self._SketchFabTempFolder = os.path.join(tempfile.gettempdir(), "SketchfabLW")
                self._SketchFabUploaderAppPath = os.path.join(self._SketchFabTempFolder, "uploader\sketchfab_uploader.exe")
                self._isMacOSX = False
            logForDebug("TempFolder = "+ self._SketchFabTempFolder)

            if not os.path.exists(self._SketchFabTempFolder):
                logForDebug("Creating "+self._SketchFabTempFolder)
                os.makedirs(self._SketchFabTempFolder)
                if self._isMacOSX:
                    logForDebug("os.system(" + "chmod a+r "+self._SketchFabTempFolder + ")")
                    logForDebug("os.system(" + "chmod a+w "+self._SketchFabTempFolder + ")")
                    os.system("chmod a+r "+self._SketchFabTempFolder)
                    os.system("chmod a+w "+self._SketchFabTempFolder)
                    os.system("chmod a+x "+self._SketchFabTempFolder)

        if (self._SketchFabTempDataFolder == ""):
            if self._isMacOSX:   
                #self._SketchFabTempDataFolder = os.path.join(self._SketchFabTempFolder, "data_"+os.getlogin())
                self._SketchFabTempDataFolder = os.path.join(self._SketchFabTempFolder, "data")
            else:
                self._SketchFabTempDataFolder = os.path.join(self._SketchFabTempFolder, "data")
                
            if not os.path.exists(self._SketchFabTempDataFolder):
                logForDebug("Creating "+self._SketchFabTempDataFolder)
                os.makedirs(self._SketchFabTempDataFolder)
                if self._isMacOSX:
                    logForDebug("os.system(" + "chmod a+r "+self._SketchFabTempDataFolder + ")")
                    logForDebug("os.system(" + "chmod a+w "+self._SketchFabTempDataFolder + ")")
                    os.system("chmod a+r "+self._SketchFabTempDataFolder)
                    os.system("chmod a+w "+self._SketchFabTempDataFolder)
                    os.system("chmod a+x "+self._SketchFabTempDataFolder)
            
    def startWaiting(self, zipSize):
        global myui
        global waitPanel
        myui = lwsdk.LWPanels()
        zipSizeKB = zipSize / 1024
        text = "Uploading %d KB! Please Wait..."%zipSizeKB
        logForDebug(text)
        #waitPanel = myui.create(text)
        waitPanel = myui.create('Sketchfab:')
        ctrl_TitleTxt = waitPanel.text_ctl(text, '')
        ctrl_TitleTxt.set_h(28)
        ctrl_TitleTxt.set_w(300)
        waitPanel.open(lwsdk.PANF_NOBUTT)
        waitPanel.handle(lwsdk.EVNT_ALL)
        #lwsdk.command("RefreshNow")

    def endWaiting(self):
        global waitPanel
        waitPanel.close()
        waitPanel = None


    def displayMsg(self, msg):
        global myui
        global msgPanel
        myui = lwsdk.LWPanels()
        msgPanel = myui.create('Sketchfab:')
        
        # Text item:        
        ctrl_TitleTxt = msgPanel.text_ctl(msg, '')
        #ctrl_TitleTxt.move(0,20)
        ctrl_TitleTxt.set_h(28)
        ctrl_TitleTxt.set_w(300)

        msgPanel.open(lwsdk.PANF_BLOCKING)
        msgPanel.handle(lwsdk.EVNT_ALL)

    def displayReturnMsg(self, msg):
        self.displayMsg(msg)

    def rotateAllObjects(self, sign):
        lwsdk.command("SelectAllObjects")
        
        # using pcore
        #print >>sys.stderr, "NumObjects= %d"%pcore.LWObjectFuncs().numObjects()
        #for oo in range(0, pcore.LWObjectFuncs().numObjects()):
            #print >>sys.stderr, "NumObjects= %d"%pcore.LWObjectFuncs().maxLayers(oo)
        #numLayer = pcore.LWObjectFuncs().maxLayers(0)
        
        lwsdk.command("FirstItem")
        if len(lwsdk.LWInterfaceInfo().selected_items()) == 0:
            return
        firstItemID = lwsdk.LWInterfaceInfo().selected_items()[0]
        if (firstItemID == None):
            return
        for l in range(0, 50000):
            if (sign == 1.0):
                lwsdk.command("AddRotation 0 -90 0")
            else:
                lwsdk.command("AddRotation 0 90 0")
            lwsdk.command("NextItem")
            itemID = lwsdk.LWInterfaceInfo().selected_items()[0]
            if (itemID == firstItemID):
                break

    def FreezeAllObjects(self):
        # Now Freeze is asked during upload => no more warning!
        #ok = lwsdk.LWMessageFuncs().okCancel("Sketchfab warning", "With 'Freeze' enabled, the scene can be modified. This option is only usefull for subpatch.", "Do you want to 'Freeze' the scene?")
        #if ok == 0:
        #    return

        lwsdk.command("SelectAllObjects")
        
        lwsdk.command("FirstItem")
        if len(lwsdk.LWInterfaceInfo().selected_items()) == 0:
            return
        firstItemID = lwsdk.LWInterfaceInfo().selected_items()[0]
        if (firstItemID == None):
            return
        nameCount = 0
        for l in range(0, 50000):
            tmpFileName = os.path.join(self._SketchFabTempDataFolder, "tmp%d.lwo"%nameCount)
            nameCount = nameCount+1
            if os.path.isfile(tmpFileName):
                os.remove(tmpFileName)
            lwsdk.command("SaveTransformed "+tmpFileName)
            lwsdk.command("Generic_Reset_All")
            lwsdk.command("ReplaceWithObject "+tmpFileName)

            lwsdk.command("NextItem")
            if os.path.isfile(tmpFileName):
                os.remove(tmpFileName)
            itemID = lwsdk.LWInterfaceInfo().selected_items()[0]
            if (itemID == firstItemID):
                break

    def scanNGons( self, mesh, polygonID ):
        if mesh.polSize( polygonID ) > 4:
            self._ngonCount = self._ngonCount + 1

    def DetectNGons(self):
        self._ngonCount = 0
        object_info = lwsdk.LWObjectInfo()
        item_info = lwsdk.LWItemInfo()
        
        #print >>sys.stderr, "DetectNGons... "
        objectID = item_info.first( lwsdk.LWI_OBJECT, lwsdk.LWITEM_NULL )
        while objectID:
            #print >>sys.stderr, "DetectNGons... ObjectID=%d"%objectID

            numPolygons = object_info.numPolygons( objectID )
            if numPolygons > 0:
                meshinfo = object_info.meshInfo( objectID, False )
                meshinfo.scanPolys(self.scanNGons, meshinfo ) #pass meshinfo
            objectID = item_info.next( objectID )

        if self._ngonCount > 0:
            #print >>sys.stderr, "DetectNGons -> %d"%self._ngonCount
            ok = lwsdk.LWMessageFuncs().yesNo("Sketchfab warning", "The scene contains %d NGons. You should triangulate them before uploading!"%self._ngonCount, "Do you want to upload anyway?")
            #lwsdk.LWMessageFuncs().info("Warning: The scene contains %d NGons.\n You should triangulate them before uploading to sketchfab!"%self._ngonCount, None)
            return ok

        return True

    def DetectSubPatch(self):
        hasSubPatch = False
        object_info = lwsdk.LWObjectInfo()
        item_info = lwsdk.LWItemInfo()
        
        objectID = item_info.first( lwsdk.LWI_OBJECT, lwsdk.LWITEM_NULL )
        while objectID:
            meshinfo_frozen = object_info.meshInfo( objectID, 1 )
            meshinfo_notfrozen = object_info.meshInfo( objectID, 0 )
            #print >>sys.stderr, "   meshinfo_frozen.numPoints = %d"%meshinfo_frozen.numPoints()
            #print >>sys.stderr, "   meshinfo_notfrozen.numPoints = %d"%meshinfo_notfrozen.numPoints()
            #print >>sys.stderr, "   flags & LWOBJF_CONTAINSPATCHES = %d"%(object_info.flags(objectID) & lwsdk.LWOBJF_CONTAINSPATCHES)
            #print >>sys.stderr, "   flags & LWOBJF_CONTAINSMETABALLS = %d"%(object_info.flags(objectID) & lwsdk.LWOBJF_CONTAINSMETABALLS)
            #print >>sys.stderr, "   PatchLevel0 = %d"%object_info.patchLevel(objectID)[0]  
            #print >>sys.stderr, "   PatchLevel1 = %d"%object_info.patchLevel(objectID)[1]

            #if object_info.patchLevel(objectID)[0] > 0:
            try:
                if meshinfo_frozen.numPoints() != meshinfo_notfrozen.numPoints():
                    hasSubPatch = True
            except AttributeError:
                hasSubPatch = False
  
            objectID = item_info.next( objectID )

        return hasSubPatch
        

    def uploadScene(self):
        self.updateTempFolder()
        if self._isMacOSX == False:
            # fix zip problem: on efface tout => comme a la 1ere execution!  (sauf pour APIKey : load+save) 
            self.loadAPIKey()
            try:
                shutil.rmtree(self._SketchFabTempFolder)
                self._SketchFabTempFolder = ""
            except Exception:
                a = 0
            if (os.path.isfile(self._SketchFabTempFolder)):
                print >>sys.stderr, "ERROR BAD ERASE FOLDER!"
            self.updateTempFolder()
            self.saveAPIKey()

        # ------- 1 - define and maybe create the temp folder + install uploader executable
        self.updateTempFolder()
        uploader_installed = self.install_uploader()
        
        if uploader_installed == False:
            self.displayReturnMsg("Failed to install "+self._SketchFabUploaderAppPath)
            return

                    
        # *** define export path: ********
        # fix locking and empty zip with SceneCounter
        scene_path=os.path.join(self._SketchFabTempDataFolder, "scene%d"%self._SceneCounter)
        archive_path = os.path.join(self._SketchFabTempDataFolder, "scene%d.zip"%self._SceneCounter)
        self._SceneCounter = self._SceneCounter+1

        #remove all previously added zip files:
        try:
            shutil.rmtree(self._SketchFabTempDataFolder)
        except Exception:
            a = 0

        if not os.path.exists(scene_path):
            os.makedirs(scene_path)
            if self._isMacOSX: # avoid file rights issue
                os.system("chmod a+w "+scene_path)

        # make valid title:
        if self._title == "":
            self._title = "NoName"

        # ------- 2 - save OBJ/DAE/FBX file
        # 2.1 : prepare the scene: freeze/rotate/detectNGon subpatch
        if self.DetectNGons() == False:
            return
        hasSubPatch = self.DetectSubPatch()
        if hasSubPatch:
            freeze = lwsdk.LWMessageFuncs().yesNo("Sketchfab warning", "Warning: The scene contains SubPatches", "Do you want to freeze them?")
            if (freeze):
                self.FreezeAllObjects()
                #lwsdk.LWMessageFuncs().yesNo("Sketchfab info", "Mesh Freezing Successful.", "")
                #lwsdk.LWMessageFuncs().info("Sketchfab info", "Mesh Freezing Successful.") # depends on user defined alert level
                self.displayMsg("Mesh Freezing Successful.")
            else:
                self.displayMsg("Base cage will then be uploaded.")
            
        if (self._rotate):
            self.rotateAllObjects(1)

        # 2.2: export
        useFBX = True
        if useFBX: # use FBX
            fbxFilename = os.path.join(scene_path, "scene.fbx")
            fbxFilename = fbxFilename.replace('\\', '/')
            #lwcmd = "Generic_ExportFBXCommand '" + fbxFilename + "'"
            lwcmd = "Generic_ExportFBXCommand '" + fbxFilename + "' FBX201100"
            lwcmd = lwcmd  + " True True False True"   # bExportCameras bExportLights bExportMorphs bExportModels
            lwcmd = lwcmd  + " False True True"   # bExportAnimations bExportMaterials bEmbedMedia
            lwcmd = lwcmd  + " False"   # False(ASCII) sAnimLayerName

            # options order: Filename sFBXVersion bExportCameras bExportLights bExportMorphs bExportModels bExportAnimations bExportMaterials bEmbedMedia bType sAnimLayerName
            # sFBXVersion: The version to be written. Valid versions: 'FBX201200', 'FBX201100', 'FBX201000', 'FBX200900', 'FBX200611'
            # bExportCameras: "True" or "False"
            # bExportLights: "True" or "False"
            # bExportMorphs: "True" or "False"
            # bExportModels: "True" or "False"
            # bExportAnimations: "True" or "False"
            # bExportMaterials: "True" or "False"
            # bEmbedMedia: "True" or "False"
            # bType: "True" for ASCII, "False" for binary FBX format
            # sAnimLayerName: The name to give the FBX Animation Layer
            # test script: 
            #import lwsdk
            #lwsdk.command("Generic_ExportFBXCommand 'C:/Dev/test_lw_export.fbx' FBX201100 True True False True False True True False")
            #lwsdk.command("Generic_ExportFBXCommand 'C:/Dev/test_lw_export.fbx' FBX201100 True True False True False True True True") ASCII version!

            logForDebug("Execute Command: "+lwcmd)
            
            lwsdk.command(lwcmd)
            
        else:
            lwcmd = "SaveObject " + os.path.join(scene_path, "scene.lwo")
            logForDebug("Execute Command: "+lwcmd)
            lwsdk.command(lwcmd)
        
        # 2.3: restore rotation
        if (self._rotate):
            self.rotateAllObjects(-1)


        # ------- 3 - compress the file
        if os.path.isfile(archive_path):
            os.remove(archive_path)
        logForDebug("Creating "+archive_path)
        filelist = os.listdir(scene_path)
        archive = zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED)
        saveCWD = os.getcwd()
        os.chdir(scene_path)
        for f in filelist:
            archive.write(f)
            logForDebug("  Add in Zip: "+f)
        archive.close()
        filelist = None
        os.chdir(saveCWD)

        # 3.1 - delete exported scene: le but est d'eviter des problemes de droit sur le Mac
                #os.system("rm -rf "+scene_path)
            #try:
                #shutil.rmtree(self._SketchFabTempDataFolder)
            #except Exception:
                #a = 0
        if self._isMacOSX: # avoid file rights issue
            os.system("chmod a+w "+archive_path)
                
        # ------- 4 - upload archive
        zipSize = os.path.getsize( archive_path )
        self.startWaiting(zipSize)
        
        # 5.1 : write settings text file
        returnmsg_path = os.path.join(self._SketchFabTempDataFolder, "returnmsg.txt")
        
        # clean strings: no newline:
        self._APIKey = self._APIKey.strip('\n')
        self._title = self._title.strip('\n')
        self._description = self._description.strip('\n')
        self._password = self._password.strip('\n')
        
        useCURL = self._isMacOSX

        if useCURL:
            logForDebug("TEST USING CURL !!!")
            if self._isMacOSX:
                cmd = '/usr/bin/curl -k -X POST https://api.sketchfab.com/v1/models'
            else:
                thisScriptFilePath = os.path.realpath(__file__)
                thisScriptFolder = os.path.dirname(thisScriptFilePath)
                #os.chdir(thisScriptFolder)
                #cmd = 'curl' + ' -k -X POST https://api.sketchfab.com/v1/models'
                cmd = 'C:/Dev/curl -k -X POST https://api.sketchfab.com/v1/models'
            cmd = cmd + ' -F "fileModel=@' + archive_path + '"'
            cmd = cmd + ' -F "filenameModel=scene0.zip"'
            cmd = cmd + ' -F "title='+self._title+'"'
            cmd = cmd + ' -F "description='+self._description+'"'
            cmd = cmd + ' -F "tags='+self._tags+' lightwave"'
            cmd = cmd + ' -F "source=lightwave-exporter"'
            if self._private:
                cmd = cmd + ' -F "private=1"'
                cmd = cmd + ' -F "password='+self._password+'"'
            cmd = cmd + ' -F "token=' + self._APIKey + '"'
            #cmd = cmd + ' --progress-bar' 
            cmd = cmd + ' -s'   # silent mode
            #cmd = cmd + ' 2> "' + returnmsg_path + '"'
            cmd = cmd + ' -o "' + returnmsg_path + '"'
            logForDebug(cmd)

        else:  # --------------- USE my uploader app 
            settingsFileName = os.path.join(self._SketchFabTempDataFolder, "settings.txt")
            settings_file = open(settingsFileName, 'w')
            settings_file.write(self._APIKey+"\n")
            settings_file.write(self._title+"\n")
            settings_file.write(self._description+"\n")
            settings_file.write(self._tags+"\n")
            if self._private:
                settings_file.write("true\n")
            else:
                settings_file.write("false\n")
            settings_file.write(self._password+"\n")
            settings_file.write(archive_path+"\n")
            settings_file.write(returnmsg_path+"\n")
            settings_file.close()
            logForDebug("settings file :"+settingsFileName)
            if self._isMacOSX: # avoid file rights issue
                os.system("chmod a+w "+settingsFileName)
            
            cmd = self._SketchFabUploaderAppPath+" -s "+settingsFileName


        if self._isMacOSX or useCURL:
            logForDebug("os.system("+cmd+")")
            ret = os.system(cmd)
            logForDebug("  returns:")
            try:
                logForDebug(ret)
            except:
                print >>sys.stderr, "Exception in logForDebug(ret)!" 

        elif True: #windows : NB subprocess.call is not working on MacOSX!
            logForDebug("subprocess.call:"+cmd)
            subprocess.call(cmd, shell=False)
        else:
            logForDebug("POPEN... ")
            p = subprocess.Popen((self._SketchFabUploaderAppPath, "-s", settingsFileName))
            p.wait
        
        # read result:
        if useCURL:
            if ret==0:
                # extract errormsg:
                errormsg = ""
                if os.path.exists(returnmsg_path):
                    logForDebug("curl out file exists ")
                    returnmsg_file = open(returnmsg_path, "r")
                    lines = returnmsg_file.readlines()
                    returnmsg_file.close()
                    if (len(lines) > 0):
                        errormsg = lines[0]
                        if errormsg.find('"success": true') != -1:
                            errormsg = ""


                if errormsg=="":
                    self.displayReturnMsg("Sketchfab upload success!")
                else:
                    self.displayReturnMsg("Sketchfab upload error:"+errormsg)
            else:
                self.displayReturnMsg("Sketchfab upload error! (%d)"%ret)
        else:
            if os.path.isfile(returnmsg_path):
                returnmsg_file = open(returnmsg_path, "r")
                lines = returnmsg_file.readlines()
                returnmsg_file.close()
                if self._isMacOSX: # avoid file rights issue
                    os.system("chmod a+w "+returnmsg_path)
                if (len(lines) > 0):
                    #logForDebug("INFO: Sketchfab:"+lines[0])
                    #lwsdk.LWMessageFuncs().info('Sketchfab:'+lines[0], None)
                    self.displayReturnMsg(lines[0])
            else:
                logForDebug("NO RETURN MSG .txt")
                lwsdk.LWMessageFuncs().info("Sketchfab: No Returned message!", None)
                
            
        self.endWaiting()

        

    def saveAPIKey(self):
        try:
            self.updateTempFolder()
            APIKeyFileName = os.path.join(self._SketchFabTempFolder, "apikey.txt")
            logForDebug("Saving APIKey in "+APIKeyFileName)
            file = open(APIKeyFileName, 'w')
            if file != None:
                file.write(self._APIKey+"\n")
                file.close()
            else:
                logForDebug("Cannot save APIKey")
        except:
            print >>sys.stderr, "Exception in saveAPIKey!" 
            
        
    def loadAPIKey(self):
        try:
            self.updateTempFolder()
            APIKeyFileName = os.path.join(self._SketchFabTempFolder, "apikey.txt")
            logForDebug("Loading APIKey in "+APIKeyFileName)
            if os.path.exists(APIKeyFileName):
                file = open(APIKeyFileName, 'r')
                lines = file.readlines()
                file.close()
                if (len(lines) > 0):
                    self._APIKey = lines[0]
                    self._APIKey = self._APIKey.strip('\n')
                    logForDebug("  -> "+self._APIKey)
                else:
                    logForDebug("  > 0 Lines in APIKey file")
        except:
            print >>sys.stderr, "Exception in loadAPIKey!" 
                
        
    def upload_event(self, control, userdata):
        self._title = self._ctrl_Title.get_str()
        self._description = self._ctrl_Description.get_str()
        self._tags = self._ctrl_Tags.get_str()
        self._APIKey = self._ctrl_APIKey.get_str()
        self._private = self._ctrl_Private.get_int()
        self._password = self._ctrl_Password.get_str()
        self._rotate = self._ctrl_Rotate.get_int()
        #self._freeze = self._ctrl_Freeze.get_int()
        
        self.saveAPIKey()
        
        self.uploadScene()

    def opendashboard_event(self, control, userdata):
        webbrowser.open("https://sketchfab.com/dashboard/recent")

        
    def logLwSdkFunctions(self):
        #import types
        #print [lwsdk.__dict__.get(a) for a in dir(lwsdk)
            #if isinstance(lwsdk.__dict__.get(a), types.FunctionType)]
        #for i in dir(lwsdk): 
            #print >>sys.stderr, i+"\n"
        print >>sys.stderr, "--------------- lwsdk:\n"
        help(lwsdk)
        
        #print >>sys.stderr, "--------------- pcore:\n"
        #help(pcore)
        #print >>sys.stderr, "--------------- LwPanels:\n"
        #help(lwsdk.LWPanels())
        #print >>sys.stderr, "--------------- LWXPanelControl:\n"
        #help(lwsdk.LWXPanelControl())
        #print >>sys.stderr, "--------------- LWXPanelFuncs:\n"
        #help(lwsdk.LWXPanelFuncs())
        #for i in dir(lwsdk.LWPanels()): 
            #print >>sys.stderr, i+"\n"
        
        
    def createPanel(self):
        #self.logLwSdkFunctions()
        
        global myui
        myui = lwsdk.LWPanels()
        self._panel = myui.create('Sketchfab uploader')
        
        VerticalPos = 15
        VerticalOffset = 28
        CtrlAlignHPos = 80
        
        # The Upload Button:
        self._ctrl_Upload = self._panel.wbutton_ctl('Upload to Sketchfab', 140)
        self._ctrl_Upload.move(CtrlAlignHPos+13, VerticalPos)
        self._ctrl_Upload.set_event(self.upload_event)
        #print >>sys.stderr, "--------------- Help Control Button:\n"
        #help(self._ctrl_Upload)

        # The Open DashBoard Button:
        self._ctrl_OpenDashboard = self._panel.wbutton_ctl('Open dashboard', 110)
        self._ctrl_OpenDashboard.move(CtrlAlignHPos+13+160, VerticalPos)
        self._ctrl_OpenDashboard.set_event(self.opendashboard_event)
        #print >>sys.stderr, "--------------- Help Control Button:\n"
        #help(self._ctrl_Upload)

        VerticalPos = VerticalPos + VerticalOffset + 12
        
        # All parameters:        
        self._ctrl_Title  = self._panel.str_ctl('.',64)
        ctrl_TitleTxt = self._panel.text_ctl('Title', '')
        ctrl_TitleTxt.move(16,VerticalPos)
        ctrl_TitleTxt.set_h(28)
        ctrl_TitleTxt.set_w(13)
        self._ctrl_Title.move(CtrlAlignHPos, VerticalPos)
        self._ctrl_Title.set_str(self._title)
        
        VerticalPos = VerticalPos + VerticalOffset
        
        self._ctrl_Description  = self._panel.str_ctl('.',64)
        ctrl_DescriptionTxt = self._panel.text_ctl('Description', '')
        ctrl_DescriptionTxt.move(16,VerticalPos)
        ctrl_DescriptionTxt.set_h(28)
        ctrl_DescriptionTxt.set_w(13)
        self._ctrl_Description.move(CtrlAlignHPos, VerticalPos)
        
        VerticalPos = VerticalPos + VerticalOffset

        self._ctrl_Tags = self._panel.str_ctl('.',64)
        ctrl_TagsTxt = self._panel.text_ctl('Tags', '')
        ctrl_TagsTxt.move(16,VerticalPos)
        ctrl_TagsTxt.set_h(28)
        ctrl_TagsTxt.set_w(13)
        self._ctrl_Tags.move(CtrlAlignHPos, VerticalPos)
        
        VerticalPos = VerticalPos + VerticalOffset
        
        self._ctrl_Private = self._panel.bool_ctl('Private')
        self._ctrl_Private.move(CtrlAlignHPos, VerticalPos)
                        
        VerticalPos = VerticalPos + VerticalOffset
        
        self._ctrl_Password = self._panel.str_ctl('.',64)
        ctrl_PasswordTxt = self._panel.text_ctl('Password', '')
        ctrl_PasswordTxt.move(16,VerticalPos)
        ctrl_PasswordTxt.set_h(28)
        ctrl_PasswordTxt.set_w(13)
        self._ctrl_Password.move(CtrlAlignHPos, VerticalPos)
        
        VerticalPos = VerticalPos + VerticalOffset + 12

        self._ctrl_APIKey = self._panel.str_ctl('.',64)
        ctrl_APIKeyTxt = self._panel.text_ctl('APIKey', '')
        ctrl_APIKeyTxt.move(16,VerticalPos)
        ctrl_APIKeyTxt.set_h(28)
        ctrl_APIKeyTxt.set_w(13)
        self._ctrl_APIKey.move(CtrlAlignHPos, VerticalPos)
        
        # load and set APIKey
        self.loadAPIKey()
        self._ctrl_APIKey.set_str(self._APIKey)

        VerticalPos = VerticalPos + VerticalOffset
        
        self._ctrl_Rotate = self._panel.bool_ctl('Rotate Vertical Axis')
        self._ctrl_Rotate.move(CtrlAlignHPos, VerticalPos)
        self._ctrl_Rotate.set_int(self._rotate)
                        
        VerticalPos = VerticalPos + VerticalOffset
        
        #self._ctrl_Freeze = self._panel.bool_ctl('Freeze')
        #self._ctrl_Freeze.move(CtrlAlignHPos, VerticalPos)
        #self._ctrl_Freeze.set_int(1)
                        
        self._panel.set_close_callback(self.panel_close_callback)

        self._panel.open(lwsdk.PANF_NOBUTT)

        self._panel.handle(lwsdk.EVNT_ALL)

        return True



    # ---------------- LWMaster --------------------------------------------
    def flags(self):
        return lwsdk.LWMAST_SCENE | lwsdk.LWMASTF_RECEIVE_NOTIFICATIONS

    def event(self, ma):
        if ma.eventCode == lwsdk.LWEVNT_NOTIFY_PLUGIN_CHANGED:
            change_struct = ma.data_as_change()
            if hasattr(change_struct, 'instance'):
                affects_me = (change_struct.instance == self)
                if affects_me:
                    if change_struct.pluginevent == lwsdk.LWEVNT_PLUGIN_CREATED:
                        self.createPanel()

                    elif change_struct.pluginevent == lwsdk.LWEVNT_PLUGIN_DISABLED:
                        #print >>sys.stderr, "LWEVNT_PLUGIN_DISABLED"
                        if self._panel != None:
                            self._panel.close()
                            self._panel = None

                    elif change_struct.pluginevent == lwsdk.LWEVNT_PLUGIN_ENABLED:
                        #print >>sys.stderr, "LWEVNT_PLUGIN_ENABLED"
                        if self._panel == None:
                            self.createPanel()

                    elif change_struct.pluginevent == lwsdk.LWEVNT_PLUGIN_UPDATED: # Double-click on the plugin!
                        #print >>sys.stderr, "LWEVNT_PLUGIN_UPDATED"
                        if self._panel == None:
                            self.createPanel()
                

                    #elif change_struct.pluginevent == lwsdk.LWEVNT_PLUGIN_DESTROYED:
                        #print >>sys.stderr, "LWEVNT_PLUGIN_DESTROYED"

                    #elif change_struct.pluginevent == lwsdk.LWEVNT_PLUGIN_DESTROYING:
                        #print >>sys.stderr, "LWEVNT_PLUGIN_DESTROYING"

        return 0.0

    # LWInstanceFuncs -------------------------------------
    def inst_copy(self, source):
        #print >>sys.stderr, "SketchfabMaster(lwsdk.IMaster)::inst_copy() called"
        self._instance_count = source._instance_count
        return None     # LWError

    def inst_descln(self):
        #print >>sys.stderr, "SketchfabMaster(lwsdk.IMaster)::inst_descln() called"
        #return "Python Info Panel - %d" % self._instance_count
        return "Sketchfab uploader"


#for Master Plugin registration:
ServerTagInfo = [
                    ( "Python Sketchfab", lwsdk.SRVTAG_USERNAME | lwsdk.LANGID_USENGLISH ),
#                    ( "Sketchfab", lwsdk.SRVTAG_BUTTONNAME | lwsdk.LANGID_USENGLISH ),
                ]

ServerRecord = { lwsdk.MasterFactory("LW_PySketchfab", SketchfabMaster) : ServerTagInfo }




