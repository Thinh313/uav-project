from ui98 import *
owned();run=sys.argv[1];out=E/'runs'/run;tap94('abort83');wait98(run,'CLOSED',seconds=5);b=raw98(run);(out/'android-raw.jsonl').open('xb').write(b);(out/'stop-request.json').open('x').write(json.dumps({'reason':'Read-only preflight blocked; no arm sent; preserve misconfigured GPS port case'}));capture(run+'-blocked-closed')
