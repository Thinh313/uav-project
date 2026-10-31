package org.json;
import java.util.*;import com.google.gson.*;
public class JSONArray {
 final JsonArray value;public JSONArray(){value=new JsonArray();}public JSONArray(String s){value=JsonParser.parseString(s).getAsJsonArray();}public JSONArray(Collection<?>c){this();for(Object v:c)put(v);}JSONArray(JsonArray a){value=a;}
 public JSONArray put(Object o){value.add(JSONObject.tree(o));return this;}public Object get(int i){return JSONObject.object(value.get(i));}public JSONObject getJSONObject(int i){return(JSONObject)get(i);}public JSONArray getJSONArray(int i){return(JSONArray)get(i);}public double getDouble(int i){Object v=get(i);return v instanceof Number?((Number)v).doubleValue():Double.parseDouble(String.valueOf(v));}public int getInt(int i){return((Number)get(i)).intValue();}public long getLong(int i){return((Number)get(i)).longValue();}public String getString(int i){return String.valueOf(get(i));}public int length(){return value.size();}public Object remove(int i){return JSONObject.object(value.remove(i));}@Override public String toString(){return value.toString();}
}
