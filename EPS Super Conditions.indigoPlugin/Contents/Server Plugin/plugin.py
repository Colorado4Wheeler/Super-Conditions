#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Core libraries
import indigo
import os
import sys
import time
import datetime
import types

# EPS Libraries
from eps.cache import cache
from eps.conditions import conditions
from eps import ui
from eps import dtutil
from eps import eps

# EPS Support Libraries
import re
from datetime import timedelta
from bs4 import BeautifulSoup
import urllib2

# Plugin specific libraries
from eps.devactions import devactions
import ast

class Plugin(indigo.PluginBase):
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		try:
			self.TVERSION = "2.0"
			self.epsInit()
			self.pluginInit()
			
		except Exception as e:
			msg = eps.debugHeader ("Plugin intialization had an error, restart required!")
			self.logger.critical(msg)
			eps.printException(e)
			raise		

	#
	# Generic EPS initialization
	#			
	def epsInit (self):
		try:
			# Set any missing prefs
			self.pluginPrefs = eps.validateDictValue (self.pluginPrefs, "logLevel", "20", True)
			self.pluginPrefs = eps.validateDictValue (self.pluginPrefs, "pollingMode", "realTime", True)
			self.pluginPrefs = eps.validateDictValue (self.pluginPrefs, "pollingInterval", 1, True)
			self.pluginPrefs = eps.validateDictValue (self.pluginPrefs, "pollingFrequency", "s", True)
		
			# Change this to true if we are watching devices
			self.pluginPrefs = eps.validateDictValue (self.pluginPrefs, "monitorChanges", False, True)
				
			# EPS common startup
			self.logger.setLevel(int(self.pluginPrefs["logLevel"]))
			if int(self.pluginPrefs["logLevel"]) < 20: 
				self.debug = True
			else:
				self.debug = False
			
			pollingMode = self.pluginPrefs["pollingMode"]
			pollingInterval = int(self.pluginPrefs["pollingInterval"])
			pollingFrequency = self.pluginPrefs["pollingFrequency"]
			self.monitor = self.pluginPrefs["monitorChanges"]
		
			# Legacy cleanup (Indigo 7 removes need for debug mode and may eliminate it entirely at some point)
			if eps.valueValid (self.pluginPrefs, "debugMode"): 
				self.logger.info(u"Upgraded plugin preferences from pre-Indigo 7, depreciated preferences removed")
				del self.pluginPrefs["debugMode"]
				
			# EPS common variables and classes
			self.pluginUrl = ""
			eps.parent = self
			self.reload = False
			
			self.cache = cache (self, self.pluginId, pollingMode, pollingInterval, pollingFrequency)
			self.cond = conditions (self)
							
		except Exception as e:
			msg = eps.debugHeader ("Plugin intialization had an error, restart required!")
			self.logger.critical(msg)
			eps.printException(e)
			raise
	
	#
	# Plugin specific initialization
	#		
	def pluginInit (self):
		try:
			self.actions = devactions (self)
			
			# New global for initialized class versions that the plugin adds
			self.CLASSVERSIONS = []
			
			self.CLASSVERSIONS.append("actions: " + self.actions.version)
			return
		
		except Exception as e:
			msg = eps.debugHeader ("Plugin intialization had an error, restart required!")
			self.logger.critical(msg)
			eps.printException(e)
			raise
			
	################################################################################
	# EPS ROUTINES
	################################################################################
	
	#
	# Plugin menu: Performance options
	#
	def performanceOptions (self, valuesDict, typeId):
		self.logger.debug(u"Saving performance options")
		errorsDict = indigo.Dict()
		
		try:
			# Save the performance options into plugin prefs
			self.pluginPrefs["pollingMode"] = valuesDict["pollingMode"]
			self.pluginPrefs["pollingInterval"] = valuesDict["pollingInterval"]
			self.pluginPrefs["pollingFrequency"] = valuesDict["pollingFrequency"]
		
			self.cache.setPollingOptions (valuesDict["pollingMode"], valuesDict["pollingInterval"], valuesDict["pollingFrequency"])
				
		except Exception as e:
			eps.printException(e)
		
		return (True, valuesDict, errorsDict)
		
	#
	# Plugin menu: Library versions
	#
	def showLibraryVersions (self, forceDebug = False):
		try:
			s =  eps.debugHeader("LIBRARY VERSIONS")
			s += eps.debugLine (self.pluginDisplayName + " - v" + self.pluginVersion)
			s += eps.debugHeaderEx ()
			
			if "TVERSION" in dir(self):
				s += eps.debugLine("base: " + self.TVERSION)
				s += eps.debugLine(" ")
				
			s += eps.debugLine("indigo: " + indigo.server.version)
			
			for name, val in globals().items():
				if isinstance(val, types.ModuleType) or isinstance(val, types.ClassType):
					#self.logger.info(val.__name__)
					if "libversion" in dir(val):
						libname = val.__name__
						libversion = getattr(val, "libversion") #()
						
						# Resolve common (and potentially confusing) lib names
						if libname == "eps.eps": libname = "core"
						if libname == "eps.dtutil": libname = "dtutil"
						if libname == "eps.ui": libname = "ui"
						
						s += eps.debugLine(libname + ": " + libversion)
						
			# Check for common libraries
			if "cache" in dir(self): s += eps.debugLine("cache: " + self.cache.version)
			if "cond" in dir(self): s += eps.debugLine("conditions: " + self.cond.version)
			if "eto" in dir(self): s += eps.debugLine("eto: " + self.eto.version)
			if "sprinkler" in dir(self): s += eps.debugLine("sprinkler: " + self.sprinkler.version)
						
			# Iterate over our loaded classes and add them
			if "CLASSVERSIONS" in dir(self):
				for v in self.CLASSVERSIONS:
					s += eps.debugLine(v)
						
			s += eps.debugHeaderEx ()
			
			if forceDebug:
				self.logger.debug (s)
				return
			
			indigo.server.log (s) # leaving at legacy logging to ensure it gets output no matter what
				
		except Exception as e:
			eps.printException(e)
			

		
	#
	# Device action: Update
	#
	def updateDevice (self, devAction):
		try:
			dev = indigo.devices[devAction.deviceId]
		
			children = self.cache.getSubDevices (dev)
			for devId in children:
				subDev = indigo.devices[int(devId)]	
				self.updateDeviceStates (dev, subDev)	
		
		except Exception as e:
			eps.printException(e)
		
		return
			
	#
	# Update device
	#
	def updateDeviceStates (self, parentDev, childDev = None):
		try:
			stateChanges = self.cache.deviceUpdate (parentDev)
			
		except Exception as e:
			eps.printException(e)
			
		return
		
	#
	# Add watched states
	#
	def addWatchedStates (self, subDevId = "*", deviceTypeId = "*", mainDevId = "*"):
		
		self.cache.addWatchState ("onOffState", subDevId, "AutoOff")
		
		#self.cache.addWatchState (848833485, "onOffState", 1089978714)
		
		#self.cache.addWatchState ("onOffState", subDevId, deviceTypeId, mainDevId) # All devices, pass vars
		#self.cache.addWatchState ("onOffState") # All devices, all subdevices, all types
		#self.cache.addWatchState ("onOffState", 848833485) # All devices, this subdevice, all types
		#self.cache.addWatchState ("onOffState", subDevId, "epslcdth") # All devices, all subdevices of this type
		#self.cache.addWatchState ("onOffState", 848833485, "*", 1089978714) # This device, this subdevice of all types
		
		return
		
	#
	# Set state display on the device
	#
	def setStateDisplay (self, dev, force = False):
		stateValue = None
		stateUIValue = ""
		stateIcon = None
		stateDecimals = -1
		
		try:
			if dev.deviceTypeId == "devtemplate":
				X = 1 # placeholder
		
			else:
				return # failsafe
				
			if stateValue is None: return # nothing to do
		
			if force == False:
				if "statedisplay.ui" in dev.states:
					if stateValue == dev.states["statedisplay"] and stateUIValue == dev.states["statedisplay.ui"]: return # nothing to do
				else:
					if stateValue == dev.states["statedisplay"]: return # nothing to do
		
			dev.updateStateImageOnServer(stateIcon)
		
			if stateDecimals > -1:
				dev.updateStateOnServer("statedisplay", value=stateValue, uiValue=stateUIValue, decimalPlaces=stateDecimals)
			else:
				dev.updateStateOnServer("statedisplay", value=stateValue, uiValue=stateUIValue)	
		
		except Exception as e:
			eps.printException(e)
	
	################################################################################
	# EPS HANDLERS
	################################################################################
		
	#
	# Device menu selection changed
	#
	def onDeviceSelectionChange (self, valuesDict, typeId, devId):
		# This is only for the IF..THEN..ELSE plugin:
		if typeId == "condition":
			valuesDict = self.methodConditionChange (valuesDict, "Pass")
			valuesDict = self.methodConditionChange (valuesDict, "Fail")
			
		return valuesDict
		
	#
	# Device menu selection changed (for MenuItems.xml only)
	#
	def onMenuDeviceSelectionChange (self, valuesDict, typeId):
		# Just here so we can refresh the states for dynamic UI
		return valuesDict
	
	#
	# Return folder list
	#
	def getIndigoFolders(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getIndigoFolders (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of device states to (filter is the device to query)
	#
	def getStatesForDevice(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getStatesForDevice (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of Indigo operations
	#
	def getIndigoOperations(self, filter="", valuesDict=None, typeId="", targetId=0):
		return self.actions.getIndigoOperations (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of Indigo variable operations
	#
	def getIndigoVarOperations(self, filter="", valuesDict=None, typeId="", targetId=0):
		return self.actions.getIndigoVarOperations (filter, valuesDict, typeId, targetId)
	
	#
	# Return option array of devices with filter in states (filter is the state(s) to query)
	#
	def getDevicesWithStates(self, filter="onOffState", valuesDict=None, typeId="", targetId=0):
		return ui.getDevicesWithStates (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of device plugin props to (filter is the device to query)
	#
	def getPropsForDevice(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getPropsForDevice (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of plugin devices props to (filter is the plugin(s) to query)
	#
	def getPluginDevices(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getPluginDevices (filter, valuesDict, typeId, targetId)
		
	#
	# Return custom list
	#
	def getDataList(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getDataList (filter, valuesDict, typeId, targetId)
	
	#
	# Handle ui button click
	#
	def uiButtonClicked (self, valuesDict, typeId, devId):
		return valuesDict
		
	#
	# Concurrent thread process fired
	#
	def onRunConcurrentThread (self):
		try:
			self.updateCheck(True, False)
		
		except Exception as e:
			eps.printException(e)

		return
		
	################################################################################
	# EPS CONDITIONS ROUTINES
	################################################################################		
	
	#
	# Conditions field changed
	#
	def onConditionsChange (self, valuesDict, typeId, devId):
		# Just here so we can refresh the states for dynamic UI
		self.logger.debug("Condition field changed")
		try:
			if typeId == "condition":
				valuesDict = self.cond.setUIDefaults (valuesDict)
		
		except Exception as e:
			eps.printException(e)
								
		return valuesDict
		
	#
	# Return conditions library options
	#
	def getConditionsList (self, filter="conditions", valuesDict=None, typeId="", targetId=0):
		self.logger.debug("Condition field being populated")
		
		try:
			if filter.lower() == "conditions": return self.cond.appendUIConditions ([], "all")	
			if filter.lower() == "evals": return self.cond.addUIEvals ([])	
			if filter.lower() == "conditionmenu": return self.cond.addUIConditionMenu ([])	
		
		except Exception as e:
			eps.printException(e)
			
		
	
	#
	# Return custom list with condition options
	#
	def getConditionDateValues(self, filter="", valuesDict=None, typeId="", targetId=0):
		return self.cond.getConditionDateValues (filter, valuesDict, typeId, targetId)	
		
		
	################################################################################
	# EPS ROUTINES TO BE PUT INTO THEIR OWN CLASSES / METHODS
	################################################################################
		
	
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	#
	# Device starts communication
	#
	def deviceStartComm(self, dev):
		self.logger.debug(u"%s starting communication" % dev.name)
		
		try:
			dev.stateListOrDisplayStateIdChanged() # Make sure any device.xml changes are incorporated
			if self.cache is None: return
		
			if "lastreset" in dev.states:
				d = indigo.server.getTime()
				if dev.states["lastreset"] == "": dev.updateStateOnServer("lastreset", d.strftime("%Y-%m-%d "))
				
			if self.cache.deviceInCache (dev.id) == False:
				self.logger.debug(u"%s not in cache, appears to be a new device or plugin was just started" % dev.name)
				self.cache.cacheDevices() # Failsafe
			
			self.addWatchedStates("*", dev.deviceTypeId, dev.id) # Failsafe
			#self.cache.dictDump (self.cache.devices[dev.id])

			self.setStateDisplay(dev)
		
		except Exception as e:
			eps.printException(e)	
			
		return
			
	#
	# Device stops communication
	#
	def deviceStopComm(self, dev):
		self.logger.debug(u"%s stopping communication" % dev.name)
		
	#
	# Device property changed
	#
	def didDeviceCommPropertyChange(self, origDev, newDev):
		self.logger.debug(u"%s property changed" % origDev.name)
		return True	
			
	#
	# Device property changed
	#
	def deviceUpdated(self, origDev, newDev):
		if self.cache is None: return
		
		try:
			if eps.isNewDevice(origDev, newDev):
				self.logger.debug("New device '%s' detected, restarting device communication" % newDev.name)
				self.deviceStartComm (newDev)
				return		
		
			if origDev.pluginId == self.pluginId:
				self.logger.debug(u"Plugin device %s was updated" % origDev.name)
			
				# Re-cache the device and it's subdevices and states
				if eps.dictChanged (origDev, newDev):
					self.logger.debug(u"Plugin device %s settings changed, rebuilding watched states" % origDev.name)
					self.cache.removeDevice (origDev.id)
					self.deviceStartComm (newDev)
				
				# Collapse conditions if they got expanded
				self.cond.collapseAllConditions (newDev)
			
			else:
				changedStates = self.cache.watchedStateChanged (origDev, newDev)
				if changedStates:
					self.logger.debug(u"The monitored device %s had a watched state change" % origDev.name)
					# Send parent device array and changed states array to function to disseminate
					#self.logger.info(unicode(changedStates))
					X = 1 # placeholder		
		
		except Exception as e:
			eps.printException(e)	
		
		return
		
	#
	# Variable updated
	#
	def variableUpdated (self, origVariable, newVariable):
		# Since we don't use variable caching find any date/time devices using variables
		return
		
	#
	# Device deleted
	#
	def deviceDeleted(self, dev):
		try:
			if dev.pluginId == self.pluginId:
				self.logger.debug("%s was deleted" % dev.name)
				self.cache.removeDevice (dev.id)
					
		except Exception as e:
			eps.printException(e)
		
	
	################################################################################
	# INDIGO DEVICE UI EVENTS
	################################################################################	
	
		
	#
	# Device pre-save event
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		dev = indigo.devices[devId]
		self.logger.debug(u"%s is validating device configuration UI" % dev.name)
		
		if len(valuesDict["devicelist"]) == 0:
			errorDict = indigo.Dict()
			errorDict["devicelist"] = "You must select at least one device"
			errorDict["showAlertText"] = "You must select at least one device for this plugin to work!"
			return (False, valuesDict, errorDict)
		
		# Make sure they aren't choosing a device that is already on another auto off device
		for deviceId in valuesDict["devicelist"]:
			for dev in indigo.devices.iter(self.pluginId):
				if str(dev.id) != str(devId):
					if eps.valueValid (dev.pluginProps, "devicelist", True):
						for d in dev.pluginProps["devicelist"]:
							if d == deviceId and valuesDict["allowSave"] == False:
								errorDict = indigo.Dict()
								errorDict["devicelist"] = "One or more devices are already managed by other Powermiser auto-off devices"
								errorDict["showAlertText"] = "You are already managing %s in another Powermiser auto-off device, the conditions could overlap and cause problems.\n\nBe sure that your conditions are different enough not to collide with the other Powermiser device.\n\nThis is only a warning, hit save again to ignore this warning." % indigo.devices[int(deviceId)].name
								valuesDict["allowSave"] = True
								return (False, valuesDict, errorDict)
		
		# All is good, set the allowSave back to false for the next round
		valuesDict["allowSave"] = False
		
		# If we get here all is good so far, return from conditions in case there are problems there
		return self.cond.validateDeviceConfigUi(valuesDict, typeId, devId)
		
	#
	# Device config button clicked event
	#
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId):
		try:
			dev = indigo.devices[devId]
			self.logger.debug(u"%s is closing device configuration UI" % dev.name)
		
			if userCancelled == False: 
				self.logger.debug(u"%s configuration UI was not cancelled" % dev.name)
			
			#self.cache.dictDump (self.cache.devices[dev.id])
		
		except Exception as e:
			eps.printException(e)	
				
		return
		
	#
	# Event pre-save event
	#
	def validateEventConfigUi(self, valuesDict, typeId, eventId):
		self.logger.debug(u"Validating event configuration UI")
		return (True, valuesDict)
		
	#
	# Event config button clicked event
	#
	def closedEventConfigUi(self, valuesDict, userCancelled, typeId, eventId):
		self.logger.debug(u"Closing event configuration UI")
		return
		
	#
	# Action pre-save event
	#
	def validateActionConfigUi(self, valuesDict, typeId, actionId):
		self.logger.debug(u"Validating event configuration UI")
		return (True, valuesDict)
		
	#
	# Action config button clicked event
	#
	def closedActionConfigUi(self, valuesDict, userCancelled, typeId, actionId):
		self.logger.debug(u"Closing action configuration UI")
		return
		
		
	################################################################################
	# INDIGO PLUGIN EVENTS
	################################################################################	
	
	#
	# Plugin startup
	#
	def startup(self):
		self.logger.debug(u"Starting plugin")
		if self.cache is None: return
		
		if self.monitor: 
			if self.cache.pollingMode == "realTime": 
				#indigo.variables.subscribeToChanges()
				#indigo.devices.subscribeToChanges()
				#indigo.insteon.subscribeToIncoming()
				#indigo.insteon.subscribeToOutgoing()
				#indigo.zwave.subscribeToIncoming() # 2.0
				#indigo.zwave.subscribeToOutgoing() # 2.0
				X = 1 #placeholder
		
		# Add all sub device variables that our plugin links to, reloading only on the last one
		#self.cache.addSubDeviceVar ("weathersnoop", False) # Add variable, don't reload cache
		#self.cache.addSubDeviceVar ("irrigation") # Add variable, reload cache
		
		# Not adding any sub device variables, reload the cache manually
		self.cache.cacheDevices()
		
		#self.cache.dictDump (self.cache.devices)
		#indigo.server.log(unicode(dir(indigo.kFanMode)))
		
		
		return
		
	#	
	# Plugin shutdown
	#
	def shutdown(self):
		self.logger.debug(u"Plugin shut down")	
	
	#
	# Concurrent thread
	#
	def runConcurrentThread(self):
		if self.cache is None:
			try:
				while True:
					self.sleep(1)
					if self.reload: break
			except self.StopThread:
				pass
			
			# Only happens if we break out due to a restart command
			serverPlugin = indigo.server.getPlugin(self.pluginId)
			serverPlugin.restart(waitUntilDone=False)
				
			return
		
		try:
			while True:
				if self.cache.pollingMode == "realTime" or self.cache.pollingMode == "pollDevice":
					self.onRunConcurrentThread()
					self.sleep(1)
					if self.reload: break
				else:
					self.onRunConcurrentThread()
					self.sleep(self.cache.pollingInterval)
					if self.reload: break
					
				# Only happens if we break out due to a restart command
				serverPlugin = indigo.server.getPlugin(self.pluginId)
         		serverPlugin.restart(waitUntilDone=False)
		
		except self.StopThread:
			pass	# Optionally catch the StopThread exception and do any needed cleanup.
			
			
	################################################################################
	# INDIGO PLUGIN UI EVENTS
	################################################################################	
	
	#
	# Plugin config pre-save event
	#
	def validatePrefsConfigUi(self, valuesDict):
		self.logger.debug(u"%s is validating plugin config UI" % self.pluginDisplayName)
		return (True, valuesDict)
		
	#
	# Plugin config button clicked event
	#
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.logger.debug(u"%s is closing plugin config UI" % self.pluginDisplayName)
		
		try:
			if userCancelled == False:
				if "logLevel" in valuesDict:
					self.logger.setLevel(int(valuesDict["logLevel"]))
					
					if int(valuesDict["logLevel"]) < 20: 
						if self.debug == False: self.logger.info("Turning on debug logging")
						self.debug = True
					else:
						if self.debug: self.logger.info("Turning off debug logging")
						self.debug = False
				
		except Exception as e:
			eps.printException(e)	
		
		return
			
	#
	# Stop concurrent thread
	#
	def stopConcurrentThread(self):
		self.logger.debug(u"Plugin stopping concurrent threads")	
		self.stopThread = True
		
	#
	# Delete
	#
	def __del__(self):
		self.logger.debug(u"Plugin delete")	
		indigo.PluginBase.__del__(self)
		
	
	################################################################################
	# PLUGIN SPECIFIC ROUTINES
	################################################################################	
	
	#
	# Condition action executed
	#
	def onConditionAction (self, pluginAction):
		#self.logger.info(unicode(pluginAction))
		if self.cond.conditionsPass (pluginAction.props):
			self.logger.info ("Conditions pass, running the IF commands")
			self.actions.runAction (pluginAction.props, "Pass")
		else:
			self.logger.info ("Conditions fail, running the ELSE commands")
			self.actions.runAction (pluginAction.props, "Fail")
			
	#
	# Return menu options for a device that has choices 
	#
	def getCustomListList(self, filter="", valuesDict=None, typeId="", targetId=0):
		nonevalue = [("default", "No options to choose from")]
		retOptions = []
		
		if len(valuesDict) == 0: return nonevalue # failsafe
		
		try:
			for x in range (0, 1):
				method = "Pass"
				if x == 1: method = "Fail"
				
				# Device options
				if valuesDict["listValue" + method + "On"] == True and valuesDict["if" + method] == "device" and eps.valueValid (valuesDict, "device" + method, True) and eps.valueValid (valuesDict, "deviceAction" + method, True):
					# There are opt values to get, type is device, a device is chosen and an action is chosen, get the [field, opt] dict
					dev = indigo.devices[int(valuesDict["device" + method])]
					toggles = self.actions.getOptionFields (dev, valuesDict["deviceAction" + method])
					
					for toggle in toggles[1]:
						optAry = toggle.split("=")
						if optAry[0] == "listValue" and valuesDict["listValue" + method + "On"] == True:
							opts = optAry[1].split(";")
							for opt in opts:
								o = opt.split(":")
								
								if o[0] == "~":
									thisopt = ("-1", self.actions.getLine())
								else:
									thisopt = (o[0], o[1])
	
								retOptions.append (thisopt)
					
					if len(retOptions) > 0: return retOptions
					
				
		
		except Exception as e:
			eps.printException(e)
			
		return nonevalue
		
	#
	# Return menu options for a device that has choices 
	#
	def getCustomOptionList(self, filter="", valuesDict=None, typeId="", targetId=0):
		nonevalue = [("default", "No options to choose from")]
		retOptions = []
		
		if len(valuesDict) == 0: return nonevalue # failsafe
		
		try:
			for x in range (0, 1):
				method = "Pass"
				if x == 1: method = "Fail"
				
				# Device options
				if valuesDict["optsValue" + method + "On"] == True and valuesDict["if" + method] == "device" and eps.valueValid (valuesDict, "device" + method, True) and eps.valueValid (valuesDict, "deviceAction" + method, True):
					retOptions = self.generateCustomOptionList("device", valuesDict, method)
					if len(retOptions) > 0: return retOptions
					
				# Variable options
				if valuesDict["optsValue" + method + "On"] == True and valuesDict["if" + method] == "variable" and eps.valueValid (valuesDict, "variable" + method, True):
					retOptions = self.generateCustomOptionList("variable", valuesDict, method)
					if len(retOptions) > 0: return retOptions
				
		
		except Exception as e:
			eps.printException(e)
			indigo.server.log(unicode(valuesDict))
			
		return nonevalue
		
	#
	# Generate a custom options list
	#
	def generateCustomOptionList (self, type, valuesDict, method):
		try:
			ind = None
			retOptions = []
			
			if type == "device": ind = indigo.devices[int(valuesDict["device" + method])]
			if type == "variable": ind = indigo.variables[int(valuesDict["variable" + method])]
			
			# There are opt values to get, type is device, a device is chosen and an action is chosen, get the [field, opt] dict
			toggles = self.actions.getOptionFields (ind, valuesDict[type + "Action" + method])
			
			for toggle in toggles[1]:
				optAry = toggle.split("=")
				if optAry[0] == "optsValue" and valuesDict["optsValue" + method + "On"] == True:
					opts = optAry[1].split(";")
					for opt in opts:
						o = opt.split(":")
						
						if o[0] == "~":
							thisopt = ("-1", self.actions.getLine())
						else:
							thisopt = (o[0], o[1])

						retOptions.append (thisopt)
						
			return retOptions
						
		except Exception as e:
			eps.printException(e)
			
		return []
		
	#
	# Set form options for pass and fail methods
	#
	def methodConditionChange (self, valuesDict, method):
		try:
			# See if they changed from one type to another so we can clear and hide fields
			clearAllFields = False
			if eps.valueValid (valuesDict, "device" + method, True) and valuesDict["if" + method] != "device": clearAllFields = True
			if eps.valueValid (valuesDict, "action" + method, True) and valuesDict["if" + method] != "action": clearAllFields = True
			if eps.valueValid (valuesDict, "variable" + method, True) and valuesDict["if" + method] != "variable": clearAllFields = True
			if eps.valueValid (valuesDict, "server" + method, True) and valuesDict["if" + method] != "server": clearAllFields = True
			
			if clearAllFields:
				valuesDict["strValue" + method] = ""
				valuesDict["intValue" + method] = ""
				valuesDict["fltValue" + method] = ""
				valuesDict["boolValue" + method] = ""
				valuesDict["listValue" + method] = ""
				
				valuesDict["deviceAction" + method] = ""
				valuesDict["strValue" + method + "On"] = False
				valuesDict["intValue" + method + "On"] = False
				valuesDict["fltValue" + method + "On"] = False
				valuesDict["boolValue" + method + "On"] = False
				valuesDict["optsValue" + method + "On"] = False
				valuesDict["listValue" + method + "On"] = False
				
			# They selected a variable, show the variable commands
			if valuesDict["if" + method] == "variable" and eps.valueValid (valuesDict, "variable" + method, True):
				opts = self.actions.getIndigoVarOperations ("#variable" + method, valuesDict, typeId="", targetId=int(valuesDict["variable" + method]))
				optOk = False
				for opt in opts:
					if opt[0] == valuesDict["variableAction" + method]: optOk = True
					
				if optOk == False:
					# Get first non separator option as the default
					for opt in opts:
						if opt[0] != "-1": 
							valuesDict["variableAction" + method] = opt[0]
							break
							
					# Wipe out the previous values so they aren't static
					valuesDict["strValue" + method] = ""
					valuesDict["intValue" + method] = ""
					valuesDict["fltValue" + method] = ""
					valuesDict["boolValue" + method] = ""
					valuesDict["listValue" + method] = ""
			
			# They selected a device, populate the default action for that device
			if valuesDict["if" + method] == "device" and eps.valueValid (valuesDict, "device" + method, True):
				# Make sure the currently selected action is valid for this device
				opts = self.actions.getIndigoOperations ("#device" + method, valuesDict, typeId="", targetId=int(valuesDict["device" + method]))
				optOk = False
				for opt in opts:
					if opt[0] == valuesDict["deviceAction" + method]: optOk = True
					
				if optOk == False:
					# Get first non separator option as the default
					for opt in opts:
						if opt[0] != "-1": 
							valuesDict["deviceAction" + method] = opt[0]
							break
							
					# Wipe out the previous values so they aren't static
					valuesDict["strValue" + method] = ""
					valuesDict["intValue" + method] = ""
					valuesDict["fltValue" + method] = ""
					valuesDict["boolValue" + method] = ""
					valuesDict["listValue" + method] = ""
				
				#self.logger.info(unicode(opts))
			
			# Find out what device and action they have selected
			if valuesDict["if" + method] == "device" and eps.valueValid (valuesDict, "device" + method, True) and eps.valueValid (valuesDict, "deviceAction" + method, True):
				valuesDict = self.setActionOptions ("device", valuesDict, method)
						
			# Find out what variable and action they have selected
			if valuesDict["if" + method] == "variable" and eps.valueValid (valuesDict, "variable" + method, True) and eps.valueValid (valuesDict, "variableAction" + method, True):
				valuesDict = self.setActionOptions ("variable", valuesDict, method)
						
			# optValue is visible, populate the default action (must be after we toggle optsValue on or off)
			if valuesDict["optsValue" + method + "On"]:
				if valuesDict["if" + method] == "variable" and eps.valueValid (valuesDict, "variable" + method, True) and eps.valueValid (valuesDict, "variableAction" + method, True):
					valuesDict = self.setActionDefaultOption ("variable", valuesDict, method)
				
				if valuesDict["if" + method] == "device" and eps.valueValid (valuesDict, "device" + method, True) and eps.valueValid (valuesDict, "deviceAction" + method, True):
					valuesDict = self.setActionDefaultOption ("device", valuesDict, method)
									
				
						
		
		except Exception as e:
			eps.printException(e)
			
		return valuesDict
		
	#
	# Set the optValue default value if needed
	#
	def setActionDefaultOption (self, type, valuesDict, method):
		try:
			ind = None
			
			if type == "device": ind = indigo.devices[int(valuesDict["device" + method])]
			if type == "variable": ind = indigo.variables[int(valuesDict["variable" + method])]
			
			toggles = self.actions.getOptionFields (ind, valuesDict[type + "Action" + method])
			
			defOpt = ""
			optOk = False
			for toggle in toggles[1]:
				optAry = toggle.split("=")
				if optAry[0] == "optsValue" and valuesDict["optsValue" + method + "On"] == True:
					opts = optAry[1].split(";")
					for opt in opts:
						o = opt.split(":")
						if o[0] == valuesDict["optsValue" + method]:
							optOk = True
							break
							
			if optOk == False:
				for toggle in toggles[1]:
					optAry = toggle.split("=")
					if optAry[0] == "optsValue" and valuesDict["optsValue" + method + "On"] == True:
						opts = optAry[1].split(";")
						for opt in opts:
							o = opt.split(":")
							valuesDict["optsValue" + method] = o[0]
							break
		
		except Exception as e:
			eps.printException(e)
			
		return valuesDict
		
	#
	# Set device/variable/server options once action is selected
	#
	def setActionOptions (self, type, valuesDict, method):
		try:
			ind = None
			
			if type == "device": ind = indigo.devices[int(valuesDict["device" + method])]
			if type == "variable": ind = indigo.variables[int(valuesDict["variable" + method])]
			
			valuesDict["strValue" + method + "On"] = False
			valuesDict["intValue" + method + "On"] = False
			valuesDict["fltValue" + method + "On"] = False
			valuesDict["boolValue" + method + "On"] = False
			valuesDict["optsValue" + method + "On"] = False
			valuesDict["listValue" + method + "On"] = False
			
			# Get the [field, opt] dict
			toggles = self.actions.getOptionFields (ind, valuesDict[type + "Action" + method])
			for toggle in toggles[0]:
				# Filter out special characters before we try to turn on the field
				toggle = toggle.replace("[", "")
				toggle = toggle.replace("]", "")
				toggle = toggle.replace("{", "")
				toggle = toggle.replace("}", "")
				
				if toggle == "id" or eps.valueValid (valuesDict, toggle + "" + method + "On"):					
					if toggle != "id": valuesDict[toggle + "" + method + "On"] = True
				else:
					self.logger.error ("Unable to parse %s option field %s, check that the field name is valid" % (type, toggle))
					valuesDict["deviceAction" + method] = ""
					valuesDict["strValue" + method + "On"] = False
					valuesDict["intValue" + method + "On"] = False
					valuesDict["fltValue" + method + "On"] = False
					valuesDict["boolValue" + method + "On"] = False
					valuesDict["optsValue" + method + "On"] = False
					valuesDict["listValue" + method + "On"] = False
		
		except Exception as e:
			eps.printException(e)
		
		return valuesDict
			
	
	################################################################################
	# SUPPORT DEBUG ROUTINE
	################################################################################	
	
	#
	# Plugin menu: Support log
	#
	def supportLog (self):
		try:
			self.showLibraryVersions ()
		
			s = eps.debugHeader("SUPPORT LOG")
		
			# Get plugin prefs
			s += eps.debugHeader ("PLUGIN PREFRENCES", "=")
			for k, v in self.pluginPrefs.iteritems():
				s += eps.debugLine(k + " = " + unicode(v), "=")
			
			s += eps.debugHeaderEx ("=")
		
			# Report on cache
			s += eps.debugHeader ("DEVICE CACHE", "=")
		
			for devId, devProps in self.cache.devices.iteritems():
				s += eps.debugHeaderEx ("*")
				s += eps.debugLine(devProps["name"] + ": " + str(devId) + " - " + devProps["deviceTypeId"], "*")
				s += eps.debugHeaderEx ("*")
			
				s += eps.debugHeaderEx ("-")
				s += eps.debugLine("SUBDEVICES", "-")
				s += eps.debugHeaderEx ("-")
			
				for subDevId, subDevProps in devProps["subDevices"].iteritems():
					s += eps.debugHeaderEx ("+")
					s += eps.debugLine(subDevProps["name"] + ": " + str(devId) + " - " + subDevProps["deviceTypeId"] + " (Var: " + subDevProps["varName"] + ")", "+")
					s += eps.debugHeaderEx ("+")
				
					s += eps.debugLine("WATCHING STATES:", "+")
				
					for z in subDevProps["watchStates"]:
						s += eps.debugLine("     " + z, "+")
					
					s += eps.debugHeaderEx ("+")
					
					s += eps.debugLine("WATCHING PROPERTIES:", "+")
				
					for z in subDevProps["watchProperties"]:
						s += eps.debugLine("     " + z, "+")
					
					if subDevId in indigo.devices:
						d = indigo.devices[subDevId]
						if d.pluginId != self.pluginId:
							s += eps.debugHeaderEx ("!")
							s += eps.debugLine(d.name + ": " + str(d.id) + " - " + d.deviceTypeId, "!")
							s += eps.debugHeaderEx ("!")
					
							s += eps.debugHeaderEx ("-")
							s += eps.debugLine("PREFERENCES", "-")
							s += eps.debugHeaderEx ("-")
			
							for k, v in d.pluginProps.iteritems():
								s += eps.debugLine(k + " = " + unicode(v), "-")
				
							s += eps.debugHeaderEx ("-")
							s += eps.debugLine("STATES", "-")
							s += eps.debugHeaderEx ("-")
			
							for k, v in d.states.iteritems():
								s += eps.debugLine(k + " = " + unicode(v), "-")
						
							s += eps.debugHeaderEx ("-")
							s += eps.debugLine("RAW DUMP", "-")
							s += eps.debugHeaderEx ("-")
							s += unicode(d) + "\n"
				
							s += eps.debugHeaderEx ("-")
						else:
							s += eps.debugHeaderEx ("!")
							s += eps.debugLine("Plugin Device Already Summarized", "+")
							s += eps.debugHeaderEx ("!")
					else:
						s += eps.debugHeaderEx ("!")
						s += eps.debugLine("!!!!!!!!!!!!!!! DEVICE DOES NOT EXIST IN INDIGO !!!!!!!!!!!!!!!", "+")
						s += eps.debugHeaderEx ("!")
				
				s += eps.debugHeaderEx ("-")
		
		
			s += eps.debugHeaderEx ("=")
		
			# Loop through all devices for this plugin and report
			s += eps.debugHeader ("PLUGIN DEVICES", "=")
		
			for dev in indigo.devices.iter(self.pluginId):
				s += eps.debugHeaderEx ("*")
				s += eps.debugLine(dev.name + ": " + str(dev.id) + " - " + dev.deviceTypeId, "*")
				s += eps.debugHeaderEx ("*")
			
				s += eps.debugHeaderEx ("-")
				s += eps.debugLine("PREFERENCES", "-")
				s += eps.debugHeaderEx ("-")
			
				for k, v in dev.pluginProps.iteritems():
					s += eps.debugLine(k + " = " + unicode(v), "-")
				
				s += eps.debugHeaderEx ("-")
				s += eps.debugLine("STATES", "-")
				s += eps.debugHeaderEx ("-")
			
				for k, v in dev.states.iteritems():
					s += eps.debugLine(k + " = " + unicode(v), "-")
				
				s += eps.debugHeaderEx ("-")
			
			s += eps.debugHeaderEx ("=")
		
		
		
		
			self.logger.info(s)
		
		except Exception as e:
			eps.printException(e)	

	################################################################################
	# UPDATE CHECKS
	################################################################################

	def updateCheck (self, onlyNewer = False, force = True):
		try:
			try:
				if self.pluginUrl == "": 
					if force: self.logger.info ("This plugin currently does not check for newer versions", isError = True)
					return
			except:
				# Normal if pluginUrl hasn't been defined
				if force: self.logger.info ("This plugin currently does not check for newer versions", isError = True)
				return
			
			d = indigo.server.getTime()
			
			if eps.valueValid (self.pluginPrefs, "latestVersion") == False: self.pluginPrefs["latestVersion"] = False
			
			if force == False and eps.valueValid (self.pluginPrefs, "lastUpdateCheck", True):
				last = datetime.datetime.strptime (self.pluginPrefs["lastUpdateCheck"], "%Y-%m-%d %H:%M:%S")
				lastCheck = dtutil.DateDiff ("hours", d, last)
								
				if self.pluginPrefs["latestVersion"]:
					if lastCheck < 72: return # if last check has us at the latest then only check every 3 days
				else:
					if lastCheck < 2: return # only check every four hours in case they don't see it in the log
			
			
			page = urllib2.urlopen(self.pluginUrl)
			soup = BeautifulSoup(page)
		
			versions = soup.find(string=re.compile("\#Version\|"))
			versionData = unicode(versions)
		
			versionInfo = versionData.split("#Version|")
			newVersion = float(versionInfo[1][:-1])
		
			if newVersion > float(self.pluginVersion):
				self.pluginPrefs["latestVersion"] = False
				self.logger.warning ("Version %s of %s is available, you are currently using %s." % (str(round(newVersion,2)), self.pluginDisplayName, str(round(float(self.pluginVersion), 2))))
			
			else:
				self.pluginPrefs["latestVersion"] = True
				if onlyNewer == False: self.logger.info("%s version %s is the most current version of the plugin" % (self.pluginDisplayName, str(round(float(self.pluginVersion), 2))))
				
			self.pluginPrefs["lastUpdateCheck"] = d.strftime("%Y-%m-%d %H:%M:%S")
			
				
		except Exception as e:
			eps.printException(e)
		
	################################################################################
	# LEGACY MIGRATED ROUTINES
	################################################################################
	


	

	
