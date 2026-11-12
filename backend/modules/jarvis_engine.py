import os
import re
import json
import time
import ctypes
import random
import logging
import psutil
import datetime
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("viralcut.jarvis")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = BASE_DIR / "output" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
CUSTOM_COMMANDS_FILE = BASE_DIR / "backend" / "database" / "jarvis_custom_commands.json"

VK_VOLUME_MUTE = 0xAD        # 173
VK_VOLUME_DOWN = 0xAE        # 174
VK_VOLUME_UP = 0xAF          # 175
VK_MEDIA_NEXT_TRACK = 0xB0   # 176
VK_MEDIA_PREV_TRACK = 0xB1   # 177
VK_MEDIA_PLAY_PAUSE = 0xB3   # 179

KEYEVENTF_KEYUP = 0x0002

JARVIS_AFFIRMATIONS = [
    "Right away, sir.",
    "At your service, sir.",
    "Executing now, sir.",
    "Consider it done, sir.",
    "Certainly, sir.",
    "Right on it, sir."
]

def _send_vk(vk_code: int):
    try:
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.04)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
    except Exception as e:
        logger.warning(f"Failed to send VK {vk_code}: {e}")

# Hardware & System Vitals
def get_system_vitals() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    freq_mhz = round(cpu_freq.current, 1) if cpu_freq else 0

    mem = psutil.virtual_memory()
    ram_percent = mem.percent
    ram_used_gb = round(mem.used / (1024 ** 3), 2)
    ram_total_gb = round(mem.total / (1024 ** 3), 2)

    disks = []
    for mount in ["C:\\", "D:\\"]:
        if os.path.exists(mount):
            try:
                du = psutil.disk_usage(mount)
                disks.append({
                    "drive": mount[:2],
                    "total_gb": round(du.total / (1024 ** 3), 1),
                    "used_gb": round(du.used / (1024 ** 3), 1),
                    "free_gb": round(du.free / (1024 ** 3), 1),
                    "percent": du.percent
                })
            except Exception:
                pass

    battery_info = {"has_battery": False, "percent": 100, "is_charging": True}
    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {
                "has_battery": True,
                "percent": int(battery.percent),
                "is_charging": bool(battery.power_plugged),
                "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            }
    except Exception:
        pass

    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    top_procs = []
    try:
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                if info and info['name'] and info['memory_percent'] > 0.5:
                    top_procs.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu": round(info['cpu_percent'] or 0.0, 1),
                        "mem": round(info['memory_percent'] or 0.0, 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        top_procs = sorted(top_procs, key=lambda x: x['mem'], reverse=True)[:6]
    except Exception:
        pass

    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": {"percent": cpu_percent, "cores": cpu_count, "freq_mhz": freq_mhz},
        "memory": {"percent": ram_percent, "used_gb": ram_used_gb, "total_gb": ram_total_gb},
        "disks": disks,
        "battery": battery_info,
        "uptime": f"{hours}h {minutes}m",
        "top_processes": top_procs
    }

# Hardware Control
def volume_up(steps: int = 5) -> str:
    for _ in range(max(1, min(steps, 25))):
        _send_vk(VK_VOLUME_UP)
    return f"Master volume increased by {steps * 2}%."

def volume_down(steps: int = 5) -> str:
    for _ in range(max(1, min(steps, 25))):
        _send_vk(VK_VOLUME_DOWN)
    return f"Master volume decreased by {steps * 2}%."

def volume_mute_toggle() -> str:
    _send_vk(VK_VOLUME_MUTE)
    return "Master audio mute toggled."

def set_volume_level(target_percent: int) -> str:
    target = max(0, min(100, int(target_percent)))
    for _ in range(50):
        _send_vk(VK_VOLUME_DOWN)
    time.sleep(0.04)
    steps_up = target // 2
    for _ in range(steps_up):
        _send_vk(VK_VOLUME_UP)
    return f"Master volume set to approximately {target}%."

def media_play_pause() -> str:
    _send_vk(VK_MEDIA_PLAY_PAUSE)
    return "Media playback toggled."

def lock_workstation() -> str:
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked, sir."
    except Exception as e:
        return f"Could not lock workstation: {e}"

def minimize_all_windows() -> str:
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], check=False)
        return "All desktop windows minimized."
    except Exception as e:
        return f"Minimize error: {e}"

def take_screenshot() -> Dict[str, Any]:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = SCREENSHOTS_DIR / filename
    saved = False

    try:
        import mss
        with mss.MSS() as sct:
            sct.shot(output=str(filepath))
            if filepath.exists() and filepath.stat().st_size > 1000:
                saved = True
    except Exception:
        pass

    if not saved:
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(all_screens=True)
            img.save(str(filepath), "PNG")
            saved = True
        except Exception:
            pass

    if saved:
        return {
            "success": True,
            "filename": filename,
            "filepath": str(filepath),
            "url": f"/screenshots/{filename}",
            "message": f"Screenshot captured: {filename}"
        }
    return {
        "success": False,
        "message": "Screenshot capture could not access active display buffer."
    }

def launch_app(app_target: str) -> str:
    target_clean = app_target.lower().strip()
    shortcuts = {
        "code": "code", "vscode": "code", "vs code": "code",
        "chrome": "chrome", "notepad": "notepad", "calculator": "calc", "calc": "calc",
        "explorer": "explorer", "cmd": "cmd", "terminal": "wt", "powershell": "powershell",
        "task manager": "taskmgr", "taskmgr": "taskmgr", "spotify": "spotify", "discord": "discord"
    }
    cmd = shortcuts.get(target_clean, target_clean)
    try:
        subprocess.Popen(f'start "" "{cmd}"', shell=True)
        return f"Launched application '{app_target}', sir."
    except Exception as e:
        return f"Could not launch '{app_target}': {e}"

def terminate_process(target: str) -> str:
    target = target.strip()
    proc_name = target if target.endswith(".exe") else f"{target}.exe"
    killed = 0
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'] and p.info['name'].lower() == proc_name.lower():
                p.kill()
                killed += 1
        except Exception:
            pass
    if killed > 0:
        return f"Terminated {killed} instance(s) of '{proc_name}'."
    return f"No active process found matching '{target}'."

def web_search(query: str, engine: str = "google") -> str:
    import urllib.parse
    clean_q = query.strip()
    encoded = urllib.parse.quote(clean_q)
    if engine == "youtube":
        url = f"https://www.youtube.com/results?search_query={encoded}"
    else:
        url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Searching {engine.title()} for '{clean_q}', sir."

def get_live_weather(city: str = "auto") -> Dict[str, Any]:
    import requests
    target = city.strip() if city and city != "auto" else ""
    try:
        url = f"https://wttr.in/{target}?format=j1"
        res = requests.get(url, timeout=3.5)
        if res.ok:
            data = res.json()
            curr = data.get("current_condition", [{}])[0]
            temp_c = curr.get("temp_C", "N/A")
            temp_f = curr.get("temp_F", "N/A")
            desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear")
            area = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", city)
            return {
                "success": True,
                "summary": f"Weather in {area}: {desc}, {temp_c}°C ({temp_f}°F), humidity {curr.get('humidity')}%, wind {curr.get('windspeedKmph')} km/h."
            }
    except Exception:
        pass
    return {"success": False, "summary": "Live weather service currently unavailable, sir."}

def get_wikipedia_summary(query: str) -> str:
    import requests
    import urllib.parse
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query.strip())}"
        headers = {"User-Agent": "ViralCutJarvis/1.0"}
        res = requests.get(url, headers=headers, timeout=3.5)
        if res.ok:
            extract = res.json().get("extract")
            if extract:
                return extract[:320] + ("..." if len(extract) > 320 else "")
    except Exception:
        pass
    return f"I could not locate detailed encyclopedic records for '{query}', sir."


# Custom Commands / Macros ("Costume Commands")
def load_custom_commands() -> List[Dict[str, Any]]:
    if not CUSTOM_COMMANDS_FILE.exists():
        return []
    try:
        with open(CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load custom commands: {e}")
        return []

def save_custom_commands(commands: List[Dict[str, Any]]):
    try:
        with open(CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(commands, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save custom commands: {e}")

def add_or_update_custom_command(cmd_data: Dict[str, Any]) -> Dict[str, Any]:
    commands = load_custom_commands()
    cmd_id = cmd_data.get("id") or f"cmd_{int(datetime.datetime.now().timestamp())}"
    cmd_data["id"] = cmd_id

    updated = False
    for i, c in enumerate(commands):
        if c.get("id") == cmd_id:
            commands[i] = cmd_data
            updated = True
            break
    if not updated:
        commands.append(cmd_data)

    save_custom_commands(commands)
    return cmd_data

def delete_custom_command(cmd_id: str) -> bool:
    commands = load_custom_commands()
    init_len = len(commands)
    commands = [c for c in commands if c.get("id") != cmd_id]
    if len(commands) < init_len:
        save_custom_commands(commands)
        return True
    return False

def execute_custom_command(cmd: Dict[str, Any], app_context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    actions = cmd.get("actions", [])
    executed_log: List[Dict[str, Any]] = []
    spoken_messages: List[str] = []
    app_directive: Dict[str, Any] = {}

    for act in actions:
        act_type = act.get("type", "")

        if act_type == "system_volume":
            v_act = act.get("action", "")
            if v_act == "mute":
                res = volume_mute_toggle()
            elif v_act == "set":
                res = set_volume_level(act.get("level", 50))
            else:
                res = volume_up(5)
            executed_log.append({"action": "volume", "result": res})

        elif act_type == "system_lock":
            res = lock_workstation()
            executed_log.append({"action": "lock", "result": res})

        elif act_type == "system_url":
            target = act.get("target", "")
            webbrowser.open(target)
            executed_log.append({"action": "url", "result": f"Opened {target}"})

        elif act_type == "app_setting":
            app_directive[act.get("key", "setting")] = act.get("value")
            executed_log.append({"action": "app_setting", "key": act.get("key"), "value": act.get("value")})

        elif act_type == "app_action":
            app_directive["trigger_action"] = act.get("action")
            app_directive["action_param"] = act.get("tab") or act.get("interval")
            executed_log.append({"action": "app_action", "detail": act.get("action")})

        elif act_type == "special" and act.get("action") == "channel_briefing":
            analytics = app_context.get("analytics") if app_context else {}
            vitals = get_system_vitals()
            tot_vids = analytics.get("total_videos", 0)
            tot_shorts = analytics.get("total_shorts", 0)
            comp_up = analytics.get("completed_uploads", 0)
            brief = (
                f"Studio Briefing, sir: You have {tot_vids} master videos loaded and {tot_shorts} viral Shorts ready. "
                f"A total of {comp_up} Shorts are published or scheduled on YouTube. "
                f"System CPU is at {vitals['cpu']['percent']}%, and workstation memory is running smoothly."
            )
            spoken_messages.append(brief)
            executed_log.append({"action": "briefing", "result": brief})

        elif act_type == "speak":
            msg = act.get("message", "")
            if msg:
                spoken_messages.append(msg)

    reply = " ".join(spoken_messages) if spoken_messages else f"Executed routine: {cmd.get('name')}, sir."
    return reply, executed_log, app_directive


class JarvisViralCutEngine:
    """
    JARVIS Co-Pilot Engine integrated inside ViralCut AI.
    Controls both ViralCut AI Studio pipelines and Windows System actions.
    """

    def process_command(self, user_text: str, app_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raw = (user_text or "").strip()
        if not raw:
            return {"response": "Standing by, sir. What are your orders?", "action_type": "none"}

        text_lower = raw.lower()
        clean = re.sub(r'^(hey\s+|ok\s+|hello\s+)?jarvis[,:\s]*', '', text_lower).strip()

        if not clean:
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} I am listening, sir.", "action_type": "greeting"}

        app_context = app_context or {}
        analytics = app_context.get("analytics") or {}

        # 1. Custom Commands / Macros ("Costume Commands")
        for cmd in load_custom_commands():
            if not cmd.get("enabled", True):
                continue
            triggers = [t.lower().strip() for t in cmd.get("triggers", [])]
            for trig in triggers:
                if trig == clean or trig in clean:
                    reply, log_steps, directive = execute_custom_command(cmd, app_context)
                    return {
                        "response": reply,
                        "action_type": "custom_macro",
                        "command_name": cmd.get("name"),
                        "directive": directive,
                        "details": {"steps": log_steps}
                    }

        # 2. Add New Custom Command via voice/chat
        custom_create_match = re.search(r'(?:add|create|new)\s+(?:custom\s+)?command\s*:\s*(?:when\s+i\s+say\s+)?[\'"]?([^\'"]+)[\'"]?\s*(?:,|then|do)\s*(.+)', clean)
        if custom_create_match:
            trigger_phrase = custom_create_match.group(1).strip()
            action_phrase = custom_create_match.group(2).strip()
            new_id = f"cmd_{int(datetime.datetime.now().timestamp())}"
            actions = []
            if "mute" in action_phrase:
                actions.append({"type": "system_volume", "action": "mute"})
            if "1080p" in action_phrase or "quality" in action_phrase:
                actions.append({"type": "app_setting", "key": "quality", "value": "high"})
            if "schedule" in action_phrase:
                actions.append({"type": "app_action", "action": "open_batch_scheduler", "interval": 30})
            if "editor" in action_phrase:
                actions.append({"type": "app_action", "action": "switch_tab", "tab": "editor"})
            actions.append({"type": "speak", "message": f"Custom routine '{trigger_phrase}' activated, sir."})

            new_cmd = {
                "id": new_id,
                "name": trigger_phrase.title(),
                "triggers": [trigger_phrase.lower()],
                "description": f"Custom action for: {action_phrase}",
                "enabled": True,
                "actions": actions
            }
            add_or_update_custom_command(new_cmd)
            return {
                "response": f"New custom command '{trigger_phrase}' created and activated, sir. Say '{trigger_phrase}' at any time to run it.",
                "action_type": "create_custom_command",
                "details": new_cmd
            }

        # 3. ViralCut AI Studio Controls
        # 3.1 YouTube Discovery / Find Videos
        if any(kw in clean for kw in ["find videos", "discover videos", "search videos", "find best videos", "gta 6 videos", "podcast videos"]):
            topic = "podcast mindset discipline"
            if "gta" in clean:
                topic = "GTA 6 trailer breakdown hidden details gameplay secrets"
            elif "mystery" in clean or "crime" in clean:
                topic = "unsolved mystery true crime documentary story explained"
            elif "luxury" in clean:
                topic = "billionaire luxury lifestyle supercars mansion tour wealth secrets"
            elif "tech" in clean or "ai" in clean:
                topic = "AI future technology breakthrough explained podcast"
            elif "podcast" in clean:
                topic = "podcast full episode best moments interview life advice"

            return {
                "response": f"{random.choice(JARVIS_AFFIRMATIONS)} Scanning YouTube for top high-retention source videos on '{topic}'.",
                "action_type": "app_discover",
                "directive": {"trigger_action": "run_discovery", "query": topic}
            }

        # 3.2 Switch Application Tab
        tab_map = {
            "dashboard": "dashboard",
            "new project": "upload",
            "upload": "upload",
            "import": "upload",
            "discover": "discover",
            "moments": "clips",
            "clips": "clips",
            "editor": "editor",
            "history": "youtube",
            "published": "youtube",
            "scheduled": "youtube"
        }
        for kw, tab_name in tab_map.items():
            if f"go to {kw}" in clean or f"open {kw}" in clean or f"show {kw}" in clean:
                return {
                    "response": f"Switching to the {tab_name.title()} view, sir.",
                    "action_type": "app_navigate",
                    "directive": {"trigger_action": "switch_tab", "tab": tab_name}
                }

        # 3.3 Schedule All / Batch Scheduler
        if any(kw in clean for kw in ["schedule all", "batch schedule", "open scheduler", "publish all"]):
            return {
                "response": f"{random.choice(JARVIS_AFFIRMATIONS)} Opening the Automated Batch Scheduler. All clips are selected.",
                "action_type": "app_schedule",
                "directive": {"trigger_action": "open_batch_scheduler", "interval": 30}
            }

        # 3.4 Studio Status & Analytics Briefing
        if any(kw in clean for kw in ["studio status", "channel status", "how many clips", "how many videos", "analytics"]):
            tot_vids = analytics.get("total_videos", 0)
            tot_shorts = analytics.get("total_shorts", 0)
            comp_up = analytics.get("completed_uploads", 0)
            pend_up = analytics.get("pending_uploads", 0)
            return {
                "response": f"ViralCut AI Studio report: You have {tot_vids} long videos analyzed, {tot_shorts} viral 9:16 Shorts created, and {comp_up} videos published or scheduled to YouTube ({pend_up} pending in queue). All pipelines ready.",
                "action_type": "app_stats",
                "details": analytics
            }

        # 3.5 Retention & Watch Percentage Advice (40.9% -> 65%+)
        if any(kw in clean for kw in ["retention", "watch rate", "percentage", "swipe away", "swiped away", "stayed to watch", "improve views", "get more views"]):
            return {
                "response": "To increase your 40.9% 'Stayed to Watch' rate past 65%, sir: 1. Ensure our 2.8s Opening Hook Banner is enabled so scrolling viewers stop instantly. 2. Use Hormozi Bold subtitles with active yellow word pop. 3. For talking heads, use Dynamic Smart Crop to follow speaker cuts; for GTA 6 or gameplay, use Blurred Background so no HUD or visual action is cut off.",
                "action_type": "studio_advice"
            }

        # 3.6 Description, Entities & YouTube Info Synthesis
        if any(kw in clean for kw in ["description", "hashtag", "who is in", "what is in", "youtube info", "seo", "reach viewers"]):
            return {
                "response": "To maximize viewer reach on YouTube Shorts, sir: Our engine extracts who and what is in the video (such as Elon Musk, Joe Rogan, or GTA 6), links the original YouTube episode title and channel credit, and structures the PDX High-Engagement Description with key takeaways, comment-driver questions, and entity hashtags. You can click 'AI Enrich Description' in the Shorts Editor to generate this instantly.",
                "action_type": "studio_advice",
                "directive": {"trigger_action": "switch_tab", "tab": "editor"}
            }

        # 4. Windows Hardware & System Controls
        # 4.1 System Vitals & Performance
        if any(kw in clean for kw in ["cpu", "ram", "memory", "battery", "disk", "storage", "performance", "pc status", "diagnostics", "vitals"]):
            vitals = get_system_vitals()
            reply = (
                f"Workstation telemetry, sir: CPU load is at {vitals['cpu']['percent']}%, "
                f"RAM usage is {vitals['memory']['percent']}% ({vitals['memory']['used_gb']} GB of {vitals['memory']['total_gb']} GB). "
                f"System uptime: {vitals['uptime']}. All subroutines nominal."
            )
            return {"response": reply, "action_type": "system_vitals", "details": vitals}

        # 4.2 Volume Controls
        if "mute" in clean:
            res = volume_mute_toggle()
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} {res}", "action_type": "system_mute"}

        vol_match = re.search(r'(?:set\s+)?volume\s+(?:to\s+)?(\d{1,3})%?', clean)
        if vol_match:
            level = int(vol_match.group(1))
            res = set_volume_level(level)
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} {res}", "action_type": "system_volume_set", "details": {"level": level}}

        if any(kw in clean for kw in ["volume up", "louder", "turn up"]):
            res = volume_up(5)
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} {res}", "action_type": "system_volume_up"}

        if any(kw in clean for kw in ["volume down", "quieter", "turn down"]):
            res = volume_down(5)
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} {res}", "action_type": "system_volume_down"}

        # 4.3 Screenshot Capture
        if any(kw in clean for kw in ["screenshot", "capture screen", "snapshot"]):
            scr = take_screenshot()
            msg = "Screenshot captured and logged, sir." if scr.get("success") else scr.get("message")
            return {"response": msg, "action_type": "system_screenshot", "details": scr}

        # 4.4 Lock Workstation / Desktop
        if any(kw in clean for kw in ["lock computer", "lock pc", "lock workstation", "lock screen"]):
            lock_workstation()
            return {"response": "Workstation locked, sir.", "action_type": "system_lock"}

        if any(kw in clean for kw in ["minimize all", "show desktop"]):
            minimize_all_windows()
            return {"response": "Minimizing all windows to reveal desktop, sir.", "action_type": "system_minimize"}

        # 4.5 Launch Applications
        app_match = re.search(r'(?:open|launch|start)\s+([a-zA-Z0-9_\-\.\s]+)', clean)
        if app_match and not any(kw in clean for kw in ["youtube", "google", "weather", "clip", "video"]):
            target = app_match.group(1).strip()
            res = launch_app(target)
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} {res}", "action_type": "system_launch", "details": {"target": target}}

        # 4.6 Kill Processes
        kill_match = re.search(r'(?:kill|close|terminate|end)\s+([a-zA-Z0-9_\-\.]+)', clean)
        if kill_match:
            target = kill_match.group(1).strip()
            res = terminate_process(target)
            return {"response": f"{random.choice(JARVIS_AFFIRMATIONS)} {res}", "action_type": "system_terminate"}

        # 4.7 Web Search & YouTube
        if "youtube" in clean:
            query = re.sub(r'.*?(?:search\s+youtube\s+for|on\s+youtube|play\s+on\s+youtube|youtube)\s*', '', clean).strip()
            if query:
                web_search(query, engine="youtube")
                return {"response": f"Opening YouTube for '{query}', sir.", "action_type": "system_youtube"}

        if any(kw in clean for kw in ["google", "search for", "search web for", "find"]):
            query = re.sub(r'.*?(?:google\s+for|google|search\s+for|search\s+web\s+for|find)\s*', '', clean).strip()
            if query:
                web_search(query, engine="google")
                return {"response": f"Searching Google for '{query}', sir.", "action_type": "system_google"}

        # 4.8 Live Weather & Time
        if "weather" in clean:
            city_m = re.search(r'weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)', clean)
            city = city_m.group(1).strip() if city_m else "auto"
            data = get_live_weather(city)
            return {"response": data["summary"], "action_type": "weather", "details": data}

        if any(kw in clean for kw in ["time is it", "what time", "current time"]):
            return {"response": f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}, sir.", "action_type": "time"}

        # 4.9 Identity & Persona
        if any(kw in clean for kw in ["who are you", "what is your name"]):
            return {
                "response": "I am J.A.R.V.I.S. — Just A Rather Very Intelligent System. I co-pilot your ViralCut AI Studio, manage video rendering pipelines, and command your Windows workstation at your word.",
                "action_type": "identity"
            }

        if any(kw in clean for kw in ["thank you", "thanks", "good job", "awesome"]):
            return {"response": "Always an absolute pleasure, sir. Let me know what to tackle next.", "action_type": "gratitude"}

        if any(kw in clean for kw in ["hello", "hi", "hey", "good morning"]):
            return {"response": f"Good day, sir. J.A.R.V.I.S. is online. Channel PDX and video pipelines are standing by.", "action_type": "greeting"}

        # General Knowledge Fallback
        wiki = get_wikipedia_summary(clean)
        if wiki and "could not locate" not in wiki:
            return {"response": wiki, "action_type": "knowledge"}

        return {
            "response": f"Understood, sir: '{raw}'. Logged in the system and awaiting further instructions.",
            "action_type": "general"
        }
