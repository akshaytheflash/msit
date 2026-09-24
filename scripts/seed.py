from pathlib import Path
import sys, secrets
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import SessionLocal, User, Lab, Asset, MaintenanceReport, MaintenanceUpdate, ComputerTelemetry, SecurityEvent, AuditLog, pwd

db=SessionLocal()
if db.query(User).count():
    print('Database already contains users; seed skipped.'); raise SystemExit(0)
people=[('Portal Administrator','admin@college.example','Admin','Administration'),('Dr. Aditi Sharma','aditi.sharma@college.example','Faculty','Computer Science'),('Mr. Rohan Mehta','rohan.mehta@college.example','Lab Assistant','Computer Science'),('Sanjay Kumar','sanjay.kumar@college.example','Technician','IT Services'),('Priya Nair','priya.nair@college.example','Technician','Electrical Services'),('Dr. Neha Verma','neha.verma@college.example','Faculty','Applied Sciences')]
users=[]
for name,email,role,dept in people:
    u=User(name=name,email=email,role=role,department=dept,phone=''); u.password_hash=pwd.hash('ChangeMe123!'); db.add(u); users.append(u)
db.flush()
lab_specs=[('Programming Laboratory','Academic Block','Room not configured','Computer Science','Computing'),('Computer Networks Laboratory','Academic Block','Room not configured','Computer Science','Networking'),('Electronics Laboratory','Engineering Block','Room not configured','Electronics','Electronics'),('Physics Laboratory','Science Block','Room not configured','Applied Sciences','Physics'),('Chemistry Laboratory','Science Block','Room not configured','Applied Sciences','Chemistry'),('Electrical Machines Laboratory','Engineering Block','Room not configured','Electrical Engineering','Electrical'),('Innovation Laboratory','Academic Block','Room not configured','Engineering','Project'),('Mechanical Workshop','Engineering Block','Room not configured','Mechanical Engineering','Workshop')]
labs=[]
for name,building,room,dept,typ in lab_specs:
    l=Lab(name=name,building=building,room_number=room,department=dept,lab_type=typ,description=f'{typ} teaching and practical laboratory.'); db.add(l); labs.append(l)
db.flush()
categories=['Computer','Monitor','Keyboard','Mouse','Projector','Network Equipment','Laboratory Equipment','Electrical Equipment','Furniture','Other']
assets=[]
for i in range(40):
    lab=labs[i%len(labs)]; computer=i<20
    code=f'COMP-{105+i//15}-{i+1:03d}' if computer else f'ASSET-{i+1:04d}'
    category='Computer' if computer else categories[(i-20)%9+1]
    name=(f'Laboratory Computer {i+1:02d}' if computer else f'{category} Unit {i-19:02d}')
    a=Asset(asset_code=code,barcode_value=code,qr_token=secrets.token_urlsafe(18),name=name,category=category,manufacturer='Campus equipment pool',model='Standard configuration' if computer else 'Institutional issue',serial_number=f'DEMO-{i+1:05d}',lab_id=lab.id,status='Operational',assigned_department=lab.department,hostname=f'{lab.name[:4].upper().replace(" ","")}-PC-{i+1:03d}' if computer else '',description='Demonstration inventory item; update details for local deployment.')
    db.add(a); assets.append(a)
db.flush()
# A small set of demo work orders illustrates active and resolved history.
for idx,(status,severity,title) in enumerate([('Open','High','System shuts down unexpectedly'),('In Progress','Medium','Display intermittently flickers'),('Resolved','Low','Keyboard keys not responding'),('Awaiting Parts','Critical','Projector does not power on'),('Resolved','Medium','Network connection drops')]):
    asset=assets[idx*5]; tech=users[3+(idx%2)]; report=MaintenanceReport(asset_id=asset.id,reported_by=users[1 if idx%2==0 else 5].id,title=title,description='Demonstration incident. Confirm the symptoms with the lab user and record diagnostic findings.',severity=severity,issue_type=['Hardware','Hardware','Peripheral','Electrical','Network'][idx],status=status,assigned_technician=tech.id)
    if status=='Resolved': report.resolved_at=report.created_at
    if status in ('Open','In Progress','Awaiting Parts'): asset.status='Under Repair' if status!='Open' else 'Reported Fault'
    db.add(report); db.flush(); db.add(MaintenanceUpdate(report_id=report.id,user_id=report.reported_by,message='Demonstration historical report',previous_status='Operational',new_status='Open'))
    if status!='Open': db.add(MaintenanceUpdate(report_id=report.id,user_id=tech.id,message='Demonstration status update',previous_status='Open',new_status=status))
for idx,a in enumerate(assets[:8]):
    db.add(ComputerTelemetry(asset_id=a.id,hostname=a.hostname,cpu_usage=8.2+idx*3,ram_usage=34+idx*2,disk_usage=46+idx,uptime_seconds=86400*(idx+1),user_session_present=idx%2==0,idle_seconds=1200*idx,process_count=82+idx*3,network_bytes_sent=1900000+idx*20000,network_bytes_received=7200000+idx*15000,active_process_summary='explorer.exe, chrome.exe, svchost.exe'))
for idx,a in enumerate(assets[:3]): db.add(SecurityEvent(asset_id=a.id,event_type=['Agent Offline','High CPU utilization','Unexpected software review rule'][idx],severity=['Low','Medium','Medium'][idx],description='Demonstration event for review workflow. This rule output does not identify or accuse a person.',evidence='Seeded example data',status='Open'))
db.commit(); print(f'Seeded {len(labs)} labs, {len(assets)} assets, 6 accounts, work orders, telemetry, and review events.')
print('Demo sign-in for every seeded user: password ChangeMe123!')
