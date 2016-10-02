
#include <string>

class Plugin
{
public:
  
  Plugin();
  
  std::string const & value();

private:

  std::string _value;
};
