
#include <string>

#ifdef _WIN32
  #ifdef PLUGIN_EXPORTS
    #define PLUGIN_API __declspec(dllexport) 
  #else
    #define PLUGIN_API __declspec(dllimport) 
  #endif
#endif

class Plugin
{
public:
  
  static creator
  std::string Plugin print();
};

