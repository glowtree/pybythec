
#include <string>

// #ifdef _WIN32
//   #ifdef DYNAMICLIB_EXPORTS
//     #define DYNAMICLIB __declspec(dllexport) 
//   #else
//     #define DYNAMICLIB __declspec(dllimport) 
//   #endif
// #endif

class DynamicLib
{
public:
  
  // #ifdef _WIN32
  //   std::string DYNAMICLIB print();
  // #else
    std::string print();
  // #endif  
};

