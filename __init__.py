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
task_running_lock = _thread.allocate_lock()

# Constants
DEFAULT_BG_COLOR = lv.color_hex3(0x000)

# Current image index
webcam_index = 0
webcam_changed = False

def load_image_from_url(url):
    global task_running
    
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
                    print(f"Calling {url} with Username '{username}' and given password") 
                    response = urequests.get(url, auth=(username,password))
            else:
                print(f"Calling {url} without basic auth")
                response = urequests.get(url)
                
            if response is not None:
                print(f"Got image with response {response.status_code}")
            
            if task_running:
                if response is not None and response.status_code == 200:                
                    image_description = lv.img_dsc_t({'data_size': len(response.content), 'data': response.content})
                    
                    response.close()
                    
                    return image_description
                else:
                    if response is None:
                        raise Exception(f"Error URL wrongly formatted")
                    else:
                        raise Exception(f"Error {response.status_code} while loading {url}")
                    
        else:
            raise Exception(f"Wifi not connected")            
    else:
        raise Exception(f"Please configure webcams in application settings")
    

def load_webcam():
    global scr, label, webcam_index, task_running, task_running_lock, webcam_changed
    
    if scr is None:
        scr = lv.obj()
        lv.scr_load(scr)

    scr.set_style_bg_color(DEFAULT_BG_COLOR, lv.PART.MAIN)
    scr.set_style_bg_img_src("A:apps/webcam/resources/bg.png", lv.PART.MAIN)

    if label is None:
        label = lv.label(scr)
        label.center()
    label.set_text(f"Loading webcam {webcam_index + 1}...")

    # Focus the key operation on the current screen and enable editing mode.
    lv.group_get_default().add_obj(scr)
    lv.group_focus_obj(scr)
    lv.group_get_default().set_editing(True)
    
    # Listen for keyboard events
    scr.add_event(event_handler, lv.EVENT.ALL, None)
    
    with task_running_lock:
        time.sleep_ms(800)  # Allow other tasks to run
        try:
            while (task_running):
                s = app_mgr.config()
                url = s.get(f"url{webcam_index + 1}", "Unknown")
                
                try:
                    image_description = load_image_from_url(url)
                    
                    if scr and not webcam_changed: # can get None, if app was exited
                        label.set_text("")
                        scr.set_style_bg_img_src(image_description, lv.PART.MAIN)
                    webcam_changed = False
                except Exception as error:
                    print(f"Error: {error}")
                    if scr: # can get None, if app was exited
                        label.set_text(str(error))
                        scr.set_style_bg_color(DEFAULT_BG_COLOR, lv.PART.MAIN)
                        time.sleep_ms(500)
                 
                if task_running:
                    time.sleep_ms(100)  # Allow other tasks to run
        except Exception as err:
            print(f'Webcam thread had an exception: {err}')
            raise
    print("Webcam thread ended")
    

def change_webcam(delta):
    global webcam_index, app_mgr, scr, label, webcam_changed
    
    s = app_mgr.config()
    webcam_changed = True
    
    while (True):
        webcam_index = (webcam_index + delta) % 5
    
        # Check if URL is valid:
        url = s.get(f"url{webcam_index + 1}", "Unknown")
        if url.startswith("http") or webcam_index == 0:
            scr.set_style_bg_color(DEFAULT_BG_COLOR, lv.PART.MAIN)
            scr.set_style_bg_img_src("A:apps/webcam/resources/bg.png", lv.PART.MAIN)
            label.set_text(f"Loading webcam {webcam_index + 1}...")
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
        #Escape key == EXIT app is handled by the underlying OS
    elif e_code == lv.EVENT.FOCUSED:
        # If not in edit mode, set to edit mode.
        if not lv.group_get_default().get_editing():
            lv.group_get_default().set_editing(True)


async def on_boot(apm):
    global app_mgr
    app_mgr = apm
    
    
async def on_resume():
    print('on resume')
    global task_running, task_running_lock
    
    if task_running_lock.locked():
        print("Waiting for lock to be released / previous thread to fininsh")
        while (task_running_lock.locked()):
            time.sleep_ms(100)
    
    print("Starting new thread")
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
        label = None
        

async def on_start():
    print('on start')
    scr = None
    label = None
    
    
def get_settings_json():
    return {
        "title":"Settings for Webcam app",
        "form": [
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 1:",
            "name": "url1",
            "tip": "Images need to have 320x240 pixels resolution. They cannot be scaled.",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 2:",
            "name": "url2",
            "tip": "Use http://{USERNAME}:{PASSWORD}@my.domain/webcam.jpg for Basic Auth.",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 3:",
            "name": "url3",
            "tip": "Leave empty, if not used.",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 4:",
            "name": "url4",
            "tip": "Leave empty, if not used.",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        },
        {
            "type": "input",
            "default": "",
            "caption": "URL for webcam 5:",
            "name": "url5",
            "tip": "Leave empty, if not used.",
            "attributes": { "placeholder": "http://my.domain/webcam.jpg"}
        }]
    }