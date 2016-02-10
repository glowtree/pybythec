
#include "../../shared/include/StaticLib.h"
#include "../../shared/include/DynamicLib.h"
// #include "../../shared/include/Plugin.h"
#include <iostream>

using namespace std;

int main(int argc, char * argv[])
{
  cout << "running the executable";
  
  /// static lib
  StaticLib sl;
  cout << " and " << sl.print();
  
  /// dynamic lib
  DynamicLib dl;
  cout << " and " << dl.print();
  
  /// plugin
  // Plugin p;
#if defined __linux

    // cout << " and " << print();
  
#elif defined __APPLE__
  
#elif defined _WIN32

  HINSTANCE plugin = LoadLibrary("Plugin.dll");
  if(!plugin) 
  {
    std::err << "could not load Plugin" << std::endl;
    return 1;
  }
  
  // resolve function address here
  f_funci funci = (f_funci)GetProcAddress(plugin, "funci");
  if (!funci) {
  std::cout << "could not locate the function" << std::endl;
  return EXIT_FAILURE;
  }
  
  std::cout << "funci() returned " << funci() << std::endl;

#endif
  
  cout << endl;
  
  return 0;
}
