package vn.rtr.aeris.control01;
import android.content.Context;
import android.graphics.*;
import android.os.SystemClock;
import android.view.*;
import java.util.*;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import vn.rtr.aeris.beta01runtime.Values;

/** Actual MotionEvent producer. Sampling is UI-thread state observation, never sender retiming. */
public final class TouchControls {
    public interface Sink {void motion(Map<String,Object> raw);void released();void invalid(String reason);}
    public final String source="touch-"+UUID.randomUUID();private final Sink sink;
    public final Stick left,right;private final double[]axes=new double[4];private final boolean[]held=new boolean[2];
    private long inputSequence,lastMotionUptime;private int lastAction=-1;private boolean releasePending;
    public TouchControls(Context context,Sink sink){this.sink=sink;left=new Stick(context,0,"control01-left-stick","YAW  /  THROTTLE");right=new Stick(context,1,"control01-right-stick","ROLL  /  PITCH FORWARD");}
    public ControlAuthority.Input sample(RunLifecycle.Context context,String provenance){long uptime=SystemClock.uptimeMillis()*1000000L;long elapsed=SystemClock.elapsedRealtimeNanos();boolean release=releasePending;releasePending=false;return new ControlAuthority.Input(context,source,"ANDROID_UPTIME_NS_SAMPLER",provenance,++inputSequence,uptime,elapsed,lastMotionUptime,axes, (held[0]?1:0)+(held[1]?1:0),lastAction,release);}
    private void clear(){Arrays.fill(axes,0);Arrays.fill(held,false);left.pointer=-1;right.pointer=-1;left.invalidate();right.invalidate();}
    public final class Stick extends View {
        private final int side;private final String label;private final Paint paint=new Paint(3);private int pointer=-1;
        Stick(Context c,int side,String desc,String label){super(c);this.side=side;this.label=label;setContentDescription(desc);setFocusable(true);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);}
        private float radius(){return Math.max(24,Math.min(getWidth(),getHeight())*.32f);}
        @Override protected void onDraw(Canvas c){super.onDraw(c);float x=getWidth()/2f,y=getHeight()/2f,r=radius();paint.setStyle(Paint.Style.FILL);paint.setColor(0xff19232c);c.drawRoundRect(8,8,getWidth()-8,getHeight()-8,18,18,paint);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(2);paint.setColor(0xff73808a);c.drawCircle(x,y,r,paint);c.drawLine(x-r,y,x+r,y,paint);c.drawLine(x,y-r,x,y+r,paint);paint.setStyle(Paint.Style.FILL);paint.setColor(0xffe8c547);float xx=side==0?(float)axes[3]:(float)axes[0],yy=side==0?(float)axes[2]:(float)axes[1];c.drawCircle(x+xx*r,y-yy*r,r*.22f,paint);paint.setColor(Color.WHITE);paint.setTextSize(16);paint.setTextAlign(Paint.Align.CENTER);c.drawText(label,x,28,paint);paint.setTextSize(14);c.drawText(side==0?"Yaw clockwise +  •  Climb +":"Right +  •  Forward +",x,getHeight()-20,paint);}
        @Override public boolean onTouchEvent(MotionEvent event){
            try {
                if((event.getSource()&InputDevice.SOURCE_TOUCHSCREEN)!=InputDevice.SOURCE_TOUCHSCREEN)throw new IllegalArgumentException("TOUCHSCREEN_SOURCE_REQUIRED_NOT_GENERIC_HID");
                if(event.getHistorySize()>32||event.getPointerCount()>2)throw new IllegalArgumentException("MOTION_HISTORY_OR_POINTER_BOUND");
                int action=event.getActionMasked(),index=event.getActionIndex();ArrayList<Object>points=new ArrayList<>(),history=new ArrayList<>();
                for(int i=0;i<event.getPointerCount();i++){float x=event.getX(i),y=event.getY(i);if(!Float.isFinite(x)||!Float.isFinite(y))throw new IllegalArgumentException("NONFINITE_MOTION");points.add(Values.map("id",event.getPointerId(i),"xPx",x,"yPx",y));}
                for(int h=0;h<event.getHistorySize();h++){ArrayList<Object>positions=new ArrayList<>();for(int i=0;i<event.getPointerCount();i++){float x=event.getHistoricalX(i,h),y=event.getHistoricalY(i,h);if(!Float.isFinite(x)||!Float.isFinite(y))throw new IllegalArgumentException("NONFINITE_MOTION_HISTORY");positions.add(Values.map("id",event.getPointerId(i),"xPx",x,"yPx",y));}history.add(Values.map("eventUptimeMs",event.getHistoricalEventTime(h),"points",positions));}
                sink.motion(Values.map("source",source,"kind","ANDROID_MOTION_EVENT","side",side,"eventSource",event.getSource(),"deviceId",event.getDeviceId(),"flags",event.getFlags(),"action",action,"eventUptimeMs",event.getEventTime(),"downUptimeMs",event.getDownTime(),"receiptElapsedNs",SystemClock.elapsedRealtimeNanos(),"viewWidthPx",getWidth(),"viewHeightPx",getHeight(),"radiusPx",radius(),"points",points,"history",history));
                lastMotionUptime=event.getEventTime()*1000000L;lastAction=action;
                if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL||action==MotionEvent.ACTION_POINTER_UP){clear();releasePending=true;sink.released();return true;}
                if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){pointer=event.getPointerId(index);held[side]=true;}
                int at=event.findPointerIndex(pointer);if(at<0)return true;
                double dx=Math.max(-1,Math.min(1,(event.getX(at)-getWidth()/2f)/radius())),up=Math.max(-1,Math.min(1,(getHeight()/2f-event.getY(at))/radius()));
                if(side==0){axes[3]=dx;axes[2]=up;}else{axes[0]=dx;axes[1]=up;}invalidate();return true;
            }catch(Exception e){clear();sink.invalid(e.getMessage());return false;}
        }
    }
}
