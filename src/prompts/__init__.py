import os

class Prompts:
    _CACHED_MESSAGES = {}
    _ROOT = os.path.abspath(os.path.dirname(__file__))

    def _get_file_path(self, filename):
        return os.path.join(self._ROOT, filename)

    def get_galfit_system_message(self):
        filename = "galfit_system_message.md"    

        if filename in self._CACHED_MESSAGES:
            return self._CACHED_MESSAGES[filename]

        absfile = self._get_file_path(filename)    
        with open(absfile) as f:
            content = f.read().strip()
            self._CACHED_MESSAGES[filename] = content
            return content

    def get_galfits_system_message(self):
        filename = "galfits_system_message.md"    

        if filename in self._CACHED_MESSAGES:
            return self._CACHED_MESSAGES[filename]

        absfile = self._get_file_path(filename)    
        with open(absfile) as f:
            content = f.read().strip()
            self._CACHED_MESSAGES[filename] = content
            return content

    @property
    def GALFIT_SYSTEM_MESSAGE(self):
        return self.get_galfit_system_message()

    @property
    def GALFITS_SYSTEM_MESSAGE(self):
        return self.get_galfits_system_message()

prompts = Prompts()        

if __name__ == '__main__':
    print(prompts.GALFIT_SYSTEM_MESSAGE)
    print(prompts.GALFITS_SYSTEM_MESSAGE)