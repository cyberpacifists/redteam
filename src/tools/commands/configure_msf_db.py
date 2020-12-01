import yaml
import os

from ..settings import DATABASES
from src.tools.models import replace_variables


class Command:
    """
    This command will replace the current configuration of the Metasploit version installed in the image
    the given one, considering the settings
    """
    conf_file = "msf_db_conf.yml"
    filename = "database.yml"
    paths = [
        "/usr/share/metasploit-framework/config/",  # Linux (apk)
        "/opt/metasploit-framework/embedded/framework/config/"  # Mac (brew)
    ]

    @staticmethod
    def grant_perms_temp(filepath, st_mode=None, verbose=False):
        su_mode = "777"

        # store the current access level to the file
        st = str(os.stat(filepath).st_mode)

        print(f'Attempting to change st_mode: {st} -> {st_mode if st_mode else su_mode}')

        # attempt to include the given level to the file
        import subprocess
        chmod_args = ['chmod', st_mode if st_mode else su_mode, filepath]
        sp = subprocess.run(chmod_args, capture_output=True)

        if verbose:
            # print what happens when the attempt finalizes
            print(sp.stdout)

            if sp.stderr:
                print('\n[ERRORS]', sp.stderr)

        return st

    def handle(self):
        conf_file = replace_variables(path=self.conf_file, conf=DATABASES['default'])

        for path_ in self.paths:
            if os.path.exists(path_):
                print(f'[+] Configuration path found: {path_}')

                # add the file to the path
                filepath = path_ + self.filename

                # dump the content of the new configuration into the file, or create the file with the content
                with open(filepath, 'w+') as file:
                    yaml.dump(conf_file, file)
                    print(f'[+] MSF Configuration swapped')

                break
            else:
                print(f'"{path_}" does not exists')


