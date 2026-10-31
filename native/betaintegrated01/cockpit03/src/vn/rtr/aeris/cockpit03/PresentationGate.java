package vn.rtr.aeris.cockpit03;
import java.io.IOException;
import java.util.Arrays;
/** Read-only visual acknowledgement; cannot grant flight authority or start a writer. */
public final class PresentationGate {
 private String chosen="survey",presented;
 public boolean choose(String view){if(!Arrays.asList("survey","preflight","fly","review").contains(view))throw new IllegalArgumentException("VIEW");if(chosen.equals(view))return false;chosen=view;presented=null;return true;}
 public void acknowledge(String view)throws IOException{if(!chosen.equals(view))throw new IOException("PRESENTATION_ACK_VIEW_MISMATCH");presented=view;}
 public boolean ready(){return chosen.equals(presented);}
 public String chosen(){return chosen;}
 public String presented(){return presented;}
}
