
#include "StaticLib.h"
#include "DynamicLib.h"
#include <iostream>

#ifdef _WIN32
  #include <windows.h>
#endif

using namespace std;

int main(int argc, char * argv[])
{
  cout << "running a executable";
  
  /// static lib
  StaticLib sl;
  cout << " and " << sl.value();
  
  /// dynamic lib
  DynamicLib dl;
  cout << " and " << dl.value();
  
  /// plugin
#if defined __linux

#elif defined __APPLE__
  
#elif defined _WIN32

  HINSTANCE pluginLib = LoadLibrary("../../Plugin/Plugin.dll");
  if(!pluginLib) 
  {
    cerr << "LoadLibrary failed" << endl;
    return 1;
  }
  
  typedef bool (*loadPluginFunc)();
  loadPluginFunc loadPlugin = (loadPluginFunc) GetProcAddress(pluginLib, "loadPlugin");
  if(!loadPlugin)
  {
    cerr << "GetProcAddress failed for loadPlugin" << endl;
    return 1;
  }
  
  typedef bool (*unloadPluginFunc)();
  unloadPluginFunc unloadPlugin = (unloadPluginFunc) GetProcAddress(pluginLib, "unloadPlugin");
  if(!unloadPlugin)
  {
    cerr << "GetProcAddress failed for unloadPlugin" << endl;
    return 1;
  }
  
#endif
  
  loadPlugin();
  unloadPlugin();
  
  /// finished
  cout << endl;
  return 0;
}
