
#include "Plugin.h"

Plugin * Plugin::creator()
{
  return new Plugin();
}

std::string Plugin::print()
{
  return "the plugin";
}
