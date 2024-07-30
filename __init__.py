import lvgl as lv
import urequests
import net
import uasyncio as asyncio

# App Name
NAME = "Webcam"

# App Icon
ICON = "A:apps/webcam/resources/icon.png"

# LVGL widgets
scr = None
label = None

# App manager
app_mgr = None


# Constants
DEFAULT_BG_COLOR = lv.color_hex3(0x000)
retrieving_image = asyncio.Lock()
task = None

# Current image index
webcam_index = 0

async def load_webcam(lock):
    global scr, label, webcam_index
    
    await lock.acquire()
    # automatically aquires lock and releases it
    
    error = False
    
    try:
        while (not error):
            if scr:
                s = app_mgr.config()
                url = s.get(f"url{webcam_index + 1}", "Unknown")
                if url.startswith("http"):
                    if net.connected():
                        response = None
                        if '@' in url and ':' in url:
                            # we need to do basic auth
                            start = url.index(':') + 3
                            end = url.index('@')
                            usernamepassword = url[start:end]
                            url = url[:start] + url[(end + 1):]
                            if ':' in usernamepassword:
                                sep_index = usernamepassword.index(':')
                                username = usernamepassword[:sep_index]
                                password = usernamepassword[(sep_index + 1):]
                                print(f"Calling {url} with Username {username} and given password") 
                                response = urequests.get(url, auth=(username,password))
                        else:
                            print(f"Calling {url} without basic auth")
                            response = urequests.get(url)
                        
                        print(f"Got image from {url} with response {response.status_code}")

                        if response is not None and response.status_code == 200:                
                            image_description = lv.img_dsc_t()
                            image_description.data = response.content
                            image_description.data_size = len(response.content)
                            
                            image = lv.img(scr)
                            image.set_src(image_description)
                            image.center()
                            
                            scr.set_style_bg_color(lv.color_hex(0x000000),0)
                        else:
                            if response is None:
                                label.set_text(f"Error URL wrongly formatted")
                            else:
                                label.set_text(f"Error {response.status_code} while loading {url}")
                            lv.scr_load(scr)
                    else:
                        label.set_text(f"Wifi not connected")
                        lv.scr_load(scr)
                else:
                    label.set_text(f"Please configure webcams in application settings")
                    lv.scr_load(scr)
                    error = True
            await asyncio.sleep_ms(100)  # Ensure producer has time to grab the lock4
    except asyncio.CancelledError:
        print('Webcam thread received cancel command')
        raise
    lock.release()

def change_webcam(delta):
    global webcam_index, app_mgr, scr
    
    s = app_mgr.config()
    
    while (True):
        webcam_index = (webcam_index + delta) % 5
    
        # Check if URL is valid:
        url = s.get(f"url{webcam_index + 1}", "Unknown")
        if url.startswith("http") or webcam_index == 0:
            scr.set_style_bg_color(DEFAULT_BG_COLOR, lv.PART.MAIN)    
            label = lv.label(scr)
            label.center()
            label.set_text(f"Loading webcam {webcam_index + 1}...")
            lv.scr_load(scr)
            break
        

def event_handler(event):
    global app_mgr
    e_code = event.get_code()
    if e_code == lv.EVENT.KEY:
        e_key = event.get_key()
        print(f"Got key {e_key}")
        if e_key == lv.KEY.RIGHT:
            change_webcam(1)
        elif e_key == lv.KEY.LEFT:
            change_webcam(-1)
        elif e_key == lv.KEY.ESC:
            await app_mgr.exit()
    elif e_code == lv.EVENT.FOCUSED:
        # If not in edit mode, set to edit mode.
        if not lv.group_get_default().get_editing():
            lv.group_get_default().set_editing(True)

async def on_boot(apm):
    global app_mgr
    app_mgr = apm
    
async def on_pause():
    print('on pause')
    global task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Webcam loading task is cancelled now")
    
async def on_resume():
    print('on resume')
    global task
    task = asyncio.create_task(load_webcam(retrieving_image))
    
async def on_stop():
    print('on stop')
    global scr
    if scr:
        scr.clean()
        scr.del_async()
        scr = None

async def on_start():
    print('on start')
    global scr, label
    scr = lv.obj()
    lv.scr_load(scr)

    scr.set_style_bg_color(DEFAULT_BG_COLOR, lv.PART.MAIN)    
    label = lv.label(scr)
    label.center()
    label.set_text("Loading webcam 1...")
    lv.scr_load(scr)

    scr.add_event(event_handler, lv.EVENT.ALL, None)

    # Focus the key operation on the current screen and enable editing mode.
    lv.group_get_default().add_obj(scr)
    lv.group_focus_obj(scr)
    lv.group_get_default().set_editing(True)

#async def on_running_foreground():
#    """Called when the app is active, approximately every 200ms."""
#    global retrieving_image
#    if not retrieving_image.locked():
#        asyncio.create_task(load_webcam(retrieving_image))
        
def get_settings_json():
    return {
        "title":"Settings for Webcam app",
        "form": [
        # Generate an input and save the config with key 'username'
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 1:",
            "name": "url1",
            "tip": "Use http://{USERNAME}:{PASSWORD}@my.domain/webcam.jpg for Basic Auth",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 2:",
            "name": "url2",
            "tip": "Use http://{USERNAME}:{PASSWORD}@my.domain/webcam.jpg for Basic Auth",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 3:",
            "name": "url3",
            "tip": "Use http://{USERNAME}:{PASSWORD}@my.domain/webcam.jpg for Basic Auth",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 4:",
            "name": "url4",
            "tip": "Use http://{USERNAME}:{PASSWORD}@my.domain/webcam.jpg for Basic Auth",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 5:",
            "name": "url5",
            "tip": "Use http://{USERNAME}:{PASSWORD}@my.domain/webcam.jpg for Basic Auth",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        }]
    }