import time
import datetime
import math
import re
import requests
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction

def main():
    start = time.time()
    print('Start: ' + datetime.datetime.now().strftime('%H:%M:%S'))

    driver = setup_appium()

    try:
        dismissDialogIfNecessary(driver)

        # Set long duration to wait for loading top page and the store tab page finished.
        # Tweak it according to the actual behaviour (basically no need to shorten).
        driver.implicitly_wait(120)

        # Login: don't automate it because it has OTA process that cannot be automated.
        # If you got to need to login to the app again (e.g. Session expired) please login manually.

        # Move to Stores tab
        driver.find_element_by_accessibility_id('Stores, tab, 2 of 3').click()

        # On Android there's no way to get elements not displayed in the current viewport,
        # so we'll go with the following workaround for that.
        # 1. Retrieve all elements in a screen and create hashes for restaurant name and order count.
        # 2. Scroll on a screen in some extent.
        # 3. Retrieve all elements in a screen again and add only new value to the map.
        total_count = get_total_store_count(driver)
        # {"店舗名1":"¥100", "店舗名2":"¥2,000"}
        sales_hash = {}
        # {"店舗名1":"3", "店舗名2":"4"}
        orders_hash = {}

        all_stores_displayed = find_displayed_stores(driver)
        # Remove the first item that is not the store info.
        all_stores_displayed.pop(0)

        for store_element in all_stores_displayed:
            data = get_data_from_store_info(store_element)
            if (data is not None):
                (store_name, sales_value, orders_count) = data
                sales_hash[store_name] = sales_value
                orders_hash[store_name] = orders_count

        # Reset the wait duration set earlier.
        driver.implicitly_wait(0)

        prev_total_count = len(sales_hash)
        # for _ in range(5):  # For debug
        while len(sales_hash) < total_count:
            dismissDialogIfNecessary(driver)
            scroll_down(driver)

            for store_element in find_displayed_stores(driver):
                data = get_data_from_store_info(store_element)
                if (data is not None):
                    (store_name, sales_value, orders_count) = data
                    sales_hash[store_name] = sales_value
                    orders_hash[store_name] = orders_count

            # Note: There seems some cases the `while` condition cannot meat:
            # - The total amount displayed doesn't match the actual list length
            # - Duplication of store name in the list
            # So stop scraping here if there are no new store added (considering it as it
            # scrolls to the end of screen) even though the while condition doesn't meet.
            if len(sales_hash) == prev_total_count:
                print('Stop scraping as it seems done for all stores')
                break

            prev_total_count = len(sales_hash)
            print_progress(current=prev_total_count, total=total_count)


        # Print elapsed time for scraping all restaurants.
        print (f'elapsed_time: {time.time() - start}[sec]')

        # Send data to API
        endpoint = 'https://sample.amazonaws.com/v1/uber'
        headers = {'Content-Type': 'application/json'}
        data = {'data': create_api_post_data(sales_hash, orders_hash)}
        res = requests.post(endpoint, json=data, headers=headers)
        print(res)

        driver.close_app()

    except Exception as e:
        print(f'Error: {e}')
    finally:
        driver.quit()

def setup_appium():
    desired_caps = dict(
        platformName='Android',
        platformVersion='11.0',
        automationName='UiAutomator2',
        deviceName='emulator-5554',
        noReset=True,
        appPackage='com.uber.restaurantmanager',
        appActivity="com.uber.restaurantmanager.RootActivity"
    )
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    return driver

def get_total_store_count(driver):
    total_count_element = driver.find_element_by_xpath('/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.ViewGroup/android.widget.TextView')
    return int(re.findall(r'\d+', total_count_element.text)[0])

def find_displayed_stores(driver):
    return driver.find_elements_by_xpath('/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup')

def get_data_from_store_info(store_element):
    text_views = store_element.find_elements_by_class_name('android.widget.TextView')
    # Can be less than 6 when a store info is partially displayed.
    if len(text_views) < 6:
        return None
    store_name = text_views[0].text
    sales_value = text_views[-2].text
    orders_count = text_views[-1].text
    return (store_name, sales_value, orders_count)

def scroll_down(driver):
    window_height = get_window_height(driver)
    scroll_distance = window_height * 2 / 3  # Here can be more optimized
    TouchAction(driver).long_press(x=0, y=window_height).move_to(x=0, y=max(window_height-scroll_distance, 0)).release().perform()

def get_window_height(driver):
    bottom_bar_height = 100  ## 56px + additional bottom space
    scale = driver.get_display_density() / 160
    bottom_bar_height = bottom_bar_height * scale
    return driver.get_window_size()['height'] - bottom_bar_height

def print_progress(current, total):
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")}: {current}/{total} ({math.floor(current/total*100)}%)')

def create_api_post_data(sales_hash, orders_hash):
    # [{"restaurantName":"店舗名1", "sales":100,"orderCount":3},{"restaurantName":"店舗名2", "sales":2000,"orderCount":4}]
    result_hash_array = []
    for restaurant_name in sales_hash.keys():
        result_hash_array.append({
            'restaurantName': restaurant_name,
            'sales': int(re.sub('¥|,', '', sales_hash[restaurant_name])),
            'orderCount': int(orders_hash[restaurant_name])
        })
    return result_hash_array

# Close the error dialog that says "System UI isn't responding" if it appears.
# If it keeps appearing, refer to the Troubleshoot section in README.
def dismissDialogIfNecessary(driver):
    try:
        driver.find_element_by_id('android:id/aerr_wait').click()
    except:
        pass

while True:
    main()
    time.sleep(10)