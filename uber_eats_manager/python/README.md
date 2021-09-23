## Setup

### Server

```sh
$ npm i -g appium
$ appium
```

### Client

```sh
$ pip install Appium-Python-Client requests
```

## Usage

Launch Appium server beforehand and then run the following commands.

```
$ git clone git@github.com:torufuruya/appium-scraping-examples.git
$ python3 appium-scraping-examples/uber_eats_manager/python/scraping.py
```

## How to use Appium Desktop

You'll need to use Appium Desktop when Uber Eats Manager app changes their UI/structure. Appium Desktop allows you to see the actual DOM structure in the app and see the path for each components like XPath. Here briefly introduces how to use Appium Desktop

1. D/L [Appium Desktop](https://github.com/appium/appium-desktop/releases/download/v1.21.0/Appium-mac-1.21.0.dmg)
2. Open Appium Desktop
3. Click the Start Server button
4. Click the magnify glass icon on the top right
5. Input the following info into Desired Capabilities
    - "platformName": "Android"
    - "platformVersion": "11"  # Change here as appropriate
    - "automationName": "UiAutomator2"
    - "deviceName": "emulator-5554"  # Change here as appropriate
    - "appActivity": "com.uber.restaurantmanager.RootActivity"
    - "appPackage": "com.uber.restaurantmanager"
    - "noReset": true
6. Click the Start Session button

## Troubleshoot

- If a popup dialog that says "System UI isn't responding" appears in the Android emulator (should be a bug of simulator), you cannot contionue scraping. So terminate the emulator and cold boot it again, then the dialog should not appear (at least for a while).
  - Cold boot an emulator by CLI: `$ emulator @<emulator_name> -no-snapshot-load`
  - Get the list of emulator names by CLI: `$ emulator -list-avds`
- If `socket hang up` error appears and nothing helps to resolve, try to uninstall the Appium app from Android emulator and run the script again.
