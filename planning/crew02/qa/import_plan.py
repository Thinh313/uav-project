from ui01 import *
owned();name=sys.argv[1];assert name in ['operator-nominal.kml','operator-loss.kml'];source=R/'evidence/product-milestones/p1-corpus'/name;label=name[:-4]+('-'+sys.argv[2]if len(sys.argv)>2 else'')
before=journal(label+'-before-import');doc=json.loads(before['journals']['workspaces/initial']['latest']['body']);ack=doc['mission']['draft']['options']['datumAcknowledged']
adb('push',source,'/sdcard/Download/'+name);tap01('import-kml94');time.sleep(.4)
if not any(n.get('text')==name for n in nodes()):tap_label('Show roots');time.sleep(.3);tap_label('Downloads');time.sleep(.4)
tap_label(name);time.sleep(.5);tap01('inspect92');
# Import/edit preserves options. Reaffirm Home explicitly, ending checked.
if ack:tap01('datum92')
tap01('datum92');capture(label+'-kml-datum');tap01('native-compile');capture(label+'-compiled');show()
