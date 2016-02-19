
#include "StaticLib.h"

StaticLib::StaticLib()
{
  _value = "a statically linked library";
}

std::string const & StaticLib::value()
{
  return _value;
}
