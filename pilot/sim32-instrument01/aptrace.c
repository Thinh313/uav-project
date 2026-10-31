#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/select.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <time.h>
#include <string.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdatomic.h>

/* Syscall observer only; never modifies AP arguments/clock/return values. */
typedef struct {uint64_t seq,frame;uint32_t kind,tid;uint64_t begin,end,arg,extra;int64_t result;} Event;
typedef struct {char magic[8];uint64_t capacity;_Atomic uint64_t committed,failed;uint64_t event_size;} Header;
static Header *h; static Event *events;static int json_fd=-1;
static __thread uint64_t frame;static __thread int active;
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static void logevent(uint32_t kind,uint64_t begin,uint64_t end,uint64_t arg,int64_t result,int error){
 if(!h||!active)return;uint64_t i=atomic_load_explicit(&h->committed,memory_order_relaxed);
 if(i>=h->capacity){atomic_store(&h->failed,1);_exit(93);}
 events[i]=(Event){i,frame,kind,(uint32_t)syscall(SYS_gettid),begin,end,arg,(uint64_t)error,result};
 atomic_store_explicit(&h->committed,i+1,memory_order_release);
}
__attribute__((constructor)) static void init(void){
 const char *p=getenv("AERIS_AP_TRACE");if(!p)return;
 int fd=open(p,O_RDWR|O_CREAT|O_EXCL,0600);if(fd<0)_exit(90);
 size_t size=64*1024*1024;if(posix_fallocate(fd,0,size))_exit(91);
 h=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);close(fd);if(h==MAP_FAILED)_exit(92);
 memcpy(h->magic,"AERISTR1",8);h->capacity=(size-4096)/sizeof(Event);h->event_size=sizeof(Event);events=(Event*)((char*)h+4096);
}
ssize_t sendto(int fd,const void *buf,size_t len,int flags,const struct sockaddr *addr,socklen_t alen){
 static ssize_t(*real)(int,const void*,size_t,int,const struct sockaddr*,socklen_t);if(!real)real=dlsym(RTLD_NEXT,"sendto");
 if(h&&len==40&&((const unsigned char*)buf)[0]==0x1a&&((const unsigned char*)buf)[1]==0x48){uint32_t seq;memcpy(&seq,(const char*)buf+4,4);json_fd=fd;frame=seq;active=1;}
 int track=h&&active&&fd==json_fd;uint64_t a=track?ns():0;ssize_t n=real(fd,buf,len,flags,addr,alen);int e=errno;
 if(track)logevent(1,a,ns(),len,n,e);errno=e;return n;
}
ssize_t recvfrom(int fd,void *buf,size_t len,int flags,struct sockaddr *addr,socklen_t *alen){
 static ssize_t(*real)(int,void*,size_t,int,struct sockaddr*,socklen_t*);if(!real)real=dlsym(RTLD_NEXT,"recvfrom");
 int track=h&&active&&fd==json_fd;uint64_t a=track?ns():0;ssize_t n=real(fd,buf,len,flags,addr,alen);int e=errno;
 if(track)logevent(2,a,ns(),len,n,e);errno=e;return n;
}
ssize_t recv(int fd,void *buf,size_t len,int flags){
 static ssize_t(*real)(int,void*,size_t,int);if(!real)real=dlsym(RTLD_NEXT,"recv");
 int track=h&&active&&fd==json_fd;uint64_t a=track?ns():0;ssize_t n=real(fd,buf,len,flags);int e=errno;
 if(track)logevent(2,a,ns(),len,n,e);errno=e;return n;
}
int select(int nfds,fd_set *r,fd_set *w,fd_set *x,struct timeval *timeout){
 static int(*real)(int,fd_set*,fd_set*,fd_set*,struct timeval*);if(!real)real=dlsym(RTLD_NEXT,"select");
 int track=h&&active&&json_fd>=0&&json_fd<nfds&&r&&FD_ISSET(json_fd,r);uint64_t a=track?ns():0;
 uint64_t wait=timeout?timeout->tv_sec*1000000ULL+timeout->tv_usec:UINT64_MAX;int n=real(nfds,r,w,x,timeout);int e=errno;
 if(track)logevent(3,a,ns(),wait,n,e);errno=e;return n;
}
int usleep(useconds_t usec){
 static int(*real)(useconds_t);if(!real)real=dlsym(RTLD_NEXT,"usleep");int track=h&&active;uint64_t a=track?ns():0;
 int n=real(usec);int e=errno;if(track)logevent(4,a,ns(),usec,n,e);errno=e;return n;
}
