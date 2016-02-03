
#include <string>

#ifdef DYNAMICLIB_EXPORTS
#define DYNAMICLIB_API __declspec(dllexport) 
#else
#define DYNAMICLIB_API __declspec(dllimport) 
#endif

class DynamicLib
{
public:
  std::string DYNAMICLIB_API print();
};

