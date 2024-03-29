from crossview import CrossView
from argparse import ArgumentParser, SUPPRESS
import os
try:
    import readline
except:
    pass # will work without it

# NOTES:
#     This was developed and tested as a demonstration of how to control 
#     the LaCrosse C82929 Projection Clock programmatically.
#     It can set/arm/disarm the alarm, and change the "data stream" choices
#     that cycle on the right top corner of the display.
#     
#     My hope is to see these functions one day integrated into Home Assistant,
#     making it possible to have weather or traffic conditions adjust wake-up
#     time, as one example. The data-stream capabilities are endless, as any
#     measurement or status we have in Home Assistant could be displayed on 
#     the clock. If the HA developers who maintain the LaCrosse View integration
#     don't provide this functionality, I'll probably work on a NodeRED alternative.

# TODO:
#     consider programatic creation of location? device (if it's possible)?
#     support for command/argument syntax, instead of always prompting
#     support for command-line syntax to run one (or multiple?) commands with no prompt
#     provide reverse-engineering features, to try out other parts of the API
#     investigate if the data-streams can be made to change automatically scheduled in the API

class StashedValue:
    def __init__(self, fn, prompt, prefix, opt, lookup=False):
        self.val = None
        self.opt = opt
        self.fn = fn
        self.prompt = prompt
        self.lookup = lookup
        self.var = prefix + opt.upper()

    def get(self, opts=None, ask=False):
        if not self.val and not ask and opts:
            self.val = getattr(opts,self.opt)
            if not self.val and self.var in os.environ:
                self.val = os.environ[self.var]
            if self.val and self.lookup:
                self.val = self.fn(self.prompt, self.val)
        if not self.val or ask:
            self.val = self.fn(self.prompt, None)
        return self.val

    def show(self):
        print(self.prompt + " " + (str(self.val) if self.val else '<none>'))

def parse_cmdline():
    p = ArgumentParser( description='Control a lacrosse WiFi-connected clock without the phone app' )
    p.add_argument('-u', '--user', metavar='USER', help='LaCrosse View username')
    p.add_argument('-p', '--password', metavar='PASS', help='LaCrosse View password')
    p.add_argument('-s', '--device-serial', metavar='AB123C', help='Device serial, for alarm set/show operations')
    p.add_argument('-l', '--location', metavar='HOME', help='Location (set up in the phone app) where to find devices')
    p.add_argument('-d', '--device', metavar='CLOCK', help='Device for data-stream operations')
    p.add_argument('-P', '--prefix', metavar='CV_', default='CV_', help='Prefix for environment variable settings')
    p.add_argument('-i', '--id', metavar='ID', help='datastream id')
    p.add_argument('commands', metavar='"cmd"', nargs='*', help='command(s) to run in non-interactive mode')
    return p.parse_args()

def choose( prompt, what, choices, key, headings = None ):
    if key:
        subset = [ c for c in choices if str(c[0]) == str(key) ]
        if len( subset ) == 1:
            return what[ subset[0][1] - 1 ]

    print( prompt.capitalize()+ "s:" )
    if headings:
       for h in headings: print( h )
    for c in choices: print( c[ 2 ] )
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

def get_cmd_argument( prompt, cmds ):
    if len( cmds ) > 0:
        return( cmds.pop( 0 ) )
    return input( prompt )

def msg( s ):
    return '' if s == ':auto' else s

def get_streams( cv, dev ):
    ds = cv.get_data_streams( dev )
    if isinstance( ds, str ):
        print( ds )
        return False
    return sorted( ds.get( 'cards' ), key=lambda card: -card['weight'] )

def format_streams( streams, index = False ):
    padding = ''
    if index: padding = '         '

    headings = [ padding + f"{'identifier'.ljust(10)} {'enable'.ljust(8)} {'sort key'.ljust(10)} {'message_one'.ljust(20)} {'message_two'.ljust(20)} {'reading'}",
                 padding + f"{'------'.ljust(10,'-')} {'-'.ljust(8,'-')} {'----'.ljust(10,'-')} {'-------'.ljust(20,'-')} {'-------'.ljust(20,'-')} {''.ljust(20,'-')}" ]
    cards = [ [ card['identifier'], 0, f"{str(card['identifier']).ljust(10)} {str(card['enabled?']).ljust(8)} {str(card['weight']).ljust(10)} " + \
              f"{msg(card['message_one']).ljust(20)} {msg(card['message_two']).ljust(20)} {card['reading'] if 'reading' in card else ''}" ]
              for card in streams ]
    for i in range( len( cards ) ): 
        cards[i][1] = i+1
        if index: cards[i][2] = str( i + 1 ).rjust(6) + ' - ' + cards[i][2]
    return { "headings" : headings, "cards" : cards }

def list( cv, dev ):
    streams = get_streams( cv, dev )
    if streams:
        data = format_streams( streams )
        for header in data["headings"]:
            print(header)
        for card in data["cards"]:
            print(card[2])

def catalog( cv ):
    n = 0
    for sub in cv.catalog():
        n += 1
        print( f"    {n} - {sub}" )

def choose_location( cv, name, key ):
    choices = [ [ loc.name, loc.index, f"    {loc.index} - {loc.name}" ] for loc in cv.locations ]
    return choose( 'location', cv.locations, choices, key )

def choose_device( cv, loc, name, key ):
    devices = cv.get_location_devices( loc )
    choices = [ [ d.name, d.index, f"    {d.index} - {d.name} ({d.sensor_type})" ] for d in devices ]
    return choose( 'device', devices, choices, key )

def choose_id( cv, loc, dev, key, type ):
    streams = get_streams( cv, dev )
    if streams:
        data = format_streams( streams, index = True )
        stream = choose( 'id', data["cards"], data["cards"], key, headings = data['headings'] )
        return( str( stream[ 0 ] ) )
    return None

def help():
    print('Options:')
    print('    username        - enter username')
    print('    password        - enter password')
    print('    serial          - enter device serial# (from barcode on C82929 WiFi Projection Alarm Clock)')
    print('    location        - choose a location')
    print('    device          - choose a device')
    print('    id              - choose a data stream identifier')
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
    have_command = len( opts.commands ) > 0
    m1 = "message one: "
    m2 = "message two: "

    dev_serial = StashedValue(lambda prompt, key: input(prompt), "Your device serial: ", opts.prefix, "device_serial")
    username = StashedValue(lambda prompt, key: input(prompt), "Username: ", opts.prefix, "user")
    password = StashedValue(lambda prompt, key: input(prompt), "Password: ", opts.prefix, "password")
    cv = StashedValue(lambda prompt, key: CrossView(username.get(opts), password.get(opts)), "cv: ", opts.prefix, "cv")
    location = StashedValue(lambda prompt, key: choose_location(cv.get(), 'location', key), "Location: ", opts.prefix, "location", lookup=True)
    device = StashedValue(lambda prompt, key: choose_device(cv.get(), location.get(opts), 'device', key), "Device: ", opts.prefix, "device", lookup=True)
    id = StashedValue(lambda prompt, key: choose_id(cv.get(), location.get(opts), device.get(opts), key, 'id'), "ID: ", opts.prefix, "id", lookup=True)

    miscount = 0
    while True:
        if have_command:
            if len( opts.commands ) > 0:
                operation = opts.commands.pop( 0 )
            else:
                return
        else:
            operation = input("> ")
        operation = operation.strip()
        missed = False
        if operation == 'help': help()
        elif operation == 'serial': dev_serial.get(opts,ask=True)
        elif operation == 'username': username.get(opts,ask=True)
        elif operation == 'password': password.get(opts,ask=True)
        elif operation == 'show': print( cv.get().get_alarm( dev_serial.get( opts ) ) )
        elif operation == 'id': id.get(opts,ask=True)
        elif operation == 'set': print( cv.get().set_alarm( dev_serial.get( opts ), get_cmd_argument( "JSON-format alarm data: ", opts.commands ) ) )
        elif operation == 'catalog': catalog( cv.get() )
        elif operation == 'list': list( cv.get(), device.get(opts) )
        elif operation == 'delete': print( cv.get().delete_data_stream( device.get(opts), id.get( opts ) ) )
        elif operation == 'get': print( cv.get().get_single_stream( device.get(opts), id.get( opts ) ) )
        elif operation == 'add': print( cv.get().add_data_stream( device.get(opts), get_cmd_argument( m1, opts.commands ), get_cmd_argument( m2, opts.commands ) ) )
        elif operation == 'replace': print( cv.get().update_data_stream( device.get(opts), id.get( opts ), get_cmd_argument( m1, opts.commands ), get_cmd_argument( m2, opts.commands ) ) )
        elif operation == 'subscribe': print( cv.get().subscribe( device.get(opts), input( "subscription name or number: " ) ) )
        elif operation == 'info':
            dev_serial.show()
            username.show()
            location.show()
            device.show()
        elif operation == 'location':
            dev = None
            location.get(opts, ask=True)
        elif operation == 'device':
            device.get(opts, ask=True)
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
