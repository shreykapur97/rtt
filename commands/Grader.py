#! python3
import os, csv, json, shutil, tempfile, datetime, difflib
import Rhino, rhinoscriptsyntax as rs
import Eto.Forms as ef, Eto.Drawing as ed
import Grasshopper as GH

root=rs.BrowseForFolder(message="Submissions folder")
rel=lambda p:os.path.relpath(p,root).replace('\\','/')
stem=lambda p:os.path.splitext(os.path.basename(p))[0]
mp=os.path.join(root or '','meta.json')
GD=GH.Kernel.GH_Document

def scan():
    auto,r3,rg=[],[],[]
    for d,_,fs in os.walk(root):
        m=[rel(os.path.join(d,f)) for f in fs if f.lower().endswith('.3dm')]
        g=[rel(os.path.join(d,f)) for f in fs if f.lower().endswith(('.gh','.ghx'))]
        pre='' if d==root else rel(d)
        if len(m)==1 and len(g)==1:
            auto.append({'name':pre or stem(m[0]),'3dm':m[0],'gh':g[0],'how':'auto'})
        else:
            gs={stem(x).lower():x for x in g}
            for x in m:
                y=gs.pop(stem(x).lower(),None)
                if y: auto.append({'name':(pre+'/' if pre else '')+stem(x),'3dm':x,'gh':y,'how':'auto'})
                else: r3.append(x)
            rg+=list(gs.values())
    return auto,r3,rg

def suggest():
    sc=sorted(((difflib.SequenceMatcher(None,os.path.splitext(m)[0].lower(),os.path.splitext(g)[0].lower()).ratio(),m,g) for m in R3 for g in RG),reverse=True)
    used,out=set(),[]
    for r,m,g in sc:
        if r<0.5: break
        if m in used or g in used: continue
        used|={m,g}; out.append((m,g,r))
    return out

def save_meta():
    meta['version']=1
    meta['updated']=datetime.datetime.now().isoformat(timespec='seconds')
    meta['pairs']={'before':{'matched':auto,'rogue_3dm':r3,'rogue_gh':rg},'after':Q}
    with open(mp,'w',encoding='utf-8') as f: json.dump(meta,f,indent=2)
    with open(os.path.join(root,'grades.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['student','grade','notes','3dm','gh','how'])
        for p in Q:
            s=meta['students'].get(p['name'],{})
            w.writerow([p['name'],s.get('grade',''),s.get('notes',''),p['3dm'] or '',p['gh'] or '',p['how']])

def stack(items,horiz=False):
    s=ef.StackLayout(); s.Spacing=6
    if horiz: s.Orientation=ef.Orientation.Horizontal
    else: s.HorizontalContentAlignment=ef.HorizontalAlignment.Stretch
    for c in items: s.Items.Add(ef.StackLayoutItem(c))
    return s

def btn(t,fn):
    b=ef.Button(); b.Text=t; b.Click+=lambda s,e:fn(); return b

def lab(t):
    l=ef.Label(); l.Text=t; return l

def listbox(w,h):
    l=ef.ListBox(); l.Size=ed.Size(w,h); return l

def card(t,c):
    g=ef.GroupBox(); g.Text=t; g.Padding=ed.Padding(6); g.Content=c; return g

def bar(left,right):
    t=ef.TableLayout(); t.Spacing=ed.Size(6,0); r=ef.TableRow()
    for c in left: r.Cells.Add(ef.TableCell(c))
    r.Cells.Add(ef.TableCell(None,True))
    for c in right: r.Cells.Add(ef.TableCell(c))
    t.Rows.Add(r); return t

if root:
    auto,r3,rg=scan()
    all3=[p['3dm'] for p in auto]+r3; allg=[p['gh'] for p in auto]+rg
    meta=json.load(open(mp,encoding='utf-8')) if os.path.exists(mp) else {}
    meta.setdefault('students',{})
    A=[p for p in meta['pairs']['after'] if p['how'] in ('auto','manual','suggested') and p['3dm'] in all3 and p['gh'] in allg] if 'pairs' in meta else list(auto)
    R3=[x for x in all3 if x not in {p['3dm'] for p in A}]
    RG=[x for x in allg if x not in {p['gh'] for p in A}]
    Q=[]; st={'go':False,'i':0,'doc':None,'S':[]}

    lbM=listbox(640,180); lbS=listbox(640,100); lb3=listbox(315,150); lbG=listbox(315,150)

    def refresh():
        A.sort(key=lambda p:p['name'].lower()); R3.sort(); RG.sort(); st['S']=suggest()
        for lb,items in ((lbM,['{}:  {} ↔ {}  [{}]'.format(p['name'],p['3dm'],p['gh'],p['how']) for p in A]),
                         (lbS,['{} ↔ {}  ({:.0%})'.format(m,g,r) for m,g,r in st['S']]),(lb3,R3),(lbG,RG)):
            lb.Items.Clear()
            for t in items: lb.Items.Add(t)

    def onS(s,e):
        if lbS.SelectedIndex>=0: lb3.SelectedIndex=-1; lbG.SelectedIndex=-1

    def onR(s,e):
        if s.SelectedIndex>=0: lbS.SelectedIndex=-1

    lbS.SelectedIndexChanged+=onS; lb3.SelectedIndexChanged+=onR; lbG.SelectedIndexChanged+=onR

    def link():
        k,i,j=lbS.SelectedIndex,lb3.SelectedIndex,lbG.SelectedIndex
        if k>=0: m,g,_=st['S'][k]; how='suggested'
        elif i>=0 and j>=0: m,g=R3[i],RG[j]; how='manual'
        else: return
        R3.remove(m); RG.remove(g)
        A.append({'name':os.path.splitext(m)[0],'3dm':m,'gh':g,'how':how}); refresh()

    def unlink():
        k=lbM.SelectedIndex
        if k>=0: p=A.pop(k); R3.append(p['3dm']); RG.append(p['gh']); refresh()

    def confirm():
        Q.extend(A)
        Q.extend({'name':os.path.splitext(m)[0],'3dm':m,'gh':None,'how':'rhino-only'} for m in R3)
        Q.extend({'name':os.path.splitext(g)[0],'3dm':None,'gh':g,'how':'gh-only'} for g in RG)
        Q.sort(key=lambda p:p['name'].lower())
        save_meta(); st['go']=True; dlg.Close()

    dlg=ef.Dialog(); dlg.Title="Match submissions"; dlg.Resizable=True; dlg.Padding=ed.Padding(10)
    dlg.Content=stack([
        card("Automatic links",lbM),
        card("Suggestions",lbS),
        card("Manual linking",stack([stack([lab("Rhino (.3dm)"),lb3]),stack([lab("Grasshopper (.gh)"),lbG])],True)),
        bar([btn("Link",link),btn("Unlink",unlink)],[btn("Confirm && Grade",confirm),btn("Exit",dlg.Close)])])
    refresh(); dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if st['go'] and Q:
        tmp=tempfile.mkdtemp(); busy=[False]; orig=GD.EnableSolutions

        cur=lambda:meta['students'].setdefault(Q[st['i']]['name'],{})

        def tag(k):
            p=Q[k]; s=meta['students'].get(p['name'],{})
            return '{}{}. {}{}'.format('✓ ' if s.get('grade') else '',k+1,p['name'],' ('+p['how']+')' if p['how'] in ('rhino-only','gh-only') else '')

        def fill():
            busy[0]=True; dd.Items.Clear()
            for k in range(len(Q)): dd.Items.Add(tag(k))
            dd.SelectedIndex=st['i']; busy[0]=False

        def setlock(on):
            GD.EnableSolutions=on
            tb.Text="Lock solver" if on else "Unlock solver"
            if on and st['doc']: st['doc'].NewSolution(False)

        def toggle():
            on=not GD.EnableSolutions; cur()['unlocked']=on; setlock(on); save()

        def save():
            s=cur(); s['grade']=gr.Text; s['notes']=nt.Text; save_meta()

        def load():
            p=Q[st['i']]; srv=GH.Instances.DocumentServer
            GD.EnableSolutions=False
            if st['doc']:
                st['doc'].Enabled=False; srv.RemoveDocument(st['doc']); st['doc'].Dispose(); st['doc']=None
            d=os.path.join(tmp,str(st['i'])); os.makedirs(d,exist_ok=True)
            Rhino.RhinoDoc.ActiveDoc.Modified=False
            if p['3dm']: Rhino.RhinoApp.RunScript('_-Open "{}"'.format(shutil.copy(os.path.join(root,p['3dm']),d)),False)
            else: Rhino.RhinoApp.RunScript('_-New _None',False)
            if p['gh']:
                io=GH.Kernel.GH_DocumentIO(); io.Open(shutil.copy(os.path.join(root,p['gh']),d))
                doc=io.Document; srv.AddDocument(doc)
                GH.Instances.ActiveCanvas.Document=doc
                doc.Enabled=True; st['doc']=doc
            else: GH.Instances.ActiveCanvas.Document=None
            s=meta['students'].get(p['name'],{})
            gr.Text=s.get('grade',''); nt.Text=s.get('notes','')
            setlock(bool(s.get('unlocked'))); fill()

        def jump(k):
            if busy[0] or k<0 or k==st['i']: return
            save(); st['i']=k; load()

        nav=lambda k:jump(max(0,min(len(Q)-1,st['i']+k)))

        def close(s,e):
            save(); GD.EnableSolutions=orig

        ghp=Rhino.RhinoApp.GetPlugInObject("Grasshopper"); ghp.LoadEditor(); ghp.ShowEditor()
        f=ef.Form(); f.Title="Grader"; f.Topmost=True; f.Owner=Rhino.UI.RhinoEtoApp.MainWindow
        f.ClientSize=ed.Size(300,270); f.MinimumSize=ed.Size(300,270); f.Padding=ed.Padding(8)
        dd=ef.DropDown(); dd.SelectedIndexChanged+=lambda s,e:jump(dd.SelectedIndex)
        gr=ef.TextBox(); gr.PlaceholderText="Grade"
        nt=ef.TextArea(); nt.Size=ed.Size(260,90)
        tb=btn("Unlock solver",toggle)
        f.Content=stack([dd,gr,nt,tb,stack([btn("< Prev",lambda:nav(-1)),btn("Next >",lambda:nav(1))],True)])
        f.Closed+=close
        f.Show(); load()
