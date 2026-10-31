package vn.rtr.aeris.shell24;
import java.util.UUID;
public final class ShellState {
 public final String session=UUID.randomUUID().toString();public final InputModel input=new InputModel(session);public final VideoModel video=new VideoModel();public String workspace="Fly";public boolean focused=false;
 public void navigate(String p){if(!p.equals("Plan")&&!p.equals("Fly")&&!p.equals("Review"))throw new IllegalArgumentException("Workspace");workspace=p;}
 public void focus(boolean active,long now){focused=active;input.focus(active,now);if(!active)video.stop("LIFECYCLE_STOPPED");}
 public String report(){return "{\"format\":\"aeris-native24-preparation\",\"version\":1,\"session\":"+Json.quote(session)+",\"workspace\":"+Json.quote(workspace)+",\"focused\":"+focused+",\"operational\":false,\"transport\":\"NONE\",\"input\":"+input.json()+",\"video\":"+video.json()+"}";}
 public String checkpoint(){return "{\"format\":\"aeris-native24-history\",\"version\":1,\"historicalSession\":"+Json.quote(session)+",\"workspace\":"+Json.quote(workspace)+",\"historicalVideoSha256\":"+Json.quote(video.sha)+",\"authorityRestorable\":false}";}
}
