#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
int main(int argc,char **argv){
 if(argc!=2)return 2;int fd=open(argv[1],O_RDONLY);if(fd<0)return 3;
 struct stat st;if(fstat(fd,&st))return 4;
 void *m=mmap(0,st.st_size,PROT_READ,MAP_SHARED,fd,0);if(m==MAP_FAILED)return 5;
 int result=msync(m,st.st_size,MS_SYNC)||fsync(fd);munmap(m,st.st_size);close(fd);return result?6:0;
}
