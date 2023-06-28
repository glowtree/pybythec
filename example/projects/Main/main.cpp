
#include "StaticLib.h"
#include "DynamicLib.h"
#include <iostream>

#if defined(__linux) or defined(__APPLE__)
  #include <dlfcn.h>
#elif _WIN32
  #include <windows.h>
#endif

using namespace std;

int main(int argc, char * argv[])
{
  cout << "running an executable";
  
  /// static lib
  StaticLib sl;
  cout << " and " << sl.value();
  
  /// dynamic lib
  DynamicLib dl;
  cout << " and " << dl.value();
  
  
  /// finished
  cout << endl;
  return 0;
}
