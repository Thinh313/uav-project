package vn.rtr.aeris.shell29;
import java.util.*;import vn.rtr.aeris.shell24.Json;
/** Original Java model snapshots for host walkthrough; no alternate browser controller. */
public final class Replay {
 private static void row(List<String> rows,String label,String action,Workflow w){rows.add("{\"label\":"+Json.quote(label)+",\"nextAction\":"+Json.quote(action)+",\"state\":"+w.review()+"}");}
 public static String run(String id,int plan){Workflow w=new Workflow("host29:"+id+":"+plan);long t=0;List<String> rows=new ArrayList<>();w.focus(true,t);w.select(plan,t);row(rows,"Vùng khảo sát đã chọn","Đối chiếu mock",w);w.navigate("Preflight",++t);w.inspect(w.fixture(t),t);row(rows,"Home, profile và readback mock khớp","Xác nhận Home",w);w.confirmHome(++t);row(rows,"Home mock đã xác nhận","Xác nhận độ cao",w);w.confirmAltitude(++t);row(rows,"Preflight sẵn sàng trong mô phỏng","Bắt đầu mock",w);w.navigate("Fly",++t);w.start(t);row(rows,"Phiên mock đang chạy","ACK mock",w);w.ack(++t);row(rows,"ACK không phải thực thi","Bước mock",w);w.step(++t);
 if(id.equals("normal")){row(rows,"Điểm tuyến mock "+w.cursor()+"/"+w.plan().points(),w.phase().equals("RUNNING_MOCK")?"Bước mock":"Hạ cánh mock",w);while(w.phase().equals("RUNNING_MOCK")){w.step(++t);row(rows,"Điểm tuyến mock "+w.cursor()+"/"+w.plan().points(),w.phase().equals("RUNNING_MOCK")?"Bước mock":"Hạ cánh mock",w);}w.land(++t);w.navigate("Review",++t);row(rows,"Review hoàn tất mock",null,w);}
 else if(id.equals("focus")){w.focus(false,++t);row(rows,"Mất focus: UI bị đình chỉ, không gửi HOLD","Giữ focus lại",w);w.focus(true,++t);row(rows,"Focus trở lại không tự cấp quyền","Đối chiếu lại mock",w);w.inspect(w.fixture(++t),t);w.confirmHome(t);w.confirmAltitude(t);row(rows,"Đã kiểm lại, chưa tự resume","Tiếp tục mock rõ ràng",w);w.resume(++t);row(rows,"Chỉ tiếp tục sau thao tác rõ ràng",null,w);}
 else if(id.equals("loss")){w.disconnect(++t);row(rows,"Mất link mock: giữ hồ sơ gián đoạn","Kết nối lại mock",w);w.connect(++t);row(rows,"Kết nối mới không khôi phục lệnh cũ",null,w);}
 else if(id.equals("reboot")){w.reboot(++t);row(rows,"Reboot mock hủy gate cũ",null,w);}
 else if(id.equals("input")){w.mockNeutral(t+=10);t+=100;w.acquire("GIMBAL_FRONT",t);row(rows,"Mock deadman / neutral cấp owner front","Đổi owner mock",w);w.acquire("GIMBAL_CENTER",++t);row(rows,"Đổi đích thu hồi owner, không retarget",null,w);}
 else throw new IllegalArgumentException("Replay scenario");
 return "{\"id\":"+Json.quote(id)+",\"planIndex\":"+plan+",\"origin\":\"HOST_JAVA_SYNTHETIC_WORKFLOW\",\"frames\":["+String.join(",",rows)+"]}";}
 public static void main(String[] args){List<String> out=new ArrayList<>();for(int p=0;p<Catalog.COUNT;p++)out.add(run("normal",p));for(String id:new String[]{"focus","loss","reboot","input"})out.add(run(id,0));System.out.println("{\"format\":\"aeris-native29-host-replays\",\"version\":1,\"operational\":false,\"scenarios\":["+String.join(",",out)+"]}");}
}
