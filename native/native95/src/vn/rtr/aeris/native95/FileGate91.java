package vn.rtr.aeris.native95;
/** One foreground/busy admission rule for every UI-initiated writer. Results/status/revoke remain readable. */
public final class FileGate91 {
 private FileGate91(){}
 public static boolean writes(String a){return a.startsWith("direct95:")&&!a.equals("direct95:state")||a.startsWith("diag91:")&&!a.equals("diag91:status")||java.util.Arrays.asList("kml-import94","save","fresh","activate","import","export","file-reconcile87","bundle-export88").contains(a)||a.startsWith("sitl:")&&!java.util.Arrays.asList("sitl:state","sitl:revoke","sitl:review").contains(a);}
 public static void require(String a,boolean foreground,boolean diagnostic,boolean workspace,boolean bundle){if(!writes(a))return;if(!foreground)throw new IllegalStateException("FOREGROUND_REQUIRED_NO_QUEUED_WRITE");if(diagnostic||workspace||bundle)throw new IllegalStateException("NATIVE_FILE_OR_DIAGNOSTIC_PENDING_NO_RETRY");}
}
