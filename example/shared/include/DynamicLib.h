
#include <string>

#ifdef _WIN32
  #ifdef DYNAMICLIB_EXPORTS
    #define DYNAMICLIB_API __declspec(dllexport) 
  #else
    #define DYNAMICLIB_API __declspec(dllimport) 
  #endif
#endif

class DynamicLib
{
public:
  
  #ifdef _WIN32
    std::string DYNAMICLIB_API print();
  #else
    std::string print();
  #endif  
};

