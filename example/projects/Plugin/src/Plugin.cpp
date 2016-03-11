
#include "Plugin.h"
#include <iostream>

using namespace std;

Plugin::Plugin()
{
  _value = "a plugin";
}

std::string const & Plugin::value()
{
  return _value;
}

Plugin * p = NULL;

#ifdef _WIN32
  bool __declspec(dllexport) loadPlugin()
#else
  bool loadPlugin()
#endif
{
  p = new Plugin();
  cout << p->value();  
  return true;
}

#ifdef _WIN32
  bool __declspec(dllexport) unloadPlugin()
#else
  bool unloadPlugin()
#endif
// bool unloadPlugin()
{
  if(p) delete p;
  return true;
}
