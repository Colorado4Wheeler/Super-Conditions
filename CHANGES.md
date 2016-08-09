Release Notes
==========

Everything is still in BETA.  Some stuff won't work.  Overall the program works, just a few areas that haven't been enabled yet and lots of optimization yet to do.  

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

None

Wish List
---------------

* Chained conditions (might be impossible to reliably do this until Indigo API supports digging into Action Groups)
* Move server actions into the general Indigo actions execution instead of having them one-off