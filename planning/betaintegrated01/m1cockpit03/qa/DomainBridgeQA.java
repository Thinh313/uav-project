import java.util.*;import org.json.*;import vn.rtr.aeris.cockpit03.*;import vn.rtr.aeris.beta01runtime.Values;
public final class DomainBridgeQA {
 interface Op{void run()throws Exception;}static List<Map<String,Object>>results=new ArrayList<>();static void check(boolean b,String s){if(!b)throw new AssertionError(s);}static void deny(Op o)throws Exception{boolean fail=false;try{o.run();}catch(Exception e){fail=true;}check(fail,"invalidrequestaccepted");}static void test(String id,Op o){try{o.run();results.add(Values.map("id",id,"pass",true));}catch(Throwable e){results.add(Values.map("id",id,"pass",false,"error",e.toString()));}}
 static JSONObject draft(String kind,double[][]points){JSONArray a=new JSONArray();for(double[]p:points)a.put(new JSONArray(Arrays.asList(p[0],p[1])));return new JSONObject().put("revision",0).put("kind",kind).put("name","Khảo sát kiểm định Việt Nam").put("datum","WGS84").put("altitudeDatum","RELATIVE_HOME").put("units","m").put("geometry",a).put("altitudeM",3).put("corridorWidthM",10);}
 static double[][]good={{10.854,106.807},{10.854,106.8071},{10.8541,106.8071},{10.8541,106.807}};
 public static void main(String[]args)throws Exception{
 test("D01_VALID_POLYGON_TRAINING_REVISION",()->{JSONObject r=new JSONObject(new String(WorkspaceDomain.draft(draft("polygon",good),null,0),"UTF-8"));check(r.getInt("revision")==1&&r.getBoolean("trainingOnly")&&r.getString("datum").equals("WGS84"),"wrongcanonicaldraft");});
 test("D02_VALID_CORRIDOR",()->WorkspaceDomain.draft(draft("corridor",new double[][]{good[0],good[2]}),null,0));
 test("D03_COLLINEAR_POLYGON_DENIED",()->deny(()->WorkspaceDomain.draft(draft("polygon",new double[][]{{10.854,106.807},{10.8541,106.8071},{10.8542,106.8072}}),null,0)));
 test("D04_CROSSED_POLYGON_DENIED",()->deny(()->WorkspaceDomain.draft(draft("polygon",new double[][]{{10.854,106.807},{10.8542,106.8072},{10.854,106.8072},{10.8541,106.807}}),null,0)));
 test("D05_ZERO_LENGTH_CORRIDOR_DENIED",()->deny(()->WorkspaceDomain.draft(draft("corridor",new double[][]{good[0],good[0]}),null,0)));
 test("D06_UNKNOWN_COMMAND_FIELD_DENIED",()->deny(()->WorkspaceDomain.draft(draft("polygon",good).put("command",400),null,0)));
 test("D07_STALE_REVISION_DENIED",()->deny(()->WorkspaceDomain.draft(draft("polygon",good),null,1)));
 test("D08_BAD_DATUM_OR_UNITS_DENIED",()->{for(String key:new String[]{"datum","altitudeDatum","units"})deny(()->WorkspaceDomain.draft(draft("polygon",good).put(key,"UNKNOWN"),null,0));});
 test("D09_NUMBER_STRING_BOOLEAN_DENIED",()->{for(Object v:new Object[]{"3",true,-1,6})deny(()->WorkspaceDomain.draft(draft("polygon",good).put("altitudeM",v),null,0));});
 test("D10_FOREIGN_WGS84_DOMAIN_DENIED",()->deny(()->WorkspaceDomain.draft(draft("corridor",new double[][]{{91,106},{10,106}}),null,0)));
 test("D11_BAD_NAME_CONTROL_CHAR_DENIED",()->deny(()->WorkspaceDomain.draft(draft("polygon",good).put("name","x\u0000y"),null,0)));
 test("B01_FRESH_WORKSPACE_METHODS",()->{BridgeGate b=new BridgeGate(17);int n=0;for(String type:new String[]{"LOAD","SAVE_DRAFT","NAVIGATE","STATE","REVIEWS"})b.accept("ui-17-"+(++n),17,type,256);});
 test("B02_NO_FLIGHT_METHOD",()->{for(String type:new String[]{"ARM","CONNECT","CONTROL","RAW_MAVLINK","CONSENT","LAND","operator","send"})deny(()->new BridgeGate(17).accept("ui-17-1",17,type,256));});
 test("B03_FOREIGN_EPOCH_DUPLICATE_OLD_ID",()->{BridgeGate b=new BridgeGate(17);deny(()->b.accept("ui-18-1",18,"STATE",256));b.accept("ui-17-2",17,"STATE",256);deny(()->b.accept("ui-17-2",17,"STATE",256));deny(()->b.accept("ui-17-1",17,"STATE",256));});
 test("B04_SIZE_AND_ID_BOUNDS",()->{deny(()->new BridgeGate(17).accept("ui-17-1",17,"STATE",16385));deny(()->new BridgeGate(17).accept("ui-17-2147483648",17,"STATE",256));});
 test("B05_DESTROYED_ACTIVITY_GATE_CLOSED",()->{BridgeGate b=new BridgeGate(17);b.close();deny(()->b.accept("ui-17-1",17,"STATE",256));});
 System.out.println(Values.json(Values.map("results",results,"scope","PRODUCT_DOMAIN_AND_GATE_WITH_TEST_ONLY_GSON_JSON_ADAPTER_NOT_ANDROID_RUNTIME")));
 }
}
