package vn.rtr.aeris.shell29;
import vn.rtr.aeris.shell24.InputModel;import vn.rtr.aeris.shell24.Json;
public final class InputOwner {
 private final InputModel model;private String owner="NONE";private long generation;private boolean focused;
 public InputOwner(String session){model=new InputModel(session);}
 public void focus(boolean f,long t){focused=f;model.focus(f,t);if(!f)owner="NONE";}
 public void attach(long gen,long t){generation=gen;owner="NONE";model.attach(new InputModel.Calibration("mock-cal29-v1","mock:joystick",-1,0,1,.1,false),t);}
 public void detach(long t){owner="NONE";model.detach(t);}
 public boolean sample(String s,long gen,String device,double value,long t){if(gen!=generation)return false;boolean result=model.sample(s,device,value,t);if(!model.owned())owner="NONE";return result;}
 public void hold(boolean active,long t){model.hold(active,t);if(!model.owned())owner="NONE";}
 public boolean acquire(String target,boolean manualAllowed,long gen,long t){if(!target.equals("MANUAL_AIRCRAFT")&&!target.equals("GIMBAL_FRONT")&&!target.equals("GIMBAL_CENTER"))throw new IllegalArgumentException("Explicit input owner");if(gen!=generation||!focused||target.equals("MANUAL_AIRCRAFT")&&!manualAllowed)return false;if(!owner.equals("NONE")&&!owner.equals(target)){revoke(t);return false;}if(!model.acquire(t))return false;owner=target;return true;}
 public void tick(long t){model.tick(t);if(!model.owned())owner="NONE";}
 public void revoke(long t){model.focus(false,t);model.focus(focused,t);owner="NONE";}
 public String owner(){return model.owned()?owner:"NONE";}public String json(){return "{\"owner\":"+Json.quote(owner())+",\"connectionGeneration\":"+generation+",\"model\":"+model.json()+",\"outputTransport\":\"NONE\",\"physicalMappingVerified\":false}";}
}
