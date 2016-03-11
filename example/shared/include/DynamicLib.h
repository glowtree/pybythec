

#include <string>

#ifdef _WIN32
  #ifdef WIN_EXPORT
    class __declspec(dllexport) DynamicLib
  #else
    class __declspec(dllimport) DynamicLib
  #endif
#else
  class DynamicLib
#endif
{
public:
  
  DynamicLib();
  
  std::string const & value();
  
private:
  
  std::string _value;
};
