
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
bool loadPlugin()
{
  p = new Plugin();
  cout << p->value();  
  return true;
}

bool unloadPlugin()
{
  if(p) delete p;
  return true;
}
