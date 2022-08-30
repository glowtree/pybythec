
#include "DynamicLib.h"

DynamicLib::DynamicLib()
{
  _value = "a dynamically linked library";
}

std::string const & DynamicLib::value()
{
  return _value;
}
