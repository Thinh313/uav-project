#include <sys/socket.h>
#include <sys/select.h>
#include <arpa/inet.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
int main(void){
 int a=socket(AF_INET,SOCK_DGRAM,0),b=socket(AF_INET,SOCK_DGRAM,0);
 struct sockaddr_in peer={.sin_family=AF_INET,.sin_port=0,.sin_addr.s_addr=htonl(INADDR_LOOPBACK)};socklen_t size=sizeof(peer);
 if(bind(b,(void*)&peer,size)||getsockname(b,(void*)&peer,&size))return 2;
 for(uint32_t i=0;i<3;i++){
  char packet[40]={0x1a,0x48};memcpy(packet+4,&i,4);if(sendto(a,packet,40,0,(void*)&peer,size)!=40)return 3;
  char buf[128];struct sockaddr_in sender;socklen_t slen=sizeof(sender);if(recvfrom(b,buf,sizeof(buf),0,(void*)&sender,&slen)!=40)return 4;
  const char *reply="\n{\"timestamp\":1}\n";if(sendto(b,reply,strlen(reply),0,(void*)&sender,slen)<0)return 5;
  fd_set fds;FD_ZERO(&fds);FD_SET(a,&fds);struct timeval t={1,0};if(select(a+1,&fds,0,0,&t)!=1)return 6;
  if(recvfrom(a,buf,sizeof(buf),0,0,0)<0||usleep(1000))return 7;
 }
 close(a);close(b);return 0;
}
