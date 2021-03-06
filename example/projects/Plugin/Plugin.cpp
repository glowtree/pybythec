
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

void loadPlugin(string & value)
{
  p = new Plugin();
  value = p->value();
}

void unloadPlugin()
{
  if(p) delete p;
}
