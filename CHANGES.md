Release Notes
==========

Everything is still in BETA.  Some stuff won't work.  Overall the program works, just a few areas that haven't been enabled yet and lots of optimization yet to do.  

Version 0.5 (Beta 5)

* Added Delay and Duration to relay/dimmer Turn On and Turn Off commands
* Changed confusing debug language when evaluating equal or not equal
* Added debug language to show how each condition fares in the evaluation

Version 0.4 (Beta 4)
-----------------

* NOTE: Because this version adds fields to the ConfigUI of the condition action you may get some errors when you open a condition from previous Betas, simply save and re-open the action to clear the errors
* Upgraded core template and libraries to the latest versions (makes better use of caching and speeds up forms as a result)
* Added 3 more conditions (for a total of 5)
* Added variable manipulation to Pass and Fail conditions
* Fixed a conditions cache error that could pop up when editing existing condition actions
* Added server actions Remove Delayed Action for All/Device/Trigger/Schedule as available Pass/Fail actions
* Added server actions Enable for All/Device/Trigger/Schedule as available Pass/Fail actions
* Added server actions Disable for All/Device/Trigger/Schedule as available Pass/Fail actions
* Added server actions Send Email as available Pass/Fail actions


Version 0.3 (Beta 3)
-----------------

* Removed Devices.xml since this plugin has no devices
* After re-writing the core engine, updated this plugin to use the new engine so almost an entirely new plugin


Development Notes
==========


Known Issues As Of The Most Current Release
---------------

* When evaluating numeric values if one is a float and the other is not the condition will fail unless the user provides a decimal point to compare to - i.e., user wants a value to be less than 10 and the actual value is 9.0 it will fail unless the user says they want the value to be less than 10.0
* Because evaluations are done as unicode, numeric values can fail if the first character of one is less than the other - i.e., comparing if 200 is less than 300 will succeed, but comparing if 200 is less than 1000 will not

Wish List
---------------

* Chained conditions (might be impossible to reliably do this until Indigo API supports digging into Action Groups)
* Move server actions into the general Indigo actions execution instead of having them one-off
* Resolve state sensorValue to proper text