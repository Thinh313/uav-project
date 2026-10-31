#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOMessage.h>
#include <IOKit/pwr_mgt/IOPMLib.h>
#include <IOKit/ps/IOPowerSources.h>
#include <IOKit/ps/IOPSKeys.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <string.h>
#include <time.h>

static io_connect_t root;
static int fd=-1;static size_t bytes=0;static unsigned long rows=0;static volatile sig_atomic_t stopping=0;
static bool testMode=false;
static void event(const char *kind){
 CFTypeRef info=IOPSCopyPowerSourcesInfo();CFStringRef source=info?IOPSGetProvidingPowerSourceType(info):NULL;
 bool ac=source&&CFEqual(source,CFSTR(kIOPSACPowerValue));
 io_service_t service=IOServiceGetMatchingService(kIOMainPortDefault,IOServiceMatching("IOPMrootDomain"));
 CFTypeRef lid=service?IORegistryEntryCreateCFProperty(service,CFSTR("AppleClamshellState"),kCFAllocatorDefault,0):NULL;
 bool known=lid&&CFGetTypeID(lid)==CFBooleanGetTypeID(),closed=known&&CFBooleanGetValue((CFBooleanRef)lid);
 struct timespec t;clock_gettime(CLOCK_REALTIME,&t);char line[512];
 int n=snprintf(line,sizeof(line),"{\"n\":%lu,\"kind\":\"%s\",\"utcMs\":%lld,\"pid\":%d,\"parentPid\":%d,\"onAC\":%s,\"lidKnown\":%s,\"lidClosed\":%s,\"testMode\":%s}\n",++rows,kind,(long long)t.tv_sec*1000+t.tv_nsec/1000000,getpid(),getppid(),ac?"true":"false",known?"true":"false",closed?"true":"false",testMode?"true":"false");
 if(info)CFRelease(info);if(lid)CFRelease(lid);if(service)IOObjectRelease(service);
 if(n<=0||(size_t)n>=sizeof(line)||bytes+(size_t)n>8*1024*1024)_exit(74);
 for(int p=0;p<n;){ssize_t done=write(fd,line+p,(size_t)(n-p));if(done<0&&errno==EINTR)continue;if(done<=0)_exit(74);p+=(int)done;}
 if(fsync(fd)!=0)_exit(74);bytes+=(size_t)n;
 for(int p=0;p<n;){ssize_t done=write(STDOUT_FILENO,line+p,(size_t)(n-p));if(done<0&&errno==EINTR)continue;if(done<=0)_exit(74);p+=(int)done;}
}
static void callback(void *ctx,io_service_t s,natural_t kind,void *arg){
 (void)ctx;(void)s;
 switch(kind){
  case kIOMessageCanSystemSleep:event("CAN_SYSTEM_SLEEP");IOAllowPowerChange(root,(intptr_t)arg);break;
  case kIOMessageSystemWillSleep:event("SYSTEM_WILL_SLEEP");IOAllowPowerChange(root,(intptr_t)arg);break;
  case kIOMessageSystemWillPowerOn:event("SYSTEM_WILL_POWER_ON");break;
  case kIOMessageSystemHasPoweredOn:event("SYSTEM_HAS_POWERED_ON");break;
 }
}
static void signalStop(int s){(void)s;stopping=1;}
static void tick(CFRunLoopTimerRef t,void *ctx){(void)t;(void)ctx;if(stopping){event("STOPPED");CFRunLoopStop(CFRunLoopGetCurrent());}else event("HEARTBEAT");}
int main(int argc,char **argv){
 if(argc<2||argc>3)return 64;if(argc==3){if(strcmp(argv[2],"--test-events")!=0)return 64;testMode=true;}
 fd=open(argv[1],O_WRONLY|O_CREAT|O_EXCL|O_APPEND|O_NOFOLLOW,0600);if(fd<0)return 73;
 IONotificationPortRef port=NULL;io_object_t notifier=0;root=IORegisterForSystemPower(NULL,&port,callback,&notifier);if(!root){close(fd);return 70;}
 CFRunLoopAddSource(CFRunLoopGetCurrent(),IONotificationPortGetRunLoopSource(port),kCFRunLoopCommonModes);
 signal(SIGTERM,signalStop);signal(SIGINT,signalStop);event("READY");
 if(testMode){event("SYSTEM_WILL_SLEEP");event("SYSTEM_HAS_POWERED_ON");event("STOPPED");}
 else{CFRunLoopTimerContext c={0,NULL,NULL,NULL,NULL};CFRunLoopTimerRef timer=CFRunLoopTimerCreate(kCFAllocatorDefault,CFAbsoluteTimeGetCurrent()+1,5,0,0,tick,&c);CFRunLoopAddTimer(CFRunLoopGetCurrent(),timer,kCFRunLoopCommonModes);CFRunLoopRun();CFRunLoopRemoveTimer(CFRunLoopGetCurrent(),timer,kCFRunLoopCommonModes);CFRelease(timer);}
 CFRunLoopRemoveSource(CFRunLoopGetCurrent(),IONotificationPortGetRunLoopSource(port),kCFRunLoopCommonModes);IODeregisterForSystemPower(&notifier);IOServiceClose(root);IONotificationPortDestroy(port);close(fd);return 0;
}
