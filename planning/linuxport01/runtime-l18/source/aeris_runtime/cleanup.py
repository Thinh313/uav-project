"""Attempt every owned close; retain the original failure and bounded secondaries."""
import os,sys

def cleanup(primary,operations):
 for label,operation in operations:
  try:operation()
  except BaseException as error:
   if primary is None:primary=error
   elif len(getattr(primary,'__notes__',()))<8:primary.add_note('CLEANUP_SECONDARY:'+str(label)[:64]+':'+type(error).__name__+':'+str(error)[:256])
 return primary

def finish_cleanup(operations):
 original=sys.exc_info()[1];result=cleanup(original,operations)
 if original is None and result is not None:raise result

def close_fd(fd):finish_cleanup([('fd-close',lambda:os.close(fd))])
