
#include "PluginBase.h"
#include <string>

// #ifdef _WIN32
//   #ifdef PLUGIN_EXPORTS
//     #define PLUGIN __declspec(dllexport) 
//   #else
//     #define PLUGIN __declspec(dllimport) 
//   #endif
// #endif

class Plugin : public PluginBase
{
public:
  
// #ifdef _WIN32
//   static void * PLUGIN creator();
//   std::string PLUGIN print();
// #else
  virtual static Plugin * creator();
  virtual std::string print();
// #endif
};
