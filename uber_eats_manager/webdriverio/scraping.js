const wdio = require("webdriverio");
const fetch = require('node-fetch');

const opts = {
  path: '/wd/hub',
  port: 4723,
  capabilities: {
    platformName: "Android",
    platformVersion: "11",
    deviceName: "emulator-5554",
    appPackage: "com.uber.restaurantmanager",
    appActivity: "com.uber.restaurantmanager.RootActivity",
    automationName: "UiAutomator2",
    noReset: true,
  }
};

async function main () {
  const client = await wdio.remote(opts);

  // Set long duration to wait for loading top page and the store tab page finished.
  // Tweak it according to the actual behaviour (basically no need to shorten).
  client.setImplicitTimeout(120 * 1000);

  // Login: don't automate it because it has OTA process that cannot be automated.
  // If you got to need to login to the app again (e.g. Session expired) please login manually.

  // Move to Stores tab
  await client.$('~Stores, tab, 2 of 3').click();

  // On Android there's no way to get elements not displayed in the current viewport,
  // so we'll go with the following workaround for that.
  // 1. Retrieve all elements in a screen and create hashes for restaurant name and order count.
  // 2. Scroll on a screen in some extent.
  // 3. Retrieve all elements in a screen again and add only new value to the map.

  // 例：{"店舗名1":"¥100", "店舗名2":"¥2,000"}
  const sales_hash = new Map();

  const all_stores_displayed = await findDisplayedStores(client);
  // Remove the first item that is not the store info.
  all_stores_displayed.shift();

  for (store_element of all_stores_displayed) {
    const data = await getDataFromStoreInfo(client, store_element);
    if (data !== undefined) {
      const [store_name, sales_value] = data;
      sales_hash.set(store_name, sales_value);
    }
  }

  // Reset the wait duration set earlier.
  client.setImplicitTimeout(0);

  let prev_total_count = sales_hash.size;
  // while (prev_total_count < 10) {  // For debug
  while (true) {
    scrollDown(client)

    for (store_element of await findDisplayedStores(client)) {
      const data = await getDataFromStoreInfo(client, store_element);
      if (data !== undefined) {
        const [store_name, sales_value] = data;
        sales_hash.set(store_name, sales_value);
      }
    }

    // Stop scraping here if there are no new store added
    // (considering it as it scrolls to the end of screen).
    if (sales_hash.size == prev_total_count) {
      break
    }

    prev_total_count = sales_hash.size
  }

  // Send data to API
  const response = await fetch('https://httpbin.org/post', {
    method: 'POST',
    body: JSON.stringify(sales_hash, replacer),
    headers: {
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  console.log(data);

  await client.deleteSession();
}

async function findDisplayedStores(client) {
  return await client.$$('//hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup')
}

async function getDataFromStoreInfo(client, store_element) {
  const text_views = await client.findElementsFromElement(store_element.elementId, 'class name', 'android.widget.TextView');
  // Can be less than 6 when a store info is partially displayed.
  if (text_views.length < 6) {
    return undefined;
  }
  const store_name = await client.$(text_views[0]).getText();
  const sales_value = await client.$(text_views[text_views.length-2]).getText();
  return [store_name, sales_value];
}

async function scrollDown(client) {
  await client.touchAction([
    {action: 'longPress', x: 0, y: 1500},
    {action: 'moveTo', x: 0, y: 500},
    'release'
  ]);
}

// Function as a replacer for JSON.stringify that converts Map to Object.
function replacer(key, value) {
  if (value instanceof Map) {
    const obj = {};
    for (const [k, v] of value) {
      obj[k] = v;
    }
    return obj;
  } else {
    return value;
  }
}

main();
