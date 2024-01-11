from crossview import CrossView
from argparse import ArgumentParser, SUPPRESS

class StashedValue:
    def __init__(self, fn, prompt, opt=None):
        self.val = None
        self.opt = opt
        self.fn = fn
        self.prompt = prompt

    def get(self, opts=None, force=False):
        if not self.val and not force and opts:
            self.val = getattr(opts,self.opt)
        if not self.val or force:
            self.val = self.fn(self.prompt)
        return self.val

    def show(self):
        print(self.prompt + " " + (str(self.val) if self.val else '<none>'))

def parse_cmdline():
    p = ArgumentParser( description='Control a lacrosse WiFi-connected clock without the phone app' )
    p.add_argument('-u', '--user', metavar='USER', help='LaCrosse View username')
    p.add_argument('-p', '--password', metavar='PASS', help='LaCrosse View password')
    p.add_argument('-d', '--device-serial', metavar='AB123C', help='Device serial, for alarm set/show operations')
#   p.add_argument('-l', '--location', metavar='HOME', help='Preset location')
    return p.parse_args()

def choose( prompt, what, choices ):
    print( prompt.capitalize()+ "s:" )
    for c in choices: print( c )
    print( )
    count = len( what )
    if count == 1: return what[ 0 ]
    index = ''
    while index == '':
        index = input( 'Choose ' + prompt + ': ')
        if index.isnumeric():
            index = int( index )
            if index < 1 or index > count:
                index = ''
        else:
            index = ''
    return what[ index - 1 ]

def get_ds_id( opts ):
    return input("Data stream identifier: ")

def get_alarm_setting():
    return input("JSON-format alarm data: ")

def msg( s ):
    return '' if s == ':auto' else s

def list( cv, dev ):
    ds = cv.get_data_streams( dev )
    if isinstance( ds, str ):
        print( ds )
        return
    print( f"{'identifier'.ljust(10)} {'enable'.ljust(8)} {'sort key'.ljust(10)} {'message_one'.ljust(20)} {'message_two'.ljust(20)} {'reading'}" )
    print( f"{'------'.ljust(10,'-')} {'-'.ljust(8,'-')} {'----'.ljust(10,'-')} {'-------'.ljust(20,'-')} {'-------'.ljust(20,'-')} {''.ljust(20,'-')}" )
    for card in sorted( ds.get( 'cards' ), key=lambda card: -card['weight'] ) :
        print( f"{str(card['identifier']).ljust(10)} {str(card['enabled?']).ljust(8)} {str(card['weight']).ljust(10)} " + \
               f"{msg(card['message_one']).ljust(20)} {msg(card['message_two']).ljust(20)} {card['reading'] if 'reading' in card else ''}" )

def catalog( cv ):
    n = 0
    for sub in cv.catalog():
        n += 1
        print( f"    {n} - {sub}" )

def choose_location( cv ):
    choices = [ f"    {loc.index} - {loc.name}" for loc in cv.locations ]
    return choose( 'location', cv.locations, choices )

def choose_device( cv, loc ):
    devices = cv.get_location_devices( loc )
    choices = [ f"    {d.index} - {d.name} ({d.sensor_type})" for d in devices ]
    return choose( 'device', devices, choices )

def help():
    print('Options:')
    print('    username        - enter username')
    print('    password        - enter password')
    print('    serial          - enter device serial# (from barcode on C82929 WiFi Projection Alarm Clock)')
    print('    location        - choose a location')
    print('    device          - choose a device')
    print('    info            - show current values for user, serial, device and location')
    print('    show            - show alarm')
    print('    set             - set alarm')
    print('    list            - list data streams')
    print('    get             - get single stream')
    print('    add             - add text data stream')
    print('    delete          - delete data stream entry')
    print('    replace         - replace text data stream')
    print('    catalog         - list available weather data stream items')
    print('    subscribe       - add weather data stream')
    print('')
    print("show/set will require your display's device serial#, available from the phone app or printed on your device")

def main():
    opts = parse_cmdline()

    dev_serial = StashedValue(lambda prompt: input(prompt), "Your device serial: ", "device_serial")
    username = StashedValue(lambda prompt: input(prompt), "Username: ", "user")
    password = StashedValue(lambda prompt: input(prompt), "Password: ", "password")
    cv = StashedValue(lambda prompt: CrossView(username.get(opts), password.get(opts)), "cv")
    location = StashedValue(lambda prompt: choose_location(cv.get()), "Location: ")
    device = StashedValue(lambda prompt: choose_device(cv.get(), location.get()), "Device: ")

    miscount = 0
    while True:
        operation = input("> ")
        operation = operation.strip()
        missed = False
        if operation == 'help': help()
        elif operation == 'serial': dev_serial.get(opts,force=True)
        elif operation == 'username': username.get(opts,force=True)
        elif operation == 'password': password.get(opts,force=True)
        elif operation == 'show': print( cv.get().get_alarm( dev_serial.get( opts ) ) )
        elif operation == 'set': print( cv.get().set_alarm( dev_serial.get( opts ), get_alarm_setting() ) )
        elif operation == 'catalog': catalog( cv.get() )
        elif operation == 'list': list( cv.get(), device.get() )
        elif operation == 'delete': print( cv.get().delete_data_stream( device.get(), get_ds_id( opts ) ) )
        elif operation == 'get': print( cv.get().get_single_stream( device.get(), get_ds_id( opts ) ) )
        elif operation == 'add': print( cv.get().add_data_stream( device.get(), input( "message one: " ), input( "message two: " ) ) )
        elif operation == 'replace': print( cv.get().update_data_stream( device.get(), get_ds_id( opts ), input( "message one: " ), input( "message two: " ) ) )
        elif operation == 'subscribe': print( cv.get().subscribe( device.get(), input( "subscription name or number: " ) ) )
        elif operation == 'info':
            dev_serial.show()
            username.show()
            location.show()
            device.show()
        elif operation == 'location':
            dev = None
            location.get()
        elif operation == 'device':
            device.get()
        else:
            missed = True
        if missed:
            miscount += 1
            if miscount == 3:
                print( "Perhaps try 'help'?" )
        elif miscount < 3:
            miscount = 0

if __name__ == "__main__":
    print("Please note: LaCrosse's servers can be quite slow. Timeouts or delays of 10-20s are not uncommon.")
    try:
        main()
    except (EOFError,KeyboardInterrupt):
        pass
