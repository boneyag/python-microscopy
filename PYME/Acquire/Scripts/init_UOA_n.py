#!/usr/bin/python

##################
# init.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##################

#!/usr/bin/python
from PYME.Acquire.ExecTools import joinBGInit, HWNotPresent, init_gui, init_hardware
import scipy
import time

@init_hardware('Z Piezo')
def pz(scope):
    from PYME.Acquire.Hardware.Piezos import piezo_e816

    scope.piFoc = piezo_e816.piezo_e816('COM1', 400, -0.399)
    scope.register_piezo(scope.piFoc, 'z', needCamRestart=True)
    
@init_hardware('XY Stage')
def stage(scope):
    from PYME.Acquire.Hardware.Mercury import mercuryStepper
    scope.stage = mercuryStepper.mercuryStepper(comPort=4, axes=['A', 'B'], steppers=['M-229.25S', 'M-229.25S'])
    scope.stage.SetSoftLimits(0, [1.06, 20.7])
    scope.stage.SetSoftLimits(1, [.8, 17.6])

    scope.register_piezo(scope.stage, 'x', needCamRestart=True, channel=0)
    scope.register_piezo(scope.stage, 'y', needCamRestart=True, channel=1)
    
    scope.joystick = scope.stage.joystick
    scope.joystick.Enable(True)
    
    scope.CleanupFunctions.append(scope.stage.Cleanup)

@init_hardware('sCMOS Camera')
def sCMOS_cam(scope):
    from PYME.Acquire.Hardware.AndorNeo import AndorZyla

    cam = AndorZyla.AndorZyla(0)
    cam.Init()
    cam.port = 'R100'
    #cam.SetActive(False)
    #cam.orientation = dict(rotate=False, flipx=True, flipy=False)
    cam.DefaultEMGain = 0  # hack to make camera work with standard protocols

    scope.register_camera(cam, 'sCMOS')

@init_hardware('EMCCD Camera')
def EMCCD_cam(scope):
    from PYME.Acquire.Hardware.AndorIXon import AndorIXon

    cam = AndorIXon.iXonCamera(0)
    cam.port = 'L100'

    scope.register_camera(cam, 'EMCCD')

#scope.EnableJoystick = 'foo'

@init_gui('Camera controls')
def cam_controls(MainFrame, scope):
    from PYME.Acquire.Hardware.AndorNeo import ZylaControlPanel
    scope.camControls['sCMOS'] = ZylaControlPanel.ZylaControl(MainFrame, scope.cameras['sCMOS'], scope)
    MainFrame.camPanels.append((scope.camControls['sCMOS'], 'sCMOS Properties'))

    from PYME.Acquire.Hardware.AndorIXon import AndorControlFrame
    scope.camControls['EMCCD'] = AndorControlFrame.AndorPanel(MainFrame, scope.cameras['EMCCD'], scope)
    MainFrame.camPanels.append((scope.camControls['EMCCD'], 'EMCCD Properties'))

@init_gui('Sample database')
def samp_db(MainFrame, scope):
    from PYME.Acquire import sampleInformation
    sampPan = sampleInformation.slidePanel(MainFrame)
    MainFrame.camPanels.append((sampPan, 'Current Slide'))

@init_gui('Analysis settings')
def anal_settings(MainFrame, scope):
    from PYME.Acquire.ui import AnalysisSettingsUI
    AnalysisSettingsUI.Plug(scope, MainFrame)

@init_gui('Filter Wheel')
def filter_wheel(MainFrame, scope):
    from PYME.Acquire.Hardware.FilterWheel import WFilter, FiltFrame, FiltWheel
    filtList = [WFilter(1, 'EMPTY', 'EMPTY', 0),
                WFilter(2, 'ND.5', 'UVND 0.5', 0.5),
                WFilter(3, 'ND1', 'UVND 1', 1),
                WFilter(4, 'EMPTY', 'EMPTY', 0),
                WFilter(5, 'ND2', 'UVND 2', 2),
                WFilter(6, 'ND4.5', 'UVND 4.5', 4.5)]

    scope.filterWheel = FiltWheel(filtList, 'COM5', dichroic=None)
    fpan = FiltFrame(MainFrame, scope.filterWheel)
    scope.filterWheel.SetFilterPos("ND4.5")
    MainFrame.toolPanels.append((fpan, 'Filter Wheel'))

@init_hardware('Power Meter')
def power_meter(scope):
    from PYME.Acquire.Hardware import PM100USB

    try:
        scope.powerMeter = PM100USB.PowerMeter()
        scope.powerMeter.SetWavelength(671)
        scope.StatusCallbacks.append(scope.powerMeter.GetStatusText)
    except:
        pass


#InitGUI("""
#from PYME.Acquire.Hardware import ccdAdjPanel
##import wx
##f = wx.Frame(None)
#snrPan = ccdAdjPanel.sizedCCDPanel(notebook1, scope, acf)
#notebook1.AddPage(page=snrPan, select=False, caption='Image SNR')
##camPanels.append((snrPan, 'SNR etc ...'))
##f.Show()
##time1.WantNotification.append(snrPan.ccdPan.draw)
#""")

# @init_hardware('Lasers')
# def lasers(scope):
#     from PYME.Acquire.Hardware import lasers
#     scope.l488 = lasers.FakeLaser('l488',scope.cam,1, initPower=10)
#     scope.l488.register(scope)
#     scope.l405 = lasers.FakeLaser('l405',scope.cam,0, initPower=10)
#     scope.l405.register(scope)
    

@init_gui('Laser controls')
def laser_controls(MainFrame, scope):
    from PYME.Acquire.ui import lasersliders
    
    lcf = lasersliders.LaserToggles(MainFrame.toolPanel, scope.state)
    MainFrame.time1.WantNotification.append(lcf.update)
    MainFrame.camPanels.append((lcf, 'Laser Control'))
    
    lsf = lasersliders.LaserSliders(MainFrame.toolPanel, scope.state)
    MainFrame.time1.WantNotification.append(lsf.update)
    MainFrame.camPanels.append((lsf, 'Laser Powers'))

@init_gui('Focus Keys')
def focus_keys(MainFrame, scope):
    from PYME.Acquire.Hardware import focusKeys
    fk = focusKeys.FocusKeys(MainFrame, None, scope.piezos[0])


#InitGUI("""
#from PYME.Acquire.Hardware import splitter
#splt = splitter.Splitter(MainFrame, None, scope, scope.cam)
#""")

@init_gui('Action manager')
def action_manager(MainFrame, scope):
    from PYME.Acquire.ui import actionUI
    
    ap = actionUI.ActionPanel(MainFrame, scope.actions, scope)
    MainFrame.AddPage(ap, caption='Queued Actions')


#must be here!!!
joinBGInit() #wait for anyhting which was being done in a separate thread

#import numpy
#psf = numpy.load(r'd:\psf647.npy')
#psf = numpy.maximum(psf, 0.)
#from PYME.Analysis import MetaData
#fakeCam.rend_im.setModel(psf, MetaData.TIRFDefault)

#time.sleep(.5)
scope.initDone = True

