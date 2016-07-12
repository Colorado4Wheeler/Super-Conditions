from os import listdir
import os.path
from os.path import isfile, join
import glob
from xml.dom import minidom
import plistlib
import string
import datetime
from datetime import timedelta

import indigo
import sys
import eps
import devactiondefs
import ui

class devactions:

	INDIGO_STATUS = 	["statusRequest|Request Full Status Update|id", "~|~|~", "energyupdate|Request Energy Update|id", "resetEnergyAccumTotal|Request Energy Usage|id"]
	INDIGO_RELAY = 		["turnOn|Turn On|id", "turnOff|Turn Off|id", "toggle|Toggle On/Off|id"]
	INDIGO_DIMMER = 	["setBrightness|Set Brightness|id,int", "brighten|Brighten by %|id,int", "dim|Dim by %", "match|Match Brightness|id,int"]
	INDIGO_IO = 		["setBinaryOutput_1|Turn On Output|id,[binaryOutputsAll],bool=True", "setBinaryOutput_2|Turn Off Output|id,[binaryOutputsAll],bool=False", "setBinaryOutput_3|Turn Off All Outputs|id,[binaryOutputsAll]=*,bool=False"]
	INDIGO_SPRINKLER = 	["run|Run Schedule|id,list", "pause|Pause Schedule|id", "resume|Resume Schedule|id", "stop|Stop (all zones off & clear schedule)|id", "~|~|~", "previousZone|Activate Previous Zone|id", "nextZone|Activate Next Zone|id", "~|~|~", "setActiveZone|Turn On Specific Zone|id,int"]
	
	
	#
	# Initialize the class
	#
	def __init__ (self, parent):
		self.parent = parent
		self.version = "1.1"
		
		self.CACHE = indigo.Dict()
		
		self.cachePluginActions()
		
	#
	# Read all plugin actions
	#
	def cachePluginActions (self):
		try:
			base = indigo.server.getInstallFolderPath() + "/Plugins"
			plugins = glob.glob(base + "/*.indigoPlugin")
			
			for plugin in plugins:
				pluginInfo = self.parsePlist (plugin)
				p = indigo.Dict()
				p["id"] = pluginInfo[0]
				p["name"] = pluginInfo[1]
				p["actions"] = {}
					
				self.parent.logger.debug("Caching %s (%s)" % (p["name"], p["id"]))
					
				if os.path.isfile(plugin + "/Contents/Server Plugin/Actions.xml"):
					x = minidom.parse(plugin + "/Contents/Server Plugin/Actions.xml")
					actions = x.getElementsByTagName('Action')
					self.parent.logger.threaddebug("\tReading %i actions" % len(actions))
					
					actionIdx = 0
					allactions = indigo.Dict()
					
					for action in actions:
						paction = {}
						
						paction["id"] = action.attributes["id"].value
						paction["name"] = ""
						paction["callback"] = ""
						paction["devicefilter"] = ""
						paction["uipath"] = ""
						paction["separator"] = False
						paction["order"] = actionIdx
						paction["generic"] = True
						
						try:
							paction["devicefilter"] = action.attributes["deviceFilter"].value
						except:
							paction["devicefilter"] = "" # nothing we can do about it
						
						if paction["devicefilter"] != "":
							paction["devicefilter"] = paction["devicefilter"].replace("self", p["id"])
							
						#self.parent.logger.threaddebug(paction["devicefilter"])
							
						try:
							paction["uipath"] = action.attributes["uiPath"].value
						except:
							paction["uipath"] = "" # nothing we can do about it
						
						callback = action.getElementsByTagName("CallbackMethod")
						if callback:
							for c in callback:
								if c.parentNode.localName.lower() != "field":
									paction["callback"] = c.childNodes[0].data
									
						aname = action.getElementsByTagName("Name")
						if aname:
							for a in aname:
								paction["name"] = a.childNodes[0].data
								
						configUI = action.getElementsByTagName("ConfigUI")
						if configUI:
							paction["generic"] = False
								
						#if device != "":
						#	self.parent.logger.info("\t\tCached action '%s' method %s for action ID %s for '%s' devices" % (name, cb, id, device))
						#else:
						#	self.parent.logger.info("\t\tCached action '%s' method %s for action ID %s" % (name, cb, id))
						
						
						if action.hasChildNodes() == False:
							# Fields have children, seps do not
							#self.parent.logger.info("\t\t\tThis is a separator")	
							paction["separator"] = True
						
						self.parent.logger.threaddebug("\tAction %s for %s added" % (paction["name"], paction["devicefilter"]))
						allactions[paction["id"]] = paction
						actionIdx = actionIdx + 1
					
					p["actions"] = allactions
							
				self.CACHE[pluginInfo[0]] = p	
				
			#self.parent.logger.info(unicode(self.CACHE))				
							
		except Exception as e:
			eps.printException(e)
			
	
	#
	# Parse plist line data (a bit low brow but plist breaks XML so easy enough to do manually)
	#
	def parsePlist (self, path):
		try:
			plist = open(path + "/Contents/Info.plist")
			nameIdx = 0
			name = ""
			idIdx = 0
			id = ""
			for line in plist:
				if nameIdx == 1:
					name = line
					nameIdx = 0
					continue
					
				if idIdx == 1:
					id = line
					idIdx = 0
					continue
					
				x = string.find (line, 'CFBundleDisplayName')
				if x > -1: nameIdx = 1
				
				x = string.find (line, 'CFBundleIdentifier')
				if x > -1: idIdx = 1
				
			#self.parent.logger.info (name + "\t" + id)
			
			x = string.find (name, "<string>")
			y = string.find (name, "</string>")
			name = name[x + 8:y]
			
			x = string.find (id, "<string>")
			y = string.find (id, "</string>")
			id = id[x + 8:y]
			
			return [id, name]
		
		except Exception as e:
			eps.printException(e)
			
		return ["Unknown", "Unknown"]
	
	#
	# Compose variable operations list
	#
	def getIndigoVarOperations (self, filter, valuesDict=None, typeId="", targetId=0):
		myArray = [("default", "No compatible Indigo or variable operations found")]
		
		try:
			if filter[0] == "#":
				if eps.valueValid (valuesDict, filter[1:], True): targetId = int(valuesDict[filter[1:]])
				
			if targetId == 0: return myArray
					
			var = indigo.variables[targetId]
			self.parent.logger.threaddebug("Variable is typed as %s" % (unicode(type(var))))
			cmdList = devactiondefs.INDIGO_VARIABLE
			retAry = self.appendOptionList ([], cmdList)
			
			return retAry
		
		except Exception as e:
			eps.printException(e)
			
		return myArray
	
	#
	# Compose device operations list
	#
	def getIndigoOperations (self, filter, valuesDict=None, typeId="", targetId=0):
		myArray = [("default", "No compatible Indigo or device operations found")]
		filter = str(filter)
	
		try:
			if filter == "": return myArray
		
			retAry = []
			dev = False
		
			line = ["-1|" + self.getLine()]
		
			capable = []
		
			# If we are filtering for the target device get some info about it, otherwise use the filter passed
			if filter[0] == "#":
				if eps.valueValid (valuesDict, filter[1:], True):
					targetId = int(valuesDict[filter[1:]])
					filter = "targetId"
				else:
					filter = "none"
		
			thisFilter = filter.lower()
		
			if filter == "targetId":
				thisFilter = "none"
			
				dev = indigo.devices[int(targetId)]
				self.parent.logger.threaddebug("Detected %s is typed as %s" % (dev.name, unicode(type(dev))))
			
				#self.parent.logger.info(unicode(dev))
			
				#if dev.supportsStatusRequest: capable.append("status")
				if unicode(type(dev)) == "<class 'indigo.DimmerDevice'>": capable.append("dimmer")
				if unicode(type(dev)) == "<class 'indigo.RelayDevice'>": capable.append("relay")
				if unicode(type(dev)) == "<class 'indigo.SprinklerDevice'>": capable.append("sprinkler")
				if unicode(type(dev)) == "<class 'indigo.SensorDevice'>": capable.append("sensor")
				if unicode(type(dev)) == "<class 'indigo.SpeedControlDevice'>": capable.append("speed")
				if unicode(type(dev)) == "<class 'indigo.ThermostatDevice'>": capable.append("thermostat")
				
				self.parent.logger.threaddebug("%s base capabilities are %s" % (dev.name, unicode(capable)))
			
			# Relay device commands
			lists = 0
		
			if "relay" in capable or "sensor" in capable:
				cmdList = devactiondefs.INDIGO_RELAY
				retAry = self.appendOptionList (retAry, cmdList)
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
			
			if "dimmer" in capable:
				cmdList = devactiondefs.INDIGO_RELAY
				retAry = self.appendOptionList (retAry, cmdList)
				retAry = self.appendOptionList (retAry, line)
				
				cmdList = devactiondefs.INDIGO_DIMMER
				retAry = self.appendOptionList (retAry, cmdList)
				
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
				
			if "speed" in capable:
				cmdList = devactiondefs.INDIGO_SPEEDCONTROL
				retAry = self.appendOptionList (retAry, cmdList)
				
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
				
			if "thermostat" in capable:
				cmdList = devactiondefs.INDIGO_THERMOSTAT
				retAry = self.appendOptionList (retAry, cmdList)
				
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
				
			if "sprinkler" in capable:
				cmdList = devactiondefs.INDIGO_SPRINKLER
				retAry = self.appendOptionList (retAry, cmdList)
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
		
			if "status" in capable:
				cmdList = ["fullstatus|Request Full Status Update"]
				retAry = self.appendOptionList (retAry, cmdList)
				retAry = self.appendOptionList (retAry, line)
			
				cmdList = ["energyupdate|Request Energy Update", "energyusage|Request Energy Usage"]
				retAry = self.appendOptionList (retAry, cmdList)
			
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
		
			if dev:	
				# Ignore built-in Indigo devices, including the virtual device group and zwave plugins since even though it's a plugin it's sort of built-in
				if (dev.pluginId != "" or dev.deviceTypeId != "") and dev.pluginId != "com.perceptiveautomation.indigoplugin.zwave" and dev.pluginId != "com.perceptiveautomation.indigoplugin.devicecollection":
					# Not a built-in Indigo device						
					self.parent.logger.threaddebug("%s appears to be a plugin device rather than built-in" % dev.name)
					actionAry = self.getCachedActions (dev)
				
					if len(actionAry) > 0 and len(capable) > 0: retAry = self.appendOptionList (retAry, line) # Separate the specific commands
				
					for s in actionAry:
						retAry.append (s)
					
			if len(retAry) > 0:
				return retAry
			else:
				return myArray
	
		except Exception as e:
			eps.printException(e)
			return myArray
		
	#
	# Determine a device parent type
	#
	

	#
	# Read a list and append options to the destination list - 1.0.6
	#
	def appendOptionList (self, dstList, srcList):
		l = self.getLine()
				
		for s in srcList:
			data = s.split("|")
			
			if data[0] == "~":
				option = ("-1", l)	
			else:
				option = (data[0], data[1])

			dstList.append(option)
		
		return dstList
	
	#
	# Get action list from cache and return
	#
	def getCachedActions (self, dev):
		retAry = []
		
		try:
			# Anything without a type or id is typically an Indigo internal that we handle already
			if dev.pluginId == "" or dev.deviceTypeId == "":
				self.parent.logger.error("%s seems to be a built-in Indigo device that is not yet supported.\n\nIf you would like to see support for this device in future versions please post a request on the forum.\nPlugin:%s\nType:%s" % (dev.name, dev.pluginId, dev.deviceTypeId))
				return retAry
		
			try:
				plugin = self.CACHE[dev.pluginId]
			except:
				self.parent.logger.warning("%s does not have a cache, something may be wrong.  Info: %s.%s" % (dev.name, dev.pluginId, dev.deviceTypeId))
				return retAry
				
			line = ["-1|" + self.getLine()]		
				
			
			#self.parent.logger.info("\n" + unicode(plugin["actions"]))
			
			tempAry = []
			for i in range (0, len(plugin["actions"])):
				tempAry = self.appendOptionList (tempAry, line)
				
			for id, action in plugin["actions"].iteritems():
				isMatch = self.matchesDevice (dev, plugin, action)
				
				for index, item in enumerate(tempAry):
					if action["separator"]: continue # that is already the default value
					
					if action["uipath"] == "hidden": continue
					if isMatch == False: continue
					
					if index == action["order"]: 
						option = (action["callback"], action["name"])
						tempAry[index] = option
						
			#self.parent.logger.info(unicode(plugin))
			
			# Now audit the list to clean up entries that were not added
			newAry = []
			for index, item in enumerate(tempAry):
				for id, action in plugin["actions"].iteritems():
					if index == action["order"]:
						isMatch = self.matchesDevice (dev, plugin, action)
						
						if isMatch and action["uipath"] != "hidden" and action["generic"]: 
							newAry.append(tempAry[index])
						elif isMatch and action["generic"] == False and self.hasDefinedAction (dev, action["id"]):
							newAry.append(tempAry[index])
							
			# Final audit to clean up anywhere that has strange separators
			if len(newAry) > 1:
				lastItem = None
				for index, item in enumerate(newAry):
					if lastItem is None:
						# Make sure the first item is not a separator
						if newAry[index] == self.appendOptionList ([], line): continue
				
						lastItem = newAry[index]
						continue
					
					if lastItem != newAry[index]:
						retAry.append(newAry[index])
			else:
				retAry = newAry # Only one item, nothing more to do
							
			return retAry
		
		except Exception as e:
			eps.printException(e)
			return []
	
	
	#
	# See if a given action matches the device
	#
	def matchesDevice (self, dev, plugin, action):
		try:
			deviceMatch = False
						
			if action["devicefilter"] == "":			
				deviceMatch = True
				
			elif action["devicefilter"] == plugin["id"]:
				deviceMatch = True
				
			elif action["devicefilter"] == plugin["id"] + "." + dev.deviceTypeId:
				deviceMatch = True
			
			elif action["devicefilter"] != "":
				devFind = string.find (action["devicefilter"], plugin["id"] + "." + dev.deviceTypeId)
				if devFind > -1:
					deviceMatch = True
				else:
					devFind = string.find (action["devicefilter"], plugin["id"])
					if devFind > -1:
						devStr = action["devicefilter"][devFind:]
						
						# In case there is a comma
						devAry = devStr.split(",")
						
						if devAry[0] == plugin["id"]: deviceMatch = True
						if devAry[0] == plugin["id"] + "." + dev.deviceTypeId: deviceMatch = True
						
		
		except Exception as e:
			eps.printException(e)
			
		return deviceMatch
	
	#
	# See if we have a defined action for non-generic actions that require parameters
	#
	def hasDefinedAction (self, dev, actionId):
		try:
			# This is a future feature, we will be checking if this action ID for this device has been defined
			return False
			
		except Exception as e:
			eps.printException(e)
	
	#
	# Return custom action option array for device and action
	#
	def getOptionFields (self, dev, action):
		retVal = []
		fields = []
		fieldOptions = []
		
		try:
			cmdList = self.getDeviceActions (dev)
			
			for s in cmdList:
				cmds = s.split("|")
				
				# If the device command = the acton or if we are using generics like variables, compose list
				if cmds[0] == action:
					if cmds[3] != "":
						fopts = cmds[3].split(",")
						for fopt in fopts:
							# Check for function calls
							if string.find(fopt, "=devices:") > -1:
								fieldOptions.append (self.functionToGroup(fopt))				
																	
							else:							
								fieldOptions.append (fopt)										
					
					opts = cmds[2].split(",")
					for opt in opts:
						#self.parent.logger.info(opt)
						x = string.find (opt, "=")
						if x > -1:
							o = opt.split("=")
							#self.parent.logger.info(unicode(o))
							fields.append(o[1])
				
						
		except Exception as e:
			eps.printException(e)
			
		#self.parent.logger.info(unicode(retVal))
			
		return [fields, fieldOptions]
		
	#
	# Break down list/opt functions into virtual field options group
	#
	def functionToGroup (self, fopt):
		try:
			newFopt = ""
			
			detail = fopt.split("=")
			
			newFopt += detail[0] + "="
			
			funcInfo = detail[1].split(":")
			
			if funcInfo[0].lower() == "devices":
				for d in indigo.devices.iter(funcInfo[1]):
					newFopt += str(d.id) + ":" + d.name + ";"
					
			if newFopt != "":
				newFopt = newFopt[:-1]
				return newFopt
			
		except Exception as e:
			eps.printException(e)
			
		return fopt
	
		
	#
	# Get all actions for a given device
	#
	def getDeviceActions (self, dev):
		cmdList = []
		
		try:
			
			if unicode(type(dev)) == "<class 'indigo.Variable'>": return devactiondefs.INDIGO_VARIABLE
			if unicode(type(dev)) == "<class 'indigo.RelayDevice'>": cmdList += devactiondefs.INDIGO_RELAY
			if unicode(type(dev)) == "<class 'indigo.SensorDevice'>": cmdList += devactiondefs.INDIGO_RELAY
			if unicode(type(dev)) == "<class 'indigo.SprinklerDevice'>": cmdList += devactiondefs.INDIGO_SPRINKLER
			if unicode(type(dev)) == "<class 'indigo.DimmerDevice'>": 
				cmdList += devactiondefs.INDIGO_RELAY
				cmdList += devactiondefs.INDIGO_DIMMER
			if unicode(type(dev)) == "<class 'indigo.SpeedControlDevice'>": cmdList += devactiondefs.INDIGO_SPEEDCONTROL
			if unicode(type(dev)) == "<class 'indigo.ThermostatDevice'>": cmdList += devactiondefs.INDIGO_THERMOSTAT
		
		except Exception as e:
			eps.printException(e)
			
		return cmdList
	
	
	#
	# Run an action for a condition state
	#
	def runAction (self, dict, method):
		try:
			if dict["if" + method] == "device" and eps.valueValid (dict, "device" + method, True) and eps.valueValid (dict, "deviceAction" + method, True):
				dev = indigo.devices[int(dict["device" + method])]
				self.parent.logger.debug ("Executing device action '%s' on '%s'" % (dict["deviceAction" + method], dev.name))
				opts = self.calculateOptions (dev.id, self.getDeviceActions (dev), dict, method, dict["deviceAction" + method])
				self.executeDeviceAction (dev, dict["deviceAction" + method], opts)
				
			if dict["if" + method] == "variable" and eps.valueValid (dict, "variable" + method, True) and eps.valueValid (dict, "variableAction" + method, True):
				var = indigo.variables[int(dict["variable" + method])]
				self.parent.logger.debug ("Executing variable action '%s' on '%s'" % (dict["variableAction" + method], var.name))
				opts = self.calculateOptions (var.id, self.getDeviceActions (var), dict, method, dict["variableAction" + method])
				self.executeDeviceAction (var, dict["variableAction" + method], opts)
				
			if dict["if" + method] == "action" and eps.valueValid (dict, "action" + method, True):
				ag = indigo.actionGroups[int(dict["action" + method])]
				self.parent.logger.debug ("Executing action group '%s'" % ag.name)
				indigo.actionGroup.execute(ag.id)
				
		except Exception as e:
			eps.printException(e)
	
	
	#
	# Calculate options
	#
	def calculateOptions (self, id, cmdList, conditionValues, method, action):
		actionOpts = []
		
		try:
			for cmd in cmdList:
				c = cmd.split("|")
				if c[0] == action:
					options = c[2].split(",")
					for opts in options:
						opt = opts.split("=")
						#indigo.server.log(unicode(opt))
							
						key = ""
						value = ""
						
						if opt[0][:3] != "opt": key = opt[0] # the parameter key
							
						if opt[1] == "id":
							value = id			
										
						elif opt[1][:1] == "[":
							# List
							opt[1] = opt[1].replace("[", "")
							opt[1] = opt[1].replace("]", "")
							
							value = []
							l = conditionValues[opt[1] + method].split(",")
							
							for s in l:
								if opt[1] == "intValue": value.append(int(s.strip()))
								if opt[1] == "fltValue": value.append(float(s.strip()))
							
						elif opt[1][:1] == "{":
							# Dictionary
							X = 1
							
						else:
							value = conditionValues[opt[1] + method]
							
							if opt[1] == "intValue": value = int(value)
							if opt[1] == "fltValue": value = float(value)
						
						o = (key, value)
						actionOpts.append(o)
							
		except Exception as e:
			eps.printException(e)
			
		return actionOpts
	
	#
	# Execute dimmer device command
	#
	def executeDeviceAction (self, dev, action, opts):
		try:
			self.parent.logger.threaddebug ("Processing function with options: %s" % unicode(opts))
			
			subclass = "device"
			if unicode(type(dev)) == "<class 'indigo.RelayDevice'>": subclass = "device"
			if unicode(type(dev)) == "<class 'indigo.DimmerDevice'>": subclass = "dimmer"
			if unicode(type(dev)) == "<class 'indigo.SprinklerDevice'>": subclass = "sprinkler"
			if unicode(type(dev)) == "<class 'indigo.SensorDevice'>": subclass = "sensor"
			if unicode(type(dev)) == "<class 'indigo.SpeedControlDevice'>": subclass = "speedcontrol"
			if unicode(type(dev)) == "<class 'indigo.ThermostatDevice'>": subclass = "thermostat"
			if unicode(type(dev)) == "<class 'indigo.Variable'>": subclass = "variable"
			
			# Special conversions
			for i in range (0, len(opts)):
				try:
					if opts[i][1][:9] == "kHvacMode": opts[i] = ("", getattr(indigo.kHvacMode, opts[i][1].replace("kHvacMode.","")))
					if opts[i][1][:8] == "kFanMode": opts[i] = ("", getattr(indigo.kFanMode, opts[i][1].replace("kFanMode.","")))
					
				except:
					continue # some values are bound to crash and we don't care
				
			self.parent.logger.threaddebug ("Running function with options: %s" % unicode(opts))
			
			# Check for special actions
			if self.specialActions(dev, action, subclass, opts): return
			
			if len(opts) == 0:
				getattr(getattr(indigo, subclass), action)()
				
			elif len(opts) == 1:
				getattr(getattr(indigo, subclass), action)(opts[0][1])
				
			elif len(opts) == 2:
				getattr(getattr(indigo, subclass), action)(opts[0][1], opts[1][1])
				
			elif len(opts) == 3:
				getattr(getattr(indigo, subclass), action)(opts[0][1], opts[1][1], opts[2][1])
				
			elif len(opts) == 4:
				getattr(getattr(indigo, subclass), action)(opts[0][1], opts[1][1], opts[2][1], opts[3][1])
				
			elif len(opts) == 5:
				getattr(getattr(indigo, subclass), action)(opts[0][1], opts[1][1], opts[2][1], opts[3][1], opts[4][1])
				
			elif len(opts) == 6:
				getattr(getattr(indigo, subclass), action)(opts[0][1], opts[1][1], opts[2][1], opts[3][1], opts[4][1], opts[5][1])
				
		except Exception as e:
			eps.printException(e)
	
	#
	# Special built-in actions that we must run ourselves
	#
	def specialActions (self, dev, action, subclass, opts):
		try:
			self.parent.logger.threaddebug ("Checking special actions for %s under %s" % (action, subclass))
			
			if subclass == "dimmer" and action == "match":
				self.parent.logger.threaddebug ("Matching brightness of selected devices to %s" % dev.name)
				
				# Option 2 should contain all device ID's to match brightness
				for devId in opts[1][1]:
					indigo.dimmer.setBrightness (int(devId), int(dev.states["brightnessLevel"]))
				
				return True
				
			if subclass == "variable":
				if action == "insertTimeStamp":
					self.parent.logger.threaddebug ("Changing variable to standard time stamp on %s" % dev.name)
					d = indigo.server.getTime()
					indigo.variable.updateValue(dev.id, d.strftime("%Y-%m-%d %H:%M:%S"))
					
					return True
					
				if action == "insertTimeStampFormatted":
					self.parent.logger.threaddebug ("Changing variable to custom time stamp on %s" % dev.name)
					d = indigo.server.getTime()
					dformat = opts[1][1]
					if dformat == "": dformat = "%Y-%m-%d %H:%M:%S" 
					indigo.variable.updateValue(dev.id, d.strftime(dformat))
					
					return True
					
				if action == "toggle":
					self.parent.logger.threaddebug ("Toggling variable value on %s" % dev.name)
					var = indigo.variables[dev.id]
					curValue = False
					newValue = True
					
					if var.value.lower() == "true" or var.value.lower() == "on" or var.value.lower() == "yes" or var.value.lower() == "enabled" or var.value.lower() == "open" or var.value.lower() == "unlocked":
						curValue = True
						newValue = False
						
					varValue = unicode(newValue).lower()
					
					if opts[1][1] == "onoff":
						if newValue:
							varValue = "on"
						else:
							varValue = "off"
							
					elif opts[1][1] == "yesno":
						if newValue:
							varValue = "yes"
						else:
							varValue = "no"
							
					elif opts[1][1] == "enabledisable":
						if newValue:
							varValue = "enabled"
						else:
							varValue = "disabled"
							
					elif opts[1][1] == "openclose":
						if newValue:
							varValue = "open"
						else:
							varValue = "closed"
							
					elif opts[1][1] == "lockunlock":
						if newValue:
							varValue = "unlocked"
						else:
							varValue = "locked"
					
					indigo.variable.updateValue(dev.id, varValue)
					
					return True
				
			if subclass == "thermostat":
				if action == "cycleModes":
					self.parent.logger.threaddebug ("Cycling through HVAC modes on %s" % dev.name)
					
					if dev.hvacMode == "Cool": 
						indigo.thermostat.setHvacMode(dev.id, indigo.kHvacMode.HeatCool)

					elif dev.hvacMode == "HeatCool": 
						indigo.thermostat.setHvacMode(dev.id, indigo.kHvacMode.Heat)
						
					elif dev.hvacMode == "Heat": 
						indigo.thermostat.setHvacMode(dev.id, indigo.kHvacMode.Off)
						
					elif dev.hvacMode == "Off": 
						indigo.thermostat.setHvacMode(dev.id, indigo.kHvacMode.Cool)
						
					return True
					
				elif action == "toggleFan":
					self.parent.logger.threaddebug ("Toggling fan modes on %s" % dev.name)
					
					if dev.fanMode == "Auto": 
						indigo.thermostat.setHvacMode(dev.id, indigo.kFanMode.AlwaysOn)

					elif dev.fanMode == "AlwaysOn": 
						indigo.thermostat.setHvacMode(dev.id, indigo.kFanMode.Auto)
						
					return True
				
		
		except Exception as e:
			eps.printException(e)
	
		return False		
	
	#
	# Line
	#
	def getLine (self, length=25):
		ret = ""
		for i in range (0, length):
			ret += unicode("\xc4", "cp437")
	
		return ret
	
	
	
	
	
	
	
	
	
	
	
	
	