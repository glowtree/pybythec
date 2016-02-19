
#include <string>

class DynamicLib
{
public:
  
  DynamicLib();
  
  std::string const & value();
  
private:
  
  std::string _value;
};
