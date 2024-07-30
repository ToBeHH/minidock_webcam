import lvgl as lv
import urequests
import net
import _thread
import time

# App Name
NAME = "Webcam"

# App Icon
ICON = "A:apps/webcam/resources/icon.png"

# LVGL widgets
scr = None
label = None

# App manager
app_mgr = None
task_running = False

# Constants
DEFAULT_BG_COLOR = lv.color_hex3(0x000)

# Current image index
webcam_index = 0

def load_webcam():
    global scr, label, webcam_index, task_running
    
    error = False
    
    try:
        while (task_running and not error):
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
                            
                            scr.set_style_bg_color(DEFAULT_BG_COLOR,0)
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
            time.sleep_ms(100)  # Allow other tasks to run
    except:
        print('Webcam thread had an exception')
        raise
    print("Webcam thread ended")

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
    printf(f"Got event with code {e_code}")
    
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
    
async def on_resume():
    print('on resume')
    global task_running
    task_running = True
    _thread.start_new_thread(load_webcam, ())
    
async def on_pause():
    print('on pause')
    global task_running
    task_running = False    
    
async def on_stop():
    print('on stop')
    global scr, task_running
    task_running = False
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