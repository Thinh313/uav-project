"""Root-only explicit native UI actions with fresh measured native geometry.
No bridge evaluation, CDP, raw flight writes, automatic action retries, or physical HID claim.
"""
import json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from .cockpitio14_android_operator import AndroidOperator,OperatorError,PACKAGE,exclusive,utc
class RootOperator(AndroidOperator):
    def focus(self):
        out=self.command(['shell','dumpsys','activity','activities'],timeout=3)[0].decode(errors='replace')
        lines=[x.strip()for x in out.splitlines()if 'mResumedActivity:'in x or 'topResumedActivity='in x]
        if not any(PACKAGE in x and 'CockpitActivity' in x for x in lines):raise OperatorError('NOT_RESUMED')
        windows=self.command(['shell','dumpsys','window'],timeout=3)[0].decode(errors='replace')
        focused=[x.strip()for x in windows.splitlines()if 'mCurrentFocus='in x]
        if len(focused)!=1 or PACKAGE not in focused[0]or 'CockpitActivity'not in focused[0]:raise OperatorError('NOT_FOCUSED')
        return lines+focused
    def layout(self):
        out,_,_,d=self.command(['shell','run-as',PACKAGE,'cat','files/native-controls-layout.json'],timeout=3)
        value=json.loads(out);exclusive(d/'layout.json',value);return value
    def explicit_tap(self,key):
        desc='control01-'+key;self.focus();state=self._fresh_state()
        if not self._native_ready(desc,state):raise OperatorError('READINESS_REFUSED:'+key)
        deadline=time.monotonic()+1.5
        while True:
            layout=self.layout();node=layout['buttons'][desc]
            if node['enabled']and node['visible']:break
            if time.monotonic()>deadline:raise OperatorError('MEASURED_UI_NOT_ACTIONABLE:'+desc)
            time.sleep(.05)
        state=self._fresh_state()
        if not self._native_ready(desc,state):raise OperatorError('READINESS_CHANGED:'+key)
        if key=='confirm-home':
            home=layout['overlays']['control01-displayed-home']
            if not home['visible']or layout.get('displayedHomeSHA256')!=state['flight']['homeHash']or layout.get('displayedHomeRun')!=self.run:raise OperatorError('ACTUAL_NATIVE_HOME_TEXT_NOT_SHOWN_CURRENT')
        l,t,r,b=node['bounds']
        if r-l<48 or b-t<48:raise OperatorError('TARGET_UNDER48:'+desc)
        screen=self.screenshot();exclusive(screen.parent/'root-test-tap-intent.json',{'atUTC':utc(),'action':key,'bounds':[l,t,r,b],'state':state,'nativeMeasuredLayout':layout,'screen':str(screen),'individualVisualReview':False,'basis':'ROOT_INITIAL_VISUAL_REVIEW_AND_FRESH_NATIVE_MEASURED_LAYOUT_STATE_FOCUS','noRetry':True})
        self.command(['shell','input','tap',(l+r)//2,(t+b)//2],timeout=3)
    def explicit_connect(self):
        self.focus();deadline=time.monotonic()+1.5
        while True:
            layout=self.layout();node=layout['buttons']['control01-connect']
            if node['enabled']and node['visible']and layout['view']=='preflight':break
            if time.monotonic()>deadline:raise OperatorError('CONNECT_UI_REFUSED')
            time.sleep(.05)
        l,t,r,b=node['bounds'];screen=self.screenshot();exclusive(screen.parent/'connect-intent.json',{'layout':layout,'noRetry':True,'source':'EXPLICIT_ROOT_TEST_TOUCH_NATIVE_BUTTON','screen':str(screen)})
        self.command(['shell','input','tap',(l+r)//2,(t+b)//2],timeout=3)
    def start_stick_hold(self,description,horizontal,up,duration_ms):
        layout=self.layout();n=layout['sticks'][description]
        if layout['view']!='fly'or not n['visible']:raise OperatorError('STICK_NOT_IN_FLY')
        self.geometry[description]=tuple(n['bounds']);self.geometry_source='CURRENT_NATIVE_MEASURED_LAYOUT'
        return super().start_stick_hold(description,horizontal,up,duration_ms)
    def navigate(self,target,description):
        self.focus();screen=self.screenshot()
        if target not in self.nav_geometry:raise OperatorError('INITIAL_REVIEWED_NAV_GEOMETRY_REQUIRED')
        l,t,r,b=self.nav_geometry[target]
        exclusive(screen.parent/'navigation-intent.json',{'target':target,'description':description,'bounds':[l,t,r,b],'noRetry':True,'basis':'ROOT_REVIEWED_STABLE_UI_GEOMETRY_WITH_FRESH_SCREEN_FOCUS','screen':str(screen)})
        self.command(['shell','input','tap',(l+r)//2,(t+b)//2],timeout=3)
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            layout=self.layout()
            if layout['view']==target and layout.get('presentedView',target)==target and layout.get('viewReady',True):return layout
            time.sleep(.1)
        raise OperatorError('NAVIGATION_NOT_OBSERVED:'+target)
    def navigate_fly(self):return self.navigate('fly','Bay')
    def navigate_review(self):return self.navigate('review','Hồ sơ')
