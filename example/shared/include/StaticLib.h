
#include <string>

class StaticLib
{
public:
  
  StaticLib();
  
  std::string const & value();
  
private:
  
  std::string _value;
};
