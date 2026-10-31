"""Root test adapter: Android13 full window focus and explicit fixed-layout test taps.
No product code. Initial XML bounds + Root-reviewed screenshot, fresh context/readiness,
focus and screenshot before each action. Screens are retained, NOT claimed individually
visually reviewed. No action retries or MAVLink writes.
"""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'native'))
from android_operator import AndroidOperator,OperatorError,PACKAGE,ACTIVITY,exclusive,utc
class RootOperator(AndroidOperator):
    def focus(self):
        out=self.command(['shell','dumpsys','activity','activities'],timeout=3)[0].decode(errors='replace')
        lines=[x.strip()for x in out.splitlines()if 'mResumedActivity:'in x or 'topResumedActivity='in x]
        if not any(PACKAGE in x and 'ControlActivity' in x for x in lines):raise OperatorError('NOT_RESUMED')
        windows=self.command(['shell','dumpsys','window'],timeout=3)[0].decode(errors='replace')
        focused=[x.strip()for x in windows.splitlines()if 'mCurrentFocus='in x]
        if len(focused)!=1 or PACKAGE not in focused[0]or 'ControlActivity'not in focused[0]:raise OperatorError('NOT_FOCUSED')
        return lines+focused
    def explicit_tap(self,key):
        desc='control01-'+key
        self.focus();state=self._fresh_state()
        if not self._native_ready(desc,state):raise OperatorError('READINESS_REFUSED:'+key)
        screen=self.screenshot();bounds=self.geometry[desc];l,t,r,b=bounds
        # Root-reviewed initial screenshot + exclusive fixed native layout XML.
        # Fresh state/focus are live, original enabled flags are NOT reused.
        exclusive(screen.parent/'root-test-tap-intent.json',{'atUTC':utc(),'action':key,'bounds':bounds,'state':state,
           'geometrySource':self.geometry_source,'screen':str(screen),'individualVisualReview':False,
           'basis':'ROOT_INITIAL_VISUAL_REVIEW_FIXED_LAYOUT_PLUS_FRESH_STATE_AND_FOCUS','noRetry':True})
        self.command(['shell','input','tap',(l+r)//2,(t+b)//2],timeout=3)
