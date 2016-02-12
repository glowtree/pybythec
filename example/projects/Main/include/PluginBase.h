
#include <string>

class PluginBase
{
public:
  virtual static PluginBase * creator();
  
  virtual std::string print();
};
