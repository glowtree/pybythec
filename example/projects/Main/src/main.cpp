
#include "StaticLib.h"
#include "DynamicLib.h"
#include "PluginBase.h"
#include <iostream>

#ifdef _WIN32
  #include <windows.h>
#endif

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
  PluginBase * p;
  
#if defined __linux

#elif defined __APPLE__
  
#elif defined _WIN32

  HINSTANCE pluginLib = LoadLibrary("../../Plugin/Plugin.dll");
  if(!pluginLib) 
  {
    cerr << "LoadLibrary failed" << endl;
    return 1;
  }
  
  typedef PluginBase * (*PluginBaseCreator)();
  PluginBaseCreator pluginBaseCreator = (PluginBaseCreator) GetProcAddress(pluginLib, "creator");
  if(!pluginBaseCreator)
  {
    cerr << "GetProcAddress failed" << endl;
    return 1;
  }  
  p = (pluginBaseCreator)();
  
#endif
  
  cout << " and " << p->print();
  delete p;
  
  /// finished
  cout << endl;
  return 0;
}
