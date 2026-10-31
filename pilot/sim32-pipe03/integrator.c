/* SIM32 derivative only. No fast math, reassociation or contracted operations.
 * Compensated dot mirrors CPython3.14 float sum (PSF licensed source in evidence).
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
static double dot(const double *a,const double *b,int n){
 double hi=0,lo=0;
 for(int i=0;i<n;i++){double x=a[i]*b[i],t=hi+x;lo+=(fabs(hi)>=fabs(x))?(hi-t)+x:(x-t)+hi;hi=t;}
 return (lo && isfinite(lo))?hi+lo:hi;
}
static int vec(PyObject *p,double *v,int n){
 PyObject *s=PySequence_Fast(p,"kernel requires sequence");if(!s)return 0;
 if(PySequence_Fast_GET_SIZE(s)!=n){Py_DECREF(s);PyErr_SetString(PyExc_ValueError,"kernel vector dimension");return 0;}
 for(int i=0;i<n;i++){v[i]=PyFloat_AsDouble(PySequence_Fast_GET_ITEM(s,i));if(PyErr_Occurred()){Py_DECREF(s);return 0;}if(!isfinite(v[i])){Py_DECREF(s);PyErr_SetString(PyExc_ValueError,"kernel nonfinite input");return 0;}}
 Py_DECREF(s);return 1;
}
static int matrix(PyObject *p,double v[3][3]){
 PyObject *s=PySequence_Fast(p,"kernel matrix");if(!s)return 0;
 if(PySequence_Fast_GET_SIZE(s)!=3){Py_DECREF(s);PyErr_SetString(PyExc_ValueError,"kernel matrix dimension");return 0;}
 for(int i=0;i<3;i++)if(!vec(PySequence_Fast_GET_ITEM(s,i),v[i],3)){Py_DECREF(s);return 0;}
 Py_DECREF(s);return 1;
}
static int calc(double y[13],double force[3],double torque[3],double wind[3],double inertia[3][3],double inv[3][3],double area[3],double mass,double rho,double damping,double result[13]){
 double q[4]={y[6],y[7],y[8],y[9]},n=sqrt(dot(q,q,4));
 if(n==0){PyErr_SetString(PyExc_ValueError,"kernel zero quaternion");return 0;}
 double w=q[0]/n,x=q[1]/n,z=q[3]/n,v=q[2]/n;
 double R[3][3]={{1-2*(v*v+z*z),2*(x*v-z*w),2*(x*z+v*w)},{2*(x*v+z*w),1-2*(x*x+z*z),2*(v*z-x*w)},{2*(x*z-v*w),2*(v*z+x*w),1-2*(x*x+v*v)}};
 double relative[3]={y[3]-wind[0],y[4]-wind[1],y[5]-wind[2]},bodyForce[3];
 for(int i=0;i<3;i++){double col[3]={R[0][i],R[1][i],R[2][i]},rel=dot(col,relative,3);double drag=-.5*rho*area[i]*rel*fabs(rel);bodyForce[i]=force[i]+drag;}
 double angular[3]={y[10],y[11],y[12]},momentum[3];for(int i=0;i<3;i++)momentum[i]=dot(inertia[i],angular,3);
 double gyroscopic[3]={angular[1]*momentum[2]-angular[2]*momentum[1],angular[2]*momentum[0]-angular[0]*momentum[2],angular[0]*momentum[1]-angular[1]*momentum[0]},net[3];
 for(int i=0;i<3;i++)net[i]=(torque[i]-gyroscopic[i])-angular[i]*damping;
 double a=q[0],b=q[1],c=q[2],d=q[3],i=angular[0],j=angular[1],k=angular[2];
 double qd[4]={(a*0-b*i-c*j-d*k)*.5,(a*i+b*0+c*k-d*j)*.5,(a*j-b*k+c*0+d*i)*.5,(a*k+b*j-c*i+d*0)*.5};
 for(int h=0;h<3;h++){result[h]=y[h+3];result[h+3]=dot(R[h],bodyForce,3)*(1/mass)+(h==2?9.80665:0);result[h+10]=dot(inv[h],net,3);}for(int h=0;h<4;h++)result[h+6]=qd[h];

 return 1;
}
static PyObject *rk4(PyObject *self,PyObject *args){
 PyObject *Y,*F,*T,*W,*I,*J,*D;double mass,rho,damping,dt;
 if(!PyArg_ParseTuple(args,"OOOOOOOdddd",&Y,&F,&T,&W,&I,&J,&D,&mass,&rho,&damping,&dt))return NULL;
 double y[13],force[3],torque[3],wind[3],inertia[3][3],inv[3][3],area[3],tmp[13],k1[13],k2[13],k3[13],k4[13],z[13];
 if(!vec(Y,y,13)||!vec(F,force,3)||!vec(T,torque,3)||!vec(W,wind,3)||!matrix(I,inertia)||!matrix(J,inv)||!vec(D,area,3))return NULL;
 if(!isfinite(mass)||mass<=0||!isfinite(rho)||rho<=0||!isfinite(damping)||damping<0||!isfinite(dt)||dt<=0||dt>.005){PyErr_SetString(PyExc_ValueError,"integrator domain");return NULL;}
 #define DERIVE(src,dst) if(!calc(src,force,torque,wind,inertia,inv,area,mass,rho,damping,dst))return NULL
 DERIVE(y,k1);for(int h=0;h<13;h++)tmp[h]=y[h]+k1[h]*(dt/2);
 DERIVE(tmp,k2);for(int h=0;h<13;h++)tmp[h]=y[h]+k2[h]*(dt/2);
 DERIVE(tmp,k3);for(int h=0;h<13;h++)tmp[h]=y[h]+k3[h]*dt;
 DERIVE(tmp,k4);for(int h=0;h<13;h++)z[h]=y[h]+dt*(k1[h]+2*k2[h]+2*k3[h]+k4[h])/6;
 PyObject *out=PyList_New(13);if(!out)return NULL;for(int h=0;h<13;h++){PyObject *item=PyFloat_FromDouble(z[h]);if(!item){Py_DECREF(out);return NULL;}PyList_SET_ITEM(out,h,item);}return out;
}
static PyMethodDef methods[]={{"rk4",rk4,METH_VARARGS,"Strict same-order RK4; caller retains model conventions"},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_sim32_integrator",NULL,-1,methods};
PyMODINIT_FUNC PyInit__sim32_integrator(void){return PyModule_Create(&module);}
