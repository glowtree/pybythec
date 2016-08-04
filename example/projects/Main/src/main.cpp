
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
  
  // /// plugin
  // typedef void (*loadPluginFunc)(string);
  // typedef void (*unloadPluginFunc)();
  
  // loadPluginFunc loadPlugin;
  // unloadPluginFunc unloadPlugin;
  
  // #if defined __linux
  
  // #elif defined __APPLE__
    
  //   void * pluginHandle = dlopen("../../Plugin/Plugin.bundle", RTLD_NOW);
  //   if(!pluginHandle)
  //   {
  //     cerr << "dlopen failed because" << dlerror() << endl;
  //     return 1;
  //   }
    
  //   loadPlugin   =   (loadPluginFunc) dlsym(pluginHandle, "loadPlugin");
  //   unloadPlugin = (unloadPluginFunc) dlsym(pluginHandle, "unloadPlugin");
    
  //   if(!loadPlugin)
  //   {
  //     cerr << "failed to find loadPlugin because " << dlerror() << endl;
  //     return 1;
  //   }

  // #elif defined _WIN32
  
  //   HINSTANCE pluginHandle = LoadLibrary("../../Plugin/Plugin.dll");
  //   if(!pluginHandle) 
  //   {
  //     cerr << "LoadLibrary failed" << endl;
  //     return 1;
  //   }
    
  //   loadPlugin = (loadPluginFunc) GetProcAddress(pluginHandle, "loadPlugin");
  //   unloadPlugin = (unloadPluginFunc) GetProcAddress(pluginHandle, "unloadPlugin");

  // #endif
  

  // if(!loadPlugin)
  // {
  //   cerr << "failed to find loadPlugin" << endl;
  //   return 1;
  // }
  
  // string v;
  // loadPlugin(v);
  // cout << " and " << v;
  
  // if(!unloadPlugin)
  // {
  //   cerr << "failed to find unloadPlugin" << endl;
  //   return 1;
  // }
  // unloadPlugin();
  
  /// finished
  cout << endl;
  return 0;
}
