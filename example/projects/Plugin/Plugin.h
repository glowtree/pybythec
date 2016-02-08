
#include <string>

#ifdef _WIN32
  #ifdef PLUGIN_EXPORTS
    #define PLUGIN __declspec(dllexport) 
  #else
    #define PLUGIN __declspec(dllimport) 
  #endif
#endif

class Plugin
{
public:
  
#ifdef _WIN32
  static void * PLUGIN creator();
  std::string PLUGIN print();
#else
  static void * creator();
  std::string print();
#endif

};

