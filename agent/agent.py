"""Privacy-conscious Windows device health agent. Sends technical metrics only."""
import time, socket, platform
from datetime import datetime
import psutil, requests
from config import SERVER_URL, ASSET_CODE, AGENT_TOKEN, HEARTBEAT_SECONDS

def idle_seconds():
    if platform.system()!='Windows': return 0
    try:
        import ctypes
        from ctypes import wintypes
        class LASTINPUTINFO(ctypes.Structure):
            _fields_=[('cbSize',wintypes.UINT),('dwTime',wintypes.DWORD)]
        info=LASTINPUTINFO(); info.cbSize=ctypes.sizeof(info)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            tick=ctypes.windll.kernel32.GetTickCount(); return max(0,int((tick-info.dwTime)/1000))
    except Exception: pass
    return 0

def collect():
    net=psutil.net_io_counters(); boot=psutil.boot_time()
    # Process names only, bounded to a short list; no command lines, files, or user content.
    names=[]
    for p in psutil.process_iter(['name']):
        try:
            n=p.info.get('name')
            if n and n.lower() not in names: names.append(n.lower())
        except (psutil.NoSuchProcess,psutil.AccessDenied): pass
        if len(names)>=30: break
    return {'asset_code':ASSET_CODE,'hostname':socket.gethostname(),'cpu_usage':psutil.cpu_percent(interval=1),'ram_usage':psutil.virtual_memory().percent,'disk_usage':psutil.disk_usage('C:\\' if platform.system()=='Windows' else '/').percent,'uptime_seconds':int(time.time()-boot),'user_session_present':bool(psutil.users()),'idle_seconds':idle_seconds(),'process_count':len(psutil.pids()),'network_bytes_sent':net.bytes_sent,'network_bytes_received':net.bytes_recv,'active_process_summary':', '.join(names)}

def main():
    if not ASSET_CODE or not AGENT_TOKEN: raise SystemExit('Set LAB_ASSET_CODE and LAB_AGENT_TOKEN environment variables.')
    url=SERVER_URL.rstrip('/')+'/api/telemetry'
    while True:
        try:
            r=requests.post(url,json=collect(),headers={'Authorization':'Bearer '+AGENT_TOKEN},timeout=15); r.raise_for_status(); print(datetime.now().isoformat(timespec='seconds'),'heartbeat accepted')
        except Exception as exc: print(datetime.now().isoformat(timespec='seconds'),'heartbeat failed:',exc)
        time.sleep(max(15,HEARTBEAT_SECONDS))
if __name__=='__main__': main()
