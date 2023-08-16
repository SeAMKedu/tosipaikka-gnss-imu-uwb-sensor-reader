// imu.cpp
/**********************************************************
 * 
 * Call the IMU sensor reader application.
 * 
 * This application is to be compiled as a shared library
 * so that the Python application is able to call it. To
 * compile as shared library, run the commands below.
 * 
 * $ g++ -Wall -fPIC -c imu.cpp
 * $ g++ -shared -o imu.so imu.o
 * 
 *********************************************************/
#include <csignal>          // raise()
#include <cstdlib>          // system()
#include <unistd.h>         // chdir()
using namespace std;


int main()
{
    chdir("sensors");
    std::system("sudo ./xsens");
    raise(SIGINT);
    return 0;
}
