# Device definitions:
#
#	command | label | values | options
#
#	Command: the destination actionId to execute
#	Label: What to show the user or ~|~|~|~ for a separator
#
#	Values: id or optX = fieldPrefix,defaultValue
#		opt1 - opt9 = No valuesDict passed, the function options in that order
#		[field] = [intValue | fltValue | strValue | boolValue] where [field] is the valuesDict field id
#		[opt | field] = [optValue | lstValue] sends list array
#		[opt | field] = [...] {...} values as a list or dict - values must be separated by commas
#	
#	Options: fieldPrefix = command
#		command options:
#			[optValue | lstValue] = value:label;value:label...
#			[optValue | lstValue] = indigo.[devices | dimmer | sprinkler...]
#			[optValue | lstValue] = pluginId[.deviceTypeId]
#		

libversion = "1.0.0"	

INDIGO_DIMMER = 	[
	"setBrightness|Set Brightness|opt1=id,opt2=intValue|", 
	"brighten|Brighten by %|opt1=id,opt2=intValue|", 
	"dim|Dim by %|opt1=id,opt2=intValue|", 
	"match|Match Brightness|opt1=id,opt2=listValue|listValue=devices:indigo.dimmer"
]

INDIGO_RELAY = 		[
	"turnOn|Turn On|opt1=id|", 
	"turnOff|Turn Off|opt1=id|", 
	"toggle|Toggle On/Off|opt1=id|"
]

INDIGO_SPRINKLER =	[
	"run|Run Schedule|opt1=id,opt2=[fltValue]|",
	"pause|Pause Schedule|opt1=id",
	"resume|Resume Schedule|opt1=id",
	"stop|Stop (all zones off & clear schedule)|opt1=id",
	"~|~|~|~",
	"previousZone|Activate Previous Zone|opt1=id|",
	"nextZone|Activate Next Zone|opt1=id|",
	"~|~|~|~",
	"setActiveZone|Turn On Specific Zone|opt1=id,opt2=intValue|"
]

INDIGO_SPEEDCONTROL = [
	"setSpeedIndex|Set Fan Speed|opt1=id,opt2=intValue",
	"increaseSpeedIndex|Increase Fan Speed|opt1=id,opt2=intValue|",
	"decreaseSpeedIndex|Decrease Fan Speed|opt2=id,opt2=intValue|",
	"~|~|~|~",
	"turnOn|Turn Fan On (resume last speed)|opt1=id|",
	"turnOff|Turn Fan Off|opt1=id|",
	"toggle|Toggle Fan On/Off|opt1=id|"
]

INDIGO_THERMOSTAT =	[
	"setHeatSetpoint|Set Heat Setpoint|opt1=id,opt2=intValue|",
	"increaseHeatSetpoint|Increase Heat Setpoint|opt1=id,opt2=intValue|",
	"decreaseHeatSetpoint|Decrease Heat Setpoint|opt1=id,opt2=intValue|",
	"~|~|~|~",
	"setCoolSetpoint|Set Cool Setpoint|opt1=id,opt2=intValue|",
	"increaseCoolSetpoint|Increase Cool Setpoint|opt1=id,opt2=intValue|",
	"decreaseCoolSetpoint|Decrease Cool Setpoint|opt1=id,opt2=intValue|",
	"~|~|~|~",
	"setHvacMode|Set Main Mode|opt1=id,opt2=optsValue|optsValue=kHvacMode.Cool:Cool;kHvacMode.HeatCool:Heat/Cool;kHvacMode.Heat:Heat;~:~;kHvacMode.Off:Off;~:~;kHvacMode.ProgramHeatCool:Program Heat/Cool;kHvacMode.ProgramCool:Program Cool;kHvacMode.ProgramHeat:Program Heat",
	"setFanMode|Set Fan Mode|opt1=id,opt2=optsValue|optsValue=kFanMode.AlwaysOn:Always On;kFanMode.Auto:Auto",
	"~|~|~|~",
	"cycleModes|Cycle Through Thermostat Modes|opt1=id|",
	"toggleFan|Toggle Thermostat Fan Mode|opt1=id|"
]


INDIGO_VARIABLE = 	[
	"updateValue|Modify Variable|opt1=id,opt2=strValue|",
	"insertTimeStamp|Insert Timestamp into Variable|opt1=id|",
	"insertTimeStampFormatted|Insert Custom Format Timestamp into Variable|opt1=id,opt2=strValue|",
	"toggle|Toggle Variable|opt1=id,opt2=optsValue|optsValue=truefalse:true/false;onoff:on/off;yesno:yes/no;enabledisable:enabled/disabled;openclose:open/closed;lockunlock:unlocked/locked",
	"setToVariable|Set Variable to Variable|opt1=id,opt2=optsValue|optsValue=variables:variables"
]



































