from datetime import datetime, date
from pathlib import Path
import os, smtplib, json
from email.message import EmailMessage
from fastapi import FastAPI, Request, Depends, Form, HTTPException, UploadFile, File, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from passlib.context import CryptContext
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = 'development-only-change-me'
    database_url: str = 'sqlite:///./lab_assets.db'
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = ''
    technician_email: str = ''
    admin_email: str = ''
    telemetry_api_key: str = 'development-agent-token'
    upload_dir: str = 'uploads'
    class Config: env_file = '.env'; extra = 'ignore'
settings = Settings()
engine = create_engine(settings.database_url, connect_args={'check_same_thread': False} if settings.database_url.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class Base(DeclarativeBase): pass

class User(Base):
    __tablename__='users'
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(120)); email: Mapped[str]=mapped_column(String(200),unique=True); phone: Mapped[str]=mapped_column(String(40),default=''); password_hash: Mapped[str]=mapped_column(String(255)); role: Mapped[str]=mapped_column(String(30)); department: Mapped[str]=mapped_column(String(100),default=''); active: Mapped[bool]=mapped_column(Boolean,default=True); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Lab(Base):
    __tablename__='labs'
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(120)); building: Mapped[str]=mapped_column(String(100),default=''); room_number: Mapped[str]=mapped_column(String(40),default=''); department: Mapped[str]=mapped_column(String(100),default=''); lab_type: Mapped[str]=mapped_column(String(80),default=''); description: Mapped[str]=mapped_column(Text,default=''); active: Mapped[bool]=mapped_column(Boolean,default=True)
class Asset(Base):
    __tablename__='assets'
    id: Mapped[int]=mapped_column(primary_key=True); asset_code: Mapped[str]=mapped_column(String(80),unique=True,index=True); barcode_value: Mapped[str]=mapped_column(String(200),default=''); qr_token: Mapped[str]=mapped_column(String(100),unique=True); name: Mapped[str]=mapped_column(String(160)); category: Mapped[str]=mapped_column(String(80)); manufacturer: Mapped[str]=mapped_column(String(100),default=''); model: Mapped[str]=mapped_column(String(100),default=''); serial_number: Mapped[str]=mapped_column(String(100),default=''); lab_id: Mapped[int]=mapped_column(ForeignKey('labs.id')); status: Mapped[str]=mapped_column(String(50),default='Operational'); purchase_date: Mapped[date|None]=mapped_column(Date,nullable=True); warranty_expiry: Mapped[date|None]=mapped_column(Date,nullable=True); assigned_department: Mapped[str]=mapped_column(String(100),default=''); description: Mapped[str]=mapped_column(Text,default=''); hostname: Mapped[str]=mapped_column(String(100),default=''); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); lab: Mapped[Lab]=relationship()
class MaintenanceReport(Base):
    __tablename__='maintenance_reports'
    id: Mapped[int]=mapped_column(primary_key=True); asset_id: Mapped[int]=mapped_column(ForeignKey('assets.id')); reported_by: Mapped[int]=mapped_column(ForeignKey('users.id')); title: Mapped[str]=mapped_column(String(200)); description: Mapped[str]=mapped_column(Text); severity: Mapped[str]=mapped_column(String(20)); issue_type: Mapped[str]=mapped_column(String(80)); attachment_path: Mapped[str]=mapped_column(String(300),default=''); status: Mapped[str]=mapped_column(String(40),default='Open'); assigned_technician: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); resolved_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True); asset: Mapped[Asset]=relationship(); reporter: Mapped[User]=relationship(foreign_keys=[reported_by]); technician: Mapped[User|None]=relationship(foreign_keys=[assigned_technician])
class MaintenanceUpdate(Base):
    __tablename__='maintenance_updates'
    id: Mapped[int]=mapped_column(primary_key=True); report_id: Mapped[int]=mapped_column(ForeignKey('maintenance_reports.id')); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); message: Mapped[str]=mapped_column(Text); previous_status: Mapped[str]=mapped_column(String(40),default=''); new_status: Mapped[str]=mapped_column(String(40),default=''); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); user: Mapped[User]=relationship()
class Notification(Base):
    __tablename__='notifications'
    id: Mapped[int]=mapped_column(primary_key=True); report_id: Mapped[int]=mapped_column(ForeignKey('maintenance_reports.id')); recipient: Mapped[str]=mapped_column(String(200)); channel: Mapped[str]=mapped_column(String(20)); subject: Mapped[str]=mapped_column(String(250)); status: Mapped[str]=mapped_column(String(30)); sent_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True); error_message: Mapped[str]=mapped_column(Text,default='')
class ComputerTelemetry(Base):
    __tablename__='computer_telemetry'
    id: Mapped[int]=mapped_column(primary_key=True); asset_id: Mapped[int]=mapped_column(ForeignKey('assets.id')); hostname: Mapped[str]=mapped_column(String(100)); timestamp: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); cpu_usage: Mapped[float]=mapped_column(Float); ram_usage: Mapped[float]=mapped_column(Float); disk_usage: Mapped[float]=mapped_column(Float); uptime_seconds: Mapped[int]=mapped_column(Integer); user_session_present: Mapped[bool]=mapped_column(Boolean); idle_seconds: Mapped[int]=mapped_column(Integer); process_count: Mapped[int]=mapped_column(Integer); network_bytes_sent: Mapped[int]=mapped_column(Integer); network_bytes_received: Mapped[int]=mapped_column(Integer); active_process_summary: Mapped[str]=mapped_column(String(500),default='')
class SecurityEvent(Base):
    __tablename__='security_events'
    id: Mapped[int]=mapped_column(primary_key=True); asset_id: Mapped[int]=mapped_column(ForeignKey('assets.id')); timestamp: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); event_type: Mapped[str]=mapped_column(String(100)); severity: Mapped[str]=mapped_column(String(20)); description: Mapped[str]=mapped_column(Text); evidence: Mapped[str]=mapped_column(Text,default=''); status: Mapped[str]=mapped_column(String(30),default='Open'); asset: Mapped[Asset]=relationship()
class AuditLog(Base):
    __tablename__='audit_logs'
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True); action: Mapped[str]=mapped_column(String(120)); entity_type: Mapped[str]=mapped_column(String(80)); entity_id: Mapped[int]=mapped_column(Integer); metadata_json: Mapped[str]=mapped_column(Text,default='{}'); timestamp: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); user: Mapped[User|None]=relationship()

Base.metadata.create_all(engine)
app=FastAPI(title='Campus Lab Asset & Maintenance Portal',version='1.0.0',description='Asset identification, maintenance workflow, telemetry, and reviewable security events.')
app.add_middleware(SessionMiddleware,secret_key=settings.secret_key,same_site='lax',https_only=False)
UPLOAD_DIR=Path(settings.upload_dir); UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
app.mount('/static',StaticFiles(directory='app/static'),name='static'); app.mount('/uploads',StaticFiles(directory=str(UPLOAD_DIR)),name='uploads'); templates=Jinja2Templates(directory='app/templates')
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto')
def db_dep():
    db=SessionLocal()
    try: yield db
    finally: db.close()
def current_user(request: Request, db: Session=Depends(db_dep)):
    uid=request.session.get('user_id')
    user=db.get(User,uid) if uid else None
    if not user or not user.active: raise HTTPException(401,'Please sign in')
    return user
def allowed(*roles):
    def dep(user: User=Depends(current_user)):
        if user.role not in roles: raise HTTPException(403,'Permission denied')
        return user
    return dep
def audit(db,user,action,etype,eid,metadata=None): db.add(AuditLog(user_id=user.id if user else None,action=action,entity_type=etype,entity_id=eid,metadata_json=json.dumps(metadata or {})))
def notify(db,report,lab):
    recipients=list(dict.fromkeys(x for x in [settings.technician_email,settings.admin_email] if x))
    tech=report.technician.email if report.technician else ''
    recipients=list(dict.fromkeys(([tech] if tech else [])+recipients))
    for to in recipients:
        subject=f'[LAB MAINTENANCE] {report.severity} Priority Issue — {report.asset.asset_code}'
        status='Not configured'; err='SMTP_HOST is not configured'
        if settings.smtp_host:
            try:
                msg=EmailMessage(); msg['Subject']=subject; msg['From']=settings.smtp_from or settings.smtp_user; msg['To']=to
                url=f'http://127.0.0.1:8000/maintenance/{report.id}'
                msg.set_content(f'Asset: {report.asset.name} ({report.asset.asset_code})\nLocation: {lab.name}, Room {lab.room_number}\nReported by: {report.reporter.name}\nSeverity: {report.severity}\nIssue: {report.title}\nReport ID: {report.id}\nTimestamp: {report.created_at}\nOpen report: {url}')
                msg.add_alternative(f'<h2>Laboratory maintenance report</h2><p><b>Asset</b>: {report.asset.name} ({report.asset.asset_code})</p><p><b>Location</b>: {lab.name}, Room {lab.room_number}</p><p><b>Reported by</b>: {report.reporter.name}</p><p><b>Severity</b>: {report.severity}</p><p><b>Issue</b>: {report.title}<br>{report.description}</p><p><b>Report ID</b>: {report.id}<br><b>Timestamp</b>: {report.created_at}</p><p><a href="{url}" style="background:#17365d;color:white;padding:12px 18px">Open Maintenance Report</a></p>','html')
                with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as s:
                    s.starttls()
                    if settings.smtp_user: s.login(settings.smtp_user,settings.smtp_password)
                    s.send_message(msg)
                status='Sent'; err=''
            except Exception as e: status='Failed'; err=str(e)[:500]
        db.add(Notification(report_id=report.id,recipient=to,channel='Email',subject=subject,status=status,sent_at=datetime.utcnow() if status=='Sent' else None,error_message=err))
    if not recipients: db.add(Notification(report_id=report.id,recipient='Administrators',channel='Internal',subject='New maintenance report',status='Queued'))

@app.get('/health')
def health(): return {'status':'ok'}
@app.get('/login',response_class=HTMLResponse)
def login_page(request: Request): return templates.TemplateResponse(request,'login.html',{'error':''})
@app.post('/login',response_class=HTMLResponse)
def login(request: Request,email:str=Form(...),password:str=Form(...),db:Session=Depends(db_dep)):
    user=db.query(User).filter(func.lower(User.email)==email.lower()).first()
    if not user or not pwd.verify(password,user.password_hash): return templates.TemplateResponse(request,'login.html',{'error':'Email or password is incorrect'},status_code=401)
    request.session['user_id']=user.id; return RedirectResponse('/',status_code=303)
@app.get('/logout')
def logout(request:Request): request.session.clear(); return RedirectResponse('/login',303)
@app.get('/',response_class=HTMLResponse)
def dashboard(request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    assets=db.query(Asset).count(); open_reports=db.query(MaintenanceReport).filter(MaintenanceReport.status.notin_(['Resolved','Closed'])).count(); critical=db.query(MaintenanceReport).filter(MaintenanceReport.severity=='Critical',MaintenanceReport.status.notin_(['Resolved','Closed'])).count(); faults=db.query(Asset).filter(Asset.status!='Operational').count(); reports=db.query(MaintenanceReport).order_by(MaintenanceReport.created_at.desc()).limit(8).all()
    return templates.TemplateResponse(request,'dashboard.html',{'user':user,'assets':assets,'open_reports':open_reports,'critical':critical,'faults':faults,'reports':reports,'labs':db.query(Lab).count(),'events':db.query(SecurityEvent).count()})
@app.get('/assets',response_class=HTMLResponse)
def assets_page(request:Request,q:str='',user:User=Depends(current_user),db:Session=Depends(db_dep)):
    query=db.query(Asset)
    if q: query=query.join(Lab).filter((Asset.asset_code.contains(q))|(Asset.name.contains(q))|(Asset.serial_number.contains(q))|(Asset.hostname.contains(q))|(Asset.category.contains(q))|(Lab.name.contains(q)))
    return templates.TemplateResponse(request,'assets.html',{'user':user,'assets':query.order_by(Asset.asset_code).all(),'q':q,'labs':db.query(Lab).all()})
@app.get('/asset/{identifier}',response_class=HTMLResponse)
def asset_page(identifier:str,request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    asset=db.query(Asset).filter((Asset.asset_code==identifier)|(Asset.qr_token==identifier)|(Asset.barcode_value==identifier)).first()
    if not asset: raise HTTPException(404,'Asset not found')
    reports=db.query(MaintenanceReport).filter_by(asset_id=asset.id).order_by(MaintenanceReport.created_at.desc()).limit(10).all()
    return templates.TemplateResponse(request,'asset.html',{'user':user,'asset':asset,'reports':reports})
@app.get('/scan',response_class=HTMLResponse)
def scan(request:Request,user:User=Depends(current_user)): return templates.TemplateResponse(request,'scan.html',{'user':user})
@app.get('/maintenance',response_class=HTMLResponse)
def maintenance(request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    query=db.query(MaintenanceReport).order_by(MaintenanceReport.created_at.desc())
    if user.role=='Faculty': query=query.filter(MaintenanceReport.reported_by==user.id)
    if user.role=='Technician': query=query.filter((MaintenanceReport.assigned_technician==user.id)|(MaintenanceReport.assigned_technician==None))
    return templates.TemplateResponse(request,'maintenance.html',{'user':user,'reports':query.all()})
@app.get('/maintenance/{rid}',response_class=HTMLResponse)
def report_page(rid:int,request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    report=db.get(MaintenanceReport,rid)
    if not report: raise HTTPException(404,'Report not found')
    return templates.TemplateResponse(request,'report.html',{'user':user,'report':report,'updates':db.query(MaintenanceUpdate).filter_by(report_id=rid).order_by(MaintenanceUpdate.created_at).all(),'technicians':db.query(User).filter_by(role='Technician',active=True).all()})
@app.post('/maintenance/{rid}/update')
def update_report(rid:int,request:Request,status:str=Form(''),message:str=Form(''),technician_id:int|None=Form(None),user:User=Depends(current_user),db:Session=Depends(db_dep)):
    report=db.get(MaintenanceReport,rid)
    if not report: raise HTTPException(404,'Report not found')
    if user.role not in ('Admin','Technician'): raise HTTPException(403,'Permission denied')
    prev=report.status
    if technician_id and user.role=='Admin': report.assigned_technician=technician_id; report.status='Assigned'
    if status:
        if status not in ['Acknowledged','Assigned','In Progress','Awaiting Parts','Resolved','Closed','Open']: raise HTTPException(422,'Invalid status')
        report.status=status
    if report.status=='Resolved': report.resolved_at=datetime.utcnow(); report.asset.status='Operational'
    elif report.status not in ('Closed',): report.asset.status='Under Repair' if report.status in ('In Progress','Awaiting Parts') else 'Reported Fault'
    report.updated_at=datetime.utcnow(); db.add(MaintenanceUpdate(report_id=rid,user_id=user.id,message=message or ('Assigned technician' if technician_id else f'Status changed to {report.status}'),previous_status=prev,new_status=report.status)); audit(db,user,'Updated maintenance report','MaintenanceReport',rid,{'from':prev,'to':report.status,'technician_id':technician_id}); db.commit()
    return RedirectResponse(f'/maintenance/{rid}',303)
@app.post('/maintenance/{identifier}/create')
def create_report(identifier:str,request:Request,title:str=Form(...),description:str=Form(...),severity:str=Form('Medium'),issue_type:str=Form('Other'),contact:str=Form(''),attachment:UploadFile|None=File(None),user:User=Depends(current_user),db:Session=Depends(db_dep)):
    asset=db.query(Asset).filter((Asset.asset_code==identifier)|(Asset.qr_token==identifier)).first()
    if not asset: raise HTTPException(404,'Asset not found')
    path=''
    if attachment and attachment.filename:
        ext=Path(attachment.filename).suffix.lower()
        if ext not in ('.png','.jpg','.jpeg','.webp'): raise HTTPException(400,'Only image attachments are accepted')
        filename=f'{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}{ext}'; disk_path=UPLOAD_DIR/filename; disk_path.write_bytes(attachment.file.read(5*1024*1024+1))
        if disk_path.stat().st_size>5*1024*1024: disk_path.unlink(missing_ok=True); raise HTTPException(413,'Image attachments must be 5 MB or smaller')
        path=f'/uploads/{filename}'
    technician=db.query(User).filter_by(role='Technician',active=True).first()
    report=MaintenanceReport(asset_id=asset.id,reported_by=user.id,title=title,description=description,severity=severity,issue_type=issue_type,attachment_path=path,assigned_technician=technician.id if technician else None)
    asset.status='Reported Fault'; db.add(report); db.flush(); db.add(MaintenanceUpdate(report_id=report.id,user_id=user.id,message='Issue reported'+(f' · contact {contact}' if contact else ''),previous_status='Operational',new_status='Open')); audit(db,user,'Created maintenance report','MaintenanceReport',report.id,{'asset_code':asset.asset_code,'severity':severity}); notify(db,report,asset.lab); db.commit()
    return RedirectResponse(f'/maintenance/{report.id}',303)
@app.get('/label/{aid}',response_class=HTMLResponse)
def label(aid:int,request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    asset=db.get(Asset,aid)
    if not asset: raise HTTPException(404,'Asset not found')
    return templates.TemplateResponse(request,'label.html',{'user':user,'asset':asset,'qr':f'/api/assets/{asset.id}/qr'})
@app.get('/labs',response_class=HTMLResponse)
def labs(request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)): return templates.TemplateResponse(request,'labs.html',{'user':user,'labs':db.query(Lab).all()})
@app.get('/technicians',response_class=HTMLResponse)
def technicians(request:Request,user:User=Depends(current_user),db:Session=Depends(db_dep)): return templates.TemplateResponse(request,'technicians.html',{'user':user,'techs':db.query(User).filter_by(role='Technician',active=True).all(),'reports':db.query(MaintenanceReport).all()})
@app.get('/security-events',response_class=HTMLResponse)
def events(request:Request,user:User=Depends(allowed('Admin','Technician')),db:Session=Depends(db_dep)): return templates.TemplateResponse(request,'events.html',{'user':user,'events':db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).all()})
@app.get('/audit-logs',response_class=HTMLResponse)
def audits(request:Request,user:User=Depends(allowed('Admin')),db:Session=Depends(db_dep)): return templates.TemplateResponse(request,'audit.html',{'user':user,'logs':db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()})
@app.get('/monitoring',response_class=HTMLResponse)
def monitoring(request:Request,user:User=Depends(allowed('Admin','Technician')),db:Session=Depends(db_dep)): return templates.TemplateResponse(request,'monitoring.html',{'user':user,'assets':db.query(Asset).filter(Asset.category=='Computer').all(),'latest':db.query(ComputerTelemetry).order_by(ComputerTelemetry.timestamp.desc()).all()})

# JSON API
@app.get('/api/assets')
def api_assets(q:str='',user:User=Depends(current_user),db:Session=Depends(db_dep)):
    query=db.query(Asset)
    if q: query=query.filter((Asset.asset_code.contains(q))|(Asset.name.contains(q))|(Asset.hostname.contains(q))|(Asset.serial_number.contains(q)))
    return [{'id':a.id,'asset_code':a.asset_code,'name':a.name,'category':a.category,'lab':a.lab.name,'room':a.lab.room_number,'status':a.status,'hostname':a.hostname} for a in query.all()]
@app.get('/api/assets/{asset_id}/qr')
def qr(asset_id:int,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    import qrcode,io
    from fastapi.responses import StreamingResponse
    a=db.get(Asset,asset_id)
    if not a: raise HTTPException(404,'Asset not found')
    image=qrcode.make(a.qr_token); out=io.BytesIO(); image.save(out,format='PNG'); out.seek(0); return StreamingResponse(out,media_type='image/png')
@app.get('/api/assets/code/{code}')
def api_asset_code(code:str,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    a=db.query(Asset).filter((Asset.asset_code==code)|(Asset.qr_token==code)|(Asset.barcode_value==code)).first()
    if not a: raise HTTPException(404,'Asset not found')
    return {'id':a.id,'asset_code':a.asset_code,'name':a.name,'category':a.category,'lab':a.lab.name,'room':a.lab.room_number,'status':a.status,'model':a.model,'serial_number':a.serial_number,'warranty_expiry':str(a.warranty_expiry or ''),'url':f'/asset/{a.asset_code}'}
@app.get('/api/assets/{asset_id}')
def api_asset(asset_id:int,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    a=db.get(Asset,asset_id)
    if not a: raise HTTPException(404,'Asset not found')
    return {'id':a.id,'asset_code':a.asset_code,'name':a.name,'category':a.category,'status':a.status,'lab':a.lab.name}
@app.get('/api/labs')
def api_labs(user:User=Depends(current_user),db:Session=Depends(db_dep)): return [{'id':x.id,'name':x.name,'building':x.building,'room_number':x.room_number,'department':x.department} for x in db.query(Lab).all()]
@app.post('/api/assets')
def api_create_asset(payload:dict,user:User=Depends(allowed('Admin')),db:Session=Depends(db_dep)):
    from uuid import uuid4
    required=('asset_code','name','category','lab_id')
    if any(k not in payload for k in required): raise HTTPException(422,'asset_code, name, category, and lab_id are required')
    a=Asset(asset_code=payload['asset_code'],barcode_value=payload.get('barcode_value',''),qr_token=payload.get('qr_token',uuid4().hex),name=payload['name'],category=payload['category'],lab_id=payload['lab_id'],manufacturer=payload.get('manufacturer',''),model=payload.get('model',''),serial_number=payload.get('serial_number',''),hostname=payload.get('hostname',''),description=payload.get('description',''))
    db.add(a); db.flush(); audit(db,user,'Created asset','Asset',a.id); db.commit(); return {'id':a.id,'asset_code':a.asset_code}
@app.put('/api/assets/{aid}')
def api_update_asset(aid:int,payload:dict,user:User=Depends(allowed('Admin')),db:Session=Depends(db_dep)):
    a=db.get(Asset,aid)
    if not a: raise HTTPException(404,'Asset not found')
    for key in ('name','category','manufacturer','model','serial_number','lab_id','status','description','hostname'):
        if key in payload: setattr(a,key,payload[key])
    audit(db,user,'Updated asset','Asset',aid,payload); db.commit(); return {'id':a.id,'status':a.status}
@app.get('/api/maintenance')
def api_maintenance(user:User=Depends(current_user),db:Session=Depends(db_dep)):
    q=db.query(MaintenanceReport)
    if user.role=='Faculty': q=q.filter_by(reported_by=user.id)
    return [{'id':r.id,'asset_code':r.asset.asset_code,'title':r.title,'severity':r.severity,'status':r.status,'created_at':r.created_at.isoformat()} for r in q.order_by(MaintenanceReport.created_at.desc()).all()]
@app.get('/api/maintenance/{rid}')
def api_report(rid:int,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    r=db.get(MaintenanceReport,rid)
    if not r: raise HTTPException(404,'Report not found')
    if user.role=='Faculty' and r.reported_by!=user.id: raise HTTPException(403,'Permission denied')
    return {'id':r.id,'asset_code':r.asset.asset_code,'title':r.title,'description':r.description,'severity':r.severity,'status':r.status,'reported_by':r.reporter.name,'assigned_technician':r.technician.name if r.technician else None,'created_at':r.created_at.isoformat()}
@app.post('/api/maintenance')
def api_report_create(payload:dict,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    a=db.get(Asset,payload.get('asset_id'))
    if not a: raise HTTPException(404,'Asset not found')
    r=MaintenanceReport(asset_id=a.id,reported_by=user.id,title=payload.get('title','Issue reported'),description=payload.get('description',''),severity=payload.get('severity','Medium'),issue_type=payload.get('issue_type','Other')); a.status='Reported Fault'; db.add(r); db.flush(); db.add(MaintenanceUpdate(report_id=r.id,user_id=user.id,message='Issue reported',previous_status='Operational',new_status='Open')); audit(db,user,'Created maintenance report','MaintenanceReport',r.id); notify(db,r,a.lab); db.commit(); return {'id':r.id,'status':r.status}
@app.patch('/api/maintenance/{rid}/status')
def api_status(rid:int,payload:dict,user:User=Depends(allowed('Admin','Technician')),db:Session=Depends(db_dep)):
    r=db.get(MaintenanceReport,rid)
    if not r: raise HTTPException(404,'Report not found')
    prev=r.status; status=payload.get('status')
    if status not in ['Open','Acknowledged','Assigned','In Progress','Awaiting Parts','Resolved','Closed']: raise HTTPException(422,'Invalid status')
    r.status=status
    if status=='Resolved': r.resolved_at=datetime.utcnow(); r.asset.status='Operational'
    elif status in ('In Progress','Awaiting Parts'): r.asset.status='Under Repair'
    db.add(MaintenanceUpdate(report_id=rid,user_id=user.id,message=payload.get('message',f'Status changed to {status}'),previous_status=prev,new_status=status)); audit(db,user,'Changed report status','MaintenanceReport',rid,{'from':prev,'to':status}); db.commit(); return {'id':rid,'status':status}
@app.post('/api/maintenance/{rid}/updates')
def api_update(rid:int,payload:dict,user:User=Depends(current_user),db:Session=Depends(db_dep)):
    r=db.get(MaintenanceReport,rid)
    if not r: raise HTTPException(404,'Report not found')
    db.add(MaintenanceUpdate(report_id=rid,user_id=user.id,message=payload.get('message',''),previous_status=r.status,new_status=r.status)); audit(db,user,'Added maintenance note','MaintenanceReport',rid); db.commit(); return {'ok':True}
@app.get('/api/security-events')
def api_events(user:User=Depends(allowed('Admin','Technician')),db:Session=Depends(db_dep)): return [{'id':e.id,'asset_code':e.asset.asset_code,'timestamp':e.timestamp.isoformat(),'event_type':e.event_type,'severity':e.severity,'description':e.description,'status':e.status} for e in db.query(SecurityEvent).all()]
@app.patch('/api/security-events/{eid}')
def api_event_update(eid:int,payload:dict,user:User=Depends(allowed('Admin','Technician')),db:Session=Depends(db_dep)):
    e=db.get(SecurityEvent,eid)
    if not e: raise HTTPException(404,'Event not found')
    if payload.get('status') not in ['Open','Under Review','False Positive','Confirmed','Resolved']: raise HTTPException(422,'Invalid review status')
    e.status=payload['status']; audit(db,user,'Reviewed security event','SecurityEvent',eid,{'status':e.status}); db.commit(); return {'id':eid,'status':e.status}
@app.post('/api/telemetry')
def telemetry(payload:dict,authorization:str=Header(default=''),db:Session=Depends(db_dep)):
    if authorization.removeprefix('Bearer ')!=settings.telemetry_api_key: raise HTTPException(401,'Invalid telemetry token')
    a=db.query(Asset).filter(Asset.asset_code==payload.get('asset_code')).first()
    if not a or a.category!='Computer': raise HTTPException(404,'Computer asset not found')
    sample=ComputerTelemetry(asset_id=a.id,hostname=payload.get('hostname',a.hostname),cpu_usage=payload.get('cpu_usage',0),ram_usage=payload.get('ram_usage',0),disk_usage=payload.get('disk_usage',0),uptime_seconds=payload.get('uptime_seconds',0),user_session_present=payload.get('user_session_present',False),idle_seconds=payload.get('idle_seconds',0),process_count=payload.get('process_count',0),network_bytes_sent=payload.get('network_bytes_sent',0),network_bytes_received=payload.get('network_bytes_received',0),active_process_summary=payload.get('active_process_summary','')[:500]); db.add(sample)
    if sample.cpu_usage>=95:
        db.add(SecurityEvent(asset_id=a.id,event_type='Sustained high CPU',severity='Medium',description='CPU utilization exceeded the configured threshold in a telemetry sample.',evidence=f'{sample.cpu_usage}% CPU'))
    prohibited={'anydesk','teamviewer','xmrig','minerd','ultraviewer'}
    hits=[x.strip().lower() for x in sample.active_process_summary.split(',') if x.strip().lower() in prohibited]
    if hits: db.add(SecurityEvent(asset_id=a.id,event_type='Potential Security Event',severity='High',description='Configured process name matched a review rule. Staff review is required.',evidence=', '.join(hits)))
    db.commit(); return {'ok':True}
@app.post('/api/heartbeat')
def heartbeat(payload:dict,authorization:str=Header(default=''),db:Session=Depends(db_dep)):
    return telemetry(payload,authorization,db)
