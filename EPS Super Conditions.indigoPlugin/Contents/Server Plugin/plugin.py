#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Core libraries
import indigo
import os
import sys
import time
import datetime

# EPS 3.0 Libraries
import logging
from lib.eps import eps
from lib import ext
from lib import dtutil

# Plugin libraries

eps = eps(None)

################################################################################
# plugin - 	Basically serves as a shell for the main plugin functions, it passes
# 			all Indigo commands to the core engine to do the "standard" operations
#			and raises onBefore_ and onAfter_ if it wants to do something 
#			interesting with it.  The meat of the plugin is in here while the
#			EPS library handles the day-to-day and common operations.
################################################################################
class Plugin(indigo.PluginBase):

	# Define the plugin-specific things our engine needs to know
	TVERSION	= "3.1.0"
	PLUGIN_LIBS = ["cache", "conditions", "actions"]
	UPDATE_URL 	= ""
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		eps.__init__ (self)
		eps.loadLibs (self.PLUGIN_LIBS)
		
		#indigo.server.log (unicode(eps.plugcache.pluginCache))
		
		#self.core = core(self, libs=self.PLUGIN_LIBS, url=self.UPDATE_URL)
		#eps.plug.subscribeChanges (["devices", "variables"])
		#eps.plug.subscribeProtocols ({"zwave":"incoming|outgoing","insteon":"incoming|outgoing"})
		
		# TESTING
		#pc = plugcache(self)
		#retList = pc.getStateUIList (None)
		
		
	################################################################################
	# PLUGIN HANDLERS
	#
	# Raised onBefore_ and onAfter_ for interesting Indigo or custom commands that 
	# we want to intercept and do something with
	################################################################################	
	
	def onConditionAction (self, pluginAction):
		try:
			if eps.plug.checkConditions (pluginAction.props, None, True):
				self.logger.info ("Conditions pass, running the IF commands")
				eps.act.runAction (pluginAction.props, "Pass")
			else:
				self.logger.info ("Conditions fail, running the ELSE commands")
				eps.act.runAction (pluginAction.props, "Fail")
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	
	################################################################################
	# INDIGO COMMAND HAND-OFFS
	#
	# Everything below here are standard Indigo plugin actions that get handed off
	# to the engine, they really shouldn't change from plugin to plugin
	################################################################################
	
	################################################################################
	# INDIGO PLUGIN EVENTS
	################################################################################		
	
	# System
	def startup(self): return eps.plug.startup()
	def shutdown(self): return eps.plug.shutdown()
	def runConcurrentThread(self): return eps.plug.runConcurrentThread()
	def stopConcurrentThread(self): return eps.plug.stopConcurrentThread()
	def __del__(self): return eps.plug.delete()
	
	# UI
	def validatePrefsConfigUi(self, valuesDict): return eps.plug.validatePrefsConfigUi(valuesDict)
	def closedPrefsConfigUi(self, valuesDict, userCancelled): return eps.plug.closedPrefsConfigUi(valuesDict, userCancelled)
	
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	# Basic comm events
	def deviceStartComm (self, dev): return eps.plug.deviceStartComm (dev)
	def deviceUpdated (self, origDev, newDev): return eps.plug.deviceUpdated (origDev, newDev)
	def deviceStopComm (self, dev): return eps.plug.deviceStopComm (dev)
	def deviceDeleted(self, dev): return eps.plug.deviceDeleted(dev)
	def actionControlDimmerRelay(self, action, dev): return eps.plug.actionControlDimmerRelay(action, dev)
	
	# UI Events
	def validateDeviceConfigUi(self, valuesDict, typeId, devId): return eps.plug.validateDeviceConfigUi(valuesDict, typeId, devId)
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId): return eps.plug.closedDeviceConfigUi(valuesDict, userCancelled, typeId, devId)		
	
	################################################################################
	# INDIGO PROTOCOL EVENTS
	################################################################################
	def zwaveCommandReceived(self, cmd): return eps.plug.zwaveCommandReceived(cmd)
	def zwaveCommandSent(self, cmd): return eps.plug.zwaveCommandSent(cmd)
	def insteonCommandReceived (self, cmd): return eps.plug.insteonCommandReceived(cmd)
	def insteonCommandSent (self, cmd): return eps.plug.insteonCommandSent(cmd)
	def X10CommandReceived (self, cmd): return eps.plug.X10CommandReceived(cmd)
	def X10CommandSent (self, cmd): return eps.plug.X10CommandSent(cmd)

	################################################################################
	# INDIGO VARIABLE EVENTS
	################################################################################
	
	# Basic comm events
	def variableCreated(self, var): return eps.plug.variableCreated(var)
	def variableUpdated (self, origVar, newVar): return eps.plug.variableUpdated (origVar, newVar)
	def variableDeleted(self, var): return self.variableDeleted(var)
		
	################################################################################
	# INDIGO EVENT EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	def validateEventConfigUi(self, valuesDict, typeId, eventId): return eps.plug.validateEventConfigUi(valuesDict, typeId, eventId)
	def closedEventConfigUi(self, valuesDict, userCancelled, typeId, eventId): return eps.plug.closedEventConfigUi(valuesDict, userCancelled, typeId, eventId)
		
	################################################################################
	# INDIGO ACTION EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	def validateActionConfigUi(self, valuesDict, typeId, actionId): return eps.plug.validateActionConfigUi(valuesDict, typeId, actionId)
	def closedActionConfigUi(self, valuesDict, userCancelled, typeId, actionId): return eps.plug.closedActionConfigUi(valuesDict, userCancelled, typeId, actionId)
		
	################################################################################
	# INDIGO TRIGGER EVENTS
	################################################################################
	
	# Basic comm events
	def triggerStartProcessing(self, trigger): return eps.plug.triggerStartProcessing(trigger)
	def triggerStopProcessing(self, trigger): return eps.plug.triggerStopProcessing(trigger)
	def didTriggerProcessingPropertyChange(self, origTrigger, newTrigger): return eps.plug.didTriggerProcessingPropertyChange(origTrigger, newTrigger)
	def triggerCreated(self, trigger): return eps.plug.triggerCreated(trigger)
	def triggerUpdated(self, origTrigger, newTrigger): return eps.plug.triggerUpdated(origTrigger, newTrigger)
	def triggerDeleted(self, trigger): return eps.plug.triggerDeleted(trigger)
                                   
	# UI
	
	################################################################################
	# INDIGO SYSTEM EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	
	################################################################################
	# EPS EVENTS
	################################################################################		
	
	# Plugin menu actions
	def pluginMenuSupportData (self): return eps.plug.pluginMenuSupportData ()
	def pluginMenuSupportDataEx (self): return eps.plug.pluginMenuSupportDataEx ()
	def pluginMenuSupportInfo (self): return eps.plug.pluginMenuSupportInfo ()
	def pluginMenuCheckUpdates (self): return eps.plug.pluginMenuCheckUpdates ()
	
	# UI Events
	def getCustomList (self, filter="", valuesDict=None, typeId="", targetId=0): return eps.ui.getCustomList (filter, valuesDict, typeId, targetId)
	def formFieldChanged (self, valuesDict, typeId, devId): return eps.plug.formFieldChanged (valuesDict, typeId, devId)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	