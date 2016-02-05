
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
// #if defined __linux

    // cout << " and " << print();
  
// #elif defined __APPLE__
  
// #elif defined _WIN32
  
  // #endif
  
  cout << endl;
  
  return 0;
}

