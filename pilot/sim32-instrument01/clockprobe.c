#include <sys/socket.h>
#include <arpa/inet.h>
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
int main(void){int s=socket(AF_INET,SOCK_DGRAM,0);struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(9004),.sin_addr.s_addr=htonl(INADDR_ANY)};
 if(bind(s,(void*)&a,sizeof(a)))return 2;
 for(;;){uint64_t id;struct sockaddr_in peer;socklen_t size=sizeof(peer);ssize_t n=recvfrom(s,&id,8,0,(void*)&peer,&size);uint64_t r=ns();if(n!=8)continue;
 uint64_t usage=0,periods=0,throttles=0,throttled=0;FILE *f=fopen("/sys/fs/cgroup/cpu.stat","r");
 if(!f)return 4;char key[64];unsigned long long v;while(fscanf(f,"%63s %llu",key,&v)==2){if(!__builtin_strcmp(key,"usage_usec"))usage=v;else if(!__builtin_strcmp(key,"nr_periods"))periods=v;else if(!__builtin_strcmp(key,"nr_throttled"))throttles=v;else if(!__builtin_strcmp(key,"throttled_usec"))throttled=v;}fclose(f);
 uint64_t reply[7]={id,r,ns(),usage,periods,throttles,throttled};if(sendto(s,reply,sizeof(reply),0,(void*)&peer,size)!=sizeof(reply))return 3;}
}
