#include <stdint.h>
#include <string.h>
#include <thread>
namespace SITLStageTrace {void set_frame(uint64_t);void emit(uint32_t,uint64_t,uint64_t,int64_t);}
int main(int argc,char **argv) {
    const char *mode=argc>1?argv[1]:"normal";
    if(!strcmp(mode,"foreign")) {
        SITLStageTrace::set_frame(0);SITLStageTrace::emit(10,0,0,0);
        std::thread other([](){SITLStageTrace::emit(11,0,0,0);});other.join();return 7;
    }
    const uint64_t count=!strcmp(mode,"backpressure")?1000000:3;
    for(uint64_t i=0;i<count;i++){SITLStageTrace::set_frame(i);SITLStageTrace::emit(10,i,0,0);}
    return 0;
}
